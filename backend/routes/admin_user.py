from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import admin_role_required, role_required
from utils.response import error_response, success_response


admin_user_bp = Blueprint(
    "admin_user",
    __name__,
    url_prefix="/api/admin",
)


@admin_user_bp.get("/users")
@role_required("航司管理员", "航空公司管理员", "航司内部管理员", "系统总管理员", "平台总管理员", "总管理员")
def list_managed_users():
    name = str(request.args.get("name", "")).strip()
    phone = str(request.args.get("phone", "")).strip()
    status = str(request.args.get("status", "")).strip()

    conditions = [
        "u.role = '乘客'"
    ]

    parameters = []

    is_system_admin = (
        g.current_user.get("role") in ("系统总管理员", "平台总管理员", "总管理员")
        or g.current_user.get("admin_role") in ("系统总管理员", "平台总管理员", "总管理员")
    )

    if not is_system_admin:
        airline_id = g.current_user.get("airline_id")

        if airline_id is None:
            return error_response("当前管理员未绑定航空公司", 403)

        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM (
                    SELECT user_id, instance_id FROM active_ticket_sale
                    UNION ALL
                    SELECT user_id, instance_id FROM archive_ticket_sale
                ) AS user_orders
                JOIN flight_instance AS fi
                  ON fi.instance_id = user_orders.instance_id
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                WHERE user_orders.user_id = u.user_id
                  AND fni.airline_id = %s
            )
            """
        )
        parameters.append(airline_id)

    if name:
        conditions.append("(u.real_name LIKE %s OR u.username LIKE %s)")
        keyword = f"%{name}%"
        parameters.extend([keyword, keyword])

    if phone:
        conditions.append("u.phone LIKE %s")
        parameters.append(f"%{phone}%")

    if status:
        conditions.append("u.status = %s")
        parameters.append(status)

    where_clause = " AND ".join(conditions)

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    u.user_id,
                    u.username,
                    u.real_name,
                    u.phone,
                    u.email,
                    u.status,
                    u.created_at,
                    COUNT(DISTINCT up.passenger_id) AS passenger_count,
                    (
                        SELECT COUNT(*)
                        FROM (
                            SELECT user_id FROM active_ticket_sale
                            UNION ALL
                            SELECT user_id FROM archive_ticket_sale
                        ) AS all_orders
                        WHERE all_orders.user_id = u.user_id
                    ) AS order_count
                FROM `user` AS u
                LEFT JOIN user_passenger AS up
                  ON up.user_id = u.user_id
                WHERE {where_clause}
                GROUP BY
                    u.user_id,
                    u.username,
                    u.real_name,
                    u.phone,
                    u.email,
                    u.status,
                    u.created_at
                ORDER BY u.user_id
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        users = []

        for row in rows:
            users.append(
                {
                    "userId": row["user_id"],
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "realName": row["real_name"],
                    "real_name": row["real_name"],
                    "phone": row["phone"],
                    "email": row["email"],
                    "status": row["status"],
                    "createdAt": row["created_at"].isoformat(sep=" ", timespec="seconds"),
                    "created_at": row["created_at"].isoformat(sep=" ", timespec="seconds"),
                    "passengerCount": row["passenger_count"],
                    "passenger_count": row["passenger_count"],
                    "orderCount": row["order_count"],
                    "order_count": row["order_count"],
                }
            )

        return success_response(users, "查询成功")

    except Exception as error:
        return error_response("用户列表查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_user_bp.put("/users/<int:user_id>/status")
@admin_role_required("航司主管理员")
def update_managed_user_status(user_id):
    """启用或禁用与当前航空公司产生过订单关系的普通用户。"""
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()

    if status not in {"正常", "禁用"}:
        return error_response("账号状态不合法")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.user_id
                FROM `user` AS u
                WHERE u.user_id = %s
                  AND u.role = '乘客'
                  AND EXISTS (
                      SELECT 1
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
                      WHERE orders.user_id = u.user_id
                        AND fni.airline_id = %s
                  )
                LIMIT 1
                """,
                (
                    user_id,
                    g.current_user["airline_id"],
                ),
            )

            user = cursor.fetchone()

            if user is None:
                return error_response("未找到本航司有权限管理的普通用户", 404)

            cursor.execute(
                """
                UPDATE `user`
                SET status = %s
                WHERE user_id = %s
                """,
                (
                    status,
                    user_id,
                ),
            )

        connection.commit()

        return success_response(
            {
                "userId": user_id,
                "status": status,
            },
            "账号状态修改成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("账号状态修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()