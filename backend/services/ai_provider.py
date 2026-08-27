"""Local recipe generator with more varied cooking styles."""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

from fastapi import HTTPException

from backend.models.entities import Ingredient, Recipe, RecipeIngredient, RecipeStep
from backend.services.nutrition import nutrition_for_ingredients, recipe_payload


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


def _rotate_items(items: list[Ingredient], offset: int) -> list[Ingredient]:
    if not items:
        return []
    offset = offset % len(items)
    if not offset:
        return items[:]
    return items[offset:] + items[:offset]


def _pick_first(items: Iterable[Ingredient], exclude_ids: set[int] | None = None) -> Ingredient | None:
    exclude_ids = exclude_ids or set()
    return next((item for item in items if item.id not in exclude_ids), None)


def _pick_category(
    items: Iterable[Ingredient],
    category: set[str],
    exclude_ids: set[int] | None = None,
) -> Ingredient | None:
    exclude_ids = exclude_ids or set()
    return next((item for item in items if item.name in category and item.id not in exclude_ids), None)


def _pick_priority(
    items: Iterable[Ingredient],
    priorities: Iterable[str],
    exclude_ids: set[int] | None = None,
) -> Ingredient | None:
    exclude_ids = exclude_ids or set()
    for name in priorities:
        candidate = next(
            (item for item in items if item.name == name and item.id not in exclude_ids),
            None,
        )
        if candidate:
            return candidate
    return None


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
                    if key in cleaned or cleaned in key
                ),
                None,
            )
        if candidate and candidate not in selected:
            selected.append(candidate)

    if not selected:
        for name in ("鸡胸肉", "西兰花", "米饭"):
            candidate = db_lookup.get(name)
            if candidate and candidate not in selected:
                selected.append(candidate)

    if not selected and all_ingredients:
        selected = all_ingredients[:3]

    return _unique_by_id(selected)


def _group_ingredients(items: list[Ingredient]) -> tuple[Ingredient | None, Ingredient | None, Ingredient | None]:
    protein = next((item for item in items if item.name in PROTEIN_NAMES), None)
    carb = next((item for item in items if item.name in CARB_NAMES), None)
    veg = next((item for item in items if item.name in VEG_NAMES), None)
    return protein, carb, veg


def _merge_portions(portions: list[tuple[Ingredient, float]]) -> list[tuple[Ingredient, float]]:
    merged: dict[int, tuple[Ingredient, float]] = {}
    for ingredient, grams in portions:
        if ingredient.id in merged:
            current, total = merged[ingredient.id]
            merged[ingredient.id] = (current, total + grams)
        else:
            merged[ingredient.id] = (ingredient, grams)
    return [(ingredient, round(grams, 1)) for ingredient, grams in merged.values()]


