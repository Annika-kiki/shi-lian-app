"""Cheap release gates for WXML handlers and privacy-sensitive startup behavior."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
HANDLER = re.compile(r"\b(?:bind|catch)(?::|[a-zA-Z]+)=\"([A-Za-z_$][\w$]*)\"")
METHOD = re.compile(r"^[ \t]+(?:async[ \t]+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", re.MULTILINE)
ICON_BUTTON = re.compile(
    r'<view\s+class="[^"]*\bicon-btn\b[^"]*"([^>]*)>([^<]*)</view>', re.DOTALL
)


def main() -> int:
    failures = []
    for template in FRONTEND.rglob("*.wxml"):
        script = template.with_suffix(".js")
        if not script.exists():
            continue
        handlers = set(HANDLER.findall(template.read_text(encoding="utf-8-sig")))
        methods = set(METHOD.findall(script.read_text(encoding="utf-8-sig")))
        for missing in sorted(handlers - methods):
            failures.append(f"{template.relative_to(ROOT)}: missing handler {missing}")
        for attributes, label in ICON_BUTTON.findall(template.read_text(encoding="utf-8-sig")):
            if label.strip() and "bind" not in attributes and "catch" not in attributes:
                failures.append(
                    f"{template.relative_to(ROOT)}: visible icon button {label.strip()} has no action"
                )

    app_source = (FRONTEND / "app.js").read_text(encoding="utf-8-sig")
    if "ensureLogin" in app_source or "wx.login" in app_source:
        failures.append("frontend/app.js: login must not run before explicit privacy consent")

    login_template = (FRONTEND / "pages/index/index.wxml").read_text(encoding="utf-8-sig")
    if "我确认已满14周岁" not in login_template:
        failures.append("frontend/pages/index/index.wxml: missing explicit 14+ self-attestation")

    forbidden_demo_values = {
        "frontend/pages/me/me.js": ("6 次", "16 天"),
        "frontend/pages/calendar/calendar.wxml": ("2026 年 8 月",),
    }
    for relative, values in forbidden_demo_values.items():
        content = (ROOT / relative).read_text(encoding="utf-8-sig")
        for value in values:
            if value in content:
                failures.append(f"{relative}: release UI contains fixed demo value {value}")

    if failures:
        print("Frontend contract checks failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Frontend binding and privacy contract checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
