#!/usr/bin/env python3
"""
validate-json.py — Validate JSON output against a JSON Schema.

Used by rad-plan skills to make the "JSON-first subagent contracts" claim real:
the dispatching skill captures the agent's JSON output, runs it through this script,
and re-prompts on validation failure rather than silently falling back to markdown.

Usage:
  python3 validate-json.py <schema.json> <data.json>
  python3 validate-json.py <schema.json> -            # read data from stdin
  python3 validate-json.py <schema.json> <data.json> --extract-from-markdown
                                                       # extract first ```json block then validate

Output:
  Default — text. "OK" + exit 0 on success; error report + exit 1 on validation failure.
  --json  — single JSON result object: {"valid": bool, "errors": [{"path": "...", "message": "..."}]}
  Exit 2 reserved for script errors (file not found, invalid schema, malformed JSON beyond extraction).

This script implements the subset of JSON Schema draft-07 we actually use across
rad-plan contracts: type, required, properties, items, enum, additionalProperties,
const, oneOf (basic), and $ref to local definitions. If the third-party `jsonschema`
package is installed it will be used preferentially for fuller draft-07 coverage.

No third-party dependencies required for the subset we use. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Optional: use jsonschema if available for fuller validation coverage
try:  # pragma: no cover
    import jsonschema  # type: ignore

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# ---------- minimal JSON Schema validator (subset) ----------


TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


def _resolve_ref(ref: str, root: dict) -> dict:
    if not ref.startswith("#/"):
        raise ValueError(f"only local $ref supported, got {ref!r}")
    parts = ref[2:].split("/")
    node: object = root
    for p in parts:
        if not isinstance(node, dict) or p not in node:
            raise ValueError(f"$ref {ref!r} could not be resolved")
        node = node[p]
    if not isinstance(node, dict):
        raise ValueError(f"$ref {ref!r} did not resolve to an object")
    return node


def _validate(data, schema: dict, path: str, root: dict, errors: list[dict]) -> None:
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], root)

    if "const" in schema:
        if data != schema["const"]:
            errors.append({"path": path, "message": f"expected const {schema['const']!r}, got {data!r}"})
            return

    if "enum" in schema:
        if data not in schema["enum"]:
            errors.append({"path": path, "message": f"value {data!r} not in enum {schema['enum']!r}"})
            return

    if "type" in schema:
        expected = schema["type"]
        types = expected if isinstance(expected, list) else [expected]
        py_types = tuple(TYPE_MAP[t] for t in types if t in TYPE_MAP)
        # Special case: bool is a subclass of int — don't accept bool when integer/number expected
        if any(t in ("integer", "number") for t in types) and isinstance(data, bool):
            errors.append({"path": path, "message": f"expected {expected}, got bool"})
            return
        if py_types and not isinstance(data, py_types):
            errors.append({"path": path, "message": f"expected {expected}, got {type(data).__name__}"})
            return

    if isinstance(data, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                errors.append({"path": f"{path}.{key}", "message": "required field missing"})
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in data.items():
            if key in properties:
                _validate(value, properties[key], f"{path}.{key}", root, errors)
            elif additional is False:
                errors.append({"path": f"{path}.{key}", "message": "additional property not allowed"})
            elif isinstance(additional, dict):
                _validate(value, additional, f"{path}.{key}", root, errors)

    elif isinstance(data, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for i, value in enumerate(data):
                _validate(value, items, f"{path}[{i}]", root, errors)
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append({"path": path, "message": f"array shorter than minItems={schema['minItems']}"})

    if "oneOf" in schema:
        matches = 0
        for sub in schema["oneOf"]:
            sub_errors: list[dict] = []
            _validate(data, sub, path, root, sub_errors)
            if not sub_errors:
                matches += 1
        if matches != 1:
            errors.append({"path": path, "message": f"oneOf matched {matches} schemas, expected 1"})


RISK_SCHEMA_ID = "risk-assessment.schema.json"
STACK_SCHEMA_ID = "stack-eval.schema.json"
RISK_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


def _risk_semantic_errors(data: object) -> list[dict]:
    if not isinstance(data, dict):
        return []

    errors: list[dict] = []
    counts = {severity: 0 for severity in RISK_SEVERITIES}
    for field in ("blocking_issues", "advisory_issues"):
        issues = data.get(field)
        if not isinstance(issues, list):
            continue
        for index, issue in enumerate(issues):
            if not isinstance(issue, dict):
                continue
            severity = issue.get("severity")
            if severity in counts:
                counts[severity] += 1
            if field == "blocking_issues" and severity in {"MEDIUM", "LOW"}:
                errors.append({
                    "path": f"$.blocking_issues[{index}].severity",
                    "message": "blocking issues must use CRITICAL or HIGH severity",
                })

    summary = data.get("summary")
    if isinstance(summary, dict):
        for severity, actual_count in counts.items():
            field = f"{severity.lower()}_count"
            if field in summary and summary[field] != actual_count:
                errors.append({
                    "path": f"$.summary.{field}",
                    "message": f"{field} must match issue arrays ({actual_count})",
                })

        if data.get("verdict") == "APPROVE":
            critical_or_high = counts["CRITICAL"] + counts["HIGH"]
            reported_critical_or_high = sum(
                summary.get(field, 0)
                for field in ("critical_count", "high_count")
                if isinstance(summary.get(field), int) and not isinstance(summary.get(field), bool)
            )
            if critical_or_high or reported_critical_or_high:
                errors.append({
                    "path": "$.verdict",
                    "message": "APPROVE cannot include CRITICAL or HIGH issues",
                })

    return errors


def _stack_semantic_errors(data: object) -> list[dict]:
    if not isinstance(data, dict) or data.get("compatibility_verified") is not True:
        return []
    sources = data.get("verification_sources")
    if not isinstance(sources, list) or not sources:
        return [{
            "path": "$.verification_sources",
            "message": "compatibility_verified requires at least one verification source",
        }]
    return []


def semantic_validate(data: object, schema: dict) -> list[dict]:
    schema_id = str(schema.get("$id", ""))
    if schema_id.endswith(RISK_SCHEMA_ID):
        return _risk_semantic_errors(data)
    if schema_id.endswith(STACK_SCHEMA_ID):
        return _stack_semantic_errors(data)
    return []


def validate(data, schema: dict) -> list[dict]:
    if HAS_JSONSCHEMA:
        validator = jsonschema.Draft7Validator(schema)
        errors = [
            {"path": "/".join(str(p) for p in err.absolute_path) or "$", "message": err.message}
            for err in validator.iter_errors(data)
        ]
    else:
        errors = []
        _validate(data, schema, "$", schema, errors)
    errors.extend(semantic_validate(data, schema))
    return errors


# ---------- IO helpers ----------


JSON_BLOCK_RE = re.compile(r"```json\s*(?P<body>\{.*?\})\s*```", re.DOTALL)


def extract_json_from_markdown(text: str) -> str:
    match = JSON_BLOCK_RE.search(text)
    if not match:
        # Fallback: find first balanced { ... } at top level
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    return text[start : i + 1]
        raise ValueError("no JSON block found")
    return match.group("body")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("schema", help="Path to a JSON Schema file")
    p.add_argument("data", help="Path to a JSON data file, or '-' for stdin")
    p.add_argument(
        "--extract-from-markdown",
        action="store_true",
        help="Treat data input as markdown and extract the first ```json block",
    )
    p.add_argument("--json", action="store_true", help="Emit a JSON result instead of text")
    args = p.parse_args(argv)

    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"error: schema not found: {schema_path}", file=sys.stderr)
        return 2
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: schema is not valid JSON: {e}", file=sys.stderr)
        return 2

    raw = sys.stdin.read() if args.data == "-" else Path(args.data).read_text(encoding="utf-8", errors="replace")
    if args.extract_from_markdown:
        try:
            raw = extract_json_from_markdown(raw)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        msg = f"data is not valid JSON: {e}"
        if args.json:
            print(json.dumps({"valid": False, "errors": [{"path": "$", "message": msg}]}))
        else:
            print(f"FAIL — {msg}")
        return 1

    errors = validate(data, schema)
    if args.json:
        print(json.dumps({"valid": not errors, "errors": errors, "validator": "jsonschema" if HAS_JSONSCHEMA else "builtin"}))
    elif not errors:
        print(f"OK — schema={schema_path.name} validator={'jsonschema' if HAS_JSONSCHEMA else 'builtin'}")
    else:
        print(f"FAIL — {len(errors)} error(s):")
        for err in errors:
            print(f"  {err['path']}: {err['message']}")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
