from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import role_required
from utils.response import error_response, success_response


admin_pricing_bp = Blueprint(
    "admin_pricing",
    __name__,
    url_prefix="/api/admin",
)


@admin_pricing_bp.post("/flights/<int:instance_id>/cabins")
@role_required("航空公司管理员")
def create_cabin_pricing(instance_id):
    """为当前航司的指定航班新增一段时间内生效的舱位价格。"""
    data = request.get_json(silent=True) or {}

    cabin_type = str(data.get("cabin_type", "")).strip()
    sale_price_raw = data.get("sale_price")
    valid_from_text = str(data.get("valid_from", "")).strip()
    valid_to_text = str(data.get("valid_to", "")).strip()

    if cabin_type not in {"经济舱", "头等舱"}:
        return error_response("舱位类型不合法")

    try:
        sale_price = Decimal(str(sale_price_raw))
    except (InvalidOperation, ValueError):
        return error_response("票价格式不正确")

    if sale_price <= 0:
        return error_response("票价必须大于 0")

    try:
        valid_from = datetime.fromisoformat(valid_from_text)
        valid_to = datetime.fromisoformat(valid_to_text)
    except ValueError:
        return error_response("价格生效时间格式不正确")

    if valid_to <= valid_from:
        return error_response("价格失效时间必须晚于生效时间")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT fi.instance_id
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE fi.instance_id = %s
                  AND fni.airline_id = %s
                LIMIT 1
                """,
                (
                    instance_id,
                    g.current_user["airline_id"],
                ),
            )

            if cursor.fetchone() is None:
                return error_response("未找到本航司的该航班", 404)

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
                    cabin_type,
                    valid_to,
                    valid_from,
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
                    cabin_type,
                    sale_price,
                    valid_from,
                    valid_to,
                ),
            )

            pricing_id = cursor.lastrowid

        connection.commit()

        return success_response(
            {
                "pricingId": pricing_id,
                "instanceId": instance_id,
                "cabinType": cabin_type,
                "salePrice": float(sale_price),
                "validFrom": valid_from.isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "validTo": valid_to.isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
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
@role_required("航空公司管理员")
def list_cabin_pricing(instance_id):
    """查询本航司指定航班的全部舱位价格记录。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT fi.instance_id
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE fi.instance_id = %s
                  AND fni.airline_id = %s
                LIMIT 1
                """,
                (
                    instance_id,
                    g.current_user["airline_id"],
                ),
            )

            if cursor.fetchone() is None:
                return error_response("未找到本航司的该航班", 404)

            cursor.execute(
                """
                SELECT
                    pricing_id,
                    instance_id,
                    cabin_type,
                    sale_price,
                    valid_from,
                    valid_to,
                    NOW() BETWEEN valid_from AND valid_to AS is_currently_effective
                FROM cabin_pricing
                WHERE instance_id = %s
                ORDER BY cabin_type, valid_from DESC, pricing_id DESC
                """,
                (instance_id,),
            )

            rows = cursor.fetchall()

        pricing_list = [
            {
                "pricingId": row["pricing_id"],
                "instanceId": row["instance_id"],
                "cabinType": row["cabin_type"],
                "salePrice": float(row["sale_price"]),
                "validFrom": row["valid_from"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "validTo": row["valid_to"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "isCurrentlyEffective": bool(
                    row["is_currently_effective"]
                ),
            }
            for row in rows
        ]

        return success_response(pricing_list, "查询成功")

    except Exception as error:
        return error_response("舱位价格查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_pricing_bp.put("/cabins/<int:pricing_id>")
@role_required("航空公司管理员")
def update_cabin_pricing(pricing_id):
    """修改当前航司已有的舱位价格记录。"""
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
                    cp.valid_to
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

            cabin_type = str(
                data.get("cabin_type", pricing["cabin_type"])
            ).strip()

            sale_price_raw = data.get(
                "sale_price",
                pricing["sale_price"],
            )

            valid_from_text = str(
                data.get(
                    "valid_from",
                    pricing["valid_from"].isoformat(
                        sep=" ",
                        timespec="seconds",
                    ),
                )
            ).strip()

            valid_to_text = str(
                data.get(
                    "valid_to",
                    pricing["valid_to"].isoformat(
                        sep=" ",
                        timespec="seconds",
                    ),
                )
            ).strip()

            if cabin_type not in {"经济舱", "头等舱"}:
                return error_response("舱位类型不合法")

            try:
                sale_price = Decimal(str(sale_price_raw))
            except (InvalidOperation, ValueError):
                return error_response("票价格式不正确")

            if sale_price <= 0:
                return error_response("票价必须大于 0")

            try:
                valid_from = datetime.fromisoformat(valid_from_text)
                valid_to = datetime.fromisoformat(valid_to_text)
            except ValueError:
                return error_response("价格生效时间格式不正确")

            if valid_to <= valid_from:
                return error_response("价格失效时间必须晚于生效时间")

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
                    cabin_type,
                    pricing_id,
                    valid_to,
                    valid_from,
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
                    cabin_type,
                    sale_price,
                    valid_from,
                    valid_to,
                    pricing_id,
                ),
            )

        connection.commit()

        return success_response(
            {
                "pricingId": pricing_id,
                "instanceId": pricing["instance_id"],
                "cabinType": cabin_type,
                "salePrice": float(sale_price),
                "validFrom": valid_from.isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "validTo": valid_to.isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
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