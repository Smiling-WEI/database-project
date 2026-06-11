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
    """查询当前已登录用户的信息。"""
    return success_response(
        {
            "user_id": g.current_user["user_id"],
            "username": g.current_user["username"],
            "real_name": g.current_user["real_name"],
            "role": g.current_user["role"],
            "airline_id": g.current_user["airline_id"],
        },
        "查询成功",
    )