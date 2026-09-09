"""Local recipe generator with more varied cooking styles."""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

from fastapi import HTTPException

from backend.models.entities import Ingredient
from backend.services.nutrition import nutrition_for_ingredients


PROTEIN_NAMES = {
    "鸡胸肉",
    "鸡腿肉",
    "牛肉",
    "三文鱼",
    "虾仁",
    "鸡蛋",
    "北豆腐",
    "嫩豆腐",
    "金枪鱼",
    "无糖酸奶",
    "牛奶",
}

CARB_NAMES = {
    "米饭",
    "糙米饭",
    "燕麦",
    "全麦面包",
    "红薯",
    "土豆",
    "玉米",
    "荞麦面",
    "南瓜",
    "杂粮饭",
}

VEG_NAMES = {
    "西兰花",
    "菠菜",
    "生菜",
    "番茄",
    "黄瓜",
    "胡萝卜",
    "香菇",
    "金针菇",
    "洋葱",
    "菜花",
    "青椒",
    "茄子",
    "芹菜",
    "白菜",
    "芦笋",
    "小白菜",
    "娃娃菜",
    "秋葵",
    "西葫芦",
    "彩椒",
}

OIL_NAMES = {"橄榄油", "芝麻油", "花生油", "菜籽油", "亚麻籽油"}

STYLE_ORDER = [
    "steam",
    "soup",
    "bowl",
    "stir_fry",
    "roast",
    "braise",
    "salad",
]

STYLE_EXTRA_PRIORITY = {
    "steam": ["香菇", "番茄", "白菜", "芦笋"],
    "soup": ["番茄", "香菇", "金针菇", "白菜"],
    "bowl": ["生菜", "黄瓜", "番茄", "玉米"],
    "stir_fry": ["洋葱", "青椒", "胡萝卜", "香菇"],
    "roast": ["菜花", "洋葱", "南瓜", "土豆"],
    "braise": ["土豆", "胡萝卜", "洋葱", "香菇"],
    "salad": ["生菜", "黄瓜", "番茄", "胡萝卜"],
}

STYLE_MINUTES = {
    "steam": 20,
    "soup": 22,
    "bowl": 15,
    "stir_fry": 18,
    "roast": 25,
    "braise": 28,
    "salad": 12,
}

STYLE_TAGS = {
    "steam": ["清爽", "蒸制"],
    "soup": ["暖胃", "轻负担"],
    "bowl": ["快手", "均衡"],
    "stir_fry": ["少油", "快手"],
    "roast": ["烤箱", "低脂"],
    "braise": ["焖煮", "饱足"],
    "salad": ["清爽", "轻负担"],
}


def _split_preferences(preference: str | None) -> set[str]:
    if not preference:
        return set()
    parts = re.split(r"[，,；;、|+]+", preference)
    cleaned: set[str] = set()
    for part in parts:
        token = re.sub(r"\s+", "", part or "").strip()
        if token:
            cleaned.add(token)
    return cleaned


def _split_aliases(text: str) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in re.split(r"[，,；;、]+", text) if part.strip()]


def _load_ingredient_index(db) -> tuple[list[Ingredient], dict[str, Ingredient]]:
    ingredients = db.query(Ingredient).all()
    lookup: dict[str, Ingredient] = {}
    for item in ingredients:
        lookup[item.name] = item
        for alias in _split_aliases(item.aliases):
            lookup.setdefault(alias, item)
    return ingredients, lookup


def _unique_by_id(items: Iterable[Ingredient]) -> list[Ingredient]:
    seen: set[int] = set()
    result: list[Ingredient] = []
    for item in items:
        if item.id in seen:
            continue
        seen.add(item.id)
        result.append(item)
    return result


