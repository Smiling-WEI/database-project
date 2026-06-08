from datetime import date, datetime

from flask import Blueprint, g, request

from db import get_db_connection
from services.change_service import (
    calculate_change_amounts,
    determine_change_type,
    find_active_airline_irregularity,
    find_matching_change_rule,
    get_hours_before_departure,
)
from utils.auth import login_required
from utils.response import error_response, success_response


change_bp = Blueprint("change", __name__, url_prefix="/api")


def build_change_context(
    cursor,
    user_id,
    order_id,
    data,
    lock_rows=False,
):
    """校验改签条件，匹配规则并计算金额。"""
    new_pricing_id = data.get("new_pricing_id")
    new_seat_no = str(data.get("new_seat_no", "")).strip() or None
    reason_type = str(
        data.get("reason_type", "乘客主动改签")
    ).strip()

    if type(new_pricing_id) is not int:
        return None, "新舱位价格编号必须为整数", 400

    if new_seat_no is not None and len(new_seat_no) > 10:
        return None, "座位号不能超过 10 个字符", 400

    lock_clause = " FOR UPDATE" if lock_rows else ""

    cursor.execute(
        f"""
        SELECT
            ats.order_id,
            ats.user_id,
            ats.passenger_id,
            ats.instance_id AS old_instance_id,
            ats.pricing_id AS old_pricing_id,
            ats.seat_no AS old_seat_no,
            ats.purchase_time AS old_purchase_time,
            ats.order_status,
            old_cp.cabin_type AS old_cabin_type,
            old_cp.sale_price AS old_ticket_price,
            old_fi.flight_no AS old_flight_no,
            old_fi.flight_date AS old_flight_date,
            old_fi.status AS old_flight_status,
            old_fni.airline_id AS old_airline_id,
            old_fni.route_id AS old_route_id
        FROM active_ticket_sale AS ats
        JOIN cabin_pricing AS old_cp
          ON old_cp.pricing_id = ats.pricing_id
        JOIN flight_instance AS old_fi
          ON old_fi.instance_id = ats.instance_id
        JOIN flight_no_info AS old_fni
          ON old_fni.flight_no = old_fi.flight_no
        WHERE ats.order_id = %s
          AND ats.user_id = %s
        LIMIT 1
        {lock_clause}
        """,
        (
            order_id,
            user_id,
        ),
    )

    old_order = cursor.fetchone()

    if old_order is None:
        return None, "未找到该有效订单", 404

    if old_order["order_status"] != "已支付":
        return None, "当前订单状态不允许改签", 409

    if old_order["old_flight_status"] == "已完成":
        return None, "已完成的航班不能改签", 409

    cursor.execute(
        f"""
        SELECT
            cp.pricing_id AS new_pricing_id,
            cp.instance_id AS new_instance_id,
            cp.cabin_type AS new_cabin_type,
            cp.sale_price AS new_ticket_price,
            cp.valid_from,
            cp.valid_to,
            new_fi.flight_no AS new_flight_no,
            new_fi.flight_date AS new_flight_date,
            new_fi.status AS new_flight_status,
            new_fni.airline_id AS new_airline_id,
            new_fni.route_id AS new_route_id,
            CASE
                WHEN cp.cabin_type = '头等舱' THEN new_fi.first_seats
                WHEN cp.cabin_type = '经济舱' THEN new_fi.economy_seats
                ELSE 0
            END AS total_seats
        FROM cabin_pricing AS cp
        JOIN flight_instance AS new_fi
          ON new_fi.instance_id = cp.instance_id
        JOIN flight_no_info AS new_fni
          ON new_fni.flight_no = new_fi.flight_no
        WHERE cp.pricing_id = %s
        LIMIT 1
        {lock_clause}
        """,
        (new_pricing_id,),
    )

    new_pricing = cursor.fetchone()

    if new_pricing is None:
        return None, "未找到新的舱位价格", 404

    if new_pricing["new_flight_status"] in ("取消", "已完成"):
        return None, "目标航班当前不可改签", 409

    if new_pricing["new_flight_date"] < date.today():
        return None, "不能改签到已经结束的日期", 409

    now = datetime.now()

    if (
        new_pricing["valid_from"] > now
        or new_pricing["valid_to"] < now
    ):
        return None, "目标舱位价格当前无效", 409

    if new_pricing["new_route_id"] != old_order["old_route_id"]:
        return None, "新航班必须与原订单属于同一航线", 409

    if new_pricing_id == old_order["old_pricing_id"]:
        return None, "新旧机票完全相同，无需改签", 409

    if new_pricing["total_seats"] <= 0:
        return None, "目标舱位暂不支持售票", 409

    cursor.execute(
        """
        SELECT 1
        FROM active_ticket_sale
        WHERE passenger_id = %s
          AND instance_id = %s
          AND order_status = '已支付'
          AND order_id <> %s
        LIMIT 1
        """,
        (
            old_order["passenger_id"],
            new_pricing["new_instance_id"],
            old_order["order_id"],
        ),
    )

    if cursor.fetchone() is not None:
        return None, "该乘机人已经持有目标航班的有效机票", 409

    cursor.execute(
        """
        SELECT COUNT(*) AS sold_count
        FROM active_ticket_sale AS ats
        JOIN cabin_pricing AS sold_cp
          ON sold_cp.pricing_id = ats.pricing_id
        WHERE ats.instance_id = %s
          AND sold_cp.cabin_type = %s
          AND ats.order_status = '已支付'
          AND ats.order_id <> %s
        """,
        (
            new_pricing["new_instance_id"],
            new_pricing["new_cabin_type"],
            old_order["order_id"],
        ),
    )

    sold_count = cursor.fetchone()["sold_count"]

    if sold_count >= new_pricing["total_seats"]:
        return None, "目标舱位已经售罄", 409

    if new_seat_no is not None:
        cursor.execute(
            """
            SELECT 1
            FROM active_ticket_sale
            WHERE instance_id = %s
              AND seat_no = %s
              AND order_status = '已支付'
              AND order_id <> %s
            LIMIT 1
            """,
            (
                new_pricing["new_instance_id"],
                new_seat_no,
                old_order["order_id"],
            ),
        )

        if cursor.fetchone() is not None:
            return None, "目标座位已经被占用", 409

    irregularity = find_active_airline_irregularity(
        cursor,
        old_order["old_instance_id"],
    )

    change_type, change_type_error = determine_change_type(
        reason_type,
        old_order["old_airline_id"],
        new_pricing["new_airline_id"],
        irregularity,
    )

    if change_type_error is not None:
        return None, change_type_error, 409

    hours_before_departure = get_hours_before_departure(
        old_order["old_flight_date"]
    )

    rule = find_matching_change_rule(
        cursor,
        old_order["old_airline_id"],
        change_type,
        hours_before_departure,
    )

    if rule is None:
        return None, "未找到适用的改签规则", 409

    amounts = calculate_change_amounts(
        old_order["old_ticket_price"],
        new_pricing["new_ticket_price"],
        rule,
        change_type,
    )

    return {
        "old_order": old_order,
        "new_pricing": new_pricing,
        "new_seat_no": new_seat_no,
        "reason_type": reason_type,
        "change_type": change_type,
        "irregularity": irregularity,
        "rule": rule,
        "hours_before_departure": hours_before_departure,
        "amounts": amounts,
    }, None, None


