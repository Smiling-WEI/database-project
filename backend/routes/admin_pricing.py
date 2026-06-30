from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import admin_role_required, role_required
from utils.response import error_response, success_response


admin_pricing_bp = Blueprint(
    "admin_pricing",
    __name__,
    url_prefix="/api/admin",
)


VALID_CABIN_TYPES = {
    "经济舱",
    "头等舱",
}


def is_finished_flight(row):
    if row is None:
        return False

    if row.get("status") in ("已完成", "取消"):
        return True

    arr_time = row.get("arr_time")
    if arr_time is None:
        return False

    return arr_time < datetime.now()


def serialize_pricing(row):
    return {
        "pricingId": row["pricing_id"],
        "instanceId": row["instance_id"],
        "cabinType": row["cabin_type"],
        "salePrice": float(row["sale_price"]),
        "validFrom": row["valid_from"].isoformat(sep=" ", timespec="seconds"),
        "validTo": row["valid_to"].isoformat(sep=" ", timespec="seconds"),
        "isCurrentlyEffective": bool(row["is_currently_effective"]),
    }


def parse_pricing_payload(data, old_pricing=None):
    cabin_type = str(data.get("cabin_type", old_pricing["cabin_type"] if old_pricing else "")).strip()
    sale_price_raw = data.get("sale_price", old_pricing["sale_price"] if old_pricing else None)

    if cabin_type not in VALID_CABIN_TYPES:
        return None, error_response("舱位类型不合法")

    try:
        sale_price = Decimal(str(sale_price_raw))
    except (InvalidOperation, ValueError):
        return None, error_response("票价格式不正确")

    if sale_price <= 0:
        return None, error_response("票价必须大于 0")

    valid_from_text = str(
        data.get(
            "valid_from",
            old_pricing["valid_from"].isoformat(sep=" ", timespec="seconds") if old_pricing else "",
        )
    ).strip()

    valid_to_text = str(
        data.get(
            "valid_to",
            old_pricing["valid_to"].isoformat(sep=" ", timespec="seconds") if old_pricing else "",
        )
    ).strip()

    try:
        valid_from = datetime.fromisoformat(valid_from_text)
        valid_to = datetime.fromisoformat(valid_to_text)
    except ValueError:
        return None, error_response("价格生效时间格式不正确")

    if valid_to <= valid_from:
        return None, error_response("价格失效时间必须晚于生效时间")

    return {
        "cabin_type": cabin_type,
        "sale_price": sale_price,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }, None


def get_managed_flight(cursor, instance_id, lock=False):
    lock_clause = "FOR UPDATE" if lock else ""

    cursor.execute(
        f"""
        SELECT
            fi.instance_id,
            fi.flight_no,
            fi.flight_date,
            fi.dep_time,
            fi.arr_time,
            fi.status
        FROM flight_instance AS fi
        JOIN flight_no_info AS fni
          ON fni.flight_no = fi.flight_no
        WHERE fi.instance_id = %s
          AND fni.airline_id = %s
        {lock_clause}
        """,
        (
            instance_id,
            g.current_user["airline_id"],
        ),
    )

    return cursor.fetchone()


def _can_write_flight_module():
    role = g.current_user.get("role")
    admin_role = g.current_user.get("admin_role")

    return (
        role in ("系统总管理员", "平台总管理员", "总管理员")
        or admin_role in ("系统总管理员", "平台总管理员", "总管理员", "航司主管理员", "航班管理员")
    )


def _require_flight_write_permission():
    if not _can_write_flight_module():
        return error_response("当前岗位仅可查看航班相关信息，无权新增、编辑、修改票价或发布异常", 403)

    return None



def _forbid_order_admin_write_pricing():
    current_user = getattr(g, "current_user", {}) or {}
    admin_role = current_user.get("admin_role")

    if admin_role == "订单管理员":
        return error_response("当前岗位仅可查看舱位票价，无权新增或修改票价", 403)

    return None


