from flask import Flask, jsonify
from flask_cors import CORS

from db import get_db_connection
from routes.auth import auth_bp
from routes.flight import flight_bp
from routes.passenger import passenger_bp
from routes.order import order_bp
from routes.admin_flight import admin_flight_bp
from routes.admin_rule import admin_rule_bp
from routes.admin_order import admin_order_bp
from routes.admin_pricing import admin_pricing_bp
from routes.change import change_bp
from routes.flight_notice import flight_notice_bp


app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app)
app.register_blueprint(auth_bp)
app.register_blueprint(flight_bp)
app.register_blueprint(passenger_bp)
app.register_blueprint(order_bp)
app.register_blueprint(admin_flight_bp)
app.register_blueprint(admin_rule_bp)
app.register_blueprint(admin_order_bp)
app.register_blueprint(admin_pricing_bp)
app.register_blueprint(change_bp)
app.register_blueprint(flight_notice_bp)


@app.get("/api/health")
def health_check():
    """检查后端服务和数据库连接是否正常。"""
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            result = cursor.fetchone()

        return jsonify(
            {
                "success": True,
                "message": "后端服务和数据库连接正常",
                "data": result,
            }
        )

    except Exception as error:
        return jsonify(
            {
                "success": False,
                "message": "数据库连接失败",
                "error": str(error),
            }
        ), 500

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)