def _match_selected_ingredients(
    db_lookup: dict[str, Ingredient],
    raw_names: Iterable[str],
    all_ingredients: list[Ingredient],
) -> list[Ingredient]:
    selected: list[Ingredient] = []
    for raw in raw_names:
        cleaned = str(raw).strip()
        if not cleaned:
            continue
        candidate = db_lookup.get(cleaned)
        if not candidate:
            candidate = next(
                (
                    item
                    for key, item in db_lookup.items()
                    if key and (key in cleaned or cleaned in key)
                ),
                None,
            )
        if candidate and candidate not in selected:
            selected.append(candidate)

    # Keep the argument for call-site compatibility; unknown user input must
    # never be silently replaced with foods the user did not select.
    del all_ingredients
    return _unique_by_id(selected)


def _rotate_items(items: list[Ingredient], offset: int) -> list[Ingredient]:
    if not items:
        return []
    offset = offset % len(items)
    if not offset:
        return items[:]
    return items[offset:] + items[:offset]


def _group_ingredients(items: list[Ingredient]) -> tuple[Ingredient | None, Ingredient | None, Ingredient | None]:
    protein = next((item for item in items if item.name in PROTEIN_NAMES), None)
    carb = next((item for item in items if item.name in CARB_NAMES), None)
    veg = next((item for item in items if item.name in VEG_NAMES), None)
    return protein, carb, veg


NEW_RECIPE_STYLES = [
    {
        "style": "steam",
        "suffix": "清蒸盘",
        "minutes": 15,
        "tags": ["少油", "清爽", "蒸制"],
    },
    {
        "style": "soup",
        "suffix": "暖汤锅",
        "minutes": 15,
        "tags": ["少油", "暖胃", "轻负担"],
    },
    {
        "style": "bowl",
        "suffix": "能量碗",
        "minutes": 12,
        "tags": ["少油", "快手", "均衡"],
    },
    {
        "style": "pan",
        "suffix": "香煎盘",
        "minutes": 15,
        "tags": ["少油", "快手", "香煎"],
    },
    {
        "style": "stir",
        "suffix": "快炒盘",
        "minutes": 15,
        "tags": ["少油", "快手", "快炒"],
    },
    {
        "style": "salad",
        "suffix": "清爽拌碗",
        "minutes": 10,
        "tags": ["少油", "清爽", "低脂"],
    },
]


def _match_requested_ingredients(
    db_lookup: dict[str, Ingredient], raw_names: Iterable[str]
) -> list[Ingredient]:
    selected: list[Ingredient] = []
    for raw in raw_names:
        cleaned = str(raw).strip()
        if not cleaned:
            continue
        candidate = db_lookup.get(cleaned)
        if not candidate:
            candidate = next(
                (
                    item
                    for key, item in db_lookup.items()
                    if key and (key in cleaned or cleaned in key)
                ),
                None,
            )
        if candidate and candidate not in selected:
            selected.append(candidate)
    return _unique_by_id(selected)


def _ingredient_kind(item: Ingredient) -> str:
    if item.name in PROTEIN_NAMES:
        return "protein"
    if item.name in CARB_NAMES:
        return "carb"
    if item.name in VEG_NAMES:
        return "veg"
    return "other"


def _nutrition_note(nutrition: dict) -> str:
    protein = nutrition.get("protein_g", 0)
    carb = nutrition.get("carb_g", 0)
    fat = nutrition.get("fat_g", 0)
    protein_text = "蛋白质充足" if protein >= 25 else "蛋白质偏少"
    carb_text = "碳水适中" if 25 <= carb <= 70 else "碳水较低" if carb < 25 else "碳水偏高"
    fat_text = "脂肪较低" if fat <= 18 else "脂肪适中"
    return f"{protein_text}，{carb_text}，{fat_text}。"


def _recipe_prefers_high_protein(preferences: set[str]) -> bool:
    return bool({"高蛋白", "增肌"} & preferences)


def _clean_missing_category_text(items: list[Ingredient]) -> str:
    protein, carb, veg = _group_ingredients(items)
    missing = []
    if protein is None:
        missing.append("蛋白质")
    if carb is None:
        missing.append("碳水")
    if veg is None:
        missing.append("蔬菜")
    if len(items) < 3 and not missing:
        missing.extend(["蛋白质", "碳水", "蔬菜"])
    if not missing:
        return ""
    return f"食材不足，建议补充{'、'.join(dict.fromkeys(missing))}类食材。"


