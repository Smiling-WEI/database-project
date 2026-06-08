from flask import Blueprint

from db import get_db_connection
from utils.response import error_response, success_response


flight_notice_bp = Blueprint(
    "flight_notice",
    __name__,
    url_prefix="/api",
)


@flight_notice_bp.get("/flights/<int:instance_id>/irregularities")
def list_public_flight_irregularities(instance_id):
    """供普通用户查询航班当前生效中的异常通知。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT instance_id
                FROM flight_instance
                WHERE instance_id = %s
                LIMIT 1
                """,
                (instance_id,),
            )

            if cursor.fetchone() is None:
                return error_response("未找到该航班", 404)

            cursor.execute(
                """
                SELECT
                    irregularity_id,
                    instance_id,
                    irregularity_type,
                    responsibility_type,
                    description,
                    status,
                    created_at
                FROM flight_irregularity
                WHERE instance_id = %s
                  AND status = '生效中'
                ORDER BY created_at DESC, irregularity_id DESC
                """,
                (instance_id,),
            )

            rows = cursor.fetchall()

        notices = [
            {
                "irregularityId": row["irregularity_id"],
                "instanceId": row["instance_id"],
                "irregularityType": row["irregularity_type"],
                "responsibilityType": row["responsibility_type"],
                "description": row["description"],
                "status": row["status"],
                "createdAt": row["created_at"].isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
            }
            for row in rows
        ]

        return success_response(notices, "查询成功")

    except Exception as error:
        return error_response("航班异常通知查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()