def _build_portions(
    db_lookup: dict[str, Ingredient],
    protein: Ingredient,
    carb: Ingredient | None,
    veg_primary: Ingredient | None,
    veg_secondary: Ingredient | None,
    target_calories: int,
    low_oil: bool,
    style: str,
) -> list[tuple[Ingredient, float]]:
    if style == "steam":
        portions: list[tuple[Ingredient, float]] = [(protein, 160)]
        if carb:
            portions.append((carb, 80))
        if veg_primary:
            portions.append((veg_primary, 200))
        if veg_secondary:
            portions.append((veg_secondary, 80))
    elif style == "soup":
        portions = [(protein, 130)]
        if carb:
            portions.append((carb, 90))
        if veg_primary:
            portions.append((veg_primary, 180))
        if veg_secondary:
            portions.append((veg_secondary, 100))
    elif style == "bowl":
        portions = [(protein, 140)]
        if carb:
            portions.append((carb, 120))
        if veg_primary:
            portions.append((veg_primary, 150))
        if veg_secondary:
            portions.append((veg_secondary, 80))
    elif style == "stir_fry":
        portions = [(protein, 150)]
        if carb:
            portions.append((carb, 100))
        if veg_primary:
            portions.append((veg_primary, 170))
        if veg_secondary:
            portions.append((veg_secondary, 60))
    elif style == "roast":
        portions = [(protein, 150)]
        if carb:
            portions.append((carb, 90))
        if veg_primary:
            portions.append((veg_primary, 200))
        if veg_secondary:
            portions.append((veg_secondary, 80))
    elif style == "braise":
        portions = [(protein, 150)]
        if carb:
            portions.append((carb, 120))
        if veg_primary:
            portions.append((veg_primary, 160))
        if veg_secondary:
            portions.append((veg_secondary, 90))
    else:  # salad
        portions = [(protein, 120)]
        if carb:
            portions.append((carb, 70))
        if veg_primary:
            portions.append((veg_primary, 160))
        if veg_secondary:
            portions.append((veg_secondary, 120))

    if not low_oil:
        oil = db_lookup.get("橄榄油") or db_lookup.get("芝麻油") or db_lookup.get("花生油") or db_lookup.get("菜籽油")
        if oil:
            oil_amount = 0 if style == "salad" else 2 if style in {"steam", "soup"} else 3 if style == "roast" else 5
            if oil_amount:
                portions.append((oil, oil_amount))

    portions = _merge_portions(portions)
    current = nutrition_for_ingredients(portions)["calories_kcal"]
    diff = target_calories - current

    if abs(diff) > 25:
        adjustable = next((index for index, (item, _) in enumerate(portions) if item.name in CARB_NAMES), None)
        if adjustable is None:
            adjustable = next((index for index, (item, _) in enumerate(portions) if item.name in PROTEIN_NAMES), None)

        if adjustable is not None:
            item, grams = portions[adjustable]
            kcal_per_100 = max(item.calories_kcal, 1)
            grams_delta = diff / kcal_per_100 * 100
            if item.name in PROTEIN_NAMES:
                grams_delta *= 0.65
            new_grams = max(60, min(280, grams + grams_delta))
            portions[adjustable] = (item, round(new_grams))

    return portions


def _style_order(preferences: set[str], seed: int) -> list[str]:
    if {"少油", "低脂", "清爽"} & preferences:
        base = ["steam", "salad", "soup", "bowl", "braise", "roast", "stir_fry"]
    elif {"15分钟内", "快手"} & preferences:
        base = ["salad", "steam", "bowl", "soup", "stir_fry", "roast", "braise"]
    elif "高蛋白" in preferences:
        base = ["steam", "bowl", "stir_fry", "roast", "braise", "soup", "salad"]
    else:
        base = STYLE_ORDER[:]

    offset = seed % len(base)
    return base[offset:] + base[:offset]


def _title_for_style(style: str, protein: Ingredient, carb: Ingredient | None, veg_primary: Ingredient | None) -> str:
    veg_name = veg_primary.name if veg_primary else None
    carb_name = carb.name if carb else None

    if style == "steam":
        return f"{protein.name}{veg_name or '蔬菜'}清蒸"
    if style == "soup":
        return f"{protein.name}{veg_name or '蔬菜'}汤"
    if style == "bowl":
        return f"{protein.name}{carb_name or veg_name or '能量'}碗"
    if style == "stir_fry":
        return f"{protein.name}{veg_name or '时蔬'}快炒"
    if style == "roast":
        return f"{protein.name}{veg_name or '蔬菜'}烤盘"
    if style == "braise":
        return f"{protein.name}{carb_name or veg_name or '焖锅'}焖锅"
    return f"{protein.name}{veg_name or '时蔬'}拌碗"


