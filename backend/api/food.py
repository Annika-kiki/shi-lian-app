"""Flask food endpoints mounted inside the existing ASGI application."""
from flask import Flask, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from backend.database.session import SessionLocal
from backend.services.food import parse, search

food_app = Flask(__name__)
food_app.json.ensure_ascii = False

def error(message, status):
    return jsonify(code=status, message=message, data={}), status

@food_app.post('/parse')
def parse_food():
    body = request.get_json(silent=True)
    if not isinstance(body, dict): return error('请求必须为JSON对象', 400)
    try:
        with SessionLocal() as db:
            return jsonify(code=0, data=parse(db, body.get('text')))
    except (ValueError, OverflowError) as exc:
        return error(str(exc), 400)
    except SQLAlchemyError:
        return error('食物库暂时不可用', 503)

@food_app.get('/search')
def search_food():
    try:
        with SessionLocal() as db:
            return jsonify(code=0, data=search(db, request.args.get('q', '')))
    except SQLAlchemyError:
        return error('食物库暂时不可用', 503)
