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


ALLOWED_RULE_TYPES = {
    "乘客主动退票",
    "航司原因退票",
    "乘客主动改签",
    "航司原因同航司改签",
    "航司原因跨航司改签",
}

ALLOWED_STATUSES = {
    "启用",
    "停用",
}


def resolve_airline_id():
    if g.current_user.get("role") == "系统总管理员":
        airline_id = request.args.get("airline_id") or (request.get_json(silent=True) or {}).get("airline_id")

        if not airline_id:
            return None, error_response("系统总管理员需要先选择航空公司")

        try:
            return int(airline_id), None
        except (TypeError, ValueError):
            return None, error_response("航空公司参数不合法")

    return g.current_user["airline_id"], None


def serialize_rule(row):
    return {
        "ruleId": row["rule_id"],
        "airlineId": row["airline_id"],
        "changeType": row["change_type"],
        "minHoursBeforeDeparture": row["min_hours_before_departure"],
        "maxHoursBeforeDeparture": row["max_hours_before_departure"],
        "feeRate": float(row["fee_rate"]),
        "chargePositiveDifference": bool(row["charge_positive_difference"]),
        "refundNegativeDifference": bool(row["refund_negative_difference"]),
        "validFrom": row["valid_from"].isoformat(sep=" ", timespec="seconds"),
        "validTo": (
            row["valid_to"].isoformat(sep=" ", timespec="seconds")
            if row["valid_to"] is not None
            else None
        ),
        "status": row["status"],
        "createdBy": row["created_by"],
        "createdAt": row["created_at"].isoformat(sep=" ", timespec="seconds"),
        "updatedAt": row["updated_at"].isoformat(sep=" ", timespec="seconds"),
    }


def validate_rule_payload(data, old_rule=None, require_valid_range=False):
    change_type = str(data.get("change_type", old_rule["change_type"] if old_rule else "")).strip()
    min_hours = data.get(
        "min_hours_before_departure",
        old_rule["min_hours_before_departure"] if old_rule else None,
    )
    max_hours = data.get(
        "max_hours_before_departure",
        old_rule["max_hours_before_departure"] if old_rule else None,
    )
    fee_rate = data.get("fee_rate", float(old_rule["fee_rate"]) if old_rule else None)
    charge_positive_difference = data.get(
        "charge_positive_difference",
        bool(old_rule["charge_positive_difference"]) if old_rule else True,
    )
    refund_negative_difference = data.get(
        "refund_negative_difference",
        bool(old_rule["refund_negative_difference"]) if old_rule else False,
    )
    status = str(data.get("status", old_rule["status"] if old_rule else "启用")).strip()

    if change_type not in ALLOWED_RULE_TYPES:
        return None, error_response("退改签类型不合法")

    if type(min_hours) is not int or min_hours < 0:
        return None, error_response("距离起飞时间下限必须为非负整数")

    if max_hours is not None:
        if type(max_hours) is not int or max_hours <= min_hours:
            return None, error_response("距离起飞时间上限必须大于下限")

    if type(fee_rate) not in (int, float) or not 0 <= fee_rate <= 1:
        return None, error_response("手续费比例必须在 0 到 1 之间")

    if type(charge_positive_difference) is not bool:
        return None, error_response("是否补差价必须为布尔值")

    if type(refund_negative_difference) is not bool:
        return None, error_response("是否退差价必须为布尔值")

    if status not in ALLOWED_STATUSES:
        return None, error_response("规则状态不合法")

    if "退票" in change_type:
        charge_positive_difference = False
        refund_negative_difference = True

    valid_from = old_rule["valid_from"] if old_rule else None
    valid_to = old_rule["valid_to"] if old_rule else None

    if require_valid_range:
        valid_from_text = str(data.get("valid_from", "")).strip()
        valid_to_text = str(data.get("valid_to", "")).strip()

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
            return None, error_response("规则生效时间格式不正确")

        if valid_to is not None and valid_to <= valid_from:
            return None, error_response("规则失效时间必须晚于生效时间")

    return {
        "change_type": change_type,
        "min_hours": min_hours,
        "max_hours": max_hours,
        "fee_rate": fee_rate,
        "charge_positive_difference": charge_positive_difference,
        "refund_negative_difference": refund_negative_difference,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "status": status,
    }, None


