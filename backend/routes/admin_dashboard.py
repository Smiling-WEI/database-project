from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import role_required
from utils.response import success_response, error_response


admin_dashboard_bp = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/api/admin",
)


def is_system_admin():
    return (
        g.current_user.get("role") in ("系统总管理员", "平台总管理员", "总管理员")
        or g.current_user.get("admin_role") in ("系统总管理员", "平台总管理员", "总管理员")
    )


def build_airline_scope(column_name):
    """返回 SQL 条件和参数。

    系统总管理员：
    - 不传 airline_id：不加航司过滤，查全部
    - 传 airline_id：查指定航司

    航司内部管理员：
    - 只能查自己航司
    """
    if is_system_admin():
        airline_id = request.args.get("airline_id")

        if airline_id not in (None, ""):
            try:
                airline_id = int(airline_id)
            except (TypeError, ValueError):
                return None, None, error_response("航空公司参数不合法")

            return f"{column_name} = %s", [airline_id], None

        return "1 = 1", [], None

    airline_id = g.current_user.get("airline_id")

    if airline_id is None:
        return None, None, error_response("当前管理员未绑定航空公司", 403)

    return f"{column_name} = %s", [airline_id], None


@admin_dashboard_bp.get("/dashboard/summary")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def dashboard_summary():
    flight_scope, flight_params, error = build_airline_scope("fni.airline_id")

    if error:
        return error

    admin_scope, admin_params, error = build_airline_scope("u.airline_id")

    if error:
        return error

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            # 今日航班数
            cursor.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE {flight_scope}
                  AND fi.flight_date = CURDATE()
                """,
                tuple(flight_params),
            )
            today_flight_count = cursor.fetchone()["count"]

            # 今日订单数
            cursor.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM active_ticket_sale AS ats
                JOIN flight_instance AS fi
                  ON fi.instance_id = ats.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE {flight_scope}
                  AND DATE(ats.purchase_time) = CURDATE()
                """,
                tuple(flight_params),
            )
            today_order_count = cursor.fetchone()["count"]

            # 注册乘客数：系统总管理员看全部；航司管理员看买过本航司票的用户
            if is_system_admin():
                cursor.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM `user`
                    WHERE role = '乘客'
                    """
                )
            else:
                cursor.execute(
                    f"""
                    SELECT COUNT(DISTINCT ats.user_id) AS count
                    FROM (
                        SELECT user_id, instance_id FROM active_ticket_sale
                        UNION ALL
                        SELECT user_id, instance_id FROM archive_ticket_sale
                    ) AS ats
                    JOIN flight_instance AS fi
                      ON fi.instance_id = ats.instance_id
                    JOIN flight_no_info AS fni
                      ON fni.flight_no = fi.flight_no
                    WHERE {flight_scope}
                    """,
                    tuple(flight_params),
                )
            total_user_count = cursor.fetchone()["count"]

            # 管理员数
            cursor.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM `user` AS u
                WHERE {admin_scope}
                  AND (
                    u.role IN ('航司管理员', '航空公司管理员', '航司内部管理员')
                    OR u.role IN ('系统总管理员', '平台总管理员', '总管理员')
                  )
                """,
                tuple(admin_params),
            )
            admin_count = cursor.fetchone()["count"]

            # 今日航班概览
            cursor.execute(
                f"""
                SELECT
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    DATE_FORMAT(fi.dep_time, '%%H:%%i') AS dep_time,
                    DATE_FORMAT(fi.arr_time, '%%H:%%i') AS arr_time,
                    fi.status,
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
                WHERE {flight_scope}
                  AND fi.flight_date = CURDATE()
                ORDER BY fi.dep_time
                LIMIT 5
                """,
                tuple(flight_params),
            )
            today_flights = cursor.fetchall()

            # 近期订单
            cursor.execute(
                f"""
                SELECT
                    x.order_id,
                    x.order_status,
                    u.username,
                    fi.flight_no,
                    ac.airline_name
                FROM (
                    SELECT order_id, user_id, instance_id, order_status, purchase_time
                    FROM active_ticket_sale
                    UNION ALL
                    SELECT order_id, user_id, instance_id, order_status, purchase_time
                    FROM archive_ticket_sale
                ) AS x
                JOIN `user` AS u
                  ON u.user_id = x.user_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = x.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                JOIN airline_company AS ac
                  ON ac.airline_id = fni.airline_id
                WHERE {flight_scope}
                ORDER BY x.purchase_time DESC, x.order_id DESC
                LIMIT 5
                """,
                tuple(flight_params),
            )
            recent_orders = cursor.fetchall()

        data = {
            "todayFlightCount": today_flight_count,
            "todayOrderCount": today_order_count,
            "totalUserCount": total_user_count,
            "adminCount": admin_count,
            "todayFlights": [
                {
                    "instanceId": row["instance_id"],
                    "flightNo": row["flight_no"],
                    "flightDate": row["flight_date"].isoformat(),
                    "depTime": row["dep_time"],
                    "arrTime": row["arr_time"],
                    "status": row["status"],
                    "airlineName": row["airline_name"],
                    "depAirportName": row["dep_airport_name"],
                    "arrAirportName": row["arr_airport_name"],
                }
                for row in today_flights
            ],
            "recentOrders": [
                {
                    "orderId": row["order_id"],
                    "username": row["username"],
                    "flightNo": row["flight_no"],
                    "airlineName": row["airline_name"],
                    "orderStatus": row["order_status"],
                }
                for row in recent_orders
            ],
            "notices": [],
        }

        return success_response(data, "查询成功")

    except Exception as error:
        return error_response("控制台数据查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
