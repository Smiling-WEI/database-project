from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import admin_role_required, role_required
from utils.response import error_response, success_response
from datetime import date

admin_flight_bp = Blueprint(
    "admin_flight",
    __name__,
    url_prefix="/api/admin",
)


@admin_flight_bp.get("/flights")
@role_required("航空公司管理员")
def list_managed_flights():
    """查询当前航司管理员所属航空公司的航班。"""
    flight_date = str(request.args.get("date", "")).strip()
    status = str(request.args.get("status", "")).strip()

    conditions = [
        "fni.airline_id = %s",
    ]

    parameters = [
        g.current_user["airline_id"],
    ]

    if flight_date:
        conditions.append("fi.flight_date = %s")
        parameters.append(flight_date)

    if status:
        conditions.append("fi.status = %s")
        parameters.append(status)

    where_clause = " AND ".join(conditions)

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    fi.aircraft_model,
                    fi.first_seats,
                    fi.economy_seats,
                    fi.status,
                    ac.airline_name,
                    dep_airport.airport_name AS dep_airport,
                    arr_airport.airport_name AS arr_airport
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                JOIN airline_company AS ac
                  ON ac.airline_id = fni.airline_id
                JOIN route AS r
                  ON r.route_id = fni.route_id
                JOIN airport AS dep_airport
                  ON dep_airport.airport_code = r.dep_airport_code
                JOIN airport AS arr_airport
                  ON arr_airport.airport_code = r.arr_airport_code
                WHERE {where_clause}
                ORDER BY fi.flight_date, fi.flight_no
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        flights = [
            {
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "aircraftModel": row["aircraft_model"],
                "firstSeats": row["first_seats"],
                "economySeats": row["economy_seats"],
                "status": row["status"],
                "airlineName": row["airline_name"],
                "depAirport": row["dep_airport"],
                "arrAirport": row["arr_airport"],
            }
            for row in rows
        ]

        return success_response(flights, "查询成功")

    except Exception as error:
        return error_response("航司航班查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_flight_bp.get("/flights/<int:instance_id>")
@role_required("航空公司管理员")
def get_managed_flight_detail(instance_id):
    """查询当前航司管理员有权限查看的单个航班实例。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    fi.aircraft_model,
                    fi.first_seats,
                    fi.economy_seats,
                    fi.status,
                    ac.airline_name,
                    dep_airport.airport_name AS dep_airport,
                    arr_airport.airport_name AS arr_airport
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                JOIN airline_company AS ac
                  ON ac.airline_id = fni.airline_id
                JOIN route AS r
                  ON r.route_id = fni.route_id
                JOIN airport AS dep_airport
                  ON dep_airport.airport_code = r.dep_airport_code
                JOIN airport AS arr_airport
                  ON arr_airport.airport_code = r.arr_airport_code
                WHERE fi.instance_id = %s
                  AND fni.airline_id = %s
                LIMIT 1
                """,
                (
                    instance_id,
                    g.current_user["airline_id"],
                ),
            )

            row = cursor.fetchone()

        if row is None:
            return error_response("未找到本航司的该航班", 404)

        return success_response(
            {
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "aircraftModel": row["aircraft_model"],
                "firstSeats": row["first_seats"],
                "economySeats": row["economy_seats"],
                "status": row["status"],
                "airlineName": row["airline_name"],
                "depAirport": row["dep_airport"],
                "arrAirport": row["arr_airport"],
            },
            "查询成功",
        )

    except Exception as error:
        return error_response("航班详情查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_flight_bp.put("/flights/<int:instance_id>")
@admin_role_required("航司主管理员", "航班管理员")
def update_managed_flight(instance_id):
    """修改当前航司所属的航班实例。"""
    data = request.get_json(silent=True) or {}

    allowed_statuses = {"正常", "延误", "取消", "已完成"}

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    fi.instance_id,
                    fi.aircraft_model,
                    fi.first_seats,
                    fi.economy_seats,
                    fi.status
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE fi.instance_id = %s
                  AND fni.airline_id = %s
                FOR UPDATE
                """,
                (
                    instance_id,
                    g.current_user["airline_id"],
                ),
            )

            flight = cursor.fetchone()

            if flight is None:
                return error_response("未找到本航司的该航班", 404)

            aircraft_model = str(
                data.get("aircraft_model", flight["aircraft_model"])
            ).strip()

            first_seats = data.get(
                "first_seats",
                flight["first_seats"],
            )

            economy_seats = data.get(
                "economy_seats",
                flight["economy_seats"],
            )

            status = str(
                data.get("status", flight["status"])
            ).strip()

            if not aircraft_model:
                return error_response("执飞机型不能为空")

            if type(first_seats) is not int or first_seats < 0:
                return error_response("头等舱座位数必须为非负整数")

            if type(economy_seats) is not int or economy_seats < 0:
                return error_response("经济舱座位数必须为非负整数")

            if status not in allowed_statuses:
                return error_response("航班状态不合法")

            cursor.execute(
                """
                SELECT
                    SUM(
                        CASE
                            WHEN cp.cabin_type = '头等舱' THEN 1
                            ELSE 0
                        END
                    ) AS sold_first_seats,
                    SUM(
                        CASE
                            WHEN cp.cabin_type = '经济舱' THEN 1
                            ELSE 0
                        END
                    ) AS sold_economy_seats
                FROM active_ticket_sale AS ats
                JOIN cabin_pricing AS cp
                  ON cp.pricing_id = ats.pricing_id
                WHERE ats.instance_id = %s
                  AND ats.order_status = '已支付'
                """,
                (instance_id,),
            )

            sold = cursor.fetchone()

            sold_first_seats = sold["sold_first_seats"] or 0
            sold_economy_seats = sold["sold_economy_seats"] or 0

            if first_seats < sold_first_seats:
                return error_response("头等舱座位数不能少于已售票数量", 409)

            if economy_seats < sold_economy_seats:
                return error_response("经济舱座位数不能少于已售票数量", 409)

            cursor.execute(
                """
                UPDATE flight_instance
                SET aircraft_model = %s,
                    first_seats = %s,
                    economy_seats = %s,
                    status = %s
                WHERE instance_id = %s
                """,
                (
                    aircraft_model,
                    first_seats,
                    economy_seats,
                    status,
                    instance_id,
                ),
            )

        connection.commit()

        return success_response(
            {
                "instanceId": instance_id,
                "aircraftModel": aircraft_model,
                "firstSeats": first_seats,
                "economySeats": economy_seats,
                "status": status,
            },
            "航班修改成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("航班修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_flight_bp.post("/flights/<int:instance_id>/irregularities")
@admin_role_required("航司主管理员", "航班管理员")
def publish_flight_irregularity(instance_id):
    """发布本航司航班的延误、取消或航班调整通知。"""
    data = request.get_json(silent=True) or {}

    irregularity_type = str(
        data.get("irregularity_type", "")
    ).strip()

    responsibility_type = str(
        data.get("responsibility_type", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip() or None

    allowed_irregularity_types = {
        "延误",
        "取消",
        "航班调整",
    }

    allowed_responsibility_types = {
        "航司原因",
        "天气原因",
        "其他原因",
    }

    if irregularity_type not in allowed_irregularity_types:
        return error_response("异常类型不合法")

    if responsibility_type not in allowed_responsibility_types:
        return error_response("责任类型不合法")

    if description is not None and len(description) > 500:
        return error_response("异常说明不能超过 500 个字符")

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
                FOR UPDATE
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
                INSERT INTO flight_irregularity (
                    instance_id,
                    irregularity_type,
                    responsibility_type,
                    description,
                    published_by,
                    status,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, '生效中', NOW())
                """,
                (
                    instance_id,
                    irregularity_type,
                    responsibility_type,
                    description,
                    g.current_user["user_id"],
                ),
            )

            irregularity_id = cursor.lastrowid

            if irregularity_type in ("延误", "取消"):
                cursor.execute(
                    """
                    UPDATE flight_instance
                    SET status = %s
                    WHERE instance_id = %s
                    """,
                    (
                        irregularity_type,
                        instance_id,
                    ),
                )

        connection.commit()

        return success_response(
            {
                "irregularityId": irregularity_id,
                "instanceId": instance_id,
                "irregularityType": irregularity_type,
                "responsibilityType": responsibility_type,
                "description": description,
                "status": "生效中",
            },
            "航班异常发布成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("航班异常发布失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_flight_bp.get("/flights/<int:instance_id>/irregularities")
@role_required("航空公司管理员")
def list_flight_irregularities(instance_id):
    """查询本航司指定航班的异常记录。"""
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
                    irregularity_id,
                    instance_id,
                    irregularity_type,
                    responsibility_type,
                    description,
                    published_by,
                    status,
                    created_at,
                    resolved_at
                FROM flight_irregularity
                WHERE instance_id = %s
                ORDER BY created_at DESC, irregularity_id DESC
                """,
                (instance_id,),
            )

            rows = cursor.fetchall()

        irregularities = [
            {
                "irregularityId": row["irregularity_id"],
                "instanceId": row["instance_id"],
                "irregularityType": row["irregularity_type"],
                "responsibilityType": row["responsibility_type"],
                "description": row["description"],
                "publishedBy": row["published_by"],
                "status": row["status"],
                "createdAt": row["created_at"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "resolvedAt": (
                    row["resolved_at"].isoformat(
                        sep=" ",
                        timespec="seconds",
                    )
                    if row["resolved_at"] is not None
                    else None
                ),
            }
            for row in rows
        ]

        return success_response(irregularities, "查询成功")

    except Exception as error:
        return error_response("航班异常记录查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_flight_bp.put("/irregularities/<int:irregularity_id>/resolve")
@admin_role_required("航司主管理员", "航班管理员")
def resolve_flight_irregularity(irregularity_id):
    """解除本航司发布的航班异常记录。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    fir.irregularity_id,
                    fir.instance_id,
                    fir.status
                FROM flight_irregularity AS fir
                JOIN flight_instance AS fi
                  ON fi.instance_id = fir.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE fir.irregularity_id = %s
                  AND fni.airline_id = %s
                FOR UPDATE
                """,
                (
                    irregularity_id,
                    g.current_user["airline_id"],
                ),
            )

            irregularity = cursor.fetchone()

            if irregularity is None:
                return error_response("未找到本航司的该异常记录", 404)

            if irregularity["status"] == "已解除":
                return error_response("该异常记录已经解除", 409)

            cursor.execute(
                """
                UPDATE flight_irregularity
                SET status = '已解除',
                    resolved_at = NOW()
                WHERE irregularity_id = %s
                """,
                (irregularity_id,),
            )

            cursor.execute(
                """
                SELECT 1
                FROM flight_irregularity
                WHERE instance_id = %s
                  AND status = '生效中'
                LIMIT 1
                """,
                (irregularity["instance_id"],),
            )

            has_active_irregularity = cursor.fetchone() is not None

            if not has_active_irregularity:
                cursor.execute(
                    """
                    UPDATE flight_instance
                    SET status = '正常'
                    WHERE instance_id = %s
                    """,
                    (irregularity["instance_id"],),
                )

        connection.commit()

        return success_response(
            {
                "irregularityId": irregularity_id,
                "instanceId": irregularity["instance_id"],
                "status": "已解除",
            },
            "航班异常已解除",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("航班异常解除失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_flight_bp.post("/flights")
@admin_role_required("航司主管理员", "航班管理员")
def create_managed_flight():
    """为当前航司新增一个具体日期的航班实例。"""
    data = request.get_json(silent=True) or {}

    flight_no = str(data.get("flight_no", "")).strip()
    flight_date_text = str(data.get("flight_date", "")).strip()
    aircraft_model = str(data.get("aircraft_model", "")).strip()
    first_seats = data.get("first_seats")
    economy_seats = data.get("economy_seats")
    status = str(data.get("status", "正常")).strip()

    if not flight_no:
        return error_response("航班号不能为空")

    try:
        flight_date_value = date.fromisoformat(flight_date_text)
    except ValueError:
        return error_response("航班日期格式应为 YYYY-MM-DD")

    if not aircraft_model:
        return error_response("执飞机型不能为空")

    if type(first_seats) is not int or first_seats < 0:
        return error_response("头等舱座位数必须为非负整数")

    if type(economy_seats) is not int or economy_seats < 0:
        return error_response("经济舱座位数必须为非负整数")

    if status not in {"正常", "延误", "取消", "已完成"}:
        return error_response("航班状态不合法")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT flight_no
                FROM flight_no_info
                WHERE flight_no = %s
                  AND airline_id = %s
                LIMIT 1
                """,
                (
                    flight_no,
                    g.current_user["airline_id"],
                ),
            )

            if cursor.fetchone() is None:
                return error_response("该航班号不存在或不属于当前航司", 404)

            cursor.execute(
                """
                SELECT instance_id
                FROM flight_instance
                WHERE flight_no = %s
                  AND flight_date = %s
                LIMIT 1
                """,
                (
                    flight_no,
                    flight_date_value,
                ),
            )

            if cursor.fetchone() is not None:
                return error_response("该日期已经存在对应航班实例", 409)

            cursor.execute(
                """
                INSERT INTO flight_instance (
                    flight_no,
                    flight_date,
                    aircraft_model,
                    first_seats,
                    economy_seats,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    flight_no,
                    flight_date_value,
                    aircraft_model,
                    first_seats,
                    economy_seats,
                    status,
                ),
            )

            instance_id = cursor.lastrowid

        connection.commit()

        return success_response(
            {
                "instanceId": instance_id,
                "flightNo": flight_no,
                "flightDate": flight_date_value.isoformat(),
                "aircraftModel": aircraft_model,
                "firstSeats": first_seats,
                "economySeats": economy_seats,
                "status": status,
            },
            "航班新增成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("航班新增失败", 500, error)

    finally:
        if connection is not None:
            connection.close()