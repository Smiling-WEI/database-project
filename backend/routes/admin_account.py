from hashlib import sha256

from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import role_required
from utils.response import error_response, success_response


admin_account_bp = Blueprint(
    "admin_account",
    __name__,
    url_prefix="/api/admin",
)

AIRLINE_ADMIN_ROLE = "航司管理员"

PRIMARY_ADMIN_ROLE = "航司主管理员"

SUBORDINATE_ADMIN_ROLES = {
    "航班管理员",
    "订单管理员",
}

ALL_ADMIN_ROLES = {
    PRIMARY_ADMIN_ROLE,
    *SUBORDINATE_ADMIN_ROLES,
}

ALLOWED_STATUSES = {
    "正常",
    "禁用",
}

PLATFORM_ROLES = {
    "系统总管理员",
    "平台总管理员",
    "总管理员",
}


def hash_password(password):
    return sha256(password.encode("utf-8")).hexdigest()


def normalize_optional_text(value):
    text = str(value or "").strip()
    return text or None


def is_platform_admin():
    return g.current_user.get("role") in PLATFORM_ROLES


def can_manage_admins():
    if is_platform_admin():
        return True

    return (
        g.current_user.get("role") in ("航司管理员", "航空公司管理员")
        and g.current_user.get("admin_role") == PRIMARY_ADMIN_ROLE
    )


def resolve_target_airline_id(data=None):
    if is_platform_admin():
        airline_id = None

        if data is not None:
            airline_id = data.get("airline_id")

        if airline_id is None:
            airline_id = request.args.get("airline_id")

        if airline_id in (None, ""):
            return None, error_response("平台总管理员需要先选择航空公司")

        try:
            return int(airline_id), None
        except (TypeError, ValueError):
            return None, error_response("航空公司参数不合法")

    return g.current_user["airline_id"], None


def ensure_can_manage():
    if not can_manage_admins():
        return error_response("无权管理管理员账号", 403)

    return None


def format_admin(row):
    return {
        "adminId": row["user_id"],
        "name": row["real_name"],
        "account": row["username"],
        "idCard": row["id_card"],
        "phone": row["phone"],
        "email": row["email"],
        "role": row["admin_role"],
        "airlineId": row["airline_id"],
        "airlineName": row.get("airline_name"),
        "lastLoginTime": (
            row["last_login_at"].isoformat(sep=" ", timespec="seconds")
            if row["last_login_at"] is not None
            else None
        ),
        "status": row["status"],
        "createdAt": row["created_at"].isoformat(sep=" ", timespec="seconds"),
    }


def validate_admin_fields(name, account, id_card, phone, email, admin_role, status):
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

    if phone is not None and (len(phone) != 11 or not phone.isdigit()):
        return "手机号必须为 11 位数字"

    if email is not None and len(email) > 100:
        return "邮箱不能超过 100 个字符"

    if admin_role not in ALL_ADMIN_ROLES:
        return "管理员角色不合法"

    if status not in ALLOWED_STATUSES:
        return "账号状态不合法"

    if not is_platform_admin() and admin_role == PRIMARY_ADMIN_ROLE:
        return "航司主管理员不能新增或设置新的航司主管理员"

    return None


def is_last_active_primary_admin(cursor, admin_id, airline_id, next_admin_role, next_status):
    cursor.execute(
        """
        SELECT admin_role, status
        FROM `user`
        WHERE user_id = %s
          AND role IN ('航司管理员', '航空公司管理员')
          AND airline_id = %s
        LIMIT 1
        """,
        (admin_id, airline_id),
    )

    current_admin = cursor.fetchone()

    if current_admin is None:
        return False

    currently_active_primary = (
        current_admin["admin_role"] == PRIMARY_ADMIN_ROLE
        and current_admin["status"] == "正常"
    )

    remains_active_primary = (
        next_admin_role == PRIMARY_ADMIN_ROLE
        and next_status == "正常"
    )

    if not currently_active_primary or remains_active_primary:
        return False

    cursor.execute(
        """
        SELECT COUNT(*) AS active_primary_count
        FROM `user`
        WHERE role IN ('航司管理员', '航空公司管理员')
          AND airline_id = %s
          AND admin_role = %s
          AND status = '正常'
        """,
        (airline_id, PRIMARY_ADMIN_ROLE),
    )

    result = cursor.fetchone()

    return result["active_primary_count"] <= 1


