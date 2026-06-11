from flask import Blueprint, g

from db import get_db_connection
from utils.auth import role_required
from utils.response import error_response, success_response


admin_dashboard_bp = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/api/admin",
)


@admin_dashboard_bp.get("/dashboard/summary")
@role_required("航空公司管理员")
def get_dashboard_summary():
    """查询当前航司管理端控制台的汇总数据。"""
    airline_id = g.current_user["airline_id"]
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS today_flight_count
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE fni.airline_id = %s
                  AND fi.flight_date = CURDATE()
                """,
                (airline_id,),
            )
            today_flight_count = cursor.fetchone()["today_flight_count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS today_order_count
                FROM (
                    SELECT
                        ats.order_id,
                        ats.instance_id,
                        ats.purchase_time
                    FROM active_ticket_sale AS ats

                    UNION ALL

                    SELECT
                        archive.order_id,
                        archive.instance_id,
                        archive.purchase_time
                    FROM archive_ticket_sale AS archive
                ) AS orders
                JOIN flight_instance AS fi
                  ON fi.instance_id = orders.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE fni.airline_id = %s
                  AND DATE(orders.purchase_time) = CURDATE()
                """,
                (airline_id,),
            )
            today_order_count = cursor.fetchone()["today_order_count"]

            cursor.execute(
                """
                SELECT COUNT(DISTINCT orders.user_id) AS total_user_count
                FROM (
                    SELECT user_id, instance_id
                    FROM active_ticket_sale

                    UNION ALL

                    SELECT user_id, instance_id
                    FROM archive_ticket_sale
                ) AS orders
                JOIN flight_instance AS fi
                  ON fi.instance_id = orders.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE fni.airline_id = %s
                """,
                (airline_id,),
            )
            total_user_count = cursor.fetchone()["total_user_count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS admin_count
                FROM `user`
                WHERE role = '航空公司管理员'
                  AND airline_id = %s
                """,
                (airline_id,),
            )
            admin_count = cursor.fetchone()["admin_count"]

            cursor.execute(
                """
                SELECT
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    CONCAT(
                        dep_airport.airport_name,
                        ' → ',
                        arr_airport.airport_name
                    ) AS route,
                    fi.status
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                JOIN route AS r
                  ON r.route_id = fni.route_id
                JOIN airport AS dep_airport
                  ON dep_airport.airport_code = r.dep_airport_code
                JOIN airport AS arr_airport
                  ON arr_airport.airport_code = r.arr_airport_code
                WHERE fni.airline_id = %s
                  AND fi.flight_date = CURDATE()
                ORDER BY fi.flight_no
                """,
                (airline_id,),
            )
            today_flight_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    orders.order_id,
                    u.username,
                    fi.flight_no,
                    orders.order_status
                FROM (
                    SELECT
                        order_id,
                        user_id,
                        instance_id,
                        purchase_time,
                        order_status
                    FROM active_ticket_sale

                    UNION ALL

                    SELECT
                        order_id,
                        user_id,
                        instance_id,
                        purchase_time,
                        order_status
                    FROM archive_ticket_sale
                ) AS orders
                JOIN `user` AS u
                  ON u.user_id = orders.user_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = orders.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE fni.airline_id = %s
                ORDER BY orders.purchase_time DESC,
                         orders.order_id DESC
                LIMIT 5
                """,
                (airline_id,),
            )
            recent_order_rows = cursor.fetchall()

        today_flights = [
            {
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "route": row["route"],
                "status": row["status"],
            }
            for row in today_flight_rows
        ]

        recent_orders = [
            {
                "orderId": row["order_id"],
                "username": row["username"],
                "flightNo": row["flight_no"],
                "orderStatus": row["order_status"],
            }
            for row in recent_order_rows
        ]

        return success_response(
            {
                "todayFlightCount": today_flight_count,
                "todayOrderCount": today_order_count,
                "totalUserCount": total_user_count,
                "adminCount": admin_count,
                "todayFlights": today_flights,
                "recentOrders": recent_orders,
                "notices": [],
            },
            "查询成功",
        )

    except Exception as error:
        return error_response("控制台汇总数据查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()