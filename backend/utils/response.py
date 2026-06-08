from flask import jsonify


def success_response(data=None, message="操作成功", status_code=200):
    """返回成功响应。"""
    payload = {
        "code": status_code,
        "success": True,
        "message": message,
    }

    if data is not None:
        payload["data"] = data

    return jsonify(payload), status_code


def error_response(message="操作失败", status_code=400, error=None):
    """返回失败响应。"""
    payload = {
        "code": status_code,
        "success": False,
        "message": message,
    }

    if error is not None:
        payload["error"] = str(error)

    return jsonify(payload), status_code