def _clean_style_matches(style_info: dict, preferences: set[str], items: list[Ingredient]) -> bool:
    tags = set(style_info.get("tags", []))
    if {"少油", "低脂"} & preferences and "少油" not in tags:
        return False
    if {"15分钟内", "快手"} & preferences and int(style_info.get("minutes", 99)) > 15:
        return False
    if "清爽" in preferences and "清爽" not in tags:
        return False
    if _recipe_prefers_high_protein(preferences) and not any(_ingredient_kind(item) == "protein" for item in items):
        return False
    return True


def _clean_portion_for(item: Ingredient, style: str, target_calories: int, index: int) -> float:
    kind = _ingredient_kind(item)
    if kind == "protein":
        base = 160 if style in {"pan", "stir"} else 140
    elif kind == "carb":
        base = 120 if target_calories <= 450 else 150
    elif kind == "veg":
        base = 180 if style in {"steam", "salad", "soup"} else 150
    else:
        base = 60
    return float(max(40, min(260, base + (index - 1) * 10)))


def _clean_portions(items: list[Ingredient], style: str, target_calories: int) -> list[tuple[Ingredient, float]]:
    return [(item, _clean_portion_for(item, style, target_calories, idx)) for idx, item in enumerate(items)]


def _clean_steps(style: str, names: list[str]) -> list[str]:
    main = names[0] if names else "食材"
    second = names[1] if len(names) > 1 else main
    third = names[2] if len(names) > 2 else second
    if style == "steam":
        return [
            f"把{main}、{second}、{third}切成合适大小。",
            "放入蒸锅蒸到熟透，尽量少放油。",
            "出锅后用盐、生抽或黑胡椒简单调味。",
        ]
    if style == "soup":
        return [
            f"先把{main}和{second}加水煮出味道。",
            f"再放入{third}小火煮熟。",
            "最后用盐、味精或蒜末调味即可。",
        ]
    if style == "bowl":
        return [
            f"把{main}、{second}、{third}分别煮熟或焯水。",
            "全部装入碗中，用生抽、醋、黑胡椒拌匀。",
            "口味重时加一点蒜末或辣椒粉。",
        ]
    if style == "pan":
        return [
            f"{main}先用黑胡椒和少许盐抓匀。",
            f"平底锅少油煎熟{main}，旁边放入{second}和{third}。",
            "出锅前用少量生抽提味。",
        ]
    if style == "stir":
        return [
            f"把{main}切片，{second}切条，{third}切小块。",
            "热锅少油快速翻炒，先放蛋白质再放蔬菜。",
            "最后用盐和生抽收味，保持清爽。",
        ]
    return [
        f"把{main}、{second}、{third}焯水或直接切好备用。",
        "拌入少量生抽、醋、黑胡椒和蒜末。",
        "喜欢口感丰富可以加一点辣椒粉。",
    ]


def _clean_build_recipe_spec(
    items: list[Ingredient],
    target_calories: int,
    preferences: set[str],
    style_info: dict,
    warning: str,
) -> dict:
    portions = _clean_portions(items, style_info["style"], target_calories)
    nutrition = nutrition_for_ingredients(portions)
    names = [item.name for item, _ in portions]
    title = f"{''.join(names[:2])}{style_info['suffix']}"

    ingredients = []
    for ingredient, amount_g in portions:
        kind = _ingredient_kind(ingredient)
        ingredients.append({
            "ingredient": ingredient,
            "amount_g": round(amount_g, 0),
            "note": {
                "protein": "主蛋白",
                "carb": "主碳水",
                "veg": "蔬菜",
            }.get(kind, "基础食材"),
        })

    tags = []
    if _recipe_prefers_high_protein(preferences) and any(_ingredient_kind(item) == "protein" for item, _ in portions):
        tags.append("高蛋白")
    if {"少油", "低脂"} & preferences and "少油" in style_info["tags"]:
        tags.append("少油")
    if "清爽" in preferences and "清爽" in style_info["tags"]:
        tags.append("清爽")
    if {"15分钟内", "快手"} & preferences and style_info["minutes"] <= 15:
        tags.append("快手")
    tags.extend(style_info["tags"])
    if warning:
        tags.append("均衡")

    description = f"{warning}{_nutrition_note(nutrition)}"
    return {
        "name": title,
        "description": description,
        "minutes": style_info["minutes"],
        "tags": ",".join(dict.fromkeys(tags)),
        "cover_url": None,
        "is_system": False,
        "ingredients": ingredients,
        "steps": _clean_steps(style_info["style"], names),
        "nutrition": nutrition,
    }


