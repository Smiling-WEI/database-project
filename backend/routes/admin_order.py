from flask import Blueprint, g, request
from decimal import Decimal

from db import get_db_connection
from utils.auth import role_required
from utils.response import error_response, success_response
from routes.change import build_change_context, serialize_change_context
from routes.order import _load_refund_context, _serialize_refund_context


admin_order_bp = Blueprint(
    "admin_order",
    __name__,
    url_prefix="/api/admin",
)

def is_platform_scope_admin():
    return (
        g.current_user.get("role") in ("系统总管理员", "平台总管理员", "总管理员")
        or g.current_user.get("admin_role") in ("系统总管理员", "平台总管理员", "总管理员")
    )


def get_optional_airline_filter(column_name):
    parameters = []

    if is_platform_scope_admin():
        airline_id = request.args.get("airline_id")

        if airline_id not in (None, ""):
            try:
                airline_id = int(airline_id)
            except (TypeError, ValueError):
                return None, None, error_response("航空公司参数不合法")

            return f"{column_name} = %s", [airline_id], None

        return None, [], None

    airline_id = g.current_user.get("airline_id")

    if airline_id is None:
        return None, None, error_response("当前管理员未绑定航空公司", 403)

    return f"{column_name} = %s", [airline_id], None



@admin_order_bp.get("/orders")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def list_managed_orders():
    """查询订单列表。

    系统总管理员：
    - 不传 airline_id：查全部航空公司订单
    - 传 airline_id：查指定航空公司订单

    航司内部管理员：
    - 永远只查本航司订单
    """
    order_id = str(request.args.get("order_id", "")).strip()
    flight_no = str(request.args.get("flight_no", "")).strip()
    order_status = str(request.args.get("order_status", "")).strip()
    record_type = str(request.args.get("record_type", "")).strip()
    passenger_name = str(request.args.get("passenger_name", "")).strip()
    phone = str(request.args.get("phone", "")).strip()
    start_date = str(request.args.get("start_date", "")).strip()
    end_date = str(request.args.get("end_date", "")).strip()

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

            conditions.append("fni.airline_id = %s")
            parameters.append(airline_id)
    else:
        airline_id = g.current_user.get("airline_id")

        if airline_id is None:
            return error_response("当前管理员未绑定航空公司", 403)

        conditions.append("fni.airline_id = %s")
        parameters.append(airline_id)

    if order_id:
        conditions.append("CAST(o.order_id AS CHAR) LIKE %s")
        parameters.append(f"%{order_id}%")

    if flight_no:
        conditions.append("fi.flight_no LIKE %s")
        parameters.append(f"%{flight_no}%")

    if order_status:
        conditions.append("o.order_status = %s")
        parameters.append(order_status)

    if record_type:
        conditions.append("o.record_type = %s")
        parameters.append(record_type)

    if passenger_name:
        conditions.append("p.real_name LIKE %s")
        parameters.append(f"%{passenger_name}%")

    if phone:
        conditions.append("u.phone LIKE %s")
        parameters.append(f"%{phone}%")

    if start_date:
        conditions.append("DATE(o.purchase_time) >= %s")
        parameters.append(start_date)

    if end_date:
        conditions.append("DATE(o.purchase_time) <= %s")
        parameters.append(end_date)

    where_clause = " AND ".join(conditions) if conditions else "1 = 1"

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    o.order_id,
                    o.user_id,
                    u.username,
                    u.phone,
                    p.real_name AS passenger_name,
                    p.id_card AS passenger_id_card,
                    o.instance_id,
                    fi.flight_no,
                    fi.flight_date,
                    DATE_FORMAT(fi.dep_time, '%%H:%%i') AS dep_time,
                    DATE_FORMAT(fi.arr_time, '%%H:%%i') AS arr_time,
                    fni.airline_id,
                    ac.airline_name,
                    cp.cabin_type,
                    cp.sale_price,
                    o.seat_no,
                    o.purchase_time,
                    o.order_status,
                    o.record_type,
                    o.source_table
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
                        '有效订单' AS record_type,
                        'active' AS source_table
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
                        '历史订单' AS record_type,
                        'archive' AS source_table
                    FROM archive_ticket_sale
                ) AS o
                JOIN `user` AS u
                  ON u.user_id = o.user_id
                JOIN passenger AS p
                  ON p.passenger_id = o.passenger_id
                JOIN flight_instance AS fi
                  ON fi.instance_id = o.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                JOIN airline_company AS ac
                  ON ac.airline_id = fni.airline_id
                LEFT JOIN cabin_pricing AS cp
                  ON cp.pricing_id = o.pricing_id
                WHERE {where_clause}
                ORDER BY o.order_id DESC
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        records = []

        for row in rows:
            records.append(
                {
                    "orderId": row["order_id"],
                    "order_id": row["order_id"],
                    "userId": row["user_id"],
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "phone": row["phone"] or "-",
                    "passengerName": row["passenger_name"],
                    "passenger_name": row["passenger_name"],
                    "passengerIdCard": row["passenger_id_card"],
                    "instanceId": row["instance_id"],
                    "instance_id": row["instance_id"],
                    "flightNo": row["flight_no"],
                    "flight_no": row["flight_no"],
                    "flightDate": row["flight_date"].isoformat(),
                    "flight_date": row["flight_date"].isoformat(),
                    "depTime": row["dep_time"] or "",
                    "arrTime": row["arr_time"] or "",
                    "airlineId": row["airline_id"],
                    "airline_id": row["airline_id"],
                    "airlineName": row["airline_name"],
                    "airline_name": row["airline_name"],
                    "airlineCompany": row["airline_name"],
                    "airline": row["airline_name"],
                    "cabinType": row["cabin_type"],
                    "cabin_type": row["cabin_type"],
                    "ticketPrice": float(row["sale_price"] or 0),
                    "salePrice": float(row["sale_price"] or 0),
                    "price": float(row["sale_price"] or 0),
                    "seatNo": row["seat_no"],
                    "seat_no": row["seat_no"],
                    "purchaseTime": row["purchase_time"].isoformat(sep=" ", timespec="seconds"),
                    "purchase_time": row["purchase_time"].isoformat(sep=" ", timespec="seconds"),
                    "orderStatus": row["order_status"],
                    "order_status": row["order_status"],
                    "recordType": row["record_type"],
                    "record_type": row["record_type"],
                    "sourceTable": row["source_table"],
                    "source_table": row["source_table"],
                }
            )

        return success_response(records, "查询成功")

    except Exception as error:
        return error_response("订单列表查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_order_bp.get("/change-records")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def list_managed_change_records():
    """查询与当前航司相关的改签记录。"""
    change_type = str(request.args.get("change_type", "")).strip()
    status = str(request.args.get("status", "")).strip()

    conditions = []
    parameters = []

    if is_platform_scope_admin():
        airline_id = request.args.get("airline_id")

        if airline_id not in (None, ""):
            try:
                airline_id = int(airline_id)
            except (TypeError, ValueError):
                return error_response("航空公司参数不合法")

            conditions.append("(old_fni.airline_id = %s OR new_fni.airline_id = %s)")
            parameters.extend([airline_id, airline_id])
    else:
        airline_id = g.current_user.get("airline_id")

        if airline_id is None:
            return error_response("当前管理员未绑定航空公司", 403)

        conditions.append("(old_fni.airline_id = %s OR new_fni.airline_id = %s)")
        parameters.extend([airline_id, airline_id])

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


def _is_platform_admin_for_orders():
    return (
        g.current_user.get("role") in ("系统总管理员", "平台总管理员", "总管理员")
        or g.current_user.get("admin_role") in ("系统总管理员", "平台总管理员", "总管理员")
    )


def _resolve_order_airline_scope():
    if _is_platform_admin_for_orders():
        airline_id = request.args.get("airline_id")

        if airline_id in (None, ""):
            return None, None

        try:
            return int(airline_id), None
        except (TypeError, ValueError):
            return None, error_response("航空公司参数不合法")

    airline_id = g.current_user.get("airline_id")

    if airline_id is None:
        return None, error_response("当前管理员未绑定航空公司", 403)

    return airline_id, None


@admin_order_bp.get("/refund-records")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def list_managed_refund_records():
    """查询当前航司退票记录。

    退票记录统一来自 change_record：
    - 乘客主动退票
    - 航司原因退票
    new_order_id 允许为空。
    """
    airline_id, error = _resolve_order_airline_scope()

    if error:
        return error

    change_type = str(request.args.get("change_type", "")).strip()
    status = str(request.args.get("status", "")).strip()
    order_id = str(request.args.get("order_id", "")).strip()

    conditions = [
        "cr.change_type LIKE %s"
    ]

    parameters = [
        "%退票%"
    ]

    if airline_id is not None:
        conditions.append("old_fni.airline_id = %s")
        parameters.append(airline_id)

    if change_type:
        conditions.append("cr.change_type = %s")
        parameters.append(change_type)

    if status:
        conditions.append("cr.status = %s")
        parameters.append(status)

    if order_id:
        conditions.append("CAST(cr.old_order_id AS CHAR) LIKE %s")
        parameters.append(f"%{order_id}%")

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
                    cr.rule_id,
                    cr.change_type,
                    cr.irregularity_id,
                    cr.old_ticket_price,
                    cr.change_fee,
                    cr.refundable_amount,
                    cr.operator_user_id,
                    cr.change_reason,
                    cr.status,
                    cr.created_at,
                    cr.completed_at,
                    old_order.user_id,
                    u.username,
                    p.real_name AS passenger_name,
                    old_order.instance_id,
                    old_fi.flight_no,
                    old_fi.flight_date,
                    old_ac.airline_name
                FROM change_record AS cr
                JOIN archive_ticket_sale AS old_order
                  ON old_order.order_id = cr.old_order_id
                JOIN `user` AS u
                  ON u.user_id = old_order.user_id
                JOIN passenger AS p
                  ON p.passenger_id = old_order.passenger_id
                JOIN flight_instance AS old_fi
                  ON old_fi.instance_id = old_order.instance_id
                JOIN flight_no_info AS old_fni
                  ON old_fni.flight_no = old_fi.flight_no
                JOIN airline_company AS old_ac
                  ON old_ac.airline_id = old_fni.airline_id
                WHERE {where_clause}
                ORDER BY cr.created_at DESC, cr.change_id DESC
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        records = [
            {
                "refundId": row["change_id"],
                "oldOrderId": row["old_order_id"],
                "ruleId": row["rule_id"],
                "changeType": row["change_type"],
                "irregularityId": row["irregularity_id"],
                "userId": row["user_id"],
                "username": row["username"],
                "passengerName": row["passenger_name"],
                "instanceId": row["instance_id"],
                "flightNo": row["flight_no"],
                "flightDate": row["flight_date"].isoformat(),
                "airlineName": row["airline_name"],
                "oldTicketPrice": float(row["old_ticket_price"] or 0),
                "changeFee": float(row["change_fee"] or 0),
                "refundableAmount": float(row["refundable_amount"] or 0),
                "operatorUserId": row["operator_user_id"],
                "changeReason": row["change_reason"],
                "status": row["status"],
                "createdAt": row["created_at"].isoformat(sep=" ", timespec="seconds"),
                "completedAt": (
                    row["completed_at"].isoformat(sep=" ", timespec="seconds")
                    if row["completed_at"] is not None
                    else None
                ),
            }
            for row in rows
        ]

        return success_response(records, "查询成功")

    except Exception as error:
        return error_response("退票记录查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()



# ===== admin order refund/change actions patch start =====

def _is_system_total_admin():
    role = g.current_user.get("role")
    admin_role = g.current_user.get("admin_role")

    return (
        role in ("系统总管理员", "平台总管理员", "总管理员")
        or admin_role in ("系统总管理员", "平台总管理员", "总管理员")
    )


def _can_assist_order_actions():
    if _is_system_total_admin():
        return True

    admin_role = g.current_user.get("admin_role")

    return admin_role in ("航司主管理员", "订单管理员")


def _require_assist_permission():
    if not _can_assist_order_actions():
        return error_response("当前岗位无权代办退票或改签", 403)

    return None


def _decimal_money(value):
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(Decimal("0.01"))


def _get_table_columns(cursor, table_name):
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    return [row["Field"] for row in cursor.fetchall()]


def _next_order_id(cursor):
    cursor.execute(
        """
        SELECT COALESCE(MAX(order_id), 50000) + 1 AS next_id
        FROM (
            SELECT order_id FROM active_ticket_sale
            UNION ALL
            SELECT order_id FROM archive_ticket_sale
        ) AS all_orders
        """
    )

    row = cursor.fetchone()
    return int(row["next_id"])


def _load_active_order_for_admin(cursor, order_id, lock_rows=False):
    lock_sql = " FOR UPDATE" if lock_rows else ""

    cursor.execute(
        f"""
        SELECT
            ats.*,
            fni.airline_id,
            ac.airline_name,
            fi.flight_no,
            fi.flight_date,
            fi.dep_time,
            fi.arr_time
        FROM active_ticket_sale AS ats
        JOIN flight_instance AS fi
          ON fi.instance_id = ats.instance_id
        JOIN flight_no_info AS fni
          ON fni.flight_no = fi.flight_no
        JOIN airline_company AS ac
          ON ac.airline_id = fni.airline_id
        WHERE ats.order_id = %s
        {lock_sql}
        """,
        (order_id,),
    )

    order = cursor.fetchone()

    if order is None:
        return None, "未找到该有效订单", 404

    if not _is_system_total_admin():
        current_airline_id = g.current_user.get("airline_id")

        if current_airline_id is None:
            return None, "当前管理员未绑定航空公司", 403

        if int(order["airline_id"]) != int(current_airline_id):
            return None, "无权处理其他航空公司的订单", 403

    return order, None, None


def _archive_active_order(cursor, active_order, archive_status):
    archive_columns = _get_table_columns(cursor, "archive_ticket_sale")
    insert_data = {}

    for column in archive_columns:
        if column in active_order:
            insert_data[column] = active_order[column]

    if "order_status" in archive_columns:
        insert_data["order_status"] = archive_status

    if "status" in archive_columns:
        insert_data["status"] = archive_status

    if "archive_time" in archive_columns:
        insert_data["archive_time"] = None

    if "archived_at" in archive_columns:
        insert_data["archived_at"] = None

    columns = list(insert_data.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(f"`{column}`" for column in columns)

    cursor.execute(
        f"""
        INSERT INTO archive_ticket_sale ({column_sql})
        VALUES ({placeholders})
        """,
        tuple(insert_data[column] for column in columns),
    )


def _delete_active_order(cursor, order_id):
    cursor.execute(
        """
        DELETE FROM active_ticket_sale
        WHERE order_id = %s
        """,
        (order_id,),
    )


def _get_table_column_defs(cursor, table_name):
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    return {row["Field"]: row for row in cursor.fetchall()}


def _default_value_for_column(column_def):
    column_type = str(column_def.get("Type") or "").lower()
    nullable = column_def.get("Null") == "YES"
    default = column_def.get("Default")
    extra = str(column_def.get("Extra") or "").lower()

    if "auto_increment" in extra:
        return None

    if default is not None:
        return default

    if nullable:
        return None

    if "int" in column_type:
        return 0

    if "decimal" in column_type or "float" in column_type or "double" in column_type:
        return Decimal("0.00")

    if "date" in column_type or "time" in column_type:
        return "__SQL_NOW__"

    return ""


def _create_active_order_from_old(
    cursor,
    old_order,
    new_order_id,
    new_instance_id,
    new_ticket_price,
    target_pricing=None,
):
    active_defs = _get_table_column_defs(cursor, "active_ticket_sale")
    active_columns = list(active_defs.keys())

    insert_data = {}

    for column in active_columns:
        if column in old_order:
            insert_data[column] = old_order[column]

    target_pricing = target_pricing or {}
    target_pricing_id = target_pricing.get("pricing_id")
    target_cabin_type = target_pricing.get("cabin_type")

    # 新订单核心字段
    if "order_id" in active_columns:
        insert_data["order_id"] = new_order_id

    if "instance_id" in active_columns:
        insert_data["instance_id"] = new_instance_id

    # 目标舱位与目标票价编号，不能继续复制旧订单
    for column in ("pricing_id", "cabin_pricing_id", "price_id"):
        if column in active_columns and target_pricing_id is not None:
            insert_data[column] = target_pricing_id

    if "cabin_type" in active_columns and target_cabin_type:
        insert_data["cabin_type"] = target_cabin_type

    if "cabin" in active_columns and target_cabin_type:
        insert_data["cabin"] = target_cabin_type

    # 新订单金额，统一写成目标舱位票价
    for column in (
        "sale_price",
        "ticket_price",
        "price",
        "order_amount",
        "pay_amount",
        "paid_amount",
        "actual_amount",
    ):
        if column in active_columns:
            insert_data[column] = new_ticket_price

    # 改签生成的新票必须重新值机、重新选座
    for column in ("seat_no", "seat_number"):
        if column in active_columns:
            if active_defs[column].get("Null") == "YES":
                insert_data[column] = None
            else:
                insert_data[column] = ""

    if "check_in_status" in active_columns:
        insert_data["check_in_status"] = "未值机"

    if "checkin_status" in active_columns:
        insert_data["checkin_status"] = "未值机"

    # 新订单状态
    for column in ("order_status", "status"):
        if column in active_columns:
            insert_data[column] = "已支付"

    # 票号类字段不要复制旧票号，否则可能唯一键冲突
    for column in ("ticket_no", "ticket_number", "ticket_code"):
        if column in active_columns:
            insert_data[column] = f"TK{new_order_id}"

    # 时间类字段改成当前时间
    for column in ("purchase_time", "created_at", "updated_at", "payment_time", "pay_time"):
        if column in active_columns:
            insert_data[column] = "__SQL_NOW__"

    # 补齐 NOT NULL 且没有默认值的字段
    for column in active_columns:
        if column not in insert_data:
            value = _default_value_for_column(active_defs[column])
            if value is not None:
                insert_data[column] = value
            elif active_defs[column].get("Null") == "YES":
                insert_data[column] = None

    columns = list(insert_data.keys())
    placeholders = []
    values = []

    for column in columns:
        value = insert_data[column]

        if value == "__SQL_NOW__":
            placeholders.append("NOW()")
        else:
            placeholders.append("%s")
            values.append(value)

    column_sql = ", ".join(f"`{column}`" for column in columns)
    placeholder_sql = ", ".join(placeholders)

    cursor.execute(
        f"""
        INSERT INTO active_ticket_sale ({column_sql})
        VALUES ({placeholder_sql})
        """,
        tuple(values),
    )


def _insert_change_record(cursor, data):
    columns = _get_table_columns(cursor, "change_record")
    insert_data = {}

    for key, value in data.items():
        if key in columns:
            insert_data[key] = value

    if "created_at" in columns and "created_at" not in insert_data:
        insert_data["created_at"] = None

    if "completed_at" in columns and "completed_at" not in insert_data:
        insert_data["completed_at"] = None

    field_names = list(insert_data.keys())
    placeholders = []
    values = []

    for field in field_names:
        value = insert_data[field]

        if field in ("created_at", "completed_at") and value is None:
            placeholders.append("NOW()")
        else:
            placeholders.append("%s")
            values.append(value)

    field_sql = ", ".join(f"`{field}`" for field in field_names)
    placeholder_sql = ", ".join(placeholders)

    cursor.execute(
        f"""
        INSERT INTO change_record ({field_sql})
        VALUES ({placeholder_sql})
        """,
        tuple(values),
    )

    return cursor.lastrowid


def _normalize_change_payload(data):
    payload = dict(data)

    target_id = (
        payload.get("new_instance_id")
        or payload.get("target_instance_id")
        or payload.get("targetInstanceId")
        or payload.get("newInstanceId")
    )

    if target_id is not None:
        payload["new_instance_id"] = target_id

    return payload


@admin_order_bp.post("/orders/<int:order_id>/refund-preview")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def preview_admin_refund(order_id):
    permission_error = _require_assist_permission()

    if permission_error is not None:
        return permission_error

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            order, message, status_code = _load_active_order_for_admin(
                cursor,
                order_id,
                lock_rows=False,
            )

            if order is None:
                return error_response(message, status_code)

            context, message, status_code = _load_refund_context(
                cursor,
                order_id,
                order["user_id"],
                lock_rows=False,
            )

            if context is None:
                return error_response(message, status_code)

            data = _serialize_refund_context(context)
            data["refundAmount"] = data.get("refundableAmount")
            data["previewToken"] = f"admin-refund-{order_id}"

        return success_response(data, "退票费用预览成功")

    except Exception as error:
        return error_response("退票费用预览失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_order_bp.post("/orders/<int:order_id>/refund")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def admin_refund_order(order_id):
    permission_error = _require_assist_permission()

    if permission_error is not None:
        return permission_error

    data = request.get_json(silent=True) or {}
    refund_reason = str(
        data.get("refund_reason")
        or data.get("reason")
        or data.get("change_reason")
        or "后台代办退票"
    ).strip()

    if len(refund_reason) > 500:
        return error_response("退票原因不能超过 500 个字符")

    connection = None

    try:
        connection = get_db_connection()
        connection.begin()

        with connection.cursor() as cursor:
            order, message, status_code = _load_active_order_for_admin(
                cursor,
                order_id,
                lock_rows=True,
            )

            if order is None:
                connection.rollback()
                return error_response(message, status_code)

            context, message, status_code = _load_refund_context(
                cursor,
                order_id,
                order["user_id"],
                lock_rows=True,
            )

            if context is None:
                connection.rollback()
                return error_response(message, status_code)

            preview = _serialize_refund_context(context)

            ticket_price = _decimal_money(
                preview.get("ticketPrice")
                or preview.get("oldTicketPrice")
                or preview.get("price")
            )
            refund_fee = _decimal_money(preview.get("refundFee"))
            refundable_amount = _decimal_money(
                preview.get("refundableAmount")
                or preview.get("refundAmount")
            )

            _archive_active_order(cursor, order, "已退票")
            _delete_active_order(cursor, order_id)

            change_id = _insert_change_record(
                cursor,
                {
                    "old_order_id": order_id,
                    "new_order_id": None,
                    "rule_id": preview.get("ruleId"),
                    "change_type": preview.get("changeType") or "乘客主动退票",
                    "irregularity_id": preview.get("irregularityId"),
                    "old_ticket_price": ticket_price,
                    "new_ticket_price": Decimal("0.00"),
                    "fare_difference": -ticket_price,
                    "change_fee": refund_fee,
                    "payable_amount": Decimal("0.00"),
                    "refundable_amount": refundable_amount,
                    "operator_user_id": g.current_user["user_id"],
                    "change_reason": refund_reason,
                    "status": "已完成",
                },
            )

        connection.commit()

        result = dict(preview)
        result["refundId"] = change_id
        result["changeId"] = change_id
        result["status"] = "已完成"
        result["refundAmount"] = result.get("refundableAmount")

        return success_response(result, "后台退票处理成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()
        return error_response("后台退票处理失败", 500, error)

    finally:
        if connection is not None:
            connection.close()




def _safe_decimal(value):
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value))
    except Exception:
        return None


def _infer_order_cabin_type(cursor, old_order):
    """尽可能从订单、价格编号、票价推断原订单舱位。"""
    for key in ("cabin_type", "cabinType", "cabin"):
        value = old_order.get(key)
        if value:
            return value

    pricing_id = (
        old_order.get("pricing_id")
        or old_order.get("cabin_pricing_id")
        or old_order.get("price_id")
    )

    if pricing_id not in (None, ""):
        cursor.execute(
            """
            SELECT cabin_type
            FROM cabin_pricing
            WHERE pricing_id = %s
            LIMIT 1
            """,
            (pricing_id,),
        )
        row = cursor.fetchone()
        if row and row.get("cabin_type"):
            return row["cabin_type"]

    old_price = _safe_decimal(
        old_order.get("sale_price")
        or old_order.get("ticket_price")
        or old_order.get("price")
        or old_order.get("order_amount")
        or old_order.get("pay_amount")
        or old_order.get("amount")
    )

    old_instance_id = old_order.get("instance_id")

    if old_price is not None and old_instance_id not in (None, ""):
        cursor.execute(
            """
            SELECT cabin_type, sale_price
            FROM cabin_pricing
            WHERE instance_id = %s
            ORDER BY ABS(sale_price - %s) ASC, sale_price DESC, pricing_id DESC
            LIMIT 1
            """,
            (old_instance_id, old_price),
        )
        row = cursor.fetchone()
        if row and row.get("cabin_type"):
            return row["cabin_type"]

    # 课程项目兜底：高价票基本视为头等舱，普通票视为经济舱
    if old_price is not None:
        if old_price >= Decimal("3000"):
            return "头等舱"
        return "经济舱"

    return None



def _safe_decimal(value):
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value))
    except Exception:
        return None


def _infer_order_cabin_type(cursor, old_order):
    """尽可能从订单、价格编号、票价推断原订单舱位。"""
    for key in ("cabin_type", "cabinType", "cabin"):
        value = old_order.get(key)
        if value:
            return value

    pricing_id = (
        old_order.get("pricing_id")
        or old_order.get("cabin_pricing_id")
        or old_order.get("price_id")
    )

    if pricing_id not in (None, ""):
        cursor.execute(
            """
            SELECT cabin_type
            FROM cabin_pricing
            WHERE pricing_id = %s
            LIMIT 1
            """,
            (pricing_id,),
        )
        row = cursor.fetchone()
        if row and row.get("cabin_type"):
            return row["cabin_type"]

    old_price = _safe_decimal(
        old_order.get("sale_price")
        or old_order.get("ticket_price")
        or old_order.get("price")
        or old_order.get("order_amount")
        or old_order.get("pay_amount")
        or old_order.get("amount")
    )

    old_instance_id = old_order.get("instance_id")

    if old_price is not None and old_instance_id not in (None, ""):
        cursor.execute(
            """
            SELECT cabin_type, sale_price
            FROM cabin_pricing
            WHERE instance_id = %s
            ORDER BY ABS(sale_price - %s) ASC, sale_price DESC, pricing_id DESC
            LIMIT 1
            """,
            (old_instance_id, old_price),
        )
        row = cursor.fetchone()
        if row and row.get("cabin_type"):
            return row["cabin_type"]

    # 课程项目兜底：高价票基本视为头等舱，普通票视为经济舱
    if old_price is not None:
        if old_price >= Decimal("3000"):
            return "头等舱"
        return "经济舱"

    return None


def _prepare_admin_change_payload(cursor, old_order, data):
    """管理端代办改签：前端选目标航班，后端自动匹配同舱位 pricing_id。"""
    payload = _normalize_change_payload(data)

    new_instance_id = (
        payload.get("new_instance_id")
        or payload.get("target_instance_id")
        or payload.get("targetInstanceId")
        or payload.get("newInstanceId")
        or payload.get("instance_id")
        or payload.get("instanceId")
    )

    if new_instance_id in (None, ""):
        return None, "请选择目标航班", 400

    try:
        new_instance_id = int(new_instance_id)
    except (TypeError, ValueError):
        return None, "目标航班编号必须为整数", 400

    payload["new_instance_id"] = new_instance_id
    payload["target_instance_id"] = new_instance_id
    payload["newInstanceId"] = new_instance_id
    payload["targetInstanceId"] = new_instance_id

    pricing_id = (
        payload.get("new_pricing_id")
        or payload.get("newPricingId")
        or payload.get("target_pricing_id")
        or payload.get("targetPricingId")
        or payload.get("new_cabin_pricing_id")
        or payload.get("newCabinPricingId")
        or payload.get("pricing_id")
        or payload.get("pricingId")
    )

    if pricing_id not in (None, ""):
        try:
            pricing_id = int(pricing_id)
        except (TypeError, ValueError):
            return None, "新舱位价格编号必须为整数", 400

        payload["new_pricing_id"] = pricing_id
        payload["newPricingId"] = pricing_id
        payload["target_pricing_id"] = pricing_id
        payload["targetPricingId"] = pricing_id
        payload["new_cabin_pricing_id"] = pricing_id
        payload["newCabinPricingId"] = pricing_id
        payload["pricing_id"] = pricing_id
        payload["pricingId"] = pricing_id

        return payload, None, None

    cabin_type = _infer_order_cabin_type(cursor, old_order)

    if not cabin_type:
        return None, "无法判断原订单舱位，请先检查该订单票价或舱位数据", 409

    cursor.execute(
        """
        SELECT
            pricing_id,
            cabin_type,
            sale_price
        FROM cabin_pricing
        WHERE instance_id = %s
          AND cabin_type = %s
        ORDER BY
          CASE
            WHEN valid_to IS NULL THEN 0
            WHEN valid_to >= NOW() THEN 0
            ELSE 1
          END ASC,
          valid_from DESC,
          pricing_id DESC
        LIMIT 1
        """,
        (new_instance_id, cabin_type),
    )

    pricing = cursor.fetchone()

    if pricing is None:
        return None, f"目标航班未配置{cabin_type}票价，请先在舱位票价页面维护该航班票价", 409

    pricing_id = int(pricing["pricing_id"])

    payload["new_pricing_id"] = pricing_id
    payload["newPricingId"] = pricing_id
    payload["target_pricing_id"] = pricing_id
    payload["targetPricingId"] = pricing_id
    payload["new_cabin_pricing_id"] = pricing_id
    payload["newCabinPricingId"] = pricing_id
    payload["pricing_id"] = pricing_id
    payload["pricingId"] = pricing_id

    return payload, None, None

@admin_order_bp.post("/orders/<int:order_id>/change-preview")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def preview_admin_change(order_id):
    permission_error = _require_assist_permission()

    if permission_error is not None:
        return permission_error

    data = _normalize_change_payload(request.get_json(silent=True) or {})

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            order, message, status_code = _load_active_order_for_admin(
                cursor,
                order_id,
                lock_rows=False,
            )

            if order is None:
                return error_response(message, status_code)

            data, message, status_code = _prepare_admin_change_payload(
                cursor,
                order,
                data,
            )

            if data is None:
                return error_response(message, status_code)

            context, message, status_code = build_change_context(
                cursor,
                order["user_id"],
                order_id,
                data,
                lock_rows=False,
            )

            if context is None:
                return error_response(message, status_code)

            result = serialize_change_context(context)
            result["previewToken"] = f"admin-change-{order_id}"

        return success_response(result, "改签费用预览成功")

    except Exception as error:
        return error_response("改签费用预览失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


def _resolve_new_instance_for_admin_change(cursor, context, data):
    """确认改签时获取目标航班实例。build_change_context 不一定返回 new_instance，所以这里兜底查询。"""
    new_instance = (
        context.get("new_instance")
        or context.get("target_instance")
        or context.get("newFlight")
        or context.get("targetFlight")
        or context.get("new_flight")
        or context.get("target_flight")
    )

    if new_instance is not None:
        return new_instance, None, None

    instance_id = (
        data.get("new_instance_id")
        or data.get("target_instance_id")
        or data.get("newInstanceId")
        or data.get("targetInstanceId")
        or data.get("instance_id")
        or data.get("instanceId")
    )

    if instance_id in (None, ""):
        return None, "缺少目标航班编号，无法生成改签新订单", 400

    try:
        instance_id = int(instance_id)
    except (TypeError, ValueError):
        return None, "目标航班编号必须为整数", 400

    cursor.execute(
        """
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
            fni.airline_id,
            ac.airline_name
        FROM flight_instance AS fi
        JOIN flight_no_info AS fni
          ON fni.flight_no = fi.flight_no
        JOIN airline_company AS ac
          ON ac.airline_id = fni.airline_id
        WHERE fi.instance_id = %s
        LIMIT 1
        """,
        (instance_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None, "目标航班不存在，无法生成改签新订单", 404

    return row, None, None


def _resolve_change_rule_for_admin_change(context):
    """确认改签时获取适用规则。"""
    rule = (
        context.get("rule")
        or context.get("change_rule")
        or context.get("applicable_rule")
        or {}
    )

    rule_id = (
        rule.get("rule_id")
        or rule.get("ruleId")
        or context.get("rule_id")
        or context.get("ruleId")
    )

    if rule_id in (None, ""):
        return {"rule_id": None}

    return {"rule_id": rule_id}

@admin_order_bp.post("/orders/<int:order_id>/change")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")

def admin_change_order(order_id):
    permission_error = _require_assist_permission()

    if permission_error is not None:
        return permission_error

    data = _normalize_change_payload(request.get_json(silent=True) or {})

    change_reason = str(
        data.get("change_reason")
        or data.get("reason")
        or "后台代办改签"
    ).strip()

    if len(change_reason) > 500:
        return error_response("改签原因不能超过 500 个字符")

    connection = None

    try:
        connection = get_db_connection()
        connection.begin()

        with connection.cursor() as cursor:
            order, message, status_code = _load_active_order_for_admin(
                cursor,
                order_id,
                lock_rows=True,
            )

            if order is None:
                connection.rollback()
                return error_response(message, status_code)

            data, message, status_code = _prepare_admin_change_payload(
                cursor,
                order,
                data,
            )

            if data is None:
                connection.rollback()
                return error_response(message, status_code)

            context, message, status_code = build_change_context(
                cursor,
                order["user_id"],
                order_id,
                data,
                lock_rows=True,
            )

            if context is None:
                connection.rollback()
                return error_response(message, status_code)

            amounts = context.get("amounts")

            if amounts is None:
                connection.rollback()
                return error_response("改签费用上下文缺少金额信息", 500)

            new_instance, message, status_code = _resolve_new_instance_for_admin_change(
                cursor,
                context,
                data,
            )

            if new_instance is None:
                connection.rollback()
                return error_response(message, status_code)

            rule = _resolve_change_rule_for_admin_change(context)
            irregularity = context.get("irregularity") or context.get("flight_irregularity")

            new_order_id = _next_order_id(cursor)

            _archive_active_order(cursor, order, "已改签")
            _delete_active_order(cursor, order_id)

            target_pricing_id = (
                data.get("new_pricing_id")
                or data.get("newPricingId")
                or data.get("target_pricing_id")
                or data.get("targetPricingId")
                or data.get("new_cabin_pricing_id")
                or data.get("newCabinPricingId")
                or data.get("pricing_id")
                or data.get("pricingId")
            )

            cursor.execute(
                """
                SELECT
                    pricing_id,
                    cabin_type,
                    sale_price
                FROM cabin_pricing
                WHERE pricing_id = %s
                LIMIT 1
                """,
                (target_pricing_id,),
            )

            target_pricing = cursor.fetchone()

            if target_pricing is None:
                connection.rollback()
                return error_response("目标舱位票价不存在，无法生成改签新订单", 409)

            _create_active_order_from_old(
                cursor,
                order,
                new_order_id,
                new_instance["instance_id"],
                amounts["new_ticket_price"],
                target_pricing,
            )

            change_id = _insert_change_record(
                cursor,
                {
                    "old_order_id": order_id,
                    "new_order_id": new_order_id,
                    "rule_id": rule.get("rule_id"),
                    "change_type": context.get("change_type") or context.get("changeType") or "乘客主动改签",
                    "irregularity_id": (
                        irregularity["irregularity_id"]
                        if irregularity is not None
                        else None
                    ),
                    "old_ticket_price": amounts["old_ticket_price"],
                    "new_ticket_price": amounts["new_ticket_price"],
                    "fare_difference": amounts["fare_difference"],
                    "change_fee": amounts["change_fee"],
                    "payable_amount": amounts["payable_amount"],
                    "refundable_amount": amounts["refundable_amount"],
                    "operator_user_id": g.current_user["user_id"],
                    "change_reason": change_reason,
                    "status": "已完成",
                },
            )

        connection.commit()

        result = serialize_change_context(context)
        result["changeId"] = change_id
        result["newOrderId"] = new_order_id
        result["status"] = "已完成"

        return success_response(result, "后台改签处理成功", 201)

    except Exception as error:
        if connection is not None:
            connection.rollback()

        import traceback
        traceback.print_exc()

        return error_response("后台改签处理失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


# ===== admin order refund/change actions patch end =====
