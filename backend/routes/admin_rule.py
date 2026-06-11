from datetime import datetime

from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import admin_role_required, role_required
from utils.response import error_response, success_response


admin_rule_bp = Blueprint(
    "admin_rule",
    __name__,
    url_prefix="/api/admin",
)


@admin_rule_bp.get("/change-rules")
@role_required("航空公司管理员")
def list_change_rules():
    """查询当前航司的改签规则。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    rule_id,
                    airline_id,
                    change_type,
                    min_hours_before_departure,
                    max_hours_before_departure,
                    fee_rate,
                    charge_positive_difference,
                    refund_negative_difference,
                    valid_from,
                    valid_to,
                    status,
                    created_by,
                    created_at,
                    updated_at
                FROM change_rule
                WHERE airline_id = %s
                ORDER BY change_type,
                         min_hours_before_departure DESC,
                         rule_id
                """,
                (g.current_user["airline_id"],),
            )

            rows = cursor.fetchall()

        rules = [
            {
                "ruleId": row["rule_id"],
                "airlineId": row["airline_id"],
                "changeType": row["change_type"],
                "minHoursBeforeDeparture": row[
                    "min_hours_before_departure"
                ],
                "maxHoursBeforeDeparture": row[
                    "max_hours_before_departure"
                ],
                "feeRate": float(row["fee_rate"]),
                "chargePositiveDifference": bool(
                    row["charge_positive_difference"]
                ),
                "refundNegativeDifference": bool(
                    row["refund_negative_difference"]
                ),
                "validFrom": row["valid_from"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "validTo": (
                    row["valid_to"].isoformat(
                        sep=" ",
                        timespec="seconds",
                    )
                    if row["valid_to"] is not None
                    else None
                ),
                "status": row["status"],
                "createdBy": row["created_by"],
                "createdAt": row["created_at"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "updatedAt": row["updated_at"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
            }
            for row in rows
        ]

        return success_response(rules, "查询成功")

    except Exception as error:
        return error_response("改签规则查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_rule_bp.post("/change-rules")
@admin_role_required("航司主管理员", "订单管理员")
def create_change_rule():
    """为当前航司新增改签规则。"""
    data = request.get_json(silent=True) or {}

    change_type = str(data.get("change_type", "")).strip()
    min_hours = data.get("min_hours_before_departure")
    max_hours = data.get("max_hours_before_departure")
    fee_rate = data.get("fee_rate")
    charge_positive_difference = data.get(
        "charge_positive_difference",
        True,
    )
    refund_negative_difference = data.get(
        "refund_negative_difference",
        False,
    )
    valid_from_text = str(data.get("valid_from", "")).strip()
    valid_to_text = str(data.get("valid_to", "")).strip()
    status = str(data.get("status", "启用")).strip()

    allowed_change_types = {
        "乘客主动改签",
        "航司原因同航司改签",
        "航司原因跨航司改签",
    }

    if change_type not in allowed_change_types:
        return error_response("改签类型不合法")

    if type(min_hours) is not int or min_hours < 0:
        return error_response("距离起飞时间下限必须为非负整数")

    if max_hours is not None:
        if type(max_hours) is not int or max_hours <= min_hours:
            return error_response("距离起飞时间上限必须大于下限")

    if type(fee_rate) not in (int, float) or not 0 <= fee_rate <= 1:
        return error_response("手续费比例必须在 0 到 1 之间")

    if type(charge_positive_difference) is not bool:
        return error_response("是否补差价必须为布尔值")

    if type(refund_negative_difference) is not bool:
        return error_response("是否退差价必须为布尔值")

    if status not in {"启用", "停用"}:
        return error_response("规则状态不合法")

    try:
        valid_from = (
            datetime.fromisoformat(valid_from_text)
            if valid_from_text
            else datetime.now()
        )

        valid_to = (
            datetime.fromisoformat(valid_to_text)
            if valid_to_text
            else None
        )

    except ValueError:
        return error_response("规则生效时间格式不正确")

    if valid_to is not None and valid_to <= valid_from:
        return error_response("规则失效时间必须晚于生效时间")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            if status == "启用":
                cursor.execute(
                    """
                    SELECT rule_id
                    FROM change_rule
                    WHERE airline_id = %s
                      AND change_type = %s
                      AND status = '启用'
                      AND (
                          max_hours_before_departure IS NULL
                          OR max_hours_before_departure > %s
                      )
                      AND (
                          %s IS NULL
                          OR min_hours_before_departure < %s
                      )
                      AND (
                          valid_to IS NULL
                          OR valid_to > %s
                      )
                      AND (
                          %s IS NULL
                          OR valid_from < %s
                      )
                    LIMIT 1
                    """,
                    (
                        g.current_user["airline_id"],
                        change_type,
                        min_hours,
                        max_hours,
                        max_hours,
                        valid_from,
                        valid_to,
                        valid_to,
                    ),
                )

                if cursor.fetchone() is not None:
                    return error_response(
                        "该时间范围与已有启用规则重叠",
                        409,
                    )

            cursor.execute(
                """
                INSERT INTO change_rule (
                    airline_id,
                    change_type,
                    min_hours_before_departure,
                    max_hours_before_departure,
                    fee_rate,
                    charge_positive_difference,
                    refund_negative_difference,
                    valid_from,
                    valid_to,
                    status,
                    created_by,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, NOW(), NOW()
                )
                """,
                (
                    g.current_user["airline_id"],
                    change_type,
                    min_hours,
                    max_hours,
                    fee_rate,
                    charge_positive_difference,
                    refund_negative_difference,
                    valid_from,
                    valid_to,
                    status,
                    g.current_user["user_id"],
                ),
            )

            rule_id = cursor.lastrowid

        connection.commit()

        return success_response(
            {
                "ruleId": rule_id,
                "airlineId": g.current_user["airline_id"],
                "changeType": change_type,
                "minHoursBeforeDeparture": min_hours,
                "maxHoursBeforeDeparture": max_hours,
                "feeRate": fee_rate,
                "chargePositiveDifference": charge_positive_difference,
                "refundNegativeDifference": refund_negative_difference,
                "status": status,
            },
            "改签规则新增成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("改签规则新增失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@admin_rule_bp.put("/change-rules/<int:rule_id>")
@admin_role_required("航司主管理员", "订单管理员")
def update_change_rule(rule_id):
    """修改当前航司已有的改签规则。"""
    data = request.get_json(silent=True) or {}

    allowed_change_types = {
        "乘客主动改签",
        "航司原因同航司改签",
        "航司原因跨航司改签",
    }

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    rule_id,
                    change_type,
                    min_hours_before_departure,
                    max_hours_before_departure,
                    fee_rate,
                    charge_positive_difference,
                    refund_negative_difference,
                    valid_from,
                    valid_to,
                    status
                FROM change_rule
                WHERE rule_id = %s
                  AND airline_id = %s
                FOR UPDATE
                """,
                (
                    rule_id,
                    g.current_user["airline_id"],
                ),
            )

            rule = cursor.fetchone()

            if rule is None:
                return error_response("未找到本航司的该改签规则", 404)

            change_type = str(
                data.get("change_type", rule["change_type"])
            ).strip()

            min_hours = data.get(
                "min_hours_before_departure",
                rule["min_hours_before_departure"],
            )

            max_hours = data.get(
                "max_hours_before_departure",
                rule["max_hours_before_departure"],
            )

            fee_rate = data.get(
                "fee_rate",
                float(rule["fee_rate"]),
            )

            charge_positive_difference = data.get(
                "charge_positive_difference",
                bool(rule["charge_positive_difference"]),
            )

            refund_negative_difference = data.get(
                "refund_negative_difference",
                bool(rule["refund_negative_difference"]),
            )

            status = str(
                data.get("status", rule["status"])
            ).strip()

            if change_type not in allowed_change_types:
                return error_response("改签类型不合法")

            if type(min_hours) is not int or min_hours < 0:
                return error_response("距离起飞时间下限必须为非负整数")

            if max_hours is not None:
                if type(max_hours) is not int or max_hours <= min_hours:
                    return error_response("距离起飞时间上限必须大于下限")

            if type(fee_rate) not in (int, float) or not 0 <= fee_rate <= 1:
                return error_response("手续费比例必须在 0 到 1 之间")

            if type(charge_positive_difference) is not bool:
                return error_response("是否补差价必须为布尔值")

            if type(refund_negative_difference) is not bool:
                return error_response("是否退差价必须为布尔值")

            if status not in {"启用", "停用"}:
                return error_response("规则状态不合法")

            if status == "启用":
                cursor.execute(
                    """
                    SELECT rule_id
                    FROM change_rule
                    WHERE airline_id = %s
                      AND rule_id <> %s
                      AND change_type = %s
                      AND status = '启用'
                      AND (
                          max_hours_before_departure IS NULL
                          OR max_hours_before_departure > %s
                      )
                      AND (
                          %s IS NULL
                          OR min_hours_before_departure < %s
                      )
                      AND (
                          valid_to IS NULL
                          OR valid_to > %s
                      )
                      AND (
                          %s IS NULL
                          OR valid_from < %s
                      )
                    LIMIT 1
                    """,
                    (
                        g.current_user["airline_id"],
                        rule_id,
                        change_type,
                        min_hours,
                        max_hours,
                        max_hours,
                        rule["valid_from"],
                        rule["valid_to"],
                        rule["valid_to"],
                    ),
                )

                if cursor.fetchone() is not None:
                    return error_response(
                        "修改后的时间范围与已有启用规则重叠",
                        409,
                    )

            cursor.execute(
                """
                UPDATE change_rule
                SET change_type = %s,
                    min_hours_before_departure = %s,
                    max_hours_before_departure = %s,
                    fee_rate = %s,
                    charge_positive_difference = %s,
                    refund_negative_difference = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE rule_id = %s
                """,
                (
                    change_type,
                    min_hours,
                    max_hours,
                    fee_rate,
                    charge_positive_difference,
                    refund_negative_difference,
                    status,
                    rule_id,
                ),
            )

        connection.commit()

        return success_response(
            {
                "ruleId": rule_id,
                "changeType": change_type,
                "minHoursBeforeDeparture": min_hours,
                "maxHoursBeforeDeparture": max_hours,
                "feeRate": fee_rate,
                "chargePositiveDifference": charge_positive_difference,
                "refundNegativeDifference": refund_negative_difference,
                "status": status,
            },
            "改签规则修改成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("改签规则修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()