@admin_pricing_bp.post("/flights/<int:instance_id>/cabins")
@admin_role_required("航司主管理员", "航班管理员")
def create_cabin_pricing(instance_id):
    pricing_permission_error = _forbid_order_admin_write_pricing()
    if pricing_permission_error is not None:
        return pricing_permission_error
    permission_error = _require_flight_write_permission()
    if permission_error is not None:
        return permission_error
    """为当前航司未结束航班新增一段时间内生效的舱位价格。"""
    data = request.get_json(silent=True) or {}

    parsed, error = parse_pricing_payload(data)
    if error:
        return error

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            flight = get_managed_flight(cursor, instance_id, lock=True)

            if flight is None:
                return error_response("未找到本航司的该航班", 404)

            if is_finished_flight(flight):
                return error_response("该航班已结束或已取消，不能新增舱位价格", 409)

            if parsed["valid_to"] > flight["dep_time"]:
                return error_response("价格失效时间不能晚于航班起飞时间")

            cursor.execute(
                """
                SELECT pricing_id
                FROM cabin_pricing
                WHERE instance_id = %s
                  AND cabin_type = %s
                  AND valid_from < %s
                  AND valid_to > %s
                LIMIT 1
                """,
                (
                    instance_id,
                    parsed["cabin_type"],
                    parsed["valid_to"],
                    parsed["valid_from"],
                ),
            )

            if cursor.fetchone() is not None:
                return error_response("该时间段与已有价格重叠", 409)

            cursor.execute(
                """
                INSERT INTO cabin_pricing (
                    instance_id,
                    cabin_type,
                    sale_price,
                    valid_from,
                    valid_to
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    instance_id,
                    parsed["cabin_type"],
                    parsed["sale_price"],
                    parsed["valid_from"],
                    parsed["valid_to"],
                ),
            )

            pricing_id = cursor.lastrowid

        connection.commit()

        return success_response(
            {
                "pricingId": pricing_id,
                "instanceId": instance_id,
                "cabinType": parsed["cabin_type"],
                "salePrice": float(parsed["sale_price"]),
                "validFrom": parsed["valid_from"].isoformat(sep=" ", timespec="seconds"),
                "validTo": parsed["valid_to"].isoformat(sep=" ", timespec="seconds"),
            },
            "舱位价格新增成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("舱位价格新增失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_pricing_bp.get("/flights/<int:instance_id>/cabins")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def get_flight_cabins(instance_id):
    """查询指定航班实例的舱位票价。

    系统总管理员可查看任意航司；
    航司内部管理员只能查看本航司。
    """
    connection = None

    is_system_admin = (
        g.current_user.get("role") in ("系统总管理员", "平台总管理员", "总管理员")
        or g.current_user.get("admin_role") in ("系统总管理员", "平台总管理员", "总管理员")
    )

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            conditions = ["fi.instance_id = %s"]
            parameters = [instance_id]

            if not is_system_admin:
                airline_id = g.current_user.get("airline_id")

                if airline_id is None:
                    return error_response("当前管理员未绑定航空公司", 403)

                conditions.append("fni.airline_id = %s")
                parameters.append(airline_id)

            where_clause = " AND ".join(conditions)

            cursor.execute(
                f"""
                SELECT
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    fi.dep_time,
                    fi.arr_time,
                    fi.aircraft_model,
                    fi.first_seats,
                    fi.economy_seats,
                    fi.status,
                    fni.airline_id,
                    ac.airline_name,
                    dep.airport_name AS dep_airport_name,
                    arr.airport_name AS arr_airport_name
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                JOIN airline_company AS ac
                  ON ac.airline_id = fni.airline_id
                JOIN route AS r
                  ON r.route_id = fni.route_id
                JOIN airport AS dep
                  ON dep.airport_code = r.dep_airport_code
                JOIN airport AS arr
                  ON arr.airport_code = r.arr_airport_code
                WHERE {where_clause}
                LIMIT 1
                """,
                tuple(parameters),
            )

            flight = cursor.fetchone()

            if flight is None:
                return error_response("未找到该航班", 404)

            cursor.execute(
                """
                SELECT
                    cp.pricing_id,
                    cp.instance_id,
                    cp.cabin_type,
                    cp.sale_price,
                    cp.valid_from,
                    cp.valid_to,
                    (
                        CASE
                            WHEN cp.cabin_type = '头等舱' THEN fi.first_seats
                            ELSE fi.economy_seats
                        END
                        -
                        (
                            SELECT COUNT(*)
                            FROM active_ticket_sale AS ats
                            WHERE ats.instance_id = cp.instance_id
                              AND ats.pricing_id = cp.pricing_id
                        )
                    ) AS remaining_tickets
                FROM cabin_pricing AS cp
                JOIN flight_instance AS fi
                  ON fi.instance_id = cp.instance_id
                WHERE cp.instance_id = %s
                ORDER BY
                    CASE cp.cabin_type
                        WHEN '头等舱' THEN 1
                        WHEN '经济舱' THEN 2
                        ELSE 9
                    END,
                    cp.pricing_id
                """,
                (instance_id,),
            )

            rows = cursor.fetchall()

        cabins = []

        for row in rows:
            cabins.append(
                {
                    "pricingId": row["pricing_id"],
                    "pricing_id": row["pricing_id"],
                    "instanceId": row["instance_id"],
                    "instance_id": row["instance_id"],
                    "cabinType": row["cabin_type"],
                    "cabin_type": row["cabin_type"],
                    "salePrice": float(row["sale_price"] or 0),
                    "sale_price": float(row["sale_price"] or 0),
                    "remainingTickets": row["remaining_tickets"],
                    "remaining_tickets": row["remaining_tickets"],
                    "validFrom": row["valid_from"].isoformat(sep=" ", timespec="seconds"),
                    "valid_from": row["valid_from"].isoformat(sep=" ", timespec="seconds"),
                    "validTo": row["valid_to"].isoformat(sep=" ", timespec="seconds"),
                    "valid_to": row["valid_to"].isoformat(sep=" ", timespec="seconds"),
                }
            )

        data = {
            "flight": {
                "instanceId": flight["instance_id"],
                "instance_id": flight["instance_id"],
                "flightNo": flight["flight_no"],
                "flight_no": flight["flight_no"],
                "flightDate": flight["flight_date"].isoformat(),
                "flight_date": flight["flight_date"].isoformat(),
                "depTime": flight["dep_time"].isoformat(sep=" ", timespec="seconds"),
                "arrTime": flight["arr_time"].isoformat(sep=" ", timespec="seconds"),
                "aircraftModel": flight["aircraft_model"],
                "firstSeats": flight["first_seats"],
                "economySeats": flight["economy_seats"],
                "status": flight["status"],
                "airlineId": flight["airline_id"],
                "airlineName": flight["airline_name"],
                "depAirportName": flight["dep_airport_name"],
                "arrAirportName": flight["arr_airport_name"],
            },
            "cabins": cabins,
            "items": cabins,
            "list": cabins,
        }

        return success_response(data, "查询成功")

    except Exception as error:
        return error_response("舱位票价查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_pricing_bp.put("/cabins/<int:pricing_id>")
@admin_role_required("航司主管理员", "航班管理员")
def update_cabin_pricing(pricing_id):
    pricing_permission_error = _forbid_order_admin_write_pricing()
    if pricing_permission_error is not None:
        return pricing_permission_error
    permission_error = _require_flight_write_permission()
    if permission_error is not None:
        return permission_error
    """修改当前航司未结束航班的舱位价格记录。"""
    data = request.get_json(silent=True) or {}

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    cp.pricing_id,
                    cp.instance_id,
                    cp.cabin_type,
                    cp.sale_price,
                    cp.valid_from,
                    cp.valid_to,
                    fi.dep_time,
                    fi.arr_time,
                    fi.status
                FROM cabin_pricing AS cp
                JOIN flight_instance AS fi
                  ON fi.instance_id = cp.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE cp.pricing_id = %s
                  AND fni.airline_id = %s
                FOR UPDATE
                """,
                (
                    pricing_id,
                    g.current_user["airline_id"],
                ),
            )

            pricing = cursor.fetchone()

            if pricing is None:
                return error_response("未找到本航司的该舱位价格", 404)

            if is_finished_flight(pricing):
                return error_response("该航班已结束或已取消，不能修改舱位价格", 409)

            parsed, error = parse_pricing_payload(data, old_pricing=pricing)
            if error:
                return error

            if parsed["valid_to"] > pricing["dep_time"]:
                return error_response("价格失效时间不能晚于航班起飞时间")

            cursor.execute(
                """
                SELECT pricing_id
                FROM cabin_pricing
                WHERE instance_id = %s
                  AND cabin_type = %s
                  AND pricing_id <> %s
                  AND valid_from < %s
                  AND valid_to > %s
                LIMIT 1
                """,
                (
                    pricing["instance_id"],
                    parsed["cabin_type"],
                    pricing_id,
                    parsed["valid_to"],
                    parsed["valid_from"],
                ),
            )

            if cursor.fetchone() is not None:
                return error_response("修改后的时间段与已有价格重叠", 409)

            cursor.execute(
                """
                UPDATE cabin_pricing
                SET cabin_type = %s,
                    sale_price = %s,
                    valid_from = %s,
                    valid_to = %s
                WHERE pricing_id = %s
                """,
                (
                    parsed["cabin_type"],
                    parsed["sale_price"],
                    parsed["valid_from"],
                    parsed["valid_to"],
                    pricing_id,
                ),
            )

        connection.commit()

        return success_response(
            {
                "pricingId": pricing_id,
                "instanceId": pricing["instance_id"],
                "cabinType": parsed["cabin_type"],
                "salePrice": float(parsed["sale_price"]),
                "validFrom": parsed["valid_from"].isoformat(sep=" ", timespec="seconds"),
                "validTo": parsed["valid_to"].isoformat(sep=" ", timespec="seconds"),
            },
            "舱位价格修改成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("舱位价格修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
