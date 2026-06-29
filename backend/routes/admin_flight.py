from datetime import date, datetime, timedelta

from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import admin_role_required, role_required
from utils.response import error_response, success_response


admin_flight_bp = Blueprint(
    "admin_flight",
    __name__,
    url_prefix="/api/admin",
)


def format_time_value(value):
    """将数据库中的 TIME/DATETIME 转成 HH:mm。"""
    if value is None:
        return ""

    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")

    text = str(value).strip()
    return text[:5] if len(text) >= 5 else text


def normalize_time_text(value, field_name, fallback=None):
    """校验并标准化前端传入的 HH:mm 时间。"""
    if value is None or str(value).strip() == "":
        if fallback is not None:
            fallback_text = format_time_value(fallback)
            if fallback_text:
                return fallback_text + ":00"
        raise ValueError(f"{field_name}不能为空")

    text = str(value).strip()
    if len(text) == 5:
        text = text + ":00"

    try:
        datetime.strptime(text, "%H:%M:%S")
    except ValueError as exc:
        raise ValueError(f"{field_name}格式应为 HH:mm") from exc

    return text


def get_flight_time_column_kind(cursor):
    """兼容 dep_time/arr_time 为 TIME 或 DATETIME 两种表结构。"""
    cursor.execute("SHOW COLUMNS FROM flight_instance LIKE 'dep_time'")
    row = cursor.fetchone()

    if row is None:
        return "datetime"

    column_type = str(row.get("Type", "")).lower()
    if column_type.startswith("time"):
        return "time"

    return "datetime"


def build_flight_time_values(
    flight_date_value,
    dep_time_text,
    arr_time_text,
    column_kind,
    fallback_dep_time=None,
    fallback_arr_time=None,
):
    dep_text = normalize_time_text(dep_time_text, "起飞时间", fallback_dep_time)
    arr_text = normalize_time_text(arr_time_text, "到达时间", fallback_arr_time)

    if column_kind == "time":
        return dep_text, arr_text

    dep_clock = datetime.strptime(dep_text, "%H:%M:%S").time()
    arr_clock = datetime.strptime(arr_text, "%H:%M:%S").time()

    base_date = flight_date_value.date() if hasattr(flight_date_value, "date") and not isinstance(flight_date_value, date) else flight_date_value

    dep_datetime = datetime.combine(base_date, dep_clock)
    arr_datetime = datetime.combine(base_date, arr_clock)

    if arr_datetime <= dep_datetime:
        arr_datetime = arr_datetime + timedelta(days=1)

    return dep_datetime, arr_datetime


def format_flight_row(row):
    return {
        "instanceId": row["instance_id"],
        "flightNo": row["flight_no"],
        "flightDate": row["flight_date"].isoformat(),
        "depTime": format_time_value(row["dep_time"]),
        "arrTime": format_time_value(row["arr_time"]),
        "routeId": row["route_id"],
        "aircraftModel": row["aircraft_model"],
        "firstSeats": row["first_seats"],
        "economySeats": row["economy_seats"],
        "status": row["status"],
        "airlineName": row["airline_name"],
        "depAirport": row["dep_airport"],
        "arrAirport": row["arr_airport"],
    }


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