def find_overlap_rule(cursor, airline_id, payload, exclude_rule_id=None):
    params = [
        airline_id,
        payload["change_type"],
        payload["min_hours"],
        payload["max_hours"],
        payload["max_hours"],
        payload["valid_from"],
        payload["valid_to"],
        payload["valid_to"],
    ]

    exclude_clause = ""

    if exclude_rule_id is not None:
        exclude_clause = "AND rule_id <> %s"
        params.insert(1, exclude_rule_id)

    cursor.execute(
        f"""
        SELECT rule_id
        FROM change_rule
        WHERE airline_id = %s
          {exclude_clause}
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
        tuple(params),
    )

    return cursor.fetchone()


@admin_rule_bp.get("/change-rules")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def list_change_rules():
    change_type = str(request.args.get("change_type", "")).strip()
    status = str(request.args.get("status", "")).strip()

    conditions = []
    parameters = []

    is_system_admin = (
        g.current_user.get("role") in ("系统总管理员", "平台总管理员", "总管理员")
        or g.current_user.get("admin_role") in ("系统总管理员", "平台总管理员", "总管理员")
    )

    if is_system_admin:
        airline_id = request.args.get("airline_id")

        if airline_id not in (None, ""):
            try:
                airline_id = int(airline_id)
            except (TypeError, ValueError):
                return error_response("航空公司参数不合法")

            conditions.append("cr.airline_id = %s")
            parameters.append(airline_id)
    else:
        airline_id = g.current_user.get("airline_id")

        if airline_id is None:
            return error_response("当前管理员未绑定航空公司", 403)

        conditions.append("cr.airline_id = %s")
        parameters.append(airline_id)

    if change_type:
        conditions.append("cr.change_type = %s")
        parameters.append(change_type)

    if status:
        conditions.append("cr.status = %s")
        parameters.append(status)

    where_clause = " AND ".join(conditions) if conditions else "1 = 1"

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    cr.rule_id,
                    cr.airline_id,
                    ac.airline_name,
                    cr.change_type,
                    cr.min_hours_before_departure,
                    cr.max_hours_before_departure,
                    cr.fee_rate,
                    cr.charge_positive_difference,
                    cr.refund_negative_difference,
                    cr.valid_from,
                    cr.valid_to,
                    cr.status,
                    cr.created_by,
                    cr.created_at,
                    cr.updated_at
                FROM change_rule AS cr
                JOIN airline_company AS ac
                  ON ac.airline_id = cr.airline_id
                WHERE {where_clause}
                ORDER BY cr.airline_id, cr.change_type, cr.min_hours_before_departure DESC, cr.rule_id
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        records = []

        for row in rows:
            records.append(
                {
                    "ruleId": row["rule_id"],
                    "rule_id": row["rule_id"],
                    "airlineId": row["airline_id"],
                    "airline_id": row["airline_id"],
                    "airlineName": row["airline_name"],
                    "airline_name": row["airline_name"],
                    "changeType": row["change_type"],
                    "change_type": row["change_type"],
                    "minHoursBeforeDeparture": row["min_hours_before_departure"],
                    "min_hours_before_departure": row["min_hours_before_departure"],
                    "maxHoursBeforeDeparture": row["max_hours_before_departure"],
                    "max_hours_before_departure": row["max_hours_before_departure"],
                    "feeRate": float(row["fee_rate"] or 0),
                    "fee_rate": float(row["fee_rate"] or 0),
                    "chargePositiveDifference": bool(row["charge_positive_difference"]),
                    "charge_positive_difference": bool(row["charge_positive_difference"]),
                    "refundNegativeDifference": bool(row["refund_negative_difference"]),
                    "refund_negative_difference": bool(row["refund_negative_difference"]),
                    "validFrom": row["valid_from"].isoformat(sep=" ", timespec="seconds"),
                    "valid_from": row["valid_from"].isoformat(sep=" ", timespec="seconds"),
                    "validTo": (
                        row["valid_to"].isoformat(sep=" ", timespec="seconds")
                        if row["valid_to"] is not None
                        else None
                    ),
                    "valid_to": (
                        row["valid_to"].isoformat(sep=" ", timespec="seconds")
                        if row["valid_to"] is not None
                        else None
                    ),
                    "status": row["status"],
                    "createdBy": row["created_by"],
                    "created_by": row["created_by"],
                    "createdAt": row["created_at"].isoformat(sep=" ", timespec="seconds"),
                    "created_at": row["created_at"].isoformat(sep=" ", timespec="seconds"),
                    "updatedAt": row["updated_at"].isoformat(sep=" ", timespec="seconds"),
                    "updated_at": row["updated_at"].isoformat(sep=" ", timespec="seconds"),
                }
            )

        return success_response(records, "查询成功")

    except Exception as error:
        return error_response("退改签规则查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_rule_bp.post("/change-rules")
@admin_role_required("航司主管理员")
def create_change_rule():
    """新增退改签规则。"""
    data = request.get_json(silent=True) or {}

    airline_id, error = resolve_airline_id()
    if error:
        return error

    payload, error = validate_rule_payload(data, require_valid_range=True)
    if error:
        return error

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            if payload["status"] == "启用":
                if find_overlap_rule(cursor, airline_id, payload) is not None:
                    return error_response("该时间范围与已有启用规则重叠", 409)

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
                    airline_id,
                    payload["change_type"],
                    payload["min_hours"],
                    payload["max_hours"],
                    payload["fee_rate"],
                    payload["charge_positive_difference"],
                    payload["refund_negative_difference"],
                    payload["valid_from"],
                    payload["valid_to"],
                    payload["status"],
                    g.current_user["user_id"],
                ),
            )

            rule_id = cursor.lastrowid

        connection.commit()

        return success_response(
            {
                "ruleId": rule_id,
                "airlineId": airline_id,
                "changeType": payload["change_type"],
                "minHoursBeforeDeparture": payload["min_hours"],
                "maxHoursBeforeDeparture": payload["max_hours"],
                "feeRate": payload["fee_rate"],
                "chargePositiveDifference": payload["charge_positive_difference"],
                "refundNegativeDifference": payload["refund_negative_difference"],
                "status": payload["status"],
            },
            "退改签规则新增成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("退改签规则新增失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_rule_bp.put("/change-rules/<int:rule_id>")
@admin_role_required("航司主管理员")
def update_change_rule(rule_id):
    """修改当前航司已有的退改签规则。"""
    data = request.get_json(silent=True) or {}

    airline_id, error = resolve_airline_id()
    if error:
        return error

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
                    airline_id,
                ),
            )

            old_rule = cursor.fetchone()

            if old_rule is None:
                return error_response("未找到本航司的该退改签规则", 404)

            payload, error = validate_rule_payload(data, old_rule=old_rule)
            if error:
                return error

            if payload["status"] == "启用":
                if find_overlap_rule(cursor, airline_id, payload, exclude_rule_id=rule_id) is not None:
                    return error_response("修改后的时间范围与已有启用规则重叠", 409)

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
                    payload["change_type"],
                    payload["min_hours"],
                    payload["max_hours"],
                    payload["fee_rate"],
                    payload["charge_positive_difference"],
                    payload["refund_negative_difference"],
                    payload["status"],
                    rule_id,
                ),
            )

        connection.commit()

        return success_response(
            {
                "ruleId": rule_id,
                "changeType": payload["change_type"],
                "minHoursBeforeDeparture": payload["min_hours"],
                "maxHoursBeforeDeparture": payload["max_hours"],
                "feeRate": payload["fee_rate"],
                "chargePositiveDifference": payload["charge_positive_difference"],
                "refundNegativeDifference": payload["refund_negative_difference"],
                "status": payload["status"],
            },
            "退改签规则修改成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("退改签规则修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
