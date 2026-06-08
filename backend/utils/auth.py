import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, request

from db import get_db_connection
from utils.response import error_response


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "airline-ticket-system-secret-key")
JWT_ALGORITHM = "HS256"


def generate_token(user):
    """为登录用户生成有效期为 24 小时的 JWT。"""
    payload = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def login_required(view_function):
    """校验请求头中的登录凭证，并将用户信息保存到 g.current_user。"""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return error_response("请先登录", 401)

        token = authorization.removeprefix("Bearer ").strip()

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
            )

        except jwt.ExpiredSignatureError:
            return error_response("登录状态已过期，请重新登录", 401)

        except jwt.InvalidTokenError:
            return error_response("登录凭证无效", 401)

        connection = None

        try:
            connection = get_db_connection()

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id, username, real_name, role, airline_id
                    FROM `user`
                    WHERE user_id = %s
                    """,
                    (payload["user_id"],),
                )

                user = cursor.fetchone()

            if user is None:
                return error_response("用户不存在", 401)

            g.current_user = user

        finally:
            if connection is not None:
                connection.close()

        return view_function(*args, **kwargs)

    return wrapped_view
def role_required(*allowed_roles):
    """限制只有指定角色可以访问接口。"""

    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            if g.current_user["role"] not in allowed_roles:
                return error_response("无权访问该接口", 403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator