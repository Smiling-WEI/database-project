from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import login_required
from utils.response import error_response, success_response


order_bp = Blueprint("order", __name__, url_prefix="/api")


@order_bp.post("/orders")
@login_required
def create_order():
    """为当前用户的常用乘机人购买机票。"""
    data = request.get_json(silent=True) or {}

    passenger_id = data.get("passenger_id")
    pricing_id = data.get("pricing_id")
    seat_no = str(data.get("seat_no", "")).strip() or None

    if not isinstance(passenger_id, int) or not isinstance(pricing_id, int):
        return error_response("乘机人编号和舱位价格编号必须为整数")

    if seat_no is not None and len(seat_no) > 10:
        return error_response("座位号不能超过 10 个字符")

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
                    fi.status,
                    CASE
                        WHEN cp.cabin_type = '头等舱' THEN fi.first_seats
                        WHEN cp.cabin_type = '经济舱' THEN fi.economy_seats
                        ELSE 0
                    END AS total_seats
                FROM cabin_pricing AS cp
                JOIN flight_instance AS fi
                  ON fi.instance_id = cp.instance_id
                WHERE cp.pricing_id = %s
                FOR UPDATE
                """,
                (pricing_id,),
            )

            pricing = cursor.fetchone()

            if pricing is None:
                return error_response("未找到该舱位价格", 404)

            if pricing["status"] in ("取消", "已完成"):
                return error_response("当前航班不可购买", 409)

            cursor.execute(
                """
                SELECT NOW() BETWEEN %s AND %s AS is_valid
                """,
                (
                    pricing["valid_from"],
                    pricing["valid_to"],
                ),
            )

            if not cursor.fetchone()["is_valid"]:
                return error_response("当前舱位价格已经失效", 409)

            cursor.execute(
                """
                SELECT 1
                FROM user_passenger
                WHERE user_id = %s
                  AND passenger_id = %s
                LIMIT 1
                """,
                (
                    g.current_user["user_id"],
                    passenger_id,
                ),
            )

            if cursor.fetchone() is None:
                return error_response("该乘机人不在你的常用乘机人列表中", 403)

            cursor.execute(
                """
                SELECT 1
                FROM active_ticket_sale
                WHERE passenger_id = %s
                  AND instance_id = %s
                  AND order_status = '已支付'
                LIMIT 1
                """,
                (
                    passenger_id,
                    pricing["instance_id"],
                ),
            )

            if cursor.fetchone() is not None:
                return error_response("该乘机人已经购买过当前航班", 409)

            cursor.execute(
                """
                SELECT COUNT(*) AS sold_count
                FROM active_ticket_sale AS ats
                JOIN cabin_pricing AS sold_cp
                  ON sold_cp.pricing_id = ats.pricing_id
                WHERE ats.instance_id = %s
                  AND sold_cp.cabin_type = %s
                  AND ats.order_status = '已支付'
                """,
                (
                    pricing["instance_id"],
                    pricing["cabin_type"],
                ),
            )

            sold_count = cursor.fetchone()["sold_count"]

            if sold_count >= pricing["total_seats"]:
                return error_response("当前舱位已经售罄", 409)

            if seat_no is not None:
                cursor.execute(
                    """
                    SELECT 1
                    FROM active_ticket_sale
                    WHERE instance_id = %s
                      AND seat_no = %s
                      AND order_status = '已支付'
                    LIMIT 1
                    """,
                    (
                        pricing["instance_id"],
                        seat_no,
                    ),
                )

                if cursor.fetchone() is not None:
                    return error_response("该座位已经被占用", 409)

            cursor.execute(
                """
                INSERT INTO active_ticket_sale (
                    user_id,
                    passenger_id,
                    instance_id,
                    pricing_id,
                    seat_no,
                    purchase_time,
                    order_status
                )
                VALUES (%s, %s, %s, %s, %s, NOW(), '已支付')
                """,
                (
                    g.current_user["user_id"],
                    passenger_id,
                    pricing["instance_id"],
                    pricing_id,
                    seat_no,
                ),
            )

            order_id = cursor.lastrowid

        connection.commit()

        return success_response(
            {
                "orderId": order_id,
                "instanceId": pricing["instance_id"],
                "pricingId": pricing_id,
                "passengerId": passenger_id,
                "cabinType": pricing["cabin_type"],
                "price": float(pricing["sale_price"]),
                "seatNo": seat_no,
                "orderStatus": "已支付",
            },
            "购票成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("购票失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@order_bp.get("/orders")
@login_required
def list_orders():
    """查询当前用户的有效订单。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ats.order_id,
                    ats.passenger_id,
                    p.real_name AS passenger_name,
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    ac.airline_name,
                    dep_airport.airport_name AS dep_airport,
                    arr_airport.airport_name AS arr_airport,
                    cp.pricing_id,
                    cp.cabin_type,
                    cp.sale_price,
                    ats.seat_no,
                    ats.purchase_time,
                    ats.order_status
                FROM active_ticket_sale AS ats
                JOIN passenger AS p
                  ON p.passenger_id = ats.passenger_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = ats.instance_id
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
                JOIN cabin_pricing AS cp
                  ON cp.pricing_id = ats.pricing_id
                WHERE ats.user_id = %s
                ORDER BY ats.purchase_time DESC, ats.order_id DESC
                """,
                (g.current_user["user_id"],),
            )

            rows = cursor.fetchall()

        orders = [
            {
                "orderId": row["order_id"],
                "passengerId": row["passenger_id"],
                "passengerName": row["passenger_name"],
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "airlineName": row["airline_name"],
                "depAirport": row["dep_airport"],
                "arrAirport": row["arr_airport"],
                "pricingId": row["pricing_id"],
                "cabinType": row["cabin_type"],
                "price": float(row["sale_price"]),
                "seatNo": row["seat_no"],
                "purchaseTime": row["purchase_time"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "orderStatus": row["order_status"],
            }
            for row in rows
        ]

        return success_response(orders, "查询成功")

    except Exception as error:
        return error_response("订单查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@order_bp.get("/orders/<int:order_id>")
@login_required
def get_order_detail(order_id):
    """查询当前用户的指定订单详情。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ats.order_id,
                    ats.passenger_id,
                    p.real_name AS passenger_name,
                    p.id_card AS passenger_id_card,
                    p.phone AS passenger_phone,
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    fi.aircraft_model,
                    fi.status AS flight_status,
                    ac.airline_name,
                    dep_airport.airport_name AS dep_airport,
                    arr_airport.airport_name AS arr_airport,
                    cp.pricing_id,
                    cp.cabin_type,
                    cp.sale_price,
                    ats.seat_no,
                    ats.purchase_time,
                    ats.order_status
                FROM active_ticket_sale AS ats
                JOIN passenger AS p
                  ON p.passenger_id = ats.passenger_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = ats.instance_id
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
                JOIN cabin_pricing AS cp
                  ON cp.pricing_id = ats.pricing_id
                WHERE ats.order_id = %s
                  AND ats.user_id = %s
                LIMIT 1
                """,
                (
                    order_id,
                    g.current_user["user_id"],
                ),
            )

            row = cursor.fetchone()

        if row is None:
            return error_response("未找到该订单", 404)

        order = {
            "orderId": row["order_id"],
            "passengerId": row["passenger_id"],
            "passengerName": row["passenger_name"],
            "passengerIdCard": row["passenger_id_card"],
            "passengerPhone": row["passenger_phone"],
            "instanceId": row["instance_id"],
            "flightNo": row["flight_no"],
            "flightDate": row["flight_date"].isoformat(),
            "aircraftModel": row["aircraft_model"],
            "flightStatus": row["flight_status"],
            "airlineName": row["airline_name"],
            "depAirport": row["dep_airport"],
            "arrAirport": row["arr_airport"],
            "pricingId": row["pricing_id"],
            "cabinType": row["cabin_type"],
            "price": float(row["sale_price"]),
            "seatNo": row["seat_no"],
            "purchaseTime": row["purchase_time"].isoformat(
                sep=" ",
                timespec="seconds",
            ),
            "orderStatus": row["order_status"],
        }

        return success_response(order, "查询成功")

    except Exception as error:
        return error_response("订单详情查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@order_bp.post("/orders/<int:order_id>/refund")
@login_required
def refund_order(order_id):
    """为当前用户办理退票，并将订单转入历史记录。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    order_id,
                    user_id,
                    passenger_id,
                    instance_id,
                    pricing_id,
                    seat_no,
                    purchase_time,
                    order_status
                FROM active_ticket_sale
                WHERE order_id = %s
                  AND user_id = %s
                FOR UPDATE
                """,
                (
                    order_id,
                    g.current_user["user_id"],
                ),
            )

            order = cursor.fetchone()

            if order is None:
                return error_response("未找到该订单", 404)

            if order["order_status"] != "已支付":
                return error_response("当前订单状态不允许退票", 409)

            cursor.execute(
                """
                INSERT INTO archive_ticket_sale (
                    order_id,
                    user_id,
                    passenger_id,
                    instance_id,
                    pricing_id,
                    seat_no,
                    purchase_time,
                    order_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, '已退票')
                """,
                (
                    order["order_id"],
                    order["user_id"],
                    order["passenger_id"],
                    order["instance_id"],
                    order["pricing_id"],
                    order["seat_no"],
                    order["purchase_time"],
                ),
            )

            cursor.execute(
                """
                DELETE FROM active_ticket_sale
                WHERE order_id = %s
                """,
                (order_id,),
            )

        connection.commit()

        return success_response(
            {
                "orderId": order_id,
                "orderStatus": "已退票",
            },
            "退票成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("退票失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@order_bp.get("/orders/history")
@login_required
def list_order_history():
    """查询当前用户的历史订单，包括已退票和已完成订单。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ats.order_id,
                    ats.passenger_id,
                    p.real_name AS passenger_name,
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    ac.airline_name,
                    dep_airport.airport_name AS dep_airport,
                    arr_airport.airport_name AS arr_airport,
                    cp.pricing_id,
                    cp.cabin_type,
                    cp.sale_price,
                    ats.seat_no,
                    ats.purchase_time,
                    ats.order_status
                FROM archive_ticket_sale AS ats
                JOIN passenger AS p
                  ON p.passenger_id = ats.passenger_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = ats.instance_id
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
                JOIN cabin_pricing AS cp
                  ON cp.pricing_id = ats.pricing_id
                WHERE ats.user_id = %s
                ORDER BY ats.purchase_time DESC, ats.order_id DESC
                """,
                (g.current_user["user_id"],),
            )

            rows = cursor.fetchall()

        orders = [
            {
                "orderId": row["order_id"],
                "passengerId": row["passenger_id"],
                "passengerName": row["passenger_name"],
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "airlineName": row["airline_name"],
                "depAirport": row["dep_airport"],
                "arrAirport": row["arr_airport"],
                "pricingId": row["pricing_id"],
                "cabinType": row["cabin_type"],
                "price": float(row["sale_price"]),
                "seatNo": row["seat_no"],
                "purchaseTime": row["purchase_time"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "orderStatus": row["order_status"],
            }
            for row in rows
        ]

        return success_response(orders, "查询成功")

    except Exception as error:
        return error_response("历史订单查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()