def _build_steps(
    style: str,
    protein: Ingredient,
    carb: Ingredient | None,
    veg_primary: Ingredient | None,
    veg_secondary: Ingredient | None,
) -> list[str]:
    protein_name = protein.name
    carb_name = carb.name if carb else None
    veg_name = veg_primary.name if veg_primary else None
    veg2_name = veg_secondary.name if veg_secondary else None

    if style == "steam":
        return [
            f"把{protein_name}和{veg_name or '蔬菜'}分层摆好，简单调味。",
            "上锅蒸至熟透，保留汁水和原味。",
            "出锅后淋少量酱汁，清爽上桌。",
        ]
    if style == "soup":
        return [
            f"把{protein_name}切块，{veg_name or '蔬菜'}洗净备用。",
            f"先煮{protein_name}，再加入{veg_name or '蔬菜'}慢慢熬出鲜味。",
            f"如果有{carb_name or '主食'}，最后一起放入，调味后出锅。",
        ]
    if style == "bowl":
        return [
            f"先把{carb_name or '主食'}煮熟或蒸熟，{protein_name}煎熟后切块。",
            f"把{veg_name or '蔬菜'}和{veg2_name or '配菜'}焯水或直接切配。",
            "按顺序装入碗中，淋少量酱汁拌匀即可。",
        ]
    if style == "stir_fry":
        return [
            f"把{protein_name}切片，{veg_name or '蔬菜'}洗净切好。",
            f"热锅少油，先炒{protein_name}，再加入{veg_name or '蔬菜'}快炒。",
            f"最后放入{veg2_name or carb_name or '配菜'}翻匀，迅速出锅。",
        ]
    if style == "roast":
        return [
            f"把{protein_name}和{veg_name or '蔬菜'}铺在烤盘里，表面刷薄薄一层油。",
            "撒盐和黑胡椒，送入烤箱烤到表面微焦。",
            f"搭配{carb_name or veg2_name or '配菜'}一起装盘，口感更完整。",
        ]
    if style == "braise":
        return [
            f"热锅先把{protein_name}煎香，再加入{veg_name or '蔬菜'}。",
            f"放入{carb_name or '主食'}和少量热水，小火焖煮。",
            "收汁后出锅，味道更浓郁。",
        ]
    return [
        f"把{protein_name}煎熟或蒸熟后切块。",
        f"把{veg_name or '蔬菜'}和{veg2_name or '配菜'}处理好，和{carb_name or '主食'}一起装碗。",
        "淋少量清爽酱汁，拌匀即可。",
    ]


def _build_recipe_spec(
    db_lookup: dict[str, Ingredient],
    protein: Ingredient,
    carb: Ingredient | None,
    veg_primary: Ingredient | None,
    veg_secondary: Ingredient | None,
    display_names: list[str],
    target_calories: int,
    preferences: set[str],
    style: str,
) -> dict:
    low_oil = {"少油", "低脂"} & preferences
    portions = _build_portions(
        db_lookup=db_lookup,
        protein=protein,
        carb=carb,
        veg_primary=veg_primary,
        veg_secondary=veg_secondary,
        target_calories=target_calories,
        low_oil=bool(low_oil),
        style=style,
    )
    nutrition = nutrition_for_ingredients(portions)
    labels = [label.strip() for label in display_names if label and label.strip()]
    while len(labels) < 4:
        labels.append(labels[-1] if labels else protein.name)

    title = _title_for_style(style, protein, carb, veg_primary)
    steps = _build_steps(style, protein, carb, veg_primary, veg_secondary)
    ingredients = _build_portion_specs(portions)

    for item in ingredients:
        ingredient = item["ingredient"]
        item["note"] = (
            "主蛋白"
            if ingredient.id == protein.id
            else "主食来源"
            if carb and ingredient.id == carb.id
            else "蔬菜"
            if ingredient.name in VEG_NAMES
            else "少量用油"
            if ingredient.name in OIL_NAMES
            else "配菜"
        )

    tag_list = []
    if protein.name in PROTEIN_NAMES:
        tag_list.append("高蛋白")
    if style in {"steam", "salad", "soup"} or low_oil:
        tag_list.append("少油")
    if style in {"stir_fry", "bowl", "salad"}:
        tag_list.append("快手")
    tag_list.extend(STYLE_TAGS.get(style, []))
    if carb:
        tag_list.append("均衡")

    return {
        "name": title,
        "description": f"根据现有食材生成的{title}，适合直接做成一餐。",
        "minutes": STYLE_MINUTES.get(style, 18),
        "tags": ",".join(dict.fromkeys(tag_list)),
        "cover_url": None,
        "is_system": False,
        "ingredients": ingredients,
        "steps": steps,
        "nutrition": nutrition,
    }


def _build_portion_specs(portions: list[tuple[Ingredient, float]]) -> list[dict]:
    merged: dict[int, dict] = {}
    for ingredient, amount_g in portions:
        item = merged.get(ingredient.id)
        if item:
            item["amount_g"] = round(item["amount_g"] + amount_g, 1)
            continue
        merged[ingredient.id] = {
            "ingredient": ingredient,
            "amount_g": round(amount_g, 1),
            "note": None,
        }
    return list(merged.values())


