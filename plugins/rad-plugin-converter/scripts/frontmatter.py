from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from models import Finding

try:
    import yaml as _yaml
except ImportError:
    _yaml = None


ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
SKILL_NAME_RE = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
INTEGER_RE = re.compile(r"^[+-]?[0-9]+$")
FLOAT_RE = re.compile(r"^[+-]?(?:[0-9]+\.[0-9]*|[0-9]*\.[0-9]+)$")


class FrontmatterError(ValueError):
    pass


@dataclass(slots=True)
class FrontmatterDocument:
    path: Path
    values: dict[str, Any]
    key_lines: dict[str, int]
    end_line: int


def _strip_inline_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and character == "\\":
            escaped = True
            continue
        if character in {'"', "'"}:
            if quote is None:
                quote = character
            elif quote == character:
                if quote == "'" and index + 1 < len(value) and value[index + 1] == "'":
                    continue
                quote = None
            continue
        if character == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.rstrip()


def _split_mapping_entry(line: str) -> tuple[str, str] | None:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and character == "\\":
            escaped = True
            continue
        if character in {'"', "'"}:
            if quote is None:
                quote = character
            elif quote == character:
                if quote == "'" and index + 1 < len(line) and line[index + 1] == "'":
                    continue
                quote = None
            continue
        if character == ":" and quote is None:
            return line[:index].strip(), line[index + 1 :]
    return None


def _split_flow_items(value: str) -> list[str]:
    items: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    depth = 0
    for index, character in enumerate(value):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and character == "\\":
            escaped = True
            continue
        if character in {'"', "'"}:
            if quote is None:
                quote = character
            elif quote == character:
                if quote == "'" and index + 1 < len(value) and value[index + 1] == "'":
                    continue
                quote = None
            continue
        if quote is not None:
            continue
        if character in "[{(":
            depth += 1
        elif character in "]})":
            depth -= 1
        elif character == "," and depth == 0:
            items.append(value[start:index].strip())
            start = index + 1
    tail = value[start:].strip()
    if tail:
        items.append(tail)
    return items


def _parse_flow(value: str) -> Any:
    if value.startswith("{") and value.endswith("}"):
        result: dict[str, Any] = {}
        inner = value[1:-1].strip()
        if not inner:
            return result
        for item in _split_flow_items(inner):
            entry = _split_mapping_entry(item)
            if entry is None:
                raise FrontmatterError("Unsupported YAML fallback syntax in flow mapping")
            raw_key, raw_value = entry
            key = _parse_scalar(raw_key)
            if not isinstance(key, str):
                raise FrontmatterError("YAML mapping keys must be strings")
            if key in result:
                raise FrontmatterError(f"Duplicate metadata key: {key}")
            result[key] = _parse_scalar(raw_value)
        return result
    if value.startswith("[") and value.endswith("]"):
        return [_parse_scalar(item) for item in _split_flow_items(value[1:-1])]
    raise FrontmatterError("Unsupported YAML fallback syntax in flow value")