@admin_account_bp.get("/admins")
@role_required("航司管理员", "航空公司管理员", "系统总管理员", "平台总管理员", "总管理员")
def list_managed_admins():
    """查询管理员列表。

    普通航司内部管理员只能查看本航司管理员；
    系统总管理员可查看全部航空公司管理员，或按 airline_id 过滤。
    """
    name = str(request.args.get("name", "")).strip()
    admin_role = str(request.args.get("role", "")).strip()
    status = str(request.args.get("status", "")).strip()

    conditions = [
        "u.role IN ('航司管理员', '航空公司管理员')"
    ]

    parameters = []

    if is_platform_admin():
        airline_id = request.args.get("airline_id")

        if airline_id not in (None, ""):
            try:
                airline_id = int(airline_id)
            except (TypeError, ValueError):
                return error_response("航空公司参数不合法")

            conditions.append("u.airline_id = %s")
            parameters.append(airline_id)
    else:
        airline_id = g.current_user.get("airline_id")

        if airline_id is None:
            return error_response("当前管理员未绑定航空公司", 403)

        conditions.append("u.airline_id = %s")
        parameters.append(airline_id)

    if name:
        conditions.append("(u.username LIKE %s OR u.real_name LIKE %s)")
        keyword = f"%{name}%"
        parameters.extend([keyword, keyword])

    if admin_role:
        conditions.append("u.admin_role = %s")
        parameters.append(admin_role)

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
                    u.id_card,
                    u.phone,
                    u.email,
                    u.admin_role,
                    u.airline_id,
                    ac.airline_name,
                    u.last_login_at,
                    u.status,
                    u.created_at
                FROM `user` AS u
                LEFT JOIN airline_company AS ac
                  ON ac.airline_id = u.airline_id
                WHERE {where_clause}
                ORDER BY u.airline_id, u.user_id
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

        return success_response([format_admin(row) for row in rows], "查询成功")

    except Exception as error:
        return error_response("管理员列表查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.post("/admins")
@role_required("航司管理员", "航空公司管理员", "系统总管理员", "平台总管理员", "总管理员")
def create_managed_admin():
    error = ensure_can_manage()
    if error:
        return error

    data = request.get_json(silent=True) or {}

    airline_id, error = resolve_target_airline_id(data)
    if error:
        return error

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
            cursor.execute(
                """
                SELECT airline_id
                FROM airline_company
                WHERE airline_id = %s
                  AND status = '正常'
                LIMIT 1
                """,
                (airline_id,),
            )

            if cursor.fetchone() is None:
                return error_response("所选航空公司不存在或已禁用", 404)

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
                return error_response("登录账号、身份证号或邮箱已被使用", 409)

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
                    %s,
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
                    AIRLINE_ADMIN_ROLE,
                    airline_id,
                ),
            )

            admin_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.real_name,
                    u.id_card,
                    u.phone,
                    u.email,
                    u.admin_role,
                    u.airline_id,
                    ac.airline_name,
                    u.last_login_at,
                    u.status,
                    u.created_at
                FROM `user` AS u
                LEFT JOIN airline_company AS ac
                  ON ac.airline_id = u.airline_id
                WHERE u.user_id = %s
                """,
                (admin_id,),
            )

            row = cursor.fetchone()

        connection.commit()

        return success_response(format_admin(row), "管理员新增成功", 201)

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("管理员新增失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.put("/admins/<int:admin_id>")
@role_required("航司管理员", "航空公司管理员", "系统总管理员", "平台总管理员", "总管理员")
def update_managed_admin(admin_id):
    error = ensure_can_manage()
    if error:
        return error

    data = request.get_json(silent=True) or {}

    airline_id, error = resolve_target_airline_id(data)
    if error:
        return error

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
                    airline_id,
                    last_login_at,
                    status,
                    created_at
                FROM `user`
                WHERE user_id = %s
                  AND role IN ('航司管理员', '航空公司管理员')
                  AND airline_id = %s
                FOR UPDATE
                """,
                (admin_id, airline_id),
            )

            current_admin = cursor.fetchone()

            if current_admin is None:
                return error_response("未找到本航司管理员", 404)

            name = str(data.get("name", current_admin["real_name"])).strip()
            account = current_admin["username"]
            id_card = str(data.get("id_card", current_admin["id_card"])).strip()
            phone = normalize_optional_text(data.get("phone", current_admin["phone"]))
            email = normalize_optional_text(data.get("email", current_admin["email"]))
            admin_role = str(data.get("role", current_admin["admin_role"])).strip()
            status = str(data.get("status", current_admin["status"])).strip()

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

            if admin_id == g.current_user["user_id"] and status == "禁用":
                return error_response("不能禁用当前登录账号", 409)

            if is_last_active_primary_admin(
                cursor,
                admin_id,
                airline_id,
                admin_role,
                status,
            ):
                return error_response("必须至少保留一个正常状态的航司主管理员", 409)

            duplicate_conditions = ["id_card = %s"]
            duplicate_parameters = [id_card]

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
                return error_response("身份证号或邮箱已被使用", 409)

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
                    u.user_id,
                    u.username,
                    u.real_name,
                    u.id_card,
                    u.phone,
                    u.email,
                    u.admin_role,
                    u.airline_id,
                    ac.airline_name,
                    u.last_login_at,
                    u.status,
                    u.created_at
                FROM `user` AS u
                LEFT JOIN airline_company AS ac
                  ON ac.airline_id = u.airline_id
                WHERE u.user_id = %s
                """,
                (admin_id,),
            )

            row = cursor.fetchone()

        connection.commit()

        return success_response(format_admin(row), "管理员信息修改成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("管理员信息修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.put("/admins/<int:admin_id>/status")
@role_required("航司管理员", "航空公司管理员", "系统总管理员", "平台总管理员", "总管理员")
def update_managed_admin_status(admin_id):
    error = ensure_can_manage()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()

    if status not in ALLOWED_STATUSES:
        return error_response("账号状态不合法")

    airline_id, error = resolve_target_airline_id(data)
    if error:
        return error

    if admin_id == g.current_user["user_id"] and status == "禁用":
        return error_response("不能禁用当前登录账号", 409)

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
                  AND role IN ('航司管理员', '航空公司管理员')
                  AND airline_id = %s
                FOR UPDATE
                """,
                (admin_id, airline_id),
            )

            current_admin = cursor.fetchone()

            if current_admin is None:
                return error_response("未找到本航司管理员", 404)

            if is_last_active_primary_admin(
                cursor,
                admin_id,
                airline_id,
                current_admin["admin_role"],
                status,
            ):
                return error_response("必须至少保留一个正常状态的航司主管理员", 409)

            cursor.execute(
                """
                UPDATE `user`
                SET status = %s
                WHERE user_id = %s
                """,
                (status, admin_id),
            )

        connection.commit()

        return success_response({"adminId": admin_id, "status": status}, "管理员账号状态修改成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("管理员账号状态修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.put("/admins/<int:admin_id>/reset-password")
@role_required("航司管理员", "航空公司管理员", "系统总管理员", "平台总管理员", "总管理员")
def reset_managed_admin_password(admin_id):
    error = ensure_can_manage()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    new_password = str(data.get("new_password", ""))

    if len(new_password) < 6:
        return error_response("新密码不能少于 6 个字符")

    airline_id, error = resolve_target_airline_id(data)
    if error:
        return error

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id
                FROM `user`
                WHERE user_id = %s
                  AND role IN ('航司管理员', '航空公司管理员')
                  AND airline_id = %s
                LIMIT 1
                """,
                (admin_id, airline_id),
            )

            if cursor.fetchone() is None:
                return error_response("未找到本航司管理员", 404)

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

        return success_response({"adminId": admin_id}, "管理员密码重置成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("管理员密码重置失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


def format_current_admin_profile(row):
    return {
        "userId": row["user_id"],
        "username": row["username"],
        "realName": row["real_name"],
        "role": row["role"],
        "adminRole": row["admin_role"],
        "airlineId": row["airline_id"],
        "airlineName": row.get("airline_name"),
        "phone": row["phone"],
        "email": row["email"],
        "status": row["status"],
    }


def get_current_admin_profile_row(cursor):
    cursor.execute(
        """
        SELECT
            u.user_id,
            u.username,
            u.real_name,
            u.role,
            u.admin_role,
            u.airline_id,
            ac.airline_name,
            u.phone,
            u.email,
            u.status,
            u.password_hash
        FROM `user` AS u
        LEFT JOIN airline_company AS ac
          ON ac.airline_id = u.airline_id
        WHERE u.user_id = %s
        LIMIT 1
        """,
        (g.current_user["user_id"],),
    )

    return cursor.fetchone()


@admin_account_bp.get("/profile")
@role_required("航司管理员", "航空公司管理员", "系统总管理员", "平台总管理员", "总管理员")
def get_admin_profile():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            row = get_current_admin_profile_row(cursor)

            if row is None:
                return error_response("当前管理员不存在", 404)

        return success_response(format_current_admin_profile(row), "查询成功")

    except Exception as error:
        return error_response("个人信息查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.put("/profile/contact")
@role_required("航司管理员", "航空公司管理员", "系统总管理员", "平台总管理员", "总管理员")
def update_admin_profile_contact():
    data = request.get_json(silent=True) or {}

    phone = normalize_optional_text(data.get("phone"))
    email = normalize_optional_text(data.get("email"))

    if phone is not None and (len(phone) != 11 or not phone.isdigit()):
        return error_response("手机号必须为 11 位数字")

    if email is not None and len(email) > 100:
        return error_response("邮箱不能超过 100 个字符")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            if email is not None:
                cursor.execute(
                    """
                    SELECT user_id
                    FROM `user`
                    WHERE email = %s
                      AND user_id <> %s
                    LIMIT 1
                    """,
                    (
                        email,
                        g.current_user["user_id"],
                    ),
                )

                if cursor.fetchone() is not None:
                    return error_response("邮箱已被其他账号使用", 409)

            cursor.execute(
                """
                UPDATE `user`
                SET phone = %s,
                    email = %s
                WHERE user_id = %s
                """,
                (
                    phone,
                    email,
                    g.current_user["user_id"],
                ),
            )

            row = get_current_admin_profile_row(cursor)

        connection.commit()

        return success_response(format_current_admin_profile(row), "联系方式更新成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("联系方式更新失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@admin_account_bp.put("/profile/password")
@role_required("航司管理员", "航空公司管理员", "系统总管理员", "平台总管理员", "总管理员")
def update_admin_profile_password():
    data = request.get_json(silent=True) or {}

    old_password = str(data.get("old_password", ""))
    new_password = str(data.get("new_password", ""))

    if not old_password:
        return error_response("请输入原密码")

    if len(new_password) < 6:
        return error_response("新密码不能少于 6 个字符")

    if old_password == new_password:
        return error_response("新密码不能与原密码相同")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            row = get_current_admin_profile_row(cursor)

            if row is None:
                return error_response("当前管理员不存在", 404)

            if row["password_hash"] != hash_password(old_password):
                return error_response("原密码不正确", 409)

            cursor.execute(
                """
                UPDATE `user`
                SET password_hash = %s
                WHERE user_id = %s
                """,
                (
                    hash_password(new_password),
                    g.current_user["user_id"],
                ),
            )

        connection.commit()

        return success_response({"userId": g.current_user["user_id"]}, "密码修改成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("密码修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()

