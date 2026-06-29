from flask import Blueprint, request

from db import get_db_connection
from utils.auth import role_required
from utils.response import success_response, error_response


admin_coordination_bp = Blueprint(
    "admin_coordination",
    __name__,
    url_prefix="/api/admin",
)


def _to_int(value):
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@admin_coordination_bp.get("/cross-airline-cases")
@admin_coordination_bp.get("/coordination/cases")
@role_required("系统总管理员", "平台总管理员", "总管理员")
def list_cross_airline_cases():
    """跨航司协调案例。

    数据来源：
    - change_record 中 old_order_id 与 new_order_id 对应的航司不同；
    - 典型场景：航班异常后，原航司订单改签到其他航司航班。
    """
    source_airline_id = (
        request.args.get("airline_id")
        or request.args.get("source_airline_id")
        or request.args.get("sourceAirlineId")
    )

    target_airline_id = (
        request.args.get("target_airline_id")
        or request.args.get("targetAirlineId")
    )

    status = str(
        request.args.get("status")
        or request.args.get("coordination_status")
        or request.args.get("coordinationStatus")
        or ""
    ).strip()

    source_airline_id = _to_int(source_airline_id)
    target_airline_id = _to_int(target_airline_id)

    conditions = [
        "cr.new_order_id IS NOT NULL",
        "old_fni.airline_id <> new_fni.airline_id",
    ]

    parameters = []

    if source_airline_id is not None:
        conditions.append("old_fni.airline_id = %s")
        parameters.append(source_airline_id)

    if target_airline_id is not None:
        conditions.append("new_fni.airline_id = %s")
        parameters.append(target_airline_id)

    if status == "已完成":
        conditions.append("cr.status = '已完成'")
    elif status == "待处理":
        conditions.append("(cr.status IS NULL OR cr.status <> '已完成')")

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
                    cr.change_type,
                    cr.irregularity_id,
                    cr.change_reason,
                    cr.status,
                    cr.created_at,
                    cr.completed_at,

                    old_order.user_id AS old_user_id,
                    old_user.username AS old_username,
                    old_passenger.real_name AS passenger_name,

                    old_fi.instance_id AS source_instance_id,
                    old_fi.flight_no AS source_flight_no,
                    old_fi.flight_date AS source_flight_date,
                    DATE_FORMAT(old_fi.dep_time, '%%H:%%i') AS source_dep_time,
                    DATE_FORMAT(old_fi.arr_time, '%%H:%%i') AS source_arr_time,
                    old_fni.airline_id AS source_airline_id,
                    old_ac.airline_name AS source_airline_name,
                    old_dep.airport_name AS source_dep_airport,
                    old_arr.airport_name AS source_arr_airport,

                    new_fi.instance_id AS target_instance_id,
                    new_fi.flight_no AS target_flight_no,
                    new_fi.flight_date AS target_flight_date,
                    DATE_FORMAT(new_fi.dep_time, '%%H:%%i') AS target_dep_time,
                    DATE_FORMAT(new_fi.arr_time, '%%H:%%i') AS target_arr_time,
                    new_fni.airline_id AS target_airline_id,
                    new_ac.airline_name AS target_airline_name,
                    new_dep.airport_name AS target_dep_airport,
                    new_arr.airport_name AS target_arr_airport
                FROM change_record AS cr

                JOIN (
                    SELECT
                        order_id,
                        user_id,
                        passenger_id,
                        instance_id,
                        order_status,
                        purchase_time
                    FROM active_ticket_sale

                    UNION ALL

                    SELECT
                        order_id,
                        user_id,
                        passenger_id,
                        instance_id,
                        order_status,
                        purchase_time
                    FROM archive_ticket_sale
                ) AS old_order
                  ON old_order.order_id = cr.old_order_id

                JOIN (
                    SELECT
                        order_id,
                        user_id,
                        passenger_id,
                        instance_id,
                        order_status,
                        purchase_time
                    FROM active_ticket_sale

                    UNION ALL

                    SELECT
                        order_id,
                        user_id,
                        passenger_id,
                        instance_id,
                        order_status,
                        purchase_time
                    FROM archive_ticket_sale
                ) AS new_order
                  ON new_order.order_id = cr.new_order_id

                JOIN `user` AS old_user
                  ON old_user.user_id = old_order.user_id

                JOIN passenger AS old_passenger
                  ON old_passenger.passenger_id = old_order.passenger_id

                JOIN flight_instance AS old_fi
                  ON old_fi.instance_id = old_order.instance_id

                JOIN flight_no_info AS old_fni
                  ON old_fni.flight_no = old_fi.flight_no

                JOIN airline_company AS old_ac
                  ON old_ac.airline_id = old_fni.airline_id

                JOIN route AS old_route
                  ON old_route.route_id = old_fni.route_id

                JOIN airport AS old_dep
                  ON old_dep.airport_code = old_route.dep_airport_code

                JOIN airport AS old_arr
                  ON old_arr.airport_code = old_route.arr_airport_code

                JOIN flight_instance AS new_fi
                  ON new_fi.instance_id = new_order.instance_id

                JOIN flight_no_info AS new_fni
                  ON new_fni.flight_no = new_fi.flight_no

                JOIN airline_company AS new_ac
                  ON new_ac.airline_id = new_fni.airline_id

                JOIN route AS new_route
                  ON new_route.route_id = new_fni.route_id

                JOIN airport AS new_dep
                  ON new_dep.airport_code = new_route.dep_airport_code

                JOIN airport AS new_arr
                  ON new_arr.airport_code = new_route.arr_airport_code

                WHERE {where_clause}
                ORDER BY cr.created_at DESC, cr.change_id DESC
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        cases = []

        for row in rows:
            coordination_status = "已完成" if row["status"] == "已完成" else "待处理"

            cases.append(
                {
                    "caseId": row["change_id"],
                    "case_id": row["change_id"],

                    "changeId": row["change_id"],
                    "change_id": row["change_id"],

                    "oldOrderId": row["old_order_id"],
                    "old_order_id": row["old_order_id"],
                    "newOrderId": row["new_order_id"],
                    "new_order_id": row["new_order_id"],

                    "irregularityId": row["irregularity_id"],
                    "irregularity_id": row["irregularity_id"],

                    "irregularityType": row["change_type"] or "跨航司改签",
                    "irregularity_type": row["change_type"] or "跨航司改签",

                    "changeReason": row["change_reason"],
                    "change_reason": row["change_reason"],

                    "passengerName": row["passenger_name"],
                    "passenger_name": row["passenger_name"],

                    "username": row["old_username"],

                    "sourceAirlineId": row["source_airline_id"],
                    "source_airline_id": row["source_airline_id"],
                    "sourceAirlineName": row["source_airline_name"],
                    "source_airline_name": row["source_airline_name"],

                    "targetAirlineId": row["target_airline_id"],
                    "target_airline_id": row["target_airline_id"],
                    "targetAirlineName": row["target_airline_name"],
                    "target_airline_name": row["target_airline_name"],

                    "sourceInstanceId": row["source_instance_id"],
                    "source_instance_id": row["source_instance_id"],
                    "sourceFlightNo": row["source_flight_no"],
                    "source_flight_no": row["source_flight_no"],
                    "sourceFlightDate": row["source_flight_date"].isoformat(),
                    "source_flight_date": row["source_flight_date"].isoformat(),
                    "sourceDepTime": row["source_dep_time"],
                    "source_dep_time": row["source_dep_time"],
                    "sourceArrTime": row["source_arr_time"],
                    "source_arr_time": row["source_arr_time"],
                    "sourceDepAirport": row["source_dep_airport"],
                    "source_dep_airport": row["source_dep_airport"],
                    "sourceArrAirport": row["source_arr_airport"],
                    "source_arr_airport": row["source_arr_airport"],

                    "targetInstanceId": row["target_instance_id"],
                    "target_instance_id": row["target_instance_id"],
                    "targetFlightNo": row["target_flight_no"],
                    "target_flight_no": row["target_flight_no"],
                    "targetFlightDate": row["target_flight_date"].isoformat(),
                    "target_flight_date": row["target_flight_date"].isoformat(),
                    "targetDepTime": row["target_dep_time"],
                    "target_dep_time": row["target_dep_time"],
                    "targetArrTime": row["target_arr_time"],
                    "target_arr_time": row["target_arr_time"],
                    "targetDepAirport": row["target_dep_airport"],
                    "target_dep_airport": row["target_dep_airport"],
                    "targetArrAirport": row["target_arr_airport"],
                    "target_arr_airport": row["target_arr_airport"],

                    "affectedOrderCount": 1,
                    "affected_order_count": 1,

                    "status": coordination_status,
                    "coordinationStatus": coordination_status,
                    "coordination_status": coordination_status,

                    "createdAt": row["created_at"].isoformat(sep=" ", timespec="seconds"),
                    "created_at": row["created_at"].isoformat(sep=" ", timespec="seconds"),
                    "completedAt": (
                        row["completed_at"].isoformat(sep=" ", timespec="seconds")
                        if row["completed_at"] is not None
                        else None
                    ),
                    "completed_at": (
                        row["completed_at"].isoformat(sep=" ", timespec="seconds")
                        if row["completed_at"] is not None
                        else None
                    ),
                }
            )

        summary = {
            "total": len(cases),
            "pending": sum(1 for item in cases if item["status"] == "待处理"),
            "completed": sum(1 for item in cases if item["status"] == "已完成"),
        }

        return success_response(
            {
                "cases": cases,
                "list": cases,
                "items": cases,
                "summary": summary,
            },
            "查询成功",
        )

    except Exception as error:
        return error_response("跨航司协调案例查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