def _parse_scalar(raw: str) -> Any:
    value = _strip_inline_comment(raw.strip())
    if not value:
        return ""
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise FrontmatterError(f"Invalid double-quoted scalar: {exc.msg}") from exc
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "~"}:
        return None
    if INTEGER_RE.fullmatch(value):
        return int(value)
    if FLOAT_RE.fullmatch(value):
        return float(value)
    if (value.startswith("[") and value.endswith("]")) or (value.startswith("{") and value.endswith("}")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return _parse_flow(value)
    return value


def _block_value(lines: list[str], start: int, style: str) -> tuple[str, int]:
    collected: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if line and not line[0].isspace():
            break
        collected.append(line)
        index += 1

    nonempty = [len(line) - len(line.lstrip()) for line in collected if line.strip()]
    indent = min(nonempty) if nonempty else 0
    content = [line[indent:] if line.strip() else "" for line in collected]
    if style.startswith(">"):
        value = " ".join(part.strip() for part in content).strip()
    else:
        value = "\n".join(content).strip("\n")
    return value, index


def _metadata_value(lines: list[str], start: int) -> tuple[dict[str, Any], int]:
    metadata: dict[str, Any] = {}
    index = start
    base_indent: int | None = None
    while index < len(lines):
        line = lines[index]
        if line and not line[0].isspace():
            break
        if not line.strip():
            index += 1
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent < 2:
            raise FrontmatterError("Metadata entries must be indented by at least two spaces")
        if stripped.startswith("#"):
            index += 1
            continue
        if base_indent is None:
            base_indent = indent
        if indent != base_indent:
            raise FrontmatterError("Unsupported YAML fallback syntax: nested metadata is not supported")
        entry = _split_mapping_entry(stripped)
        if entry is None:
            raise FrontmatterError(f"Invalid metadata entry on line {index + 2}")
        raw_key, raw_value = entry
        key = _parse_scalar(raw_key)
        if not isinstance(key, str) or not key:
            raise FrontmatterError(f"Metadata key on line {index + 2} must be a string")
        if key in metadata:
            raise FrontmatterError(f"Duplicate metadata key: {key}")
        metadata[key] = _parse_scalar(raw_value)
        index += 1
    return metadata, index


def _validate_yaml(frontmatter_lines: list[str]) -> None:
    if _yaml is None:
        return
    try:
        parsed = _yaml.safe_load("\n".join(frontmatter_lines))
    except Exception as exc:
        raise FrontmatterError(f"Invalid YAML: {exc}") from exc
    if not isinstance(parsed, dict):
        raise FrontmatterError("YAML frontmatter must contain a mapping")


def parse_frontmatter(path: Path) -> FrontmatterDocument:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("SKILL.md must start with YAML frontmatter")

    try:
        end_index = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise FrontmatterError("YAML frontmatter has no closing delimiter") from exc

    frontmatter_lines = lines[1:end_index]
    _validate_yaml(frontmatter_lines)
    values: dict[str, Any] = {}
    key_lines: dict[str, int] = {}
    index = 0
    while index < len(frontmatter_lines):
        line = frontmatter_lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[0].isspace():
            raise FrontmatterError(f"Unexpected indentation on line {index + 2}")
        entry = _split_mapping_entry(line)
        if entry is None:
            raise FrontmatterError(f"Invalid frontmatter entry on line {index + 2}")
        raw_key, raw_value = entry
        key = _parse_scalar(raw_key)
        if not isinstance(key, str) or not key:
            raise FrontmatterError(f"Frontmatter key on line {index + 2} must be a string")
        raw_value = _strip_inline_comment(raw_value).strip()
        if key in values:
            raise FrontmatterError(f"Duplicate frontmatter field: {key}")
        key_lines[key] = index + 2
        if key == "metadata" and not raw_value:
            value, next_index = _metadata_value(frontmatter_lines, index + 1)
        elif raw_value in {">", ">-", ">+", "|", "|-", "|+"}:
            value, next_index = _block_value(frontmatter_lines, index + 1, raw_value)
        else:
            value = _parse_scalar(raw_value)
            next_index = index + 1
        values[key] = value
        index = next_index

    return FrontmatterDocument(
        path=path,
        values=values,
        key_lines=key_lines,
        end_line=end_index + 1,
    )


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _type_finding(
    findings: list[Finding],
    path: str,
    document: FrontmatterDocument,
    field: str,
    expected: str,
) -> None:
    findings.append(
        Finding(
            "error",
            f"skill-{field}-type",
            path,
            f"Frontmatter field '{field}' must be {expected}.",
            document.key_lines.get(field),
        )
    )


def audit_frontmatter(skill_dir: Path, plugin_root: Path) -> list[Finding]:
    skill_path = skill_dir / "SKILL.md"
    rel = _relative(skill_path, plugin_root)
    if not skill_path.is_file():
        return [Finding("error", "missing-skill-md", rel, "Skill directory has no regular SKILL.md file.")]

    try:
        document = parse_frontmatter(skill_path)
    except (OSError, UnicodeError, FrontmatterError) as exc:
        return [Finding("error", "skill-frontmatter", rel, str(exc))]

    findings: list[Finding] = []
    unknown = sorted(set(document.values) - ALLOWED_FIELDS)
    for field in unknown:
        findings.append(
            Finding(
                "error",
                "skill-unknown-field",
                rel,
                f"Unsupported Agent Skills frontmatter field: {field}.",
                document.key_lines.get(field),
            )
        )

    name = document.values.get("name")
    if not isinstance(name, str):
        _type_finding(findings, rel, document, "name", "a string")
    elif not (1 <= len(name) <= 64) or not SKILL_NAME_RE.fullmatch(name):
        findings.append(
            Finding("error", "skill-name", rel, "Skill name does not meet Agent Skills naming rules.", document.key_lines.get("name"))
        )
    elif name != skill_dir.name:
        findings.append(
            Finding(
                "error",
                "skill-name-mismatch",
                rel,
                f"Skill name '{name}' does not match directory '{skill_dir.name}'.",
                document.key_lines.get("name"),
            )
        )

    description = document.values.get("description")
    if not isinstance(description, str):
        _type_finding(findings, rel, document, "description", "a string")
    elif not (1 <= len(description.strip()) <= 1024):
        findings.append(
            Finding(
                "error",
                "skill-description-length",
                rel,
                "Skill description must contain 1 to 1024 characters.",
                document.key_lines.get("description"),
            )
        )

    for field in ("license", "allowed-tools"):
        value = document.values.get(field)
        if field in document.values and not isinstance(value, str):
            _type_finding(findings, rel, document, field, "a string")

    compatibility = document.values.get("compatibility")
    if "compatibility" in document.values:
        if not isinstance(compatibility, str):
            _type_finding(findings, rel, document, "compatibility", "a string")
        elif not (1 <= len(compatibility.strip()) <= 500):
            findings.append(
                Finding(
                    "error",
                    "skill-compatibility-length",
                    rel,
                    "Compatibility must contain 1 to 500 characters.",
                    document.key_lines.get("compatibility"),
                )
            )

    metadata = document.values.get("metadata")
    if "metadata" in document.values:
        if not isinstance(metadata, dict):
            _type_finding(findings, rel, document, "metadata", "a string-to-string map")
        else:
            for key, value in metadata.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    findings.append(
                        Finding(
                            "error",
                            "skill-metadata-value",
                            rel,
                            "Every metadata key and value must be a string.",
                            document.key_lines.get("metadata"),
                        )
                    )
                    break
    return findings


def _atomic_write(path: Path, text: str) -> None:
    if path.is_symlink():
        raise FrontmatterError(f"Refusing to replace symbolic link: {path}")
    parent = path.parent
    while parent != parent.parent:
        if parent.is_symlink():
            raise FrontmatterError(f"Refusing to traverse symbolic link: {parent}")
        if parent.exists():
            break
        parent = parent.parent
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def skill_name_repair(skill_dir: Path) -> tuple[bool, str]:
    if not SKILL_NAME_RE.fullmatch(skill_dir.name) or len(skill_dir.name) > 64:
        return False, ""
    skill_path = skill_dir / "SKILL.md"
    if skill_dir.is_symlink() or skill_path.is_symlink():
        raise FrontmatterError(f"Refusing to traverse or replace symbolic link: {skill_path}")
    document = parse_frontmatter(skill_path)
    current = document.values.get("name")
    if current == skill_dir.name or "name" not in document.key_lines:
        return False, ""

    text = skill_path.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    index = document.key_lines["name"] - 1
    ending = "\r\n" if lines[index].endswith("\r\n") else "\n" if lines[index].endswith("\n") else ""
    lines[index] = f"name: {skill_dir.name}{ending}"
    return True, "".join(lines)


def repair_skill_name(skill_dir: Path) -> bool:
    changed, text = skill_name_repair(skill_dir)
    if changed:
        _atomic_write(skill_dir / "SKILL.md", text)
    return changed