@admin_flight_bp.get("/routes")
@role_required("航司管理员", "航空公司管理员", "系统总管理员")
def list_routes_for_flight_create():
    """查询可用于新增航班号的航线。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    r.route_id,
                    r.dep_airport_code,
                    r.arr_airport_code,
                    r.stop_airport_code,
                    dep.airport_name AS dep_airport_name,
                    dep.city_name AS dep_city_name,
                    arr.airport_name AS arr_airport_name,
                    arr.city_name AS arr_city_name
                FROM route AS r
                JOIN airport AS dep
                  ON dep.airport_code = r.dep_airport_code
                JOIN airport AS arr
                  ON arr.airport_code = r.arr_airport_code
                ORDER BY r.route_id
                """
            )

            rows = cursor.fetchall()

        routes = [
            {
                "routeId": row["route_id"],
                "depAirportCode": row["dep_airport_code"],
                "arrAirportCode": row["arr_airport_code"],
                "stopAirportCode": row["stop_airport_code"],
                "depAirportName": row["dep_airport_name"],
                "arrAirportName": row["arr_airport_name"],
                "depCityName": row["dep_city_name"],
                "arrCityName": row["arr_city_name"],
                "routeLabel": f'{row["dep_city_name"]}({row["dep_airport_code"]}) → {row["arr_city_name"]}({row["arr_airport_code"]})',
            }
            for row in rows
        ]

        return success_response(routes, "查询成功")

    except Exception as error:
        return error_response("航线列表查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_flight_bp.get("/flights")
@role_required("航司管理员", "航空公司管理员", "系统总管理员")
def list_managed_flights():
    """查询当前航司管理员所属航空公司的航班。"""
    flight_date = str(request.args.get("date", "")).strip()
    status = str(request.args.get("status", "")).strip()

    conditions = []
    parameters = []

    if g.current_user["role"] != "系统总管理员":
        conditions.append("fni.airline_id = %s")
        parameters.append(g.current_user["airline_id"])
    else:
        airline_id = request.args.get("airline_id")
        if airline_id:
            conditions.append("fni.airline_id = %s")
            parameters.append(airline_id)

    if flight_date:
        conditions.append("fi.flight_date = %s")
        parameters.append(flight_date)

    if status:
        conditions.append("fi.status = %s")
        parameters.append(status)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

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
                    fi.dep_time,
                    fi.arr_time,
                    fi.aircraft_model,
                    fi.first_seats,
                    fi.economy_seats,
                    fi.status,
                    fni.route_id,
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

        flights = [format_flight_row(row) for row in rows]

        return success_response(flights, "查询成功")

    except Exception as error:
        return error_response("航司航班查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_flight_bp.get("/flights/<int:instance_id>")
@role_required("航司管理员", "航空公司管理员", "系统总管理员")
def get_managed_flight_detail(instance_id):
    """查询单个航班实例。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            conditions = ["fi.instance_id = %s"]
            parameters = [instance_id]

            if g.current_user["role"] != "系统总管理员":
                conditions.append("fni.airline_id = %s")
                parameters.append(g.current_user["airline_id"])

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
                    fni.route_id,
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
                LIMIT 1
                """,
                tuple(parameters),
            )

            row = cursor.fetchone()

        if row is None:
            return error_response("未找到本航司的该航班", 404)

        return success_response(format_flight_row(row), "查询成功")

    except Exception as error:
        return error_response("航班详情查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_flight_bp.put("/flights/<int:instance_id>")
@admin_role_required("航司主管理员", "航班管理员")
def update_managed_flight(instance_id):
    permission_error = _require_flight_write_permission()
    if permission_error is not None:
        return permission_error
    """修改当前航司所属的航班实例。"""
    data = request.get_json(silent=True) or {}
    allowed_statuses = {"正常", "延误", "取消", "航班调整", "已完成"}

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    fi.instance_id,
                    fi.flight_date,
                    fi.dep_time,
                    fi.arr_time,
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
                (instance_id, g.current_user["airline_id"]),
            )

            flight = cursor.fetchone()

            if flight is None:
                return error_response("未找到本航司的该航班", 404)

            if flight["status"] in ("已完成", "取消", "航班调整"):
                return error_response("该航班已结束、已取消或已调整，不能继续编辑", 409)

            if flight.get("arr_time") is not None and flight["arr_time"] < datetime.now():
                return error_response("该航班已结束，不能继续编辑", 409)

            aircraft_model = str(data.get("aircraft_model", flight["aircraft_model"])).strip()
            first_seats = data.get("first_seats", flight["first_seats"])
            economy_seats = data.get("economy_seats", flight["economy_seats"])
            status = str(data.get("status", flight["status"])).strip()

            time_column_kind = get_flight_time_column_kind(cursor)

            try:
                dep_time_value, arr_time_value = build_flight_time_values(
                    flight["flight_date"],
                    data.get("dep_time"),
                    data.get("arr_time"),
                    time_column_kind,
                    flight.get("dep_time"),
                    flight.get("arr_time"),
                )
            except ValueError as exc:
                return error_response(str(exc))

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
                    SUM(CASE WHEN cp.cabin_type = '头等舱' THEN 1 ELSE 0 END) AS sold_first_seats,
                    SUM(CASE WHEN cp.cabin_type = '经济舱' THEN 1 ELSE 0 END) AS sold_economy_seats
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
                    dep_time = %s,
                    arr_time = %s,
                    first_seats = %s,
                    economy_seats = %s,
                    status = %s
                WHERE instance_id = %s
                """,
                (
                    aircraft_model,
                    dep_time_value,
                    arr_time_value,
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
                "depTime": format_time_value(dep_time_value),
                "arrTime": format_time_value(arr_time_value),
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
    permission_error = _require_flight_write_permission()
    if permission_error is not None:
        return permission_error
    """发布本航司航班的延误、取消或航班调整通知。"""
    data = request.get_json(silent=True) or {}

    irregularity_type = str(data.get("irregularity_type", "")).strip()
    responsibility_type = str(data.get("responsibility_type", "")).strip()
    description = str(data.get("description", "")).strip() or None

    allowed_irregularity_types = {"延误", "取消", "航班调整"}
    allowed_responsibility_types = {"航司原因", "天气原因", "其他原因"}

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
                (instance_id, g.current_user["airline_id"]),
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

            if irregularity_type in ("延误", "取消", "航班调整"):
                cursor.execute(
                    """
                    UPDATE flight_instance
                    SET status = %s
                    WHERE instance_id = %s
                    """,
                    (irregularity_type, instance_id),
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
@role_required("航司管理员", "航空公司管理员", "系统总管理员")
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
                (instance_id, g.current_user["airline_id"]),
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
                "createdAt": row["created_at"].isoformat(sep=" ", timespec="seconds"),
                "resolvedAt": row["resolved_at"].isoformat(sep=" ", timespec="seconds") if row["resolved_at"] is not None else None,
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
    permission_error = _require_flight_write_permission()
    if permission_error is not None:
        return permission_error
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
                (irregularity_id, g.current_user["airline_id"]),
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
                SELECT irregularity_type
                FROM flight_irregularity
                WHERE instance_id = %s
                  AND status = '生效中'
                LIMIT 1
                """,
                (irregularity["instance_id"],),
            )

            active_irregularity = cursor.fetchone()

            if active_irregularity is None:
                cursor.execute(
                    """
                    UPDATE flight_instance
                    SET status = '正常'
                    WHERE instance_id = %s
                    """,
                    (irregularity["instance_id"],),
                )
            else:
                cursor.execute(
                    """
                    UPDATE flight_instance
                    SET status = %s
                    WHERE instance_id = %s
                    """,
                    (
                        active_irregularity["irregularity_type"],
                        irregularity["instance_id"],
                    ),
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


@admin_flight_bp.get("/flights/<int:instance_id>/affected-orders")
@role_required("航司管理员", "航空公司管理员", "系统总管理员")
def list_flight_affected_orders(instance_id):
    """查询当前航班仍有效、会受异常影响的订单。"""
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
                (instance_id, g.current_user["airline_id"]),
            )

            if cursor.fetchone() is None:
                return error_response("未找到本航司的该航班", 404)

            cursor.execute(
                """
                SELECT irregularity_id
                FROM flight_irregularity
                WHERE instance_id = %s
                  AND status = '生效中'
                ORDER BY irregularity_id DESC
                LIMIT 1
                """,
                (instance_id,),
            )

            active_irregularity = cursor.fetchone()

            active_irregularity_id = (
                active_irregularity["irregularity_id"]
                if active_irregularity is not None
                else None
            )

            cursor.execute(
                """
                SELECT
                    ats.order_id,
                    u.username,
                    p.real_name AS passenger_name,
                    p.phone,
                    cp.cabin_type,
                    cp.sale_price,
                    ats.seat_no,
                    ats.order_status,
                    CASE
                        WHEN cr.change_id IS NULL THEN '待处理'
                        ELSE '已处理'
                    END AS handling_status
                FROM active_ticket_sale AS ats
                JOIN `user` AS u
                  ON u.user_id = ats.user_id
                JOIN passenger AS p
                  ON p.passenger_id = ats.passenger_id
                JOIN cabin_pricing AS cp
                  ON cp.pricing_id = ats.pricing_id
                LEFT JOIN change_record AS cr
                  ON cr.old_order_id = ats.order_id
                 AND (
                    %s IS NULL
                    OR cr.irregularity_id = %s
                 )
                WHERE ats.instance_id = %s
                  AND ats.order_status IN ('已支付', '已出票')
                ORDER BY ats.order_id
                """,
                (
                    active_irregularity_id,
                    active_irregularity_id,
                    instance_id,
                ),
            )

            rows = cursor.fetchall()

        orders = [
            {
                "orderId": row["order_id"],
                "username": row["username"],
                "passengerName": row["passenger_name"],
                "phone": row["phone"],
                "cabinType": row["cabin_type"],
                "seatNo": row["seat_no"],
                "price": float(row["sale_price"]),
                "orderStatus": row["order_status"],
                "handlingStatus": row["handling_status"],
            }
            for row in rows
        ]

        return success_response(orders, "查询成功")

    except Exception as error:
        return error_response("受影响订单查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_flight_bp.post("/flights")
@admin_role_required("航司主管理员", "航班管理员")
def create_managed_flight():
    permission_error = _require_flight_write_permission()
    if permission_error is not None:
        return permission_error
    """新增航班实例；如果航班号不存在，允许本航司按前缀新增 flight_no_info。"""
    data = request.get_json(silent=True) or {}

    flight_no = str(data.get("flight_no", "")).strip().upper()
    flight_date_text = str(data.get("flight_date", "")).strip()
    dep_time_text = str(data.get("dep_time", "")).strip()
    arr_time_text = str(data.get("arr_time", "")).strip()
    aircraft_model = str(data.get("aircraft_model", "")).strip()
    route_id = data.get("route_id")
    first_seats = data.get("first_seats")
    economy_seats = data.get("economy_seats")
    first_price = data.get("first_price")
    economy_price = data.get("economy_price")
    status = str(data.get("status", "正常")).strip()

    if not flight_no:
        return error_response("航班号不能为空")

    if len(flight_no) < 3:
        return error_response("航班号格式不合法")

    try:
        flight_date_value = date.fromisoformat(flight_date_text)
    except ValueError:
        return error_response("航班日期格式应为 YYYY-MM-DD")

    if not dep_time_text:
        return error_response("起飞时间不能为空")

    if not arr_time_text:
        return error_response("到达时间不能为空")

    try:
        normalize_time_text(dep_time_text, "起飞时间")
        normalize_time_text(arr_time_text, "到达时间")
    except ValueError as exc:
        return error_response(str(exc))

    if not aircraft_model:
        return error_response("执飞机型不能为空")

    if type(first_seats) is not int or first_seats < 0:
        return error_response("头等舱座位数必须为非负整数")

    if type(economy_seats) is not int or economy_seats < 0:
        return error_response("经济舱座位数必须为非负整数")

    try:
        first_price = float(first_price)
        economy_price = float(economy_price)
    except (TypeError, ValueError):
        return error_response("舱位票价格式不合法")

    if first_seats > 0 and first_price <= 0:
        return error_response("头等舱有座位时，头等舱票价必须大于 0")

    if economy_seats > 0 and economy_price <= 0:
        return error_response("经济舱有座位时，经济舱票价必须大于 0")

    if first_price < 0 or economy_price < 0:
        return error_response("舱位票价不能为负数")

    if status not in {"正常", "延误", "取消", "航班调整", "已完成"}:
        return error_response("航班状态不合法")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT airline_id, airline_code
                FROM airline_company
                WHERE airline_id = %s
                  AND status = '正常'
                LIMIT 1
                """,
                (g.current_user["airline_id"],),
            )

            airline = cursor.fetchone()
            if airline is None:
                return error_response("当前管理员所属航空公司不存在或已禁用", 403)

            if not flight_no.startswith(airline["airline_code"]):
                return error_response(f"航班号必须以当前航司代码 {airline['airline_code']} 开头")

            cursor.execute(
                """
                SELECT flight_no, route_id, airline_id
                FROM flight_no_info
                WHERE flight_no = %s
                LIMIT 1
                """,
                (flight_no,),
            )

            flight_no_info = cursor.fetchone()

            if flight_no_info is not None:
                if flight_no_info["airline_id"] != g.current_user["airline_id"]:
                    return error_response("该航班号不属于当前航司", 403)
            else:
                if route_id in (None, ""):
                    return error_response("新增航班号必须选择航线")

                try:
                    route_id = int(route_id)
                except (TypeError, ValueError):
                    return error_response("航线不合法")

                cursor.execute(
                    """
                    SELECT route_id
                    FROM route
                    WHERE route_id = %s
                    LIMIT 1
                    """,
                    (route_id,),
                )

                if cursor.fetchone() is None:
                    return error_response("所选航线不存在", 404)

                cursor.execute(
                    """
                    INSERT INTO flight_no_info (
                        flight_no,
                        route_id,
                        airline_id
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        flight_no,
                        route_id,
                        g.current_user["airline_id"],
                    ),
                )

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

            time_column_kind = get_flight_time_column_kind(cursor)
            dep_time_value, arr_time_value = build_flight_time_values(
                flight_date_value,
                dep_time_text,
                arr_time_text,
                time_column_kind,
            )

            cursor.execute(
                """
                INSERT INTO flight_instance (
                    flight_no,
                    flight_date,
                    dep_time,
                    arr_time,
                    aircraft_model,
                    first_seats,
                    economy_seats,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    flight_no,
                    flight_date_value,
                    dep_time_value,
                    arr_time_value,
                    aircraft_model,
                    first_seats,
                    economy_seats,
                    status,
                ),
            )

            instance_id = cursor.lastrowid

            pricing_valid_to = datetime.combine(
                flight_date_value,
                datetime.strptime(normalize_time_text(dep_time_text, "起飞时间"), "%H:%M:%S").time(),
            )

            if first_seats > 0:
                cursor.execute(
                    """
                    INSERT INTO cabin_pricing (
                        instance_id,
                        cabin_type,
                        sale_price,
                        valid_from,
                        valid_to
                    )
                    VALUES (%s, '头等舱', %s, NOW(), %s)
                    """,
                    (
                        instance_id,
                        first_price,
                        pricing_valid_to,
                    ),
                )

            if economy_seats > 0:
                cursor.execute(
                    """
                    INSERT INTO cabin_pricing (
                        instance_id,
                        cabin_type,
                        sale_price,
                        valid_from,
                        valid_to
                    )
                    VALUES (%s, '经济舱', %s, NOW(), %s)
                    """,
                    (
                        instance_id,
                        economy_price,
                        pricing_valid_to,
                    ),
                )

        connection.commit()

        return success_response(
            {
                "instanceId": instance_id,
                "flightNo": flight_no,
                "flightDate": flight_date_value.isoformat(),
                "depTime": format_time_value(dep_time_value),
                "arrTime": format_time_value(arr_time_value),
                "aircraftModel": aircraft_model,
                "firstSeats": first_seats,
                "firstPrice": first_price,
                "economySeats": economy_seats,
                "economyPrice": economy_price,
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


@admin_flight_bp.get("/airlines")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def list_admin_airlines():
    """管理端航空公司下拉列表。

    系统总管理员：可查看所有正常航空公司；
    航司内部管理员：只返回自己所属航空公司。
    """
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            if g.current_user.get("role") in ("系统总管理员", "平台总管理员", "总管理员"):
                cursor.execute(
                    """
                    SELECT
                        airline_id,
                        airline_code,
                        airline_name,
                        status
                    FROM airline_company
                    WHERE status = '正常'
                    ORDER BY airline_id
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        airline_id,
                        airline_code,
                        airline_name,
                        status
                    FROM airline_company
                    WHERE airline_id = %s
                      AND status = '正常'
                    ORDER BY airline_id
                    """,
                    (g.current_user.get("airline_id"),),
                )

            rows = cursor.fetchall()

        airlines = [
            {
                "airlineId": row["airline_id"],
                "airline_id": row["airline_id"],
                "airlineCode": row["airline_code"],
                "airline_code": row["airline_code"],
                "airlineName": row["airline_name"],
                "airline_name": row["airline_name"],
                "status": row["status"],
            }
            for row in rows
        ]

        return success_response(airlines, "查询成功")

    except Exception as error:
        return error_response("航空公司列表查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()

