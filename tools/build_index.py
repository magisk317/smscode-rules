#!/usr/bin/env python3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "rules"
META_DIR = ROOT / "_meta"
OUTPUT = META_DIR / "rules-index.json"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_index() -> dict:
    files = []
    for path in sorted(RULES_DIR.glob("*.json")):
        text = path.read_text()
        data = json.loads(text)
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "id": data["id"],
                "name": data["name"],
                "locale": data["locale"],
                "updatedAt": data["updatedAt"],
                "ruleCount": len(data["rules"]),
                "sha256": sha256_text(text),
                "size": len(text.encode("utf-8")),
            }
        )

    return {
        "sourceRepo": "magisk317/smscode-rules",
        "branch": "main",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }


def main() -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    index = build_index()
    OUTPUT.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(index['files'])} file(s).")


if __name__ == "__main__":
    main()

