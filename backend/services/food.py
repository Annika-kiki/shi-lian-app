import math
import re
import threading
import time
from difflib import SequenceMatcher
from decimal import Decimal, ROUND_HALF_UP, localcontext
from sqlalchemy import or_, select
from backend.models.food import Food

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
QUANTITY = re.compile(rf"({NUMBER}|nan|inf(?:inity)?)\s*(克|g|个|杯|碗|份)", re.I)
_cache = {}
_lock = threading.Lock()

def invalidate_catalog():
    with _lock:
        _cache.clear()

def catalog(db):
    bind = db.get_bind()
    with _lock:
        entry = _cache.get(bind)
        if entry and time.monotonic() - entry[0] < 60:
            return entry[1]
        rows = [dict(row) for row in db.execute(select(Food.__table__).order_by(Food.id)).mappings()]
        _cache[bind] = (time.monotonic(), rows)
        return rows

def numeric(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}必须为数值")
    if value > 3.4e38 or value < 0 or not math.isfinite(value) or (positive and value == 0):
        raise ValueError(f"{label}必须为{'正' if positive else '非负'}有限数值")
    return value

def labels(row):
    return [row['name']] + [s.strip() for s in (row['aliases'] or '').split(';') if s.strip()]

def rank(row, name):
    names = labels(row)
    if name == names[0]: return (0, 0, row['name'], row['id']), 1.0
    if name in names[1:]: return (1, 0, row['name'], row['id']), 1.0
    contained = [n for n in names if name in n or n in name]
    if contained:
        return (2, min(abs(len(n)-len(name)) for n in contained), row['name'], row['id']), 0.9
    similarity = max(SequenceMatcher(None, name, n).ratio() for n in names)
    return (3, -similarity, row['name'], row['id']), similarity

def parse(db, text):
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:
        raise ValueError('text必须为非空字符串，最多1000字符')
    text = text.strip()
    matches = list(QUANTITY.finditer(text))
    if len(matches) > 1: raise ValueError('一次只能解析一种食物和一个数量')
    quantity = None
    unit = None
    name = text
    if matches:
        match = matches[0]
        quantity = numeric(float(match[1]), '数量', True)
        unit = match[2].lower()
        name = (text[:match.start()] + text[match.end():]).strip()
    if not name: raise ValueError('缺少食物名称')
    candidates = sorted(((*rank(row, name), row) for row in catalog(db)), key=lambda x: x[0])
    found = candidates[0] if candidates and (candidates[0][0][0] < 3 or candidates[0][1] >= 0.6) else None
    if unit and unit not in ('g', '克'):
        if not found or unit != found[2]['unit']:
            raise ValueError('无法确定该单位与克数的换算关系，请输入克数')
        quantity *= found[2]['default_quantity_g']
    if not found:
        return dict(matched=False, food_name=name, quantity_g=quantity or 100, kcal=200,
                    protein_g=10, carbs_g=20, fat_g=8, confidence=0)
    row = found[2]
    quantity = quantity if quantity is not None else row['default_quantity_g']
    numeric(quantity, '克数', True)
    result = dict(matched=True, food_name=row['name'], quantity_g=quantity, confidence=found[1])
    for output, column, precision in [('kcal','kcal_per_100g',0), ('protein_g','protein_per_100g',1),
                                      ('carbs_g','carbs_per_100g',1), ('fat_g','fat_per_100g',1)]:
        value = row[column]
        if value is None: raise ValueError('该食物营养数据不完整，请补充食物库')
        numeric(value, column)
        amount = Decimal(str(value)) * Decimal(str(quantity)) / 100
        if amount > Decimal('3.4e38'): raise ValueError('营养计算结果超出范围')
        with localcontext() as ctx:
            ctx.prec = 64
            rounded = amount.quantize(Decimal('1') if precision == 0 else Decimal('0.1'), rounding=ROUND_HALF_UP)
        result[output] = int(rounded) if precision == 0 else float(rounded)
    return result

def search(db, q):
    q = q.strip()
    if not q: return []
    escaped = q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    rows = db.execute(select(Food).where(or_(Food.name.like(f'%{escaped}%', escape='\\'),
                                            Food.aliases.like(f'%{escaped}%', escape='\\')))).scalars().all()
    rows.sort(key=lambda row: rank({'name':row.name,'aliases':row.aliases,'id':row.id}, q)[0])
    return [dict(id=row.id, name=row.name, kcal_per_100g=row.kcal_per_100g) for row in rows[:10]]