def serialize_change_context(context):
    """将改签计算结果转换为前端可以直接使用的数据。"""
    old_order = context["old_order"]
    new_pricing = context["new_pricing"]
    amounts = context["amounts"]

    return {
        "oldOrderId": old_order["order_id"],
        "oldInstanceId": old_order["old_instance_id"],
        "oldFlightNo": old_order["old_flight_no"],
        "oldCabinType": old_order["old_cabin_type"],
        "oldTicketPrice": float(amounts["old_ticket_price"]),
        "newInstanceId": new_pricing["new_instance_id"],
        "newFlightNo": new_pricing["new_flight_no"],
        "newCabinType": new_pricing["new_cabin_type"],
        "newTicketPrice": float(amounts["new_ticket_price"]),
        "newSeatNo": context["new_seat_no"],
        "changeType": context["change_type"],
        "ruleId": context["rule"]["rule_id"],
        "irregularityId": (
            context["irregularity"]["irregularity_id"]
            if context["irregularity"] is not None
            else None
        ),
        "hoursBeforeDeparture": context["hours_before_departure"],
        "fareDifference": float(amounts["fare_difference"]),
        "changeFee": float(amounts["change_fee"]),
        "payableAmount": float(amounts["payable_amount"]),
        "refundableAmount": float(amounts["refundable_amount"]),
    }


