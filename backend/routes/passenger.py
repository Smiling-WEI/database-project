from flask import Blueprint, g, request

from db import get_db_connection
from utils.auth import login_required
from utils.response import error_response, success_response


passenger_bp = Blueprint("passenger", __name__, url_prefix="/api")


def validate_passenger_data(data):
    """校验乘机人信息，并返回清洗后的数据。"""
    real_name = str(data.get("real_name", "")).strip()
    id_card = str(data.get("id_card", "")).strip()
    phone = str(data.get("phone", "")).strip() or None
    relation_note = str(data.get("relation_note", "")).strip() or None

    if not real_name or not id_card:
        return None, "真实姓名和身份证号不能为空"

    if len(real_name) > 20:
        return None, "真实姓名不能超过 20 个字符"

    if len(id_card) != 18:
        return None, "身份证号必须为 18 位"

    if phone is not None and (len(phone) != 11 or not phone.isdigit()):
        return None, "手机号必须为 11 位数字"

    if relation_note is not None and len(relation_note) > 50:
        return None, "关系备注不能超过 50 个字符"

    return {
        "real_name": real_name,
        "id_card": id_card,
        "phone": phone,
        "relation_note": relation_note,
    }, None


@passenger_bp.get("/passengers")
@login_required
def list_passengers():
    """查询当前用户的常用乘机人。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.passenger_id,
                    p.real_name,
                    p.id_card,
                    p.phone,
                    up.relation_note
                FROM user_passenger AS up
                JOIN passenger AS p
                  ON p.passenger_id = up.passenger_id
                WHERE up.user_id = %s
                ORDER BY p.passenger_id
                """,
                (g.current_user["user_id"],),
            )

            rows = cursor.fetchall()

        passengers = [
            {
                "passengerId": row["passenger_id"],
                "realName": row["real_name"],
                "idCard": row["id_card"],
                "phone": row["phone"],
                "relationNote": row["relation_note"],
            }
            for row in rows
        ]

        return success_response(passengers, "查询成功")

    except Exception as error:
        return error_response("乘机人查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@passenger_bp.post("/passengers")
@login_required
def add_passenger():
    """新增常用乘机人，或关联已有乘机人资料。"""
    data = request.get_json(silent=True) or {}
    passenger_data, validation_error = validate_passenger_data(data)

    if validation_error is not None:
        return error_response(validation_error)

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT passenger_id
                FROM passenger
                WHERE id_card = %s
                LIMIT 1
                """,
                (passenger_data["id_card"],),
            )

            existing_passenger = cursor.fetchone()

            if existing_passenger is None:
                cursor.execute(
                    """
                    INSERT INTO passenger (
                        real_name,
                        id_card,
                        phone
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        passenger_data["real_name"],
                        passenger_data["id_card"],
                        passenger_data["phone"],
                    ),
                )

                passenger_id = cursor.lastrowid

            else:
                passenger_id = existing_passenger["passenger_id"]

            cursor.execute(
                """
                SELECT 1
                FROM user_passenger
                WHERE user_id = %s
                  AND passenger_id = %s
                LIMIT 1
                """,
                (
                    g.current_user["user_id"],
                    passenger_id,
                ),
            )

            if cursor.fetchone() is not None:
                return error_response("该乘机人已经在常用乘机人列表中", 409)

            cursor.execute(
                """
                INSERT INTO user_passenger (
                    user_id,
                    passenger_id,
                    relation_note
                )
                VALUES (%s, %s, %s)
                """,
                (
                    g.current_user["user_id"],
                    passenger_id,
                    passenger_data["relation_note"],
                ),
            )

        connection.commit()

        return success_response(
            {"passengerId": passenger_id},
            "乘机人添加成功",
            201,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("乘机人添加失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@passenger_bp.put("/passengers/<int:passenger_id>")
@login_required
def update_passenger(passenger_id):
    """修改当前用户已关联的乘机人信息。"""
    data = request.get_json(silent=True) or {}
    passenger_data, validation_error = validate_passenger_data(data)

    if validation_error is not None:
        return error_response(validation_error)

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM user_passenger
                WHERE user_id = %s
                  AND passenger_id = %s
                LIMIT 1
                """,
                (
                    g.current_user["user_id"],
                    passenger_id,
                ),
            )

            if cursor.fetchone() is None:
                return error_response("未找到该常用乘机人", 404)

            cursor.execute(
                """
                SELECT passenger_id
                FROM passenger
                WHERE id_card = %s
                  AND passenger_id <> %s
                LIMIT 1
                """,
                (
                    passenger_data["id_card"],
                    passenger_id,
                ),
            )

            if cursor.fetchone() is not None:
                return error_response("该身份证号已被其他乘机人使用", 409)

            cursor.execute(
                """
                UPDATE passenger
                SET real_name = %s,
                    id_card = %s,
                    phone = %s
                WHERE passenger_id = %s
                """,
                (
                    passenger_data["real_name"],
                    passenger_data["id_card"],
                    passenger_data["phone"],
                    passenger_id,
                ),
            )

            cursor.execute(
                """
                UPDATE user_passenger
                SET relation_note = %s
                WHERE user_id = %s
                  AND passenger_id = %s
                """,
                (
                    passenger_data["relation_note"],
                    g.current_user["user_id"],
                    passenger_id,
                ),
            )

        connection.commit()

        return success_response(message="乘机人修改成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("乘机人修改失败", 500, error)

    finally:
        if connection is not None:
            connection.close()


@passenger_bp.delete("/passengers/<int:passenger_id>")
@login_required
def delete_passenger(passenger_id):
    """删除当前用户与常用乘机人的关联关系。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM user_passenger
                WHERE user_id = %s
                  AND passenger_id = %s
                """,
                (
                    g.current_user["user_id"],
                    passenger_id,
                ),
            )

            if cursor.rowcount == 0:
                return error_response("未找到该常用乘机人", 404)

        connection.commit()

        return success_response(message="乘机人删除成功")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        return error_response("乘机人删除失败", 500, error)

    finally:
        if connection is not None:
            connection.close()