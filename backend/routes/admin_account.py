from hashlib import sha256

from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import admin_role_required, role_required
from utils.response import error_response, success_response


admin_account_bp = Blueprint(
    "admin_account",
    __name__,
    url_prefix="/api/admin",
)

ALLOWED_ADMIN_ROLES = {
    "航司主管理员",
    "航班管理员",
    "订单管理员",
    "客服管理员",
}

ALLOWED_STATUSES = {
    "正常",
    "禁用",
}


def hash_password(password):
    """将密码转换为长度为 64 位的哈希值。"""
    return sha256(password.encode("utf-8")).hexdigest()


def normalize_optional_text(value):
    """将空字符串统一转换为 None。"""
    text = str(value or "").strip()
    return text or None


def format_admin(row):
    """将数据库中的管理员记录转换为前端需要的格式。"""
    return {
        "adminId": row["user_id"],
        "name": row["real_name"],
        "account": row["username"],
        "idCard": row["id_card"],
        "phone": row["phone"],
        "email": row["email"],
        "role": row["admin_role"],
        "lastLoginTime": (
            row["last_login_at"].isoformat(
                sep=" ",
                timespec="seconds",
            )
            if row["last_login_at"] is not None
            else None
        ),
        "status": row["status"],
        "createdAt": row["created_at"].isoformat(
            sep=" ",
            timespec="seconds",
        ),
    }


def validate_admin_fields(
    name,
    account,
    id_card,
    phone,
    email,
    admin_role,
    status,
):
    """校验管理员表单字段。"""
    if not name:
        return "管理员姓名不能为空"

    if len(name) > 20:
        return "管理员姓名不能超过 20 个字符"

    if not account:
        return "登录账号不能为空"

    if len(account) > 20:
        return "登录账号不能超过 20 个字符"

    if len(id_card) != 18:
        return "身份证号必须为 18 位"

    if phone is not None and (
        len(phone) != 11
        or not phone.isdigit()
    ):
        return "手机号必须为 11 位数字"

    if email is not None and len(email) > 100:
        return "邮箱不能超过 100 个字符"

    if admin_role not in ALLOWED_ADMIN_ROLES:
        return "管理员角色不合法"

    if status not in ALLOWED_STATUSES:
        return "账号状态不合法"

    return None


def is_last_active_primary_admin(
    cursor,
    admin_id,
    airline_id,
    next_admin_role,
    next_status,
):
    """
    判断本次修改是否会让航司失去最后一个正常状态的主管理员。
    """
    cursor.execute(
        """
        SELECT admin_role, status
        FROM `user`
        WHERE user_id = %s
          AND role = '航空公司管理员'
          AND airline_id = %s
        LIMIT 1
        """,
        (
            admin_id,
            airline_id,
        ),
    )

    current_admin = cursor.fetchone()

    if current_admin is None:
        return False

    currently_active_primary = (
        current_admin["admin_role"] == "航司主管理员"
        and current_admin["status"] == "正常"
    )

    remains_active_primary = (
        next_admin_role == "航司主管理员"
        and next_status == "正常"
    )

    if not currently_active_primary or remains_active_primary:
        return False

    cursor.execute(
        """
        SELECT COUNT(*) AS active_primary_count
        FROM `user`
        WHERE role = '航空公司管理员'
          AND airline_id = %s
          AND admin_role = '航司主管理员'
          AND status = '正常'
        """,
        (airline_id,),
    )

    result = cursor.fetchone()

    return result["active_primary_count"] <= 1