@change_bp.post("/orders/<int:order_id>/change-preview")
@login_required
def preview_change_order(order_id):
    """预览改签手续费、票价差额和最终应补或应退金额。"""
    data = request.get_json(silent=True) or {}

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            context, message, status_code = build_change_context(
                cursor,
                g.current_user["user_id"],
                order_id,
                data,
            )

        if context is None:
            return error_response(message, status_code)

        return success_response(
            serialize_change_context(context),
            "改签金额计算成功",
        )

    except Exception as error:
        return error_response("改签金额计算失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@change_bp.post("/orders/<int:order_id>/change")
@login_required
def change_order(order_id):
    """执行改签：归档原订单，创建新订单，并保存改签记录。"""
    data = request.get_json(silent=True) or {}

    change_reason = str(
        data.get("change_reason", "")
    ).strip() or None

    if change_reason is not None and len(change_reason) > 500:
        return error_response("改签原因说明不能超过 500 个字符")

    connection = None

    try:
        connection = get_db_connection()
        connection.begin()

        with connection.cursor() as cursor:
            context, message, status_code = build_change_context(
                cursor,
                g.current_user["user_id"],
                order_id,
                data,
                lock_rows=True,
            )

            if context is None:
                connection.rollback()
                return error_response(message, status_code)

            old_order = context["old_order"]
            new_pricing = context["new_pricing"]
            amounts = context["amounts"]

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
                VALUES (%s, %s, %s, %s, %s, %s, %s, '已改签')
                """,
                (
                    old_order["order_id"],
                    old_order["user_id"],
                    old_order["passenger_id"],
                    old_order["old_instance_id"],
                    old_order["old_pricing_id"],
                    old_order["old_seat_no"],
                    old_order["old_purchase_time"],
                ),
            )

            cursor.execute(
                """
                DELETE FROM active_ticket_sale
                WHERE order_id = %s
                """,
                (old_order["order_id"],),
            )

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
                    old_order["user_id"],
                    old_order["passenger_id"],
                    new_pricing["new_instance_id"],
                    new_pricing["new_pricing_id"],
                    context["new_seat_no"],
                ),
            )

            new_order_id = cursor.lastrowid

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
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, '已完成', NOW(), NOW()
                )
                """,
                (
                    old_order["order_id"],
                    new_order_id,
                    context["rule"]["rule_id"],
                    context["change_type"],
                    (
                        context["irregularity"]["irregularity_id"]
                        if context["irregularity"] is not None
                        else None
                    ),
                    amounts["old_ticket_price"],
                    amounts["new_ticket_price"],
                    amounts["fare_difference"],
                    amounts["change_fee"],
                    amounts["payable_amount"],
                    amounts["refundable_amount"],
                    g.current_user["user_id"],
                    change_reason,
                ),
            )

            change_id = cursor.lastrowid

        connection.commit()

        response_data = serialize_change_context(context)
        response_data["changeId"] = change_id
        response_data["newOrderId"] = new_order_id
        response_data["status"] = "已完成"

        return success_response(
            response_data,
            "改签成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("改签失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@change_bp.get("/change-records")
@login_required
def list_change_records():
    """查询当前用户的全部改签记录。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
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
                    cr.change_reason,
                    cr.status,
                    cr.created_at,
                    cr.completed_at
                FROM change_record AS cr
                JOIN archive_ticket_sale AS old_order
                  ON old_order.order_id = cr.old_order_id
                WHERE old_order.user_id = %s
                ORDER BY cr.created_at DESC, cr.change_id DESC
                """,
                (g.current_user["user_id"],),
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
                "oldTicketPrice": float(row["old_ticket_price"]),
                "newTicketPrice": float(row["new_ticket_price"]),
                "fareDifference": float(row["fare_difference"]),
                "changeFee": float(row["change_fee"]),
                "payableAmount": float(row["payable_amount"]),
                "refundableAmount": float(row["refundable_amount"]),
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
        return error_response("改签记录查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()