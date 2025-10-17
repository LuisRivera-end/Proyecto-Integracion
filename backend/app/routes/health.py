from flask import Blueprint, jsonify

bp = Blueprint('health', __name__)

@bp.route('/v1/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200