def _resolve_recipe_components(
    selected: list[Ingredient],
    all_ingredients: list[Ingredient],
    db_lookup: dict[str, Ingredient],
    lead_exclude_ids: set[int] | None = None,
) -> tuple[Ingredient | None, Ingredient | None, Ingredient | None, Ingredient | None, list[Ingredient]]:
    lead_exclude_ids = lead_exclude_ids or set()
    if selected:
        used_ids: set[int] = set()
        lead = (
            _pick_category(selected, PROTEIN_NAMES, lead_exclude_ids)
            or _pick_category(selected, CARB_NAMES, lead_exclude_ids)
            or _pick_category(selected, VEG_NAMES, lead_exclude_ids)
            or _pick_first(selected, lead_exclude_ids)
            or _pick_category(selected, PROTEIN_NAMES)
            or _pick_category(selected, CARB_NAMES)
            or _pick_category(selected, VEG_NAMES)
            or _pick_first(selected)
        )
        if lead:
            used_ids.add(lead.id)

        carb = _pick_category(selected, CARB_NAMES, used_ids)
        if carb:
            used_ids.add(carb.id)

        veg_primary = _pick_category(selected, VEG_NAMES, used_ids)
        if veg_primary:
            used_ids.add(veg_primary.id)

        veg_secondary = _pick_first(selected, used_ids)
        return lead, carb, veg_primary, veg_secondary, selected

    protein = (
        db_lookup.get('???')
        or _pick_category(all_ingredients, PROTEIN_NAMES)
        or _pick_first(all_ingredients)
    )
    used_ids = {protein.id} if protein else set()
    carb = db_lookup.get('??') or _pick_category(all_ingredients, CARB_NAMES, used_ids)
    if carb:
        used_ids.add(carb.id)
    veg_primary = db_lookup.get('???') or _pick_category(all_ingredients, VEG_NAMES, used_ids)
    if veg_primary:
        used_ids.add(veg_primary.id)
    veg_secondary = _pick_priority(all_ingredients, STYLE_EXTRA_PRIORITY.get('salad', []), used_ids)
    return protein, carb, veg_primary, veg_secondary, all_ingredients


