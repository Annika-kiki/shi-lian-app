"""Conservative package-size gate matching frontend/project.config.json ignores."""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
MAX_MAIN_PACKAGE_BYTES = 2 * 1024 * 1024
PROJECT_CONFIG = json.loads((FRONTEND / "project.config.json").read_text(encoding="utf-8"))
IGNORE_RULES = PROJECT_CONFIG.get("packOptions", {}).get("ignore", [])


def included(path: Path) -> bool:
    relative = path.relative_to(FRONTEND)
    relative_posix = relative.as_posix()
    for rule in IGNORE_RULES:
        rule_type = rule.get("type")
        value = str(rule.get("value", "")).strip("/")
        if rule_type == "suffix" and relative_posix.endswith(value):
            return False
        if rule_type == "folder" and (
            relative_posix == value or relative_posix.startswith(value + "/")
        ):
            return False
    return True


files = [path for path in FRONTEND.rglob("*") if path.is_file() and included(path)]
total = sum(path.stat().st_size for path in files)
print(f"Estimated main package: {total / 1024:.1f} KiB across {len(files)} files")

if total > MAX_MAIN_PACKAGE_BYTES:
    raise SystemExit("Estimated main package exceeds the conservative 2 MiB gate")
