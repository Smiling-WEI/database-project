from decimal import Decimal, ROUND_HALF_UP

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
                    p.id_card AS passenger_id_card,
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    DATE_FORMAT(fi.dep_time, '%%H:%%i') AS dep_time,
                    DATE_FORMAT(fi.arr_time, '%%H:%%i') AS arr_time,
                    TIMESTAMPDIFF(MINUTE, fi.dep_time, fi.arr_time) AS duration_minutes,
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
                AND fi.arr_time >= NOW()
                AND ats.order_status NOT IN ('已退票', '已取消', '已完成')
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
                "passengerIdCard": row["passenger_id_card"],
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "depTime": row.get("dep_time") or "",
                "arrTime": row.get("arr_time") or "",
                "duration": (
                    f"{int(row['duration_minutes']) // 60}h {int(row['duration_minutes']) % 60}m"
                    if row.get("duration_minutes") is not None
                    else "-"
                ),
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
    """查询当前用户的指定订单详情，支持有效订单和历史订单。"""
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
                    DATE_FORMAT(fi.dep_time, '%%H:%%i') AS dep_time,
                    DATE_FORMAT(fi.arr_time, '%%H:%%i') AS arr_time,
                    TIMESTAMPDIFF(MINUTE, fi.dep_time, fi.arr_time) AS duration_minutes,
                    ac.airline_name,
                    dep_airport.airport_name AS dep_airport,
                    arr_airport.airport_name AS arr_airport,
                    cp.pricing_id,
                    cp.cabin_type,
                    cp.sale_price,
                    ats.seat_no,
                    ats.purchase_time,
                    ats.order_status,
                    ats.order_source
                FROM (
                    SELECT
                        order_id,
                        user_id,
                        passenger_id,
                        instance_id,
                        pricing_id,
                        seat_no,
                        purchase_time,
                        order_status,
                        'active' AS order_source
                    FROM active_ticket_sale

                    UNION ALL

                    SELECT
                        order_id,
                        user_id,
                        passenger_id,
                        instance_id,
                        pricing_id,
                        seat_no,
                        purchase_time,
                        order_status,
                        'archive' AS order_source
                    FROM archive_ticket_sale
                ) AS ats
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
            "depTime": row.get("dep_time") or "",
            "arrTime": row.get("arr_time") or "",
            "duration": (
                f"{int(row['duration_minutes']) // 60}h {int(row['duration_minutes']) % 60}m"
                if row.get("duration_minutes") is not None
                else "-"
            ),
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
            "orderSource": row["order_source"],
        }

        return success_response(order, "查询成功")

    except Exception as error:
        return error_response("订单详情查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()



def _money(value):
    """金额统一保留两位小数。"""
    return Decimal(str(value or 0)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _load_refund_context(cursor, order_id, user_id, lock_rows=False):
    """读取待退票订单，匹配退票规则，并计算手续费与退款金额。"""
    lock_sql = " FOR UPDATE" if lock_rows else ""

    cursor.execute(
        f"""
        SELECT
            ats.order_id,
            ats.user_id,
            ats.passenger_id,
            ats.instance_id,
            ats.pricing_id,
            ats.seat_no,
            ats.purchase_time,
            ats.order_status,
            cp.sale_price AS ticket_price,
            fi.flight_no,
            fi.dep_time,
            fi.arr_time,
            fni.airline_id,
            ac.airline_name,
            TIMESTAMPDIFF(MINUTE, NOW(), fi.dep_time) AS minutes_before_departure
        FROM active_ticket_sale AS ats
        JOIN cabin_pricing AS cp
          ON cp.pricing_id = ats.pricing_id
        JOIN flight_instance AS fi
          ON fi.instance_id = ats.instance_id
        JOIN flight_no_info AS fni
          ON fni.flight_no = fi.flight_no
        JOIN airline_company AS ac
          ON ac.airline_id = fni.airline_id
        WHERE ats.order_id = %s
          AND ats.user_id = %s
        LIMIT 1
        {lock_sql}
        """,
        (
            order_id,
            user_id,
        ),
    )

    order = cursor.fetchone()

    if order is None:
        return None, "未找到可退票的有效订单", 404

    if order["order_status"] not in ("已支付", "已出票"):
        return None, "当前订单状态不允许退票", 409

    minutes_before_departure = order["minutes_before_departure"]

    if minutes_before_departure is None or minutes_before_departure < 0:
        return None, "航班已起飞，不能退票", 409

    hours_before_departure = Decimal(minutes_before_departure) / Decimal(60)

    cursor.execute(
        """
        SELECT
            rule_id,
            fee_rate,
            min_hours_before_departure,
            max_hours_before_departure
        FROM change_rule
        WHERE airline_id = %s
          AND change_type = '乘客主动退票'
          AND status = '启用'
          AND min_hours_before_departure <= %s
          AND (
              max_hours_before_departure IS NULL
              OR max_hours_before_departure > %s
          )
          AND valid_from <= NOW()
          AND (
              valid_to IS NULL
              OR valid_to > NOW()
          )
        ORDER BY min_hours_before_departure DESC, rule_id DESC
        LIMIT 1
        """,
        (
            order["airline_id"],
            float(hours_before_departure),
            float(hours_before_departure),
        ),
    )

    rule = cursor.fetchone()

    if rule is None:
        return None, "未找到适用的退票规则", 409

    ticket_price = _money(order["ticket_price"])
    fee_rate = Decimal(str(rule["fee_rate"]))
    refund_fee = _money(ticket_price * fee_rate)
    refundable_amount = _money(ticket_price - refund_fee)

    if refundable_amount < 0:
        refundable_amount = Decimal("0.00")

    return {
        "order": order,
        "rule": rule,
        "ticket_price": ticket_price,
        "fee_rate": fee_rate,
        "refund_fee": refund_fee,
        "refundable_amount": refundable_amount,
        "hours_before_departure": hours_before_departure.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        ),
    }, None, None


def _serialize_refund_context(context):
    """把退票预览结果转换为前端可用数据。"""
    order = context["order"]
    rule = context["rule"]

    return {
        "orderId": order["order_id"],
        "flightNo": order["flight_no"],
        "airlineName": order["airline_name"],
        "ticketPrice": float(context["ticket_price"]),
        "feeRate": float(context["fee_rate"]),
        "refundFee": float(context["refund_fee"]),
        "refundableAmount": float(context["refundable_amount"]),
        "hoursBeforeDeparture": float(context["hours_before_departure"]),
        "ruleId": rule["rule_id"],
        "ruleText": (
            f"退票手续费按票价的 {float(context['fee_rate']) * 100:.0f}% 收取"
        ),
    }


@order_bp.post("/orders/<int:order_id>/refund-preview")
@login_required
def preview_refund_order(order_id):
    """预览退票手续费和实际退款金额。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            context, message, status_code = _load_refund_context(
                cursor,
                order_id,
                g.current_user["user_id"],
                lock_rows=False,
            )

            if context is None:
                return error_response(message, status_code)

        return success_response(
            _serialize_refund_context(context),
            "退票费用计算成功",
        )

    except Exception as error:
        return error_response("退票费用计算失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@order_bp.post("/orders/<int:order_id>/refund")
@login_required
def refund_order(order_id):
    """为当前用户办理退票：归档订单，并写入退改记录。"""
    data = request.get_json(silent=True) or {}
    refund_reason = str(data.get("refund_reason", "")).strip() or "乘客主动退票"

    if len(refund_reason) > 500:
        return error_response("退票原因不能超过 500 个字符")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            context, message, status_code = _load_refund_context(
                cursor,
                order_id,
                g.current_user["user_id"],
                lock_rows=True,
            )

            if context is None:
                return error_response(message, status_code)

            order = context["order"]

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

            cursor.execute(
                """
                INSERT INTO change_record (
                    old_order_id,
                    new_order_id,
                    rule_id,
                    change_type,
                    irregularity_id,
                    old_ticket_price,
                    new_ticket_price,
                    fare_difference,
                    change_fee,
                    payable_amount,
                    refundable_amount,
                    operator_user_id,
                    change_reason,
                    status,
                    created_at,
                    completed_at
                )
                VALUES (
                    %s, NULL, %s, '乘客主动退票', NULL,
                    %s, 0, %s, %s, 0, %s,
                    %s, %s, '已完成', NOW(), NOW()
                )
                """,
                (
                    order["order_id"],
                    context["rule"]["rule_id"],
                    context["ticket_price"],
                    -context["ticket_price"],
                    context["refund_fee"],
                    context["refundable_amount"],
                    g.current_user["user_id"],
                    refund_reason,
                ),
            )

            change_id = cursor.lastrowid

        connection.commit()

        response_data = _serialize_refund_context(context)
        response_data["changeId"] = change_id
        response_data["orderStatus"] = "已退票"

        return success_response(
            response_data,
            "退票成功，订单已转入历史记录",
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
                    p.id_card AS passenger_id_card,
                    p.phone AS passenger_phone,
                    fi.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    fi.aircraft_model,
                    fi.status AS flight_status,
                    DATE_FORMAT(fi.dep_time, '%%H:%%i') AS dep_time,
                    DATE_FORMAT(fi.arr_time, '%%H:%%i') AS arr_time,
                    TIMESTAMPDIFF(MINUTE, fi.dep_time, fi.arr_time) AS duration_minutes,
                    ac.airline_name,
                    dep_airport.airport_name AS dep_airport,
                    arr_airport.airport_name AS arr_airport,
                    cp.pricing_id,
                    cp.cabin_type,
                    cp.sale_price,
                    ats.seat_no,
                    ats.purchase_time,
                    ats.order_status
                                FROM (
                    SELECT
                        order_id,
                        user_id,
                        passenger_id,
                        instance_id,
                        pricing_id,
                        seat_no,
                        purchase_time,
                        order_status
                    FROM archive_ticket_sale
                    WHERE user_id = %s

                    UNION ALL

                    SELECT
                        active_orders.order_id,
                        active_orders.user_id,
                        active_orders.passenger_id,
                        active_orders.instance_id,
                        active_orders.pricing_id,
                        active_orders.seat_no,
                        active_orders.purchase_time,
                        '已完成' AS order_status
                    FROM active_ticket_sale AS active_orders
                    JOIN flight_instance AS active_fi
                      ON active_fi.instance_id = active_orders.instance_id
                    WHERE active_orders.user_id = %s
                      AND active_fi.arr_time < NOW()
                      AND active_orders.order_status NOT IN ('已退票', '已取消', '已完成')
                ) AS ats
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
                ORDER BY ats.purchase_time DESC, ats.order_id DESC
                """,
                (
                    g.current_user["user_id"],
                    g.current_user["user_id"],
                ),
            )

            rows = cursor.fetchall()

        orders = [
            {
                "orderId": row["order_id"],
                "passengerId": row["passenger_id"],
                "passengerName": row["passenger_name"],
                "passengerIdCard": row["passenger_id_card"],
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "depTime": row.get("dep_time") or "",
                "arrTime": row.get("arr_time") or "",
                "duration": (
                    f"{int(row['duration_minutes']) // 60}h {int(row['duration_minutes']) % 60}m"
                    if row.get("duration_minutes") is not None
                    else "-"
                ),
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


def _build_seat_map(total_seats, cabin_type, occupied_seats, current_seat_no=None):
    """根据舱位座位数生成一个简单座位图。"""
    if cabin_type == "头等舱":
        columns = ["A", "B", "C", "D"]
    else:
        columns = ["A", "B", "C", "D", "E", "F"]

    seats = []
    total_seats = int(total_seats or 0)
    row_count = (total_seats + len(columns) - 1) // len(columns)

    used = 0
    for row_no in range(1, row_count + 1):
        row_seats = []
        for col in columns:
            if used >= total_seats:
                break

            seat_no = f"{row_no}{col}"

            if current_seat_no and seat_no == current_seat_no:
                status = "selected"
            elif seat_no in occupied_seats:
                status = "occupied"
            else:
                status = "available"

            row_seats.append({
                "seatNo": seat_no,
                "row": row_no,
                "column": col,
                "status": status
            })
            used += 1

        seats.append({
            "row": row_no,
            "seats": row_seats
        })

    return {
        "columns": columns,
        "rows": seats
    }


@order_bp.get("/orders/<int:order_id>/seats")
@login_required
def get_order_seats(order_id):
    """获取当前订单可选座位图。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ats.order_id,
                    ats.user_id,
                    ats.instance_id,
                    ats.seat_no,
                    ats.check_in_status,
                    cp.cabin_type,
                    CASE
                        WHEN cp.cabin_type = '头等舱' THEN fi.first_seats
                        WHEN cp.cabin_type = '经济舱' THEN fi.economy_seats
                        ELSE fi.economy_seats
                    END AS total_seats
                FROM active_ticket_sale AS ats
                JOIN cabin_pricing AS cp
                  ON cp.pricing_id = ats.pricing_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = ats.instance_id
                WHERE ats.order_id = %s
                  AND ats.user_id = %s
                LIMIT 1
                """,
                (
                    order_id,
                    g.current_user["user_id"],
                ),
            )
            order = cursor.fetchone()

            if order is None:
                return error_response("未找到该订单", 404)

            cursor.execute(
                """
                SELECT seat_no
                FROM active_ticket_sale
                WHERE instance_id = %s
                  AND seat_no IS NOT NULL
                  AND seat_no <> ''
                  AND order_id <> %s
                """,
                (
                    order["instance_id"],
                    order_id,
                ),
            )
            occupied_rows = cursor.fetchall()

        occupied_seats = {
            row["seat_no"]
            for row in occupied_rows
            if row.get("seat_no")
        }

        seat_map = _build_seat_map(
            order["total_seats"],
            order["cabin_type"],
            occupied_seats,
            order["seat_no"],
        )

        return success_response(
            {
                "orderId": order["order_id"],
                "instanceId": order["instance_id"],
                "cabinType": order["cabin_type"],
                "currentSeatNo": order["seat_no"],
                "checkInStatus": order["check_in_status"],
                "seatMap": seat_map,
            },
            "查询成功",
        )

    except Exception as error:
        return error_response("座位图查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@order_bp.post("/orders/<int:order_id>/checkin")
@login_required
def checkin_order(order_id):
    """为当前订单办理值机并选择座位。"""
    data = request.get_json(silent=True) or {}
    seat_no = str(data.get("seatNo") or data.get("seat_no") or "").strip().upper()

    if not seat_no:
        return error_response("请选择座位")

    if len(seat_no) > 10:
        return error_response("座位号不能超过 10 个字符")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ats.order_id,
                    ats.user_id,
                    ats.instance_id,
                    ats.seat_no,
                    ats.check_in_status,
                    cp.cabin_type,
                    CASE
                        WHEN cp.cabin_type = '头等舱' THEN fi.first_seats
                        WHEN cp.cabin_type = '经济舱' THEN fi.economy_seats
                        ELSE fi.economy_seats
                    END AS total_seats
                FROM active_ticket_sale AS ats
                JOIN cabin_pricing AS cp
                  ON cp.pricing_id = ats.pricing_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = ats.instance_id
                WHERE ats.order_id = %s
                  AND ats.user_id = %s
                LIMIT 1
                """,
                (
                    order_id,
                    g.current_user["user_id"],
                ),
            )
            order = cursor.fetchone()

            if order is None:
                return error_response("未找到该订单", 404)

            if order["check_in_status"] == "已值机" or order["seat_no"]:
                return error_response("该订单已值机，不能重复值机", 409)

            seat_map = _build_seat_map(
                order["total_seats"],
                order["cabin_type"],
                set(),
            )
            valid_seats = {
                seat["seatNo"]
                for row in seat_map["rows"]
                for seat in row["seats"]
            }

            if seat_no not in valid_seats:
                return error_response("座位号不在可选范围内", 400)

            cursor.execute(
                """
                SELECT order_id
                FROM active_ticket_sale
                WHERE instance_id = %s
                  AND seat_no = %s
                  AND order_id <> %s
                LIMIT 1
                """,
                (
                    order["instance_id"],
                    seat_no,
                    order_id,
                ),
            )
            occupied = cursor.fetchone()

            if occupied is not None:
                return error_response("该座位已经被占用", 409)

            cursor.execute(
                """
                UPDATE active_ticket_sale
                SET seat_no = %s,
                    check_in_status = '已值机',
                    check_in_time = NOW()
                WHERE order_id = %s
                  AND user_id = %s
                """,
                (
                    seat_no,
                    order_id,
                    g.current_user["user_id"],
                ),
            )

        connection.commit()

        return success_response(
            {
                "orderId": order_id,
                "seatNo": seat_no,
                "checkInStatus": "已值机",
            },
            "值机成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()
        return error_response("值机失败", 500, error)

    finally:
        if connection is not None:
            connection.close()