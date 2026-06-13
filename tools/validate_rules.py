#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover - exercised in unbootstrapped environments
    print(
        "ERROR: missing dependency 'jsonschema'. Run `python3 -m pip install -r requirements.txt`.",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "rules"
SCHEMA_PATH = ROOT / "schemas" / "rule-set.schema.json"


@dataclass(frozen=True)
class RuleFileSummary:
    path: Path
    rule_set_id: str
    rule_count: int
    example_count: int


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def format_json_path(parts: list[object]) -> str:
    if not parts:
        return "$"

    formatted = "$"
    for part in parts:
        if isinstance(part, int):
            formatted += f"[{part}]"
        else:
            formatted += f".{part}"
    return formatted


def collect_schema_errors(path: Path, data: dict, validator: Draft202012Validator) -> list[str]:
    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    return [
        f"{path}: schema validation failed at {format_json_path(list(error.absolute_path))}: {error.message}"
        for error in errors
    ]


def validate_rule_file(path: Path, validator: Draft202012Validator) -> tuple[RuleFileSummary | None, list[str]]:
    data = load_json(path)
    errors = collect_schema_errors(path, data, validator)

    if errors:
        return None, errors

    rule_set_id = data["id"]
    expected_name = f"{rule_set_id}.json"
    if path.name != expected_name:
        errors.append(f"{path}: file name must match rule-set id '{expected_name}'")

    example_count = 0
    seen_rule_ids = set()
    for index, rule in enumerate(data["rules"], start=1):
        rule_id = rule["id"]
        if rule_id in seen_rule_ids:
            errors.append(f"{path}: duplicate rule id '{rule_id}'")
            continue
        seen_rule_ids.add(rule_id)

        keyword = rule["codeKeyword"]
        code_regex = rule["codeRegex"]
        company = rule.get("company")

        try:
            pattern = re.compile(code_regex)
        except re.error as exc:
            errors.append(f"{path}: rule '{rule_id}' invalid codeRegex: {exc}")
            continue

        sender_regex = rule.get("senderRegex")
        if sender_regex:
            try:
                re.compile(sender_regex)
            except re.error as exc:
                errors.append(f"{path}: rule '{rule_id}' invalid senderRegex: {exc}")
                continue

        for example_index, example in enumerate(rule["examples"], start=1):
            body = example["body"]
            expected_code = example["expectedCode"]
            if company and company not in body:
                errors.append(
                    f"{path}: rule '{rule_id}' example #{example_index} body does not contain company '{company}'"
                )
            if keyword not in body:
                errors.append(
                    f"{path}: rule '{rule_id}' example #{example_index} body does not contain keyword '{keyword}'"
                )
            matches = [m.group(0) for m in pattern.finditer(body)]
            if expected_code not in matches:
                errors.append(
                    f"{path}: rule '{rule_id}' example expectedCode '{expected_code}' "
                    f"not matched by codeRegex"
                )
                continue
            example_count += 1

    if errors:
        return None, errors

    return RuleFileSummary(path=path, rule_set_id=rule_set_id, rule_count=len(data["rules"]), example_count=example_count), []


def build_validator() -> Draft202012Validator:
    schema = load_json(SCHEMA_PATH)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate smscode-rules documents.")
    return parser.parse_args()


def main() -> None:
    parse_args()

    files = sorted(RULES_DIR.rglob("*.json"), key=lambda path: path.relative_to(ROOT).as_posix())
    if not files:
        print(f"ERROR: no rule files found under {RULES_DIR}", file=sys.stderr)
        raise SystemExit(1)

    validator = build_validator()
    errors: list[str] = []
    summaries: list[RuleFileSummary] = []
    total_rules = 0
    total_examples = 0
    seen_rule_set_ids: dict[str, Path] = {}

    for path in files:
        summary, file_errors = validate_rule_file(path, validator)
        if file_errors:
            errors.extend(file_errors)
            continue

        assert summary is not None
        previous = seen_rule_set_ids.get(summary.rule_set_id)
        if previous is not None:
            errors.append(
                f"{path}: duplicate rule-set id '{summary.rule_set_id}' already used by {previous.relative_to(ROOT)}"
            )
            continue
        seen_rule_set_ids[summary.rule_set_id] = path

        summaries.append(summary)
        total_rules += summary.rule_count
        total_examples += summary.example_count

    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(1)

    for summary in summaries:
        print(
            f"PASS: {summary.path.relative_to(ROOT)} "
            f"rules={summary.rule_count} examples={summary.example_count}"
        )

    print(f"Validated {len(files)} file(s), {total_rules} rule(s), {total_examples} example(s).")


if __name__ == "__main__":
    main()