@admin_account_bp.get("/admins")
@role_required("航空公司管理员")
def list_managed_admins():
    """查询当前航司内部管理员列表。"""
    name = str(request.args.get("name", "")).strip()
    admin_role = str(request.args.get("role", "")).strip()
    status = str(request.args.get("status", "")).strip()

    conditions = [
        "role = '航空公司管理员'",
        "airline_id = %s",
    ]

    parameters = [
        g.current_user["airline_id"],
    ]

    if name:
        conditions.append(
            "(username LIKE %s OR real_name LIKE %s)"
        )
        keyword = f"%{name}%"
        parameters.extend([keyword, keyword])

    if admin_role:
        conditions.append("admin_role = %s")
        parameters.append(admin_role)

    if status:
        conditions.append("status = %s")
        parameters.append(status)

    where_clause = " AND ".join(conditions)

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    user_id,
                    username,
                    real_name,
                    id_card,
                    phone,
                    email,
                    admin_role,
                    last_login_at,
                    status,
                    created_at
                FROM `user`
                WHERE {where_clause}
                ORDER BY user_id
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        admins = [
            format_admin(row)
            for row in rows
        ]

        return success_response(admins, "查询成功")

    except Exception as error:
        return error_response(
            "管理员列表查询失败",
            500,
            error,
        )

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.post("/admins")
@admin_role_required("航司主管理员")
def create_managed_admin():
    """新增当前航司内部管理员。"""
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    account = str(data.get("account", "")).strip()
    password = str(data.get("password", ""))
    id_card = str(data.get("id_card", "")).strip()
    phone = normalize_optional_text(data.get("phone"))
    email = normalize_optional_text(data.get("email"))
    admin_role = str(data.get("role", "")).strip()
    status = str(data.get("status", "正常")).strip()

    validation_error = validate_admin_fields(
        name,
        account,
        id_card,
        phone,
        email,
        admin_role,
        status,
    )

    if validation_error is not None:
        return error_response(validation_error)

    if len(password) < 6:
        return error_response("初始密码不能少于 6 个字符")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            duplicate_conditions = [
                "username = %s",
                "id_card = %s",
            ]

            duplicate_parameters = [
                account,
                id_card,
            ]

            if email is not None:
                duplicate_conditions.append("email = %s")
                duplicate_parameters.append(email)

            cursor.execute(
                f"""
                SELECT user_id
                FROM `user`
                WHERE {" OR ".join(duplicate_conditions)}
                LIMIT 1
                """,
                tuple(duplicate_parameters),
            )

            if cursor.fetchone() is not None:
                return error_response(
                    "登录账号、身份证号或邮箱已被使用",
                    409,
                )

            cursor.execute(
                """
                INSERT INTO `user` (
                    username,
                    password_hash,
                    real_name,
                    id_card,
                    phone,
                    email,
                    status,
                    admin_role,
                    last_login_at,
                    role,
                    airline_id,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NULL,
                    '航空公司管理员',
                    %s,
                    NOW()
                )
                """,
                (
                    account,
                    hash_password(password),
                    name,
                    id_card,
                    phone,
                    email,
                    status,
                    admin_role,
                    g.current_user["airline_id"],
                ),
            )

            admin_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT
                    user_id,
                    username,
                    real_name,
                    id_card,
                    phone,
                    email,
                    admin_role,
                    last_login_at,
                    status,
                    created_at
                FROM `user`
                WHERE user_id = %s
                """,
                (admin_id,),
            )

            row = cursor.fetchone()

        connection.commit()

        return success_response(
            format_admin(row),
            "管理员新增成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response(
            "管理员新增失败",
            500,
            error,
        )

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.put("/admins/<int:admin_id>")
@admin_role_required("航司主管理员")
def update_managed_admin(admin_id):
    """编辑当前航司内部管理员信息。"""
    data = request.get_json(silent=True) or {}

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    user_id,
                    username,
                    real_name,
                    id_card,
                    phone,
                    email,
                    admin_role,
                    last_login_at,
                    status,
                    created_at
                FROM `user`
                WHERE user_id = %s
                  AND role = '航空公司管理员'
                  AND airline_id = %s
                FOR UPDATE
                """,
                (
                    admin_id,
                    g.current_user["airline_id"],
                ),
            )

            current_admin = cursor.fetchone()

            if current_admin is None:
                return error_response(
                    "未找到本航司管理员",
                    404,
                )

            name = str(
                data.get(
                    "name",
                    current_admin["real_name"],
                )
            ).strip()

            account = current_admin["username"]

            id_card = str(
                data.get(
                    "id_card",
                    current_admin["id_card"],
                )
            ).strip()

            phone = normalize_optional_text(
                data.get(
                    "phone",
                    current_admin["phone"],
                )
            )

            email = normalize_optional_text(
                data.get(
                    "email",
                    current_admin["email"],
                )
            )

            admin_role = str(
                data.get(
                    "role",
                    current_admin["admin_role"],
                )
            ).strip()

            status = str(
                data.get(
                    "status",
                    current_admin["status"],
                )
            ).strip()

            validation_error = validate_admin_fields(
                name,
                account,
                id_card,
                phone,
                email,
                admin_role,
                status,
            )

            if validation_error is not None:
                return error_response(validation_error)

            if (
                admin_id == g.current_user["user_id"]
                and status == "禁用"
            ):
                return error_response(
                    "不能禁用当前登录账号",
                    409,
                )

            if is_last_active_primary_admin(
                cursor,
                admin_id,
                g.current_user["airline_id"],
                admin_role,
                status,
            ):
                return error_response(
                    "必须至少保留一个正常状态的航司主管理员",
                    409,
                )

            duplicate_conditions = [
                "id_card = %s",
            ]

            duplicate_parameters = [
                id_card,
            ]

            if email is not None:
                duplicate_conditions.append("email = %s")
                duplicate_parameters.append(email)

            duplicate_parameters.append(admin_id)

            cursor.execute(
                f"""
                SELECT user_id
                FROM `user`
                WHERE (
                    {" OR ".join(duplicate_conditions)}
                )
                  AND user_id <> %s
                LIMIT 1
                """,
                tuple(duplicate_parameters),
            )

            if cursor.fetchone() is not None:
                return error_response(
                    "身份证号或邮箱已被使用",
                    409,
                )

            cursor.execute(
                """
                UPDATE `user`
                SET real_name = %s,
                    id_card = %s,
                    phone = %s,
                    email = %s,
                    admin_role = %s,
                    status = %s
                WHERE user_id = %s
                """,
                (
                    name,
                    id_card,
                    phone,
                    email,
                    admin_role,
                    status,
                    admin_id,
                ),
            )

            cursor.execute(
                """
                SELECT
                    user_id,
                    username,
                    real_name,
                    id_card,
                    phone,
                    email,
                    admin_role,
                    last_login_at,
                    status,
                    created_at
                FROM `user`
                WHERE user_id = %s
                """,
                (admin_id,),
            )

            row = cursor.fetchone()

        connection.commit()

        return success_response(
            format_admin(row),
            "管理员信息修改成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response(
            "管理员信息修改失败",
            500,
            error,
        )

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.put("/admins/<int:admin_id>/status")
@admin_role_required("航司主管理员")
def update_managed_admin_status(admin_id):
    """启用或禁用当前航司内部管理员。"""
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()

    if status not in ALLOWED_STATUSES:
        return error_response("账号状态不合法")

    if admin_id == g.current_user["user_id"] and status == "禁用":
        return error_response(
            "不能禁用当前登录账号",
            409,
        )

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    user_id,
                    admin_role,
                    status
                FROM `user`
                WHERE user_id = %s
                  AND role = '航空公司管理员'
                  AND airline_id = %s
                FOR UPDATE
                """,
                (
                    admin_id,
                    g.current_user["airline_id"],
                ),
            )

            current_admin = cursor.fetchone()

            if current_admin is None:
                return error_response(
                    "未找到本航司管理员",
                    404,
                )

            if is_last_active_primary_admin(
                cursor,
                admin_id,
                g.current_user["airline_id"],
                current_admin["admin_role"],
                status,
            ):
                return error_response(
                    "必须至少保留一个正常状态的航司主管理员",
                    409,
                )

            cursor.execute(
                """
                UPDATE `user`
                SET status = %s
                WHERE user_id = %s
                """,
                (
                    status,
                    admin_id,
                ),
            )

        connection.commit()

        return success_response(
            {
                "adminId": admin_id,
                "status": status,
            },
            "管理员账号状态修改成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response(
            "管理员账号状态修改失败",
            500,
            error,
        )

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.put("/admins/<int:admin_id>/reset-password")
@admin_role_required("航司主管理员")
def reset_managed_admin_password(admin_id):
    """重置当前航司内部管理员密码。"""
    data = request.get_json(silent=True) or {}
    new_password = str(data.get("new_password", ""))

    if len(new_password) < 6:
        return error_response("新密码不能少于 6 个字符")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id
                FROM `user`
                WHERE user_id = %s
                  AND role = '航空公司管理员'
                  AND airline_id = %s
                LIMIT 1
                """,
                (
                    admin_id,
                    g.current_user["airline_id"],
                ),
            )

            if cursor.fetchone() is None:
                return error_response(
                    "未找到本航司管理员",
                    404,
                )

            cursor.execute(
                """
                UPDATE `user`
                SET password_hash = %s
                WHERE user_id = %s
                """,
                (
                    hash_password(new_password),
                    admin_id,
                ),
            )

        connection.commit()

        return success_response(
            {
                "adminId": admin_id,
            },
            "管理员密码重置成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response(
            "管理员密码重置失败",
            500,
            error,
        )

    finally:
        if connection is not None:
            connection.close()