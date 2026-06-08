from datetime import date

from flask import Blueprint, request

from db import get_db_connection
from utils.response import error_response, success_response


flight_bp = Blueprint("flight", __name__, url_prefix="/api")


@flight_bp.get("/flights/search")
def search_flights():
    """按照出发城市、到达城市和日期查询可预订航班。"""
    departure = str(request.args.get("departure", "")).strip()
    arrival = str(request.args.get("arrival", "")).strip()
    flight_date = str(request.args.get("date", "")).strip()

    if not departure or not arrival or not flight_date:
        return error_response("出发地、目的地和出发日期不能为空")

    try:
        date.fromisoformat(flight_date)
    except ValueError:
        return error_response("出发日期格式应为 YYYY-MM-DD")

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    fi.instance_id,
                    fni.flight_no,
                    ac.airline_name,
                    dep_airport.airport_name AS dep_airport,
                    arr_airport.airport_name AS arr_airport,
                    fi.status,
                    (
                        SELECT cp.sale_price
                        FROM cabin_pricing AS cp
                        WHERE cp.instance_id = fi.instance_id
                          AND cp.cabin_type = '经济舱'
                          AND cp.valid_from <= NOW()
                          AND cp.valid_to >= NOW()
                        ORDER BY cp.valid_from DESC, cp.pricing_id DESC
                        LIMIT 1
                    ) AS price,
                    GREATEST(
                        fi.economy_seats - (
                            SELECT COUNT(*)
                            FROM active_ticket_sale AS ats
                            JOIN cabin_pricing AS sold_cp
                              ON sold_cp.pricing_id = ats.pricing_id
                            WHERE ats.instance_id = fi.instance_id
                              AND sold_cp.cabin_type = '经济舱'
                              AND ats.order_status = '已支付'
                        ),
                        0
                    ) AS seats
                FROM flight_instance AS fi
                JOIN flight_no_info AS fni
                  ON fni.flight_no = fi.flight_no
                JOIN airline_company AS ac
                  ON ac.airline_id = fni.airline_id
                JOIN route AS r
                  ON r.route_id = fni.route_id
                JOIN airport AS dep_airport
                  ON dep_airport.airport_code = r.dep_airport_code
                JOIN airport AS arr_airport
                  ON arr_airport.airport_code = r.arr_airport_code
                WHERE dep_airport.city_name = %s
                  AND arr_airport.city_name = %s
                  AND fi.flight_date = %s
                  AND fi.status <> '取消'
                ORDER BY fni.flight_no
                """,
                (departure, arrival, flight_date),
            )

            rows = cursor.fetchall()

        flights = []

        for row in rows:
            flights.append(
                {
                    "instanceId": row["instance_id"],
                    "flightNo": row["flight_no"],
                    "airlineName": row["airline_name"],
                    "depAirport": row["dep_airport"],
                    "arrAirport": row["arr_airport"],
                    "depTime": "",
                    "arrTime": "",
                    "price": (
                        float(row["price"])
                        if row["price"] is not None
                        else None
                    ),
                    "seats": int(row["seats"]),
                    "status": row["status"],
                }
            )

        return success_response(flights, "查询成功")

    except Exception as error:
        return error_response("航班查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()
@flight_bp.get("/flights/<int:instance_id>/cabins")
def get_flight_cabins(instance_id):
    """查询指定航班当前有效的舱位价格和剩余座位。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    cp.pricing_id,
                    cp.cabin_type,
                    cp.sale_price,
                    CASE
                        WHEN cp.cabin_type = '头等舱' THEN fi.first_seats
                        WHEN cp.cabin_type = '经济舱' THEN fi.economy_seats
                        ELSE 0
                    END AS total_seats,
                    GREATEST(
                        CASE
                            WHEN cp.cabin_type = '头等舱' THEN fi.first_seats
                            WHEN cp.cabin_type = '经济舱' THEN fi.economy_seats
                            ELSE 0
                        END - (
                            SELECT COUNT(*)
                            FROM active_ticket_sale AS ats
                            JOIN cabin_pricing AS sold_cp
                              ON sold_cp.pricing_id = ats.pricing_id
                            WHERE ats.instance_id = fi.instance_id
                              AND sold_cp.cabin_type = cp.cabin_type
                              AND ats.order_status = '已支付'
                        ),
                        0
                    ) AS remaining_seats
                FROM flight_instance AS fi
                JOIN cabin_pricing AS cp
                  ON cp.instance_id = fi.instance_id
                WHERE fi.instance_id = %s
                  AND fi.status <> '取消'
                  AND cp.valid_from <= NOW()
                  AND cp.valid_to >= NOW()
                  AND NOT EXISTS (
                      SELECT 1
                      FROM cabin_pricing AS newer_cp
                      WHERE newer_cp.instance_id = cp.instance_id
                        AND newer_cp.cabin_type = cp.cabin_type
                        AND newer_cp.valid_from <= NOW()
                        AND newer_cp.valid_to >= NOW()
                        AND (
                            newer_cp.valid_from > cp.valid_from
                            OR (
                                newer_cp.valid_from = cp.valid_from
                                AND newer_cp.pricing_id > cp.pricing_id
                            )
                        )
                  )
                ORDER BY FIELD(cp.cabin_type, '经济舱', '商务舱', '头等舱')
                """,
                (instance_id,),
            )

            rows = cursor.fetchall()

        if not rows:
            return error_response("航班不存在或暂无有效舱位价格", 404)

        cabins = []

        for row in rows:
            cabins.append(
                {
                    "pricingId": row["pricing_id"],
                    "cabinType": row["cabin_type"],
                    "price": float(row["sale_price"]),
                    "totalSeats": int(row["total_seats"]),
                    "remainingSeats": int(row["remaining_seats"]),
                }
            )

        return success_response(cabins, "查询成功")

    except Exception as error:
        return error_response("舱位价格查询失败", 500, error)

    finally:
        if connection is not None:
            connection.close()