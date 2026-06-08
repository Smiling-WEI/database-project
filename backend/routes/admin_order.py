from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import role_required
from utils.response import error_response, success_response


admin_order_bp = Blueprint(
    "admin_order",
    __name__,
    url_prefix="/api/admin",
)


@admin_order_bp.get("/orders")
@role_required("航空公司管理员")
def list_managed_orders():
    """查询当前航司的有效订单与历史订单。"""
    flight_no = str(request.args.get("flight_no", "")).strip()
    order_status = str(request.args.get("status", "")).strip()

    conditions = [
        "fni.airline_id = %s",
    ]

    parameters = [
        g.current_user["airline_id"],
    ]

    if flight_no:
        conditions.append("fi.flight_no = %s")
        parameters.append(flight_no)

    if order_status:
        conditions.append("orders.order_status = %s")
        parameters.append(order_status)

    where_clause = " AND ".join(conditions)

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    orders.order_id,
                    orders.user_id,
                    u.username,
                    orders.passenger_id,
                    p.real_name AS passenger_name,
                    p.id_card AS passenger_id_card,
                    orders.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    cp.cabin_type,
                    cp.sale_price,
                    orders.seat_no,
                    orders.purchase_time,
                    orders.order_status,
                    orders.record_type
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
                        '有效订单' AS record_type
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
                        '历史订单' AS record_type
                    FROM archive_ticket_sale
                ) AS orders
                JOIN `user` AS u
                  ON u.user_id = orders.user_id
                JOIN passenger AS p
                  ON p.passenger_id = orders.passenger_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = orders.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                JOIN cabin_pricing AS cp
                  ON cp.pricing_id = orders.pricing_id
                WHERE {where_clause}
                ORDER BY orders.purchase_time DESC,
                         orders.order_id DESC
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        orders = [
            {
                "orderId": row["order_id"],
                "userId": row["user_id"],
                "username": row["username"],
                "passengerId": row["passenger_id"],
                "passengerName": row["passenger_name"],
                "passengerIdCard": row["passenger_id_card"],
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "cabinType": row["cabin_type"],
                "price": float(row["sale_price"]),
                "seatNo": row["seat_no"],
                "purchaseTime": row["purchase_time"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "orderStatus": row["order_status"],
                "recordType": row["record_type"],
            }
            for row in rows
        ]

        return success_response(orders, "查询成功")

    except Exception as error:
        return error_response("航司订单查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_order_bp.get("/change-records")
@role_required("航空公司管理员")
def list_managed_change_records():
    """查询与当前航司相关的改签记录。"""
    change_type = str(request.args.get("change_type", "")).strip()
    status = str(request.args.get("status", "")).strip()

    conditions = [
        "(old_fni.airline_id = %s OR new_fni.airline_id = %s)",
    ]

    parameters = [
        g.current_user["airline_id"],
        g.current_user["airline_id"],
    ]

    if change_type:
        conditions.append("cr.change_type = %s")
        parameters.append(change_type)

    if status:
        conditions.append("cr.status = %s")
        parameters.append(status)

    where_clause = " AND ".join(conditions)

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    cr.change_id,
                    cr.old_order_id,
                    cr.new_order_id,
                    cr.rule_id,
                    cr.change_type,
                    cr.irregularity_id,
                    cr.old_ticket_price,
                    cr.new_ticket_price,
                    cr.fare_difference,
                    cr.change_fee,
                    cr.payable_amount,
                    cr.refundable_amount,
                    cr.operator_user_id,
                    cr.change_reason,
                    cr.status,
                    cr.created_at,
                    cr.completed_at,
                    old_fi.flight_no AS old_flight_no,
                    old_ac.airline_name AS old_airline_name,
                    new_fi.flight_no AS new_flight_no,
                    new_ac.airline_name AS new_airline_name
                FROM change_record AS cr
                JOIN archive_ticket_sale AS old_order
                  ON old_order.order_id = cr.old_order_id
                JOIN flight_instance AS old_fi
                  ON old_fi.instance_id = old_order.instance_id
                JOIN flight_no_info AS old_fni
                  ON old_fni.flight_no = old_fi.flight_no
                JOIN airline_company AS old_ac
                  ON old_ac.airline_id = old_fni.airline_id
                JOIN (
                    SELECT order_id, instance_id
                    FROM active_ticket_sale

                    UNION ALL

                    SELECT order_id, instance_id
                    FROM archive_ticket_sale
                ) AS new_order
                  ON new_order.order_id = cr.new_order_id
                JOIN flight_instance AS new_fi
                  ON new_fi.instance_id = new_order.instance_id
                JOIN flight_no_info AS new_fni
                  ON new_fni.flight_no = new_fi.flight_no
                JOIN airline_company AS new_ac
                  ON new_ac.airline_id = new_fni.airline_id
                WHERE {where_clause}
                ORDER BY cr.created_at DESC, cr.change_id DESC
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        records = [
            {
                "changeId": row["change_id"],
                "oldOrderId": row["old_order_id"],
                "newOrderId": row["new_order_id"],
                "ruleId": row["rule_id"],
                "changeType": row["change_type"],
                "irregularityId": row["irregularity_id"],
                "oldFlightNo": row["old_flight_no"],
                "oldAirlineName": row["old_airline_name"],
                "newFlightNo": row["new_flight_no"],
                "newAirlineName": row["new_airline_name"],
                "oldTicketPrice": float(row["old_ticket_price"]),
                "newTicketPrice": float(row["new_ticket_price"]),
                "fareDifference": float(row["fare_difference"]),
                "changeFee": float(row["change_fee"]),
                "payableAmount": float(row["payable_amount"]),
                "refundableAmount": float(row["refundable_amount"]),
                "operatorUserId": row["operator_user_id"],
                "changeReason": row["change_reason"],
                "status": row["status"],
                "createdAt": row["created_at"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "completedAt": (
                    row["completed_at"].isoformat(
                        sep=" ",
                        timespec="seconds",
                    )
                    if row["completed_at"] is not None
                    else None
                ),
            }
            for row in rows
        ]

        return success_response(records, "查询成功")

    except Exception as error:
        return error_response("航司改签记录查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()