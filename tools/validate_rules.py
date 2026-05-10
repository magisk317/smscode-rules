#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "rules"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_rule_file(path: Path) -> tuple[int, int]:
    data = json.loads(path.read_text())

    required_top = ["specVersion", "id", "name", "locale", "updatedAt", "rules"]
    for key in required_top:
        if key not in data:
            fail(f"{path}: missing top-level key '{key}'")

    if data["specVersion"] != 1:
        fail(f"{path}: unsupported specVersion={data['specVersion']}")

    if not isinstance(data["rules"], list) or not data["rules"]:
        fail(f"{path}: rules must be a non-empty list")

    example_count = 0
    seen_rule_ids = set()
    for index, rule in enumerate(data["rules"], start=1):
        rule_id = rule.get("id")
        if not rule_id:
            fail(f"{path}: rule #{index} missing id")
        if rule_id in seen_rule_ids:
            fail(f"{path}: duplicate rule id '{rule_id}'")
        seen_rule_ids.add(rule_id)

        keyword = rule.get("codeKeyword", "")
        code_regex = rule.get("codeRegex", "")
        company = rule.get("company")

        if not keyword:
            fail(f"{path}: rule '{rule_id}' missing codeKeyword")
        if not code_regex:
            fail(f"{path}: rule '{rule_id}' missing codeRegex")

        try:
            pattern = re.compile(code_regex)
        except re.error as exc:
            fail(f"{path}: rule '{rule_id}' invalid codeRegex: {exc}")

        sender_regex = rule.get("senderRegex")
        if sender_regex:
            try:
                re.compile(sender_regex)
            except re.error as exc:
                fail(f"{path}: rule '{rule_id}' invalid senderRegex: {exc}")

        examples = rule.get("examples")
        if not isinstance(examples, list) or not examples:
            fail(f"{path}: rule '{rule_id}' must provide at least one example")

        for example in examples:
            body = example.get("body", "")
            expected_code = example.get("expectedCode", "")
            if not body or not expected_code:
                fail(f"{path}: rule '{rule_id}' example missing body or expectedCode")
            if company and company not in body:
                fail(f"{path}: rule '{rule_id}' example body does not contain company '{company}'")
            if keyword not in body:
                fail(f"{path}: rule '{rule_id}' example body does not contain keyword '{keyword}'")
            matches = [m.group(0) for m in pattern.finditer(body)]
            if expected_code not in matches:
                fail(
                    f"{path}: rule '{rule_id}' example expectedCode '{expected_code}' "
                    f"not matched by codeRegex"
                )
            example_count += 1

    return len(data["rules"]), example_count


def main() -> None:
    files = sorted(RULES_DIR.glob("*.json"))
    if not files:
        fail(f"no rule files found under {RULES_DIR}")

    total_rules = 0
    total_examples = 0
    for path in files:
        rule_count, example_count = validate_rule_file(path)
        total_rules += rule_count
        total_examples += example_count
        print(f"PASS: {path.relative_to(ROOT)} rules={rule_count} examples={example_count}")

    print(f"Validated {len(files)} file(s), {total_rules} rule(s), {total_examples} example(s).")


if __name__ == "__main__":
    main()

