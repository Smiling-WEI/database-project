from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP


MONEY_UNIT = Decimal("0.01")


def to_money(value):
    """将金额统一保留两位小数。"""
    return Decimal(str(value)).quantize(
        MONEY_UNIT,
        rounding=ROUND_HALF_UP,
    )


def get_hours_before_departure(flight_date):
    """计算距离原航班起飞日期结束时刻的剩余小时数。"""
    departure_datetime = datetime.combine(
        flight_date,
        time(23, 59, 59),
    )

    remaining_seconds = (
        departure_datetime - datetime.now()
    ).total_seconds()

    return max(int(remaining_seconds // 3600), 0)


def find_active_airline_irregularity(cursor, instance_id):
    """查找当前航班仍在生效的航司原因异常记录。"""
    cursor.execute(
        """
        SELECT
            irregularity_id,
            responsibility_type
        FROM flight_irregularity
        WHERE instance_id = %s
          AND responsibility_type = '航司原因'
          AND status = '生效中'
        ORDER BY created_at DESC, irregularity_id DESC
        LIMIT 1
        """,
        (instance_id,),
    )

    return cursor.fetchone()


def determine_change_type(
    requested_reason_type,
    old_airline_id,
    new_airline_id,
    irregularity,
):
    """根据用户选择和航司归属确定实际适用的改签类型。"""
    if requested_reason_type == "乘客主动改签":
        return "乘客主动改签", None

    if requested_reason_type != "航司原因":
        return None, "改签原因类型不合法"

    if irregularity is None:
        return None, "原航班不存在生效中的航司原因异常记录"

    if old_airline_id == new_airline_id:
        return "航司原因同航司改签", None

    return "航司原因跨航司改签", None


def find_matching_change_rule(
    cursor,
    airline_id,
    change_type,
    hours_before_departure,
):
    """查找当前航司在指定时间段内生效的改签规则。"""
    cursor.execute(
        """
        SELECT
            rule_id,
            fee_rate,
            charge_positive_difference,
            refund_negative_difference
        FROM change_rule
        WHERE airline_id = %s
          AND change_type = %s
          AND status = '启用'
          AND min_hours_before_departure <= %s
          AND (
              max_hours_before_departure IS NULL
              OR %s < max_hours_before_departure
          )
          AND valid_from <= NOW()
          AND (
              valid_to IS NULL
              OR valid_to >= NOW()
          )
        ORDER BY min_hours_before_departure DESC, rule_id DESC
        LIMIT 1
        """,
        (
            airline_id,
            change_type,
            hours_before_departure,
            hours_before_departure,
        ),
    )

    return cursor.fetchone()


def calculate_change_amounts(
    old_ticket_price,
    new_ticket_price,
    rule,
    change_type,
):
    """计算差价、手续费、应补金额和应退金额。"""
    old_price = to_money(old_ticket_price)
    new_price = to_money(new_ticket_price)
    fare_difference = to_money(new_price - old_price)

    if change_type == "航司原因同航司改签":
        change_fee = to_money(0)
        payable_amount = to_money(0)
        refundable_amount = to_money(0)

    else:
        change_fee = to_money(
            old_price * Decimal(str(rule["fee_rate"]))
        )

        positive_difference = (
            max(fare_difference, to_money(0))
            if bool(rule["charge_positive_difference"])
            else to_money(0)
        )

        negative_difference = (
            max(-fare_difference, to_money(0))
            if bool(rule["refund_negative_difference"])
            else to_money(0)
        )

        payable_amount = to_money(
            change_fee + positive_difference
        )

        refundable_amount = to_money(
            negative_difference
        )

    return {
        "old_ticket_price": old_price,
        "new_ticket_price": new_price,
        "fare_difference": fare_difference,
        "change_fee": change_fee,
        "payable_amount": payable_amount,
        "refundable_amount": refundable_amount,
    }