class LocalRecipeProvider:
    def generate(self, db, ingredient_names: list[str], target_calories: int, preference: str | None):
        all_ingredients, db_lookup = _load_ingredient_index(db)
        preferences = _split_preferences(preference)
        selected = _match_selected_ingredients(db_lookup, ingredient_names, all_ingredients)
        display_names = [str(name).strip() for name in ingredient_names if str(name).strip()]
        if not display_names:
            display_names = [item.name for item in selected]

        recipe_pool = _unique_by_id(selected or all_ingredients)
        if not recipe_pool:
            raise ValueError('No ingredients available to generate recipes.')

        signature = '|'.join(
            [
                ','.join(item.name for item in recipe_pool[:6]),
                ','.join(sorted(display_names)),
                str(target_calories),
                ','.join(sorted(preferences)),
            ]
        )
        seed = int(hashlib.sha1(signature.encode('utf-8')).hexdigest(), 16)
        generated_count = db.query(Recipe).filter_by(is_system=False).count()
        generated_batch = generated_count // 3
        style_order = _style_order(preferences, seed + generated_batch)
        rotation_offset = (seed + generated_batch) % len(recipe_pool)

        payloads = []
        used_ids: set[int] = set()
        used_lead_ids: set[int] = set()
        for index, style in enumerate(style_order[:3]):
            rotated_selected = _rotate_items(recipe_pool, rotation_offset + index)
            protein, carb, veg_primary, veg_secondary, recipe_pool = _resolve_recipe_components(
                selected=rotated_selected,
                all_ingredients=all_ingredients,
                db_lookup=db_lookup,
                lead_exclude_ids=used_lead_ids,
            )
            if protein is None:
                raise ValueError('No ingredients available to generate recipes.')
            used_lead_ids.add(protein.id)

            style_extra = STYLE_EXTRA_PRIORITY.get(style, [])
            extra = _pick_priority(recipe_pool, style_extra, used_ids | {protein.id})
            if extra and extra.id not in used_ids:
                veg_secondary = extra if extra.name in VEG_NAMES else veg_secondary
                used_ids.add(extra.id)

            used_ids.update(
                {
                    protein.id,
                    carb.id if carb else -1,
                    veg_primary.id if veg_primary else -1,
                }
            )
            used_ids.discard(-1)

            spec = _build_recipe_spec(
                db_lookup=db_lookup,
                protein=protein,
                carb=carb,
                veg_primary=veg_primary,
                veg_secondary=veg_secondary,
                display_names=display_names,
                target_calories=target_calories,
                preferences=preferences,
                style=style,
            )

            recipe = Recipe(
                name=spec['name'],
                description=spec['description'],
                minutes=spec['minutes'],
                tags=spec['tags'],
                cover_url=spec['cover_url'],
                is_system=False,
            )
            db.add(recipe)
            db.flush()

            for ingredient_spec in spec['ingredients']:
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient_spec['ingredient'].id,
                        amount_g=ingredient_spec['amount_g'],
                        note=ingredient_spec['note'],
                    )
                )

            for step_no, content in enumerate(spec['steps'], start=1):
                db.add(RecipeStep(recipe_id=recipe.id, order_no=step_no, content=content))

            db.flush()
            payloads.append(recipe_payload(db, recipe))

        db.commit()
        return payloads


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
            recipe = Recipe(
                name=spec["name"],
                description=spec["description"],
                minutes=spec["minutes"],
                tags=spec["tags"],
                cover_url=spec["cover_url"],
                is_system=False,
            )
            db.add(recipe)
            db.flush()

            for ingredient_spec in spec["ingredients"]:
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient_spec["ingredient"].id,
                        amount_g=ingredient_spec["amount_g"],
                        note=ingredient_spec["note"],
                    )
                )

            for step_no, content in enumerate(spec["steps"], start=1):
                db.add(RecipeStep(recipe_id=recipe.id, order_no=step_no, content=content))

            db.flush()
            payloads.append(recipe_payload(db, recipe))

        db.commit()
        return payloads


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
            recipe = Recipe(
                name=spec["name"],
                description=spec["description"],
                minutes=spec["minutes"],
                tags=spec["tags"],
                cover_url=spec["cover_url"],
                is_system=False,
            )
            db.add(recipe)
            db.flush()

            for ingredient_spec in spec["ingredients"]:
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient_spec["ingredient"].id,
                        amount_g=ingredient_spec["amount_g"],
                        note=ingredient_spec["note"],
                    )
                )

            for step_no, content in enumerate(spec["steps"], start=1):
                db.add(RecipeStep(recipe_id=recipe.id, order_no=step_no, content=content))

            db.flush()
            payloads.append(recipe_payload(db, recipe))

        db.commit()
        return payloads


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
            recipe = Recipe(
                name=spec["name"],
                description=spec["description"],
                minutes=spec["minutes"],
                tags=spec["tags"],
                cover_url=spec["cover_url"],
                is_system=False,
            )
            db.add(recipe)
            db.flush()

            for ingredient_spec in spec["ingredients"]:
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient_spec["ingredient"].id,
                        amount_g=ingredient_spec["amount_g"],
                        note=ingredient_spec["note"],
                    )
                )

            for step_no, content in enumerate(spec["steps"], start=1):
                db.add(RecipeStep(recipe_id=recipe.id, order_no=step_no, content=content))

            db.flush()
            payloads.append(recipe_payload(db, recipe))

        db.commit()
        return payloads


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
            recipe = Recipe(
                name=spec["name"],
                description=spec["description"],
                minutes=spec["minutes"],
                tags=spec["tags"],
                cover_url=spec["cover_url"],
                is_system=False,
            )
            db.add(recipe)
            db.flush()

            for ingredient_spec in spec["ingredients"]:
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient_spec["ingredient"].id,
                        amount_g=ingredient_spec["amount_g"],
                        note=ingredient_spec["note"],
                    )
                )

            for step_no, content in enumerate(spec["steps"], start=1):
                db.add(RecipeStep(recipe_id=recipe.id, order_no=step_no, content=content))

            db.flush()
            payloads.append(recipe_payload(db, recipe))

        db.commit()
        return payloads


ALLOWED_SEASONINGS = "盐、味精、蚝油、油、黑胡椒、生抽、醋、蒜末、辣椒粉"

