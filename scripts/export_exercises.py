"""Export the curated catalog for offline browsing; run from the repository root."""
import json
from pathlib import Path
from backend.database.catalog import EXERCISES

PARTS = {"胸部": "chest", "背部": "back", "肩部": "shoulder", "手臂": "arm", "臀腿": "leg", "核心": "core"}
rows = []
for name, part, primary, secondary, equipment, difficulty, image, steps, caution, met in EXERCISES:
    slug = Path(image).stem
    rows.append(dict(id=slug, slug=slug, name=name, title=name, body_part=part,
                     part=PARTS[part], primary_muscle=primary, muscle=primary,
                     secondary_muscle=secondary, equipment=equipment,
                     difficulty=difficulty, level=difficulty, steps=steps,
                     cautions=caution, met=met,
                     imageSrc=(f"/assets/exercises/{slug}.jpg" if Path(f"frontend/assets/exercises/{slug}.jpg").exists() else "")))
Path("frontend/utils/exercise-catalog.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