def _clean_choose_page_items(pool: list[Ingredient], seed: int, recipe_round: int) -> list[Ingredient]:
    if not pool:
        return []

    buckets = {
        "protein": [item for item in pool if _ingredient_kind(item) == "protein"],
        "carb": [item for item in pool if _ingredient_kind(item) == "carb"],
        "veg": [item for item in pool if _ingredient_kind(item) == "veg"],
        "other": [item for item in pool if _ingredient_kind(item) == "other"],
    }
    selected: list[Ingredient] = []
    used_ids: set[int] = set()
    for index, kind in enumerate(["protein", "carb", "veg", "other"]):
        bucket = buckets[kind]
        if not bucket:
            continue
        item = bucket[(seed + recipe_round + index) % len(bucket)]
        if item.id not in used_ids:
            selected.append(item)
            used_ids.add(item.id)
        if len(selected) >= 3:
            break

    for item in _rotate_items(pool, seed + recipe_round * 3):
        if len(selected) >= 3:
            break
        if item.id not in used_ids:
            selected.append(item)
            used_ids.add(item.id)

    return selected


class LocalRecipeProvider:
    def generate(
        self,
        db,
        ingredient_names: list[str],
        target_calories: int,
        preference: str | None,
        recipe_round: int = 0,
    ):
        all_ingredients, db_lookup = _load_ingredient_index(db)
        selected = _match_requested_ingredients(db_lookup, ingredient_names)
        if len(selected) < 2:
            selected = _match_selected_ingredients(db_lookup, ingredient_names, all_ingredients)
        if len(selected) < 2:
            raise HTTPException(
                status_code=400,
                detail=_clean_missing_category_text(selected) or "食材不足，建议补充蛋白质、碳水、蔬菜类食材。",
            )

        preferences = _split_preferences(preference)
        signature = "|".join(
            [
                ",".join(item.name for item in selected),
                str(target_calories),
                ",".join(sorted(preferences)),
            ]
        )
        seed = int(hashlib.sha1(signature.encode("utf-8")).hexdigest(), 16)
        round_index = max(0, int(recipe_round or 0))
        page_items = _clean_choose_page_items(selected, seed, round_index)
        warning = _clean_missing_category_text(page_items)

        styles = _rotate_items(NEW_RECIPE_STYLES, seed + round_index)
        filtered_styles = [style for style in styles if _clean_style_matches(style, preferences, page_items)]
        styles = filtered_styles or styles
        recipe_count = min(6, max(4, len(styles)))

        payloads = []
        for style_info in styles[:recipe_count]:
            spec = _clean_build_recipe_spec(
                items=page_items,
                target_calories=target_calories,
                preferences=preferences,
                style_info=style_info,
                warning=warning,
            )
            transient_id = hashlib.sha256(
                f"{signature}|{round_index}|{style_info['style']}".encode("utf-8")
            ).hexdigest()[:24]
            payloads.append({
                "id": f"generated-{transient_id}",
                "name": spec["name"],
                "description": spec["description"],
                "minutes": spec["minutes"],
                "tags": spec["tags"].split(",") if spec["tags"] else [],
                "cover_url": spec["cover_url"],
                "is_system": False,
                "ingredients": [
                    {
                        "id": item["ingredient"].id,
                        "name": item["ingredient"].name,
                        "amount_g": item["amount_g"],
                        "note": item["note"],
                    }
                    for item in spec["ingredients"]
                ],
                "steps": spec["steps"],
                "nutrition": spec["nutrition"],
            })
        return payloads