STYLE_LIBRARY = [
    {
        "style": "steam",
        "suffix": "???",
        "minutes": 15,
        "tags": ["??", "??", "??"],
    },
    {
        "style": "soup",
        "suffix": "??",
        "minutes": 15,
        "tags": ["??", "???", "??"],
    },
    {
        "style": "bowl",
        "suffix": "??",
        "minutes": 12,
        "tags": ["??", "??", "??"],
    },
    {
        "style": "pan",
        "suffix": "????",
        "minutes": 15,
        "tags": ["??", "??", "??"],
    },
    {
        "style": "braise",
        "suffix": "??",
        "minutes": 25,
        "tags": ["??", "??"],
    },
    {
        "style": "stir",
        "suffix": "??",
        "minutes": 15,
        "tags": ["??", "??"],
    },
    {
        "style": "cold",
        "suffix": "???",
        "minutes": 10,
        "tags": ["??", "???", "??"],
    },
]


def _style_matches_preferences(style_info: dict, preferences: set[str]) -> bool:
    tags = set(style_info.get("tags", []))
    if {"??", "??"} & preferences and "??" not in tags:
        return False
    if {"15???", "??"} & preferences and style_info["minutes"] > 15:
        return False
    if "??" in preferences and "??" not in tags:
        return False
    return True


