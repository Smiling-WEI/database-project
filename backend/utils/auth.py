from functools import wraps
from datetime import datetime, timedelta
import os

import jwt
from flask import current_app, g, request

from db import get_db_connection
from utils.response import error_response


SYSTEM_ADMIN_ROLES = {
    "系统总管理员",
    "平台总管理员",
    "总管理员",
}

AIRLINE_ADMIN_ROLES = {
    "航司管理员",
    "航空公司管理员",
    "航司内部管理员",
}


def _get_secret_key():
    return (
        current_app.config.get("SECRET_KEY")
        or current_app.config.get("JWT_SECRET")
        or os.getenv("SECRET_KEY")
        or os.getenv("JWT_SECRET")
        or "airline-ticket-secret"
    )


def generate_token(user):
    """给登录成功的用户生成 JWT。routes/auth.py 会调用这个函数。"""
    payload = {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "role": user.get("role"),
        "admin_role": user.get("admin_role"),
        "airline_id": user.get("airline_id"),
        "exp": datetime.utcnow() + timedelta(days=7),
    }

    token = jwt.encode(
        payload,
        _get_secret_key(),
        algorithm="HS256",
    )

    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token


def is_system_admin_user(user):
    if not user:
        return False

    return (
        user.get("role") in SYSTEM_ADMIN_ROLES
        or user.get("admin_role") in SYSTEM_ADMIN_ROLES
    )


def _extract_token():
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return (
        request.headers.get("X-Token")
        or request.args.get("token")
        or ""
    )


def _load_current_user_from_token():
    token = _extract_token()

    if not token:
        return error_response("请先登录", 401)

    try:
        payload = jwt.decode(
            token,
            _get_secret_key(),
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return error_response("登录已过期，请重新登录", 401)
    except Exception:
        return error_response("登录状态无效，请重新登录", 401)

    user_id = payload.get("user_id") or payload.get("userId")

    if not user_id:
        return error_response("登录状态无效，请重新登录", 401)

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
                    role,
                    airline_id,
                    admin_role,
                    status
                FROM `user`
                WHERE user_id = %s
                LIMIT 1
                """,
                (user_id,),
            )

            user = cursor.fetchone()

    except Exception as error:
        return error_response("登录状态校验失败", 500, error)

    finally:
        if connection is not None:
            connection.close()

    if user is None:
        return error_response("当前账号不存在", 401)

    if user.get("status") != "正常":
        return error_response("当前账号已被禁用", 403)

    g.current_user = {
        "user_id": user["user_id"],
        "username": user["username"],
        "real_name": user["real_name"],
        "role": user["role"],
        "airline_id": user["airline_id"],
        "admin_role": user["admin_role"],
        "status": user["status"],
    }

    return None


def _ensure_current_user():
    if hasattr(g, "current_user") and g.current_user:
        return None

    return _load_current_user_from_token()


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        error = _ensure_current_user()

        if error:
            return error

        return func(*args, **kwargs)

    return wrapper


def role_required(*roles):
    """角色权限校验。

    系统总管理员直接放行；
    其他账号按 role 判断。
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error = _ensure_current_user()

            if error:
                return error

            if is_system_admin_user(g.current_user):
                return func(*args, **kwargs)

            if g.current_user.get("role") not in roles:
                return error_response("无权访问该接口", 403)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def admin_role_required(*admin_roles):
    """航司内部岗位权限校验。

    系统总管理员直接放行；
    航司主管理员拥有本航司全部内部操作权限；
    其他岗位按 admin_role 精确判断。
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error = _ensure_current_user()

            if error:
                return error

            if is_system_admin_user(g.current_user):
                return func(*args, **kwargs)

            if g.current_user.get("role") not in AIRLINE_ADMIN_ROLES:
                return error_response("无权访问该接口", 403)

            current_admin_role = g.current_user.get("admin_role")

            if current_admin_role == "航司主管理员":
                return func(*args, **kwargs)

            if current_admin_role not in admin_roles:
                return error_response("无权访问该接口", 403)

            return func(*args, **kwargs)

        return wrapper

    return decorator
