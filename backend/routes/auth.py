from hashlib import sha256

from flask import Blueprint, g, request

from utils.auth import generate_token, login_required

from db import get_db_connection

from utils.response import error_response, success_response


auth_bp = Blueprint("auth", __name__, url_prefix="/api")


def hash_password(password):
    """将密码转换为长度为 64 位的哈希值。"""
    return sha256(password.encode("utf-8")).hexdigest()


@auth_bp.post("/register")
def register():
    """注册普通乘客账号。"""
    data = request.get_json(silent=True) or {}

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    real_name = str(data.get("real_name", "")).strip()
    id_card = str(data.get("id_card", "")).strip()
    phone = str(data.get("phone", "")).strip() or None

    if not username or not password or not real_name or not id_card:
        return error_response("用户名、密码、真实姓名和身份证号不能为空")

    if len(username) > 20:
        return error_response("用户名不能超过 20 个字符")

    if len(password) < 6:
        return error_response("密码不能少于 6 个字符")

    if len(real_name) > 20:
        return error_response("真实姓名不能超过 20 个字符")

    if len(id_card) != 18:
        return error_response("身份证号必须为 18 位")

    if phone is not None and (len(phone) != 11 or not phone.isdigit()):
        return error_response("手机号必须为 11 位数字")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id
                FROM `user`
                WHERE username = %s OR id_card = %s
                LIMIT 1
                """,
                (username, id_card),
            )

            if cursor.fetchone() is not None:
                return error_response("用户名或身份证号已被注册", 409)

            cursor.execute(
                """
                INSERT INTO `user` (
                    username,
                    password_hash,
                    real_name,
                    id_card,
                    phone,
                    role,
                    airline_id,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, '乘客', NULL, NOW())
                """,
                (
                    username,
                    hash_password(password),
                    real_name,
                    id_card,
                    phone,
                ),
            )

            user_id = cursor.lastrowid

        connection.commit()

        return success_response(
            {
                "user_id": user_id,
                "username": username,
                "real_name": real_name,
                "role": "乘客",
            },
            "注册成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("注册失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@auth_bp.post("/login")
def login():
    """登录并返回 JWT。"""
    data = request.get_json(silent=True) or {}

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return error_response("用户名和密码不能为空")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                 user_id,
                 username,
                 password_hash,
                 real_name,
                 role,
                 airline_id,
                 admin_role,
                 status
                FROM `user`
                WHERE username = %s
                LIMIT 1
                """,
                (username,),
            )

            user = cursor.fetchone()

        if user is None or user["password_hash"] != hash_password(password):
            return error_response("用户名或密码错误", 401)

        if user["status"] != "正常":
            return error_response("账号已被禁用，请联系管理员", 403)

        if user["role"] == "航空公司管理员":
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE `user`
                    SET last_login_at = NOW()
                    WHERE user_id = %s
                    """,
                    (user["user_id"],),
                )

            connection.commit()

        token = generate_token(user)

        return success_response(
            {
                "token": token,
                "user": {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "real_name": user["real_name"],
                    "role": user["role"],
                    "airline_id": user["airline_id"],
                    "admin_role": user["admin_role"],
                },
            },
            "登录成功",
        )

    except Exception as error:
        return error_response("登录失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@auth_bp.get("/users/me")
@login_required
def get_current_user():
    """查询当前已登录用户的完整个人信息。"""
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
                    role,
                    airline_id,
                    admin_role,
                    status,
                    created_at,
                    last_login_at
                FROM `user`
                WHERE user_id = %s
                LIMIT 1
                """,
                (g.current_user["user_id"],),
            )

            user = cursor.fetchone()

        if user is None:
            return error_response("未找到当前用户", 404)

        return success_response(
            {
                "user_id": user["user_id"],
                "userId": user["user_id"],
                "username": user["username"],
                "real_name": user["real_name"],
                "realName": user["real_name"],
                "id_card": user["id_card"],
                "idCard": user["id_card"],
                "phone": user["phone"],
                "email": user["email"],
                "role": user["role"],
                "airline_id": user["airline_id"],
                "airlineId": user["airline_id"],
                "admin_role": user["admin_role"],
                "adminRole": user["admin_role"],
                "status": user["status"],
                "created_at": (
                    user["created_at"].isoformat(sep=" ", timespec="seconds")
                    if user["created_at"] is not None
                    else None
                ),
                "createdAt": (
                    user["created_at"].isoformat(sep=" ", timespec="seconds")
                    if user["created_at"] is not None
                    else None
                ),
                "last_login_at": (
                    user["last_login_at"].isoformat(sep=" ", timespec="seconds")
                    if user["last_login_at"] is not None
                    else None
                ),
                "lastLoginAt": (
                    user["last_login_at"].isoformat(sep=" ", timespec="seconds")
                    if user["last_login_at"] is not None
                    else None
                ),
            },
            "查询成功",
        )

    except Exception as error:
        return error_response("当前用户信息查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@auth_bp.put("/users/me/profile")
@login_required
def update_current_user_profile():
    """修改当前用户个人信息：姓名、手机号、邮箱。"""
    data = request.get_json(silent=True) or {}

    real_name = str(data.get("realName", data.get("real_name", ""))).strip()
    phone = str(data.get("phone", "")).strip() or None
    email = str(data.get("email", "")).strip() or None

    if not real_name:
        return error_response("姓名不能为空")

    if len(real_name) > 20:
        return error_response("姓名不能超过 20 个字符")

    if phone is not None and (len(phone) != 11 or not phone.isdigit()):
        return error_response("手机号必须为 11 位数字")

    if email is not None:
        if len(email) > 100:
            return error_response("邮箱不能超过 100 个字符")
        if "@" not in email or "." not in email:
            return error_response("邮箱格式不正确")

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
                SET real_name = %s,
                    phone = %s,
                    email = %s
                WHERE user_id = %s
                """,
                (
                    real_name,
                    phone,
                    email,
                    g.current_user["user_id"],
                ),
            )

        connection.commit()

        return success_response(
            {
                "realName": real_name,
                "phone": phone,
                "email": email,
            },
            "个人信息修改成功",
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("个人信息修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@auth_bp.put("/users/me/password")
@login_required
def update_current_user_password():
    """修改当前用户登录密码。"""
    data = request.get_json(silent=True) or {}

    old_password = str(data.get("oldPassword", data.get("old_password", "")))
    new_password = str(data.get("newPassword", data.get("new_password", "")))

    if not old_password or not new_password:
        return error_response("原密码和新密码不能为空")

    if len(new_password) < 8:
        return error_response("新密码不能少于 8 个字符")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT password_hash
                FROM `user`
                WHERE user_id = %s
                LIMIT 1
                """,
                (g.current_user["user_id"],),
            )

            user = cursor.fetchone()

            if user is None:
                return error_response("未找到当前用户", 404)

            if user["password_hash"] != hash_password(old_password):
                return error_response("原密码错误", 400)

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

        return success_response(message="密码修改成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("密码修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@auth_bp.get("/users/me/login-records")
@login_required
def list_current_user_login_records():
    """查询当前用户登录记录。当前版本先返回最近一次登录记录。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    username,
                    last_login_at,
                    created_at
                FROM `user`
                WHERE user_id = %s
                LIMIT 1
                """,
                (g.current_user["user_id"],),
            )

            user = cursor.fetchone()

        if user is None:
            return error_response("未找到当前用户", 404)

        login_time = user["last_login_at"] or user["created_at"]

        records = [
            {
                "recordId": 1,
                "loginTime": (
                    login_time.isoformat(sep=" ", timespec="seconds")
                    if login_time is not None
                    else "-"
                ),
                "device": "浏览器",
                "location": "本地开发环境",
                "status": "登录成功",
            }
        ]

        return success_response(records, "查询成功")

    except Exception as error:
        return error_response("登录记录查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