def _match_requested_ingredients(
    db_lookup: dict[str, Ingredient],
    raw_names: Iterable[str],
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


def _missing_category_text(items: list[Ingredient]) -> str:
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


def _ingredient_kind(item: Ingredient) -> str:
    if item.name in PROTEIN_NAMES:
        return "protein"
    if item.name in CARB_NAMES:
        return "carb"
    if item.name in VEG_NAMES:
        return "veg"
    return "other"


def _pick_kind(items: list[Ingredient], kind: str, used_ids: set[int]) -> Ingredient | None:
    return next((item for item in items if _ingredient_kind(item) == kind and item.id not in used_ids), None)


def _choose_page_items(pool: list[Ingredient], seed: int, recipe_round: int) -> list[Ingredient]:
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
    for salt, kind in enumerate(["protein", "carb", "veg", "other"]):
        bucket = buckets[kind]
        if not bucket:
            continue
        item = bucket[(seed + recipe_round + salt) % len(bucket)]
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


def _portion_for(item: Ingredient, style: str, target_calories: int, index: int) -> float:
    kind = _ingredient_kind(item)
    if kind == "protein":
        base = 130 if style in {"soup", "cold"} else 150
    elif kind == "carb":
        if item.name in {"燕麦"}:
            base = 45
        elif item.name in {"全麦面包"}:
            base = 60
        else:
            base = 110 if target_calories <= 450 else 150
    elif kind == "veg":
        base = 160 if style in {"bowl", "cold"} else 190
    else:
        base = 100
    return float(max(40, min(260, base + (index - 1) * 10)))


def _build_strict_portions(items: list[Ingredient], style: str, target_calories: int) -> list[tuple[Ingredient, float]]:
    portions = [(item, _portion_for(item, style, target_calories, index)) for index, item in enumerate(items)]
    nutrition = nutrition_for_ingredients(portions)
    calories = nutrition["calories_kcal"]
    target = max(300, min(600, target_calories))
    adjustable_index = next(
        (
            index
            for index, (item, _) in enumerate(portions)
            if _ingredient_kind(item) in {"carb", "protein"}
        ),
        0,
    )
    item, grams = portions[adjustable_index]
    kcal_per_100 = max(item.calories_kcal, 1)
    delta = (target - calories) / kcal_per_100 * 100
    if _ingredient_kind(item) == "protein":
        delta *= 0.7
    portions[adjustable_index] = (item, round(max(50, min(260, grams + delta))))
    return _merge_portions(portions)


def _steps_for_style(style: str, names: list[str]) -> list[str]:
    main = names[0]
    second = names[1] if len(names) > 1 else names[0]
    third = names[2] if len(names) > 2 else second
    seasoning = f"只用基础调料：{ALLOWED_SEASONINGS}。"
    if style == "steam":
        return [
            f"把{main}、{second}和{third}处理成容易熟的大小。",
            "上锅蒸到熟透，出锅后用盐、生抽或黑胡椒简单调味。",
            seasoning,
        ]
    if style == "soup":
        return [
            f"先把{main}和{second}加水煮出鲜味。",
            f"再放入{third}小火煮熟，最后用盐、生抽或蒜末调味。",
            seasoning,
        ]
    if style == "bowl":
        return [
            f"把{main}做熟，{second}和{third}焯水或煮熟。",
            "全部装入碗中，用生抽、醋、黑胡椒拌匀。",
            seasoning,
        ]
    if style == "pan":
        return [
            f"{main}用黑胡椒和盐轻轻抓匀。",
            f"平底锅少油煎熟{main}，旁边放入{second}和{third}煎到变软。",
            seasoning,
        ]
    if style == "braise":
        return [
            f"锅里少油，先让{main}表面定型。",
            f"加入{second}、{third}和少量水，盖盖焖到软熟。",
            seasoning,
        ]
    if style == "cold":
        return [
            f"把{main}和{second}做熟后放凉，{third}处理干净。",
            "用醋、生抽、蒜末和少量辣椒粉拌匀。",
            seasoning,
        ]
    return [
        f"热锅少油，先放{main}快速翻炒。",
        f"再加入{second}和{third}，用盐、生抽或蚝油调味后出锅。",
        seasoning,
    ]


def _nutrition_note(nutrition: dict) -> str:
    protein = nutrition.get("protein_g", 0)
    carb = nutrition.get("carb_g", 0)
    fat = nutrition.get("fat_g", 0)
    protein_text = "蛋白质充足" if protein >= 25 else "蛋白质偏少"
    carb_text = "碳水适中" if 25 <= carb <= 70 else "碳水较低" if carb < 25 else "碳水偏高"
    fat_text = "脂肪较低" if fat <= 18 else "脂肪适中"
    return f"{protein_text}，{carb_text}，{fat_text}。"


def _build_strict_recipe_spec(
    items: list[Ingredient],
    target_calories: int,
    preferences: set[str],
    style_info: dict,
    warning: str,
) -> dict:
    portions = _build_strict_portions(items, style_info["style"], target_calories)
    nutrition = nutrition_for_ingredients(portions)
    names = [item.name for item, _ in portions]
    title = f"{''.join(names[:2])}{style_info['suffix']}"
    ingredients = _build_portion_specs(portions)
    for ingredient_spec in ingredients:
        kind = _ingredient_kind(ingredient_spec["ingredient"])
        ingredient_spec["note"] = {
            "protein": "???",
            "carb": "????",
            "veg": "??",
        }.get(kind, "????")

    tags = []
    if "???" in preferences and any(_ingredient_kind(item) == "protein" for item, _ in portions):
        tags.append("???")
    if ("??" in preferences or "??" in preferences) and "??" in style_info["tags"]:
        tags.append("??")
    if "15???" in preferences and style_info["minutes"] <= 15:
        tags.append("15???")
    if "??" in preferences and style_info["minutes"] <= 15:
        tags.append("??")
    tags.extend(style_info["tags"])
    if warning:
        tags.append("????")

    description = f"{warning}{_nutrition_note(nutrition)}"
    return {
        "name": title,
        "description": description,
        "minutes": style_info["minutes"],
        "tags": ",".join(dict.fromkeys(tags)),
        "cover_url": None,
        "is_system": False,
        "ingredients": ingredients,
        "steps": _steps_for_style(style_info["style"], names),
        "nutrition": nutrition,
    }


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
            recipe = Recipe(
                name=spec["name"],
                description=spec["description"],
                minutes=spec["minutes"],
                tags=spec["tags"],
                cover_url=spec["cover_url"],
                is_system=False,
            )
            db.add(recipe)
            db.flush()

            for ingredient_spec in spec["ingredients"]:
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient_spec["ingredient"].id,
                        amount_g=ingredient_spec["amount_g"],
                        note=ingredient_spec["note"],
                    )
                )

            for step_no, content in enumerate(spec["steps"], start=1):
                db.add(RecipeStep(recipe_id=recipe.id, order_no=step_no, content=content))

            db.flush()
            payloads.append(recipe_payload(db, recipe))

        db.commit()
        return payloads
