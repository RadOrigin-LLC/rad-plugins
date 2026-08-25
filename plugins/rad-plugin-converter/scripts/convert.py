from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from audit import (
    AUTHOR_FIELDS,
    MCP_SCHEMA,
    PLUGIN_FIELDS,
    PLUGIN_NAME_RE,
    PLUGIN_SCHEMA,
    _symlink_component,
    audit_path,
)
from frontmatter import SKILL_NAME_RE, audit_frontmatter, skill_name_repair
from models import ConversionResult, Finding
from transaction import FileTransaction, TransactionError


CLAUDE_ROOT = "${CLAUDE_PLUGIN_ROOT}"
PORTABLE_ROOT = "${PLUGIN_ROOT}"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _link_in_path(path: Path) -> Path | None:
    current = path.absolute()
    while True:
        if current.is_symlink():
            return current
        if current == current.parent:
            return None
        current = current.parent


def _atomic_write_text(path: Path, text: str) -> bool:
    if path.is_symlink():
        raise OSError(f"Refusing to replace symbolic link: {path}")
    try:
        current = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        current = None
    if current == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return True


def _atomic_write_json(path: Path, value: object) -> bool:
    return _atomic_write_text(path, _json_text(value))


def _json_text(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def _atomic_write_bytes(path: Path, value: bytes) -> bool:
    if path.is_symlink():
        raise OSError(f"Refusing to replace symbolic link: {path}")
    try:
        if path.read_bytes() == value:
            return False
    except FileNotFoundError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(value)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return True


def _create_symlink(path: Path, target: str) -> None:
    if path.exists() or path.is_symlink():
        raise OSError(f"Refusing to replace existing path: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(target, path, target_is_directory=False)


def _make_directory(path: Path) -> None:
    if path.is_symlink():
        raise OSError(f"Refusing to replace symbolic link: {path}")
    path.mkdir(exist_ok=True)


def _write_json_text(path: Path, text: str) -> bool:
    return _atomic_write_json(path, json.loads(text))


def _add_text_if_changed(
    transaction: FileTransaction,
    path: Path,
    text: str,
    writer: Any = None,
) -> bool:
    try:
        if path.read_text(encoding="utf-8-sig") == text:
            return False
    except (FileNotFoundError, UnicodeError):
        pass
    transaction.add_text(path, text, _atomic_write_text if writer is None else writer)
    return True


def _add_json_if_changed(transaction: FileTransaction, path: Path, value: object) -> bool:
    return _add_text_if_changed(transaction, path, _json_text(value), _write_json_text)


def _read_json(path: Path, root: Path) -> tuple[dict[str, Any] | None, Finding | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        return None, Finding("error", "conversion-read", _relative(path, root), str(exc))
    except json.JSONDecodeError as exc:
        return None, Finding(
            "error",
            "conversion-json",
            _relative(path, root),
            f"Invalid JSON: {exc.msg}.",
            exc.lineno,
        )
    if not isinstance(data, dict):
        return None, Finding(
            "error",
            "conversion-json-type",
            _relative(path, root),
            "Source manifest must contain a JSON object.",
        )
    return data, None


def _source_manifest(root: Path) -> tuple[dict[str, Any] | None, Path | None, Finding | None]:
    candidates = (
        root / "plugin.json",
        root / ".codex-plugin" / "plugin.json",
        root / ".claude-plugin" / "plugin.json",
    )
    for path in candidates:
        link = _symlink_component(path, root)
        if link is not None:
            return None, path, Finding(
                "error",
                "conversion-link",
                _relative(link, root),
                "Refusing to traverse or replace a symbolic link.",
            )
        if path.is_file():
            data, finding = _read_json(path, root)
            return data, path, finding
    return None, None, Finding(
        "error",
        "conversion-source-manifest",
        ".",
        "No plugin manifest was found.",
    )


def _portable_manifest(source: dict[str, Any], source_path: Path, root: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    findings: list[Finding] = []
    name = source.get("name")
    if not isinstance(name, str) or not (1 <= len(name) <= 64) or not PLUGIN_NAME_RE.fullmatch(name):
        return None, [
            Finding(
                "error",
                "conversion-plugin-name",
                _relative(source_path, root),
                "Source plugin name cannot be used as an Agent Plugins 1.0.0 name.",
            )
        ]

    result: dict[str, Any] = {"$schema": PLUGIN_SCHEMA, "name": name}
    for field in ("version", "description", "homepage", "repository", "license"):
        value = source.get(field)
        if isinstance(value, str):
            result[field] = value
        elif field in source:
            findings.append(
                Finding(
                    "warning",
                    "conversion-field-omitted",
                    _relative(source_path, root),
                    f"Non-string field '{field}' was omitted from the portable manifest.",
                )
            )

    author = source.get("author")
    if isinstance(author, dict):
        portable_author = {
            key: value
            for key, value in author.items()
            if key in AUTHOR_FIELDS and isinstance(value, str)
        }
        if portable_author:
            result["author"] = portable_author
        if portable_author != author:
            findings.append(
                Finding(
                    "warning",
                    "conversion-author-field-omitted",
                    _relative(source_path, root),
                    "Unsupported or non-string author fields were omitted from the portable manifest.",
                )
            )
    elif "author" in source:
        findings.append(
            Finding(
                "warning",
                "conversion-field-omitted",
                _relative(source_path, root),
                "Non-object author field was omitted from the portable manifest.",
            )
        )

    keywords = source.get("keywords")
    if isinstance(keywords, list) and all(isinstance(value, str) for value in keywords):
        result["keywords"] = keywords
    elif "keywords" in source:
        findings.append(
            Finding(
                "warning",
                "conversion-field-omitted",
                _relative(source_path, root),
                "Invalid keywords were omitted from the portable manifest.",
            )
        )

    extensions = source.get("extensions")
    if isinstance(extensions, dict) and all(isinstance(value, dict) for value in extensions.values()):
        result["extensions"] = extensions
    elif "extensions" in source:
        findings.append(
            Finding(
                "warning",
                "conversion-field-omitted",
                _relative(source_path, root),
                "Invalid extensions were omitted from the portable manifest.",
            )
        )

    for field in sorted(set(source) - PLUGIN_FIELDS):
        if source_path.name == "plugin.json" and source_path.parent == root:
            findings.append(
                Finding(
                    "warning",
                    "conversion-client-field-omitted",
                    "plugin.json",
                    f"Client field '{field}' was omitted from the portable manifest.",
                )
            )
    return result, findings


def _portable_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(CLAUDE_ROOT, PORTABLE_ROOT)
    if isinstance(value, list):
        return [_portable_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _portable_value(item) for key, item in value.items()}
    return value


def _convert_mcp(root: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    source_path = root / ".mcp.json"
    target_path = root / "mcp.json"
    link = _symlink_component(source_path, root) or _symlink_component(target_path, root)
    if link is not None:
        return None, [
            Finding(
                "error",
                "conversion-link",
                _relative(link, root),
                "Refusing to traverse or replace a symbolic link.",
            )
        ]
    if not source_path.is_file() or target_path.exists():
        return None, []
    source, read_finding = _read_json(source_path, root)
    if read_finding is not None:
        return None, [read_finding]
    assert source is not None
    servers = source.get("mcpServers") if "mcpServers" in source else source
    if not isinstance(servers, dict):
        return None, [
            Finding("error", "conversion-mcp-servers", ".mcp.json", "MCP servers must be an object.")
        ]

    converted: dict[str, Any] = {}
    findings: list[Finding] = []
    for name, raw_server in servers.items():
        if not isinstance(name, str) or not isinstance(raw_server, dict):
            findings.append(
                Finding("error", "conversion-mcp-server", ".mcp.json", "Every MCP server must be a named object.")
            )
            continue
        server = _portable_value(raw_server)
        transport = server.get("type")
        if transport is None and "command" in server:
            server = {"type": "stdio", **server}
        elif transport is None and "url" in server:
            findings.append(
                Finding(
                    "error",
                    "conversion-mcp-transport",
                    ".mcp.json",
                    f"MCP server '{name}' needs an explicit streamable-http or sse transport.",
                )
            )
            continue
        converted[name] = server
    if findings:
        return None, findings
    return {"$schema": MCP_SCHEMA, "mcpServers": converted}, []


def _plan_skill_repairs(root: Path) -> tuple[list[tuple[Path, str]], list[Finding]]:
    planned: list[tuple[Path, str]] = []
    findings: list[Finding] = []
    skills = root / "skills"
    link = _symlink_component(skills, root)
    if link is not None:
        return planned, [
            Finding("error", "conversion-link", _relative(link, root), "Refusing to traverse or replace a symbolic link.")
        ]
    if not skills.is_dir():
        return planned, findings
    for skill_dir in sorted(skills.iterdir(), key=lambda path: path.name.lower()):
        link = _symlink_component(skill_dir, root)
        if link is not None:
            findings.append(
                Finding(
                    "error",
                    "conversion-link",
                    _relative(link, root),
                    "Refusing to traverse or replace a symbolic link.",
                )
            )
            continue
        if not skill_dir.is_dir():
            continue
        skill_path = skill_dir / "SKILL.md"
        link = _symlink_component(skill_path, root)
        if link is not None:
            findings.append(
                Finding(
                    "error",
                    "conversion-link",
                    _relative(link, root),
                    "Refusing to traverse or replace a symbolic link.",
                )
            )
            continue
        if not skill_path.is_file():
            continue
        codes = {item.code for item in audit_frontmatter(skill_dir, root)}
        if "skill-name-mismatch" not in codes:
            continue
        try:
            changed, text = skill_name_repair(skill_dir)
        except (OSError, UnicodeError, ValueError) as exc:
            findings.append(
                Finding("error", "conversion-skill-repair", _relative(skill_path, root), str(exc))
            )
            continue
        if changed:
            planned.append((skill_path, text))
    return planned, findings


def _display_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.replace(".", "-").split("-") if part)


def create_plugin(
    path: Path,
    *,
    name: str,
    description: str,
    author: str,
    version: str = "0.1.0",
    license_id: str = "MIT",
    skill_name: str | None = None,
    skill_description: str | None = None,
    dry_run: bool = False,
) -> ConversionResult:
    link = _link_in_path(path)
    if link is not None:
        return ConversionResult(
            root=path,
            dry_run=dry_run,
            findings=[Finding("error", "creation-link", str(link), "Refusing to traverse a symbolic link.")],
        )
    root = path.resolve(strict=False)
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        return ConversionResult(
            root=root,
            findings=[
                Finding(
                    "error",
                    "creation-target-not-empty",
                    str(root),
                    "Creation target must be absent or an empty directory.",
                )
            ],
        )
    if not PLUGIN_NAME_RE.fullmatch(name) or not (1 <= len(name) <= 64):
        return ConversionResult(
            root=root,
            findings=[Finding("error", "creation-plugin-name", ".", "Plugin name is invalid.")],
        )
    if not description.strip() or not author.strip() or not version.strip() or not license_id.strip():
        return ConversionResult(
            root=root,
            findings=[
                Finding(
                    "error",
                    "creation-metadata",
                    ".",
                    "Description, author, version, and license must be non-empty.",
                )
            ],
        )
    if (skill_name is None) != (skill_description is None):
        return ConversionResult(
            root=root,
            findings=[
                Finding(
                    "error",
                    "creation-skill-metadata",
                    ".",
                    "Skill name and skill description must be supplied together.",
                )
            ],
        )
    if skill_name is not None and (
        not SKILL_NAME_RE.fullmatch(skill_name)
        or skill_description is None
        or not skill_description.strip()
    ):
        return ConversionResult(
            root=root,
            findings=[
                Finding(
                    "error",
                    "creation-skill-metadata",
                    ".",
                    "Starter skill name or description is invalid.",
                )
            ],
        )

    display_name = _display_name(name)
    portable: dict[str, Any] = {
        "$schema": PLUGIN_SCHEMA,
        "name": name,
        "version": version,
        "description": description,
        "author": {"name": author},
        "license": license_id,
    }
    codex: dict[str, Any] = {
        "name": name,
        "version": version,
        "description": description,
        "author": {"name": author},
        "license": license_id,
        "interface": {
            "displayName": display_name,
            "shortDescription": description,
            "longDescription": description,
            "developerName": author,
            "category": "Productivity",
            "capabilities": ["Agent Plugins 1.0.0 package"],
            "defaultPrompt": [f"Help me use {display_name}."],
        },
    }
    if skill_name is not None:
        codex["skills"] = "./skills/"

    transaction = FileTransaction(root.parent)
    _add_json_if_changed(transaction, root / "plugin.json", portable)
    _add_json_if_changed(transaction, root / ".codex-plugin" / "plugin.json", codex)
    if skill_name is not None and skill_description is not None:
        skill_text = (
            "---\n"
            f"name: {skill_name}\n"
            f"description: {json.dumps(skill_description, ensure_ascii=False)}\n"
            "---\n\n"
            f"# {_display_name(skill_name)}\n"
        )
        _add_text_if_changed(transaction, root / "skills" / skill_name / "SKILL.md", skill_text)

    try:
        transaction.validate()
    except OSError as exc:
        return ConversionResult(
            root=root,
            dry_run=dry_run,
            findings=[Finding("error", "creation-preflight", ".", str(exc))],
        )

    planned = [_relative(item, root) for item in transaction.planned_paths()]
    report = _audit_transaction_plan(root, transaction, source_root=None)
    if report.error_count:
        return ConversionResult(
            root=root,
            dry_run=dry_run,
            findings=report.findings,
        )
    if dry_run:
        return ConversionResult(root=root, changed_files=planned, dry_run=True, findings=report.findings)

    try:
        transaction.commit()
    except TransactionError as exc:
        return ConversionResult(
            root=root,
            findings=[Finding("error", "creation-transaction", ".", str(exc))],
        )

    report = audit_path(root)
    if report.error_count:
        recovery = transaction.rollback()
        findings = [Finding("error", "creation-validation", ".", "Created package failed its final audit.")]
        findings.extend(report.findings)
        if recovery is not None:
            findings.append(Finding("error", "creation-recovery", ".", str(recovery)))
        return ConversionResult(root=root, findings=findings)
    return ConversionResult(root=root, changed_files=planned, findings=report.findings)


def convert_in_place(path: Path, dry_run: bool = False) -> ConversionResult:
    link = _link_in_path(path)
    if link is not None:
        return ConversionResult(
            root=path,
            dry_run=dry_run,
            findings=[Finding("error", "conversion-link", str(link), "Refusing to traverse a symbolic link.")],
        )
    root = path.resolve(strict=False)
    if not root.is_dir():
        return ConversionResult(
            root=root,
            dry_run=dry_run,
            findings=[Finding("error", "conversion-root-kind", str(root), "Conversion target must be a directory.")],
        )

    fixed_paths = [
        root / "SKILL.md",
        *(root / relative for relative in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json")),
    ]
    for candidate in fixed_paths:
        link = _symlink_component(candidate, root)
        if link is not None:
            return ConversionResult(
                root=root,
                dry_run=dry_run,
                findings=[
                    Finding(
                        "error",
                        "conversion-link",
                        _relative(link, root),
                        "Refusing to traverse or replace a symbolic link.",
                    )
                ],
            )
    if fixed_paths[0].is_file() and not any(candidate.is_file() for candidate in fixed_paths[1:]):
        transaction = FileTransaction(root)
        try:
            changed, text = skill_name_repair(root)
            if changed:
                _add_text_if_changed(transaction, root / "SKILL.md", text)
            transaction.validate()
        except (OSError, UnicodeError, ValueError) as exc:
            return ConversionResult(
                root=root,
                dry_run=dry_run,
                findings=[Finding("error", "conversion-skill-repair", "SKILL.md", str(exc))],
            )
        planned = [_relative(item, root) for item in transaction.planned_paths()]
        report = _audit_transaction_plan(root, transaction, source_root=root)
        if report.error_count:
            return ConversionResult(root=root, dry_run=dry_run, findings=report.findings)
        if dry_run:
            return ConversionResult(root=root, changed_files=planned, dry_run=True, findings=report.findings)
        try:
            transaction.commit()
        except TransactionError as exc:
            return ConversionResult(
                root=root,
                findings=[Finding("error", "conversion-transaction", "SKILL.md", str(exc))],
            )
        report = audit_path(root)
        if report.error_count:
            recovery = transaction.rollback()
            findings = [Finding("error", "conversion-validation", ".", "Converted skill failed its final audit.")]
            findings.extend(report.findings)
            if recovery is not None:
                findings.append(Finding("error", "conversion-recovery", ".", str(recovery)))
            return ConversionResult(root=root, findings=findings)
        return ConversionResult(root=root, changed_files=planned, findings=report.findings)

    source, source_path, source_finding = _source_manifest(root)
    if source_finding is not None or source is None or source_path is None:
        return ConversionResult(root=root, dry_run=dry_run, findings=[source_finding] if source_finding else [])

    portable, conversion_findings = _portable_manifest(source, source_path, root)
    if portable is None:
        return ConversionResult(root=root, dry_run=dry_run, findings=conversion_findings)

    transaction = FileTransaction(root)
    _add_json_if_changed(transaction, root / "plugin.json", portable)
    skill_repairs, skill_findings = _plan_skill_repairs(root)
    conversion_findings.extend(skill_findings)
    mcp_data, mcp_findings = _convert_mcp(root)
    conversion_findings.extend(mcp_findings)
    for skill_path, text in skill_repairs:
        _add_text_if_changed(transaction, skill_path, text)
    if mcp_data is not None:
        _add_json_if_changed(transaction, root / "mcp.json", mcp_data)

    if any(item.severity == "error" for item in conversion_findings):
        return ConversionResult(root=root, dry_run=dry_run, findings=conversion_findings)

    try:
        transaction.validate()
    except OSError as exc:
        conversion_findings.append(Finding("error", "conversion-preflight", ".", str(exc)))
        return ConversionResult(root=root, dry_run=dry_run, findings=conversion_findings)

    planned = [_relative(item, root) for item in transaction.planned_paths()]
    staged_report = _audit_transaction_plan(root, transaction, source_root=root)
    if staged_report.error_count:
        findings = conversion_findings + staged_report.findings
        findings.sort(key=lambda item: (item.path.lower(), item.line or 0, item.severity, item.code))
        return ConversionResult(root=root, dry_run=dry_run, findings=findings)
    if dry_run:
        findings = conversion_findings + staged_report.findings
        findings.sort(key=lambda item: (item.path.lower(), item.line or 0, item.severity, item.code))
        return ConversionResult(root=root, changed_files=planned, dry_run=True, findings=findings)

    try:
        transaction.commit()
    except TransactionError as exc:
        conversion_findings.append(Finding("error", "conversion-transaction", ".", str(exc)))
        return ConversionResult(root=root, findings=conversion_findings)

    final_report = audit_path(root)
    if final_report.error_count:
        recovery = transaction.rollback()
        findings = [Finding("error", "conversion-validation", ".", "Converted package failed its final audit.")]
        findings.extend(conversion_findings)
        findings.extend(final_report.findings)
        if recovery is not None:
            findings.append(Finding("error", "conversion-recovery", ".", str(recovery)))
        findings.sort(key=lambda item: (item.path.lower(), item.line or 0, item.severity, item.code))
        return ConversionResult(root=root, findings=findings)

    findings = conversion_findings + final_report.findings
    findings.sort(key=lambda item: (item.path.lower(), item.line or 0, item.severity, item.code))
    return ConversionResult(root=root, changed_files=planned, findings=findings)


def _copy_source(source: Path, target: Path) -> list[str]:
    ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "*.pyo")
    if target.exists():
        shutil.copytree(source, target, dirs_exist_ok=True, symlinks=True, ignore=ignore)
    else:
        shutil.copytree(source, target, symlinks=True, ignore=ignore)
    entries: list[str] = []
    for current, directories, files in os.walk(target, followlinks=False):
        current_path = Path(current)
        for name in sorted(directories):
            item = current_path / name
            entries.append(item.relative_to(target).as_posix())
        for name in sorted(files):
            item = current_path / name
            if item.is_file() or item.is_symlink():
                entries.append(item.relative_to(target).as_posix())
    return sorted(entries)


def _audit_transaction_plan(
    root: Path,
    transaction: FileTransaction,
    *,
    source_root: Path | None,
):
    with tempfile.TemporaryDirectory(prefix="rad-plugin-converter-audit-") as temp_name:
        staging = Path(temp_name) / "package"
        if source_root is None:
            staging.mkdir(parents=True)
        else:
            _copy_source(source_root, staging)
        staged = FileTransaction(staging)
        for operation in transaction.operations:
            relative = operation.path.relative_to(root)
            destination = staging / relative
            if operation.kind == "directory":
                staged.add_directory(destination, _make_directory)
            elif operation.kind == "text":
                assert isinstance(operation.value, str)
                staged.add_text(destination, operation.value, _atomic_write_text)
            elif operation.kind == "bytes":
                assert isinstance(operation.value, bytes)
                staged.add_bytes(destination, operation.value, _atomic_write_bytes)
            else:
                assert isinstance(operation.value, str)
                staged.add_symlink(destination, operation.value, _create_symlink)
        try:
            staged.commit()
        except TransactionError as exc:
            report = audit_path(staging)
            report.findings.append(Finding("error", "conversion-staging", ".", str(exc)))
            report.findings.sort(key=lambda item: (item.path.lower(), item.line or 0, item.severity, item.code))
            return report
        return audit_path(staging)


def _plan_copy(source: Path, target: Path, transaction: FileTransaction) -> list[str]:
    planned: list[str] = []
    for current, directories, files in os.walk(source, followlinks=False):
        current_path = Path(current)
        for name in sorted(directories):
            source_path = current_path / name
            destination = target / source_path.relative_to(source)
            if source_path.is_symlink():
                transaction.add_symlink(destination, os.readlink(source_path), _create_symlink)
            else:
                transaction.add_directory(destination, _make_directory)
            planned.append(destination.relative_to(target).as_posix())
        for name in sorted(files):
            source_path = current_path / name
            destination = target / source_path.relative_to(source)
            if source_path.is_symlink():
                transaction.add_symlink(destination, os.readlink(source_path), _create_symlink)
            else:
                transaction.add_bytes(destination, source_path.read_bytes(), _atomic_write_bytes)
            planned.append(destination.relative_to(target).as_posix())
    return sorted(planned)


def convert_to_target(source_path: Path, target_path: Path, dry_run: bool = False) -> ConversionResult:
    source_link = _link_in_path(source_path)
    target_link = _link_in_path(target_path)
    if source_link is not None or target_link is not None:
        return ConversionResult(
            root=target_path,
            dry_run=dry_run,
            findings=[
                Finding(
                    "error",
                    "conversion-link",
                    str(source_link or target_link),
                    "Refusing to traverse a symbolic link.",
                )
            ],
        )
    source = source_path.resolve(strict=False)
    target = target_path.resolve(strict=False)
    if not source.is_dir():
        return ConversionResult(
            root=target,
            dry_run=dry_run,
            findings=[Finding("error", "conversion-source-kind", str(source), "Source must be a directory.")],
        )
    if target == source or target.is_relative_to(source):
        return ConversionResult(
            root=target,
            dry_run=dry_run,
            findings=[Finding("error", "conversion-target-location", str(target), "Target cannot be the source or inside it.")],
        )
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        return ConversionResult(
            root=target,
            dry_run=dry_run,
            findings=[
                Finding("error", "conversion-target-not-empty", str(target), "Target must be absent or an empty directory.")
            ],
        )

    source_report = audit_path(source)
    blocking = [item for item in source_report.findings if item.code in {"package-path-escape", "package-link"}]
    if blocking:
        return ConversionResult(root=target, dry_run=dry_run, findings=blocking)
    try:
        with tempfile.TemporaryDirectory(prefix="rad-plugin-converter-") as temp_name:
            staging = Path(temp_name) / "package"
            copied_before_conversion = _copy_source(source, staging)
            converted = convert_in_place(staging, dry_run=dry_run)
            if not converted.successful:
                converted.root = target
                converted.changed_files = []
                converted.dry_run = dry_run
                return converted
            if dry_run:
                planned = sorted(set(copied_before_conversion + converted.changed_files))
                return ConversionResult(
                    root=target,
                    changed_files=planned,
                    dry_run=True,
                    findings=converted.findings,
                )
            transaction = FileTransaction(target.parent)
            copied = _plan_copy(staging, target, transaction)
            transaction.validate()
            staged_report = _audit_transaction_plan(target, transaction, source_root=None)
            if staged_report.error_count:
                return ConversionResult(root=target, findings=staged_report.findings)
            transaction.commit()
    except TransactionError as exc:
        return ConversionResult(
            root=target,
            findings=[Finding("error", "conversion-transaction", str(target), str(exc))],
        )
    except OSError as exc:
        return ConversionResult(
            root=target,
            findings=[Finding("error", "conversion-copy", str(target), str(exc))],
        )

    final_report = audit_path(target)
    if final_report.error_count:
        recovery = transaction.rollback()
        findings = [Finding("error", "conversion-validation", str(target), "Copied package failed its final audit.")]
        findings.extend(converted.findings)
        findings.extend(final_report.findings)
        if recovery is not None:
            findings.append(Finding("error", "conversion-recovery", str(target), str(recovery)))
        return ConversionResult(root=target, findings=findings)
    findings = converted.findings + final_report.findings
    return ConversionResult(root=target, changed_files=copied, findings=findings)


def _marketplace_paths(root: Path) -> tuple[list[Path], Finding | None]:
    manifest_path = root / "marketplace.json"
    data, read_finding = _read_json(manifest_path, root)
    if read_finding is not None or data is None:
        return [], read_finding
    entries = data.get("plugins")
    if not isinstance(entries, list):
        return [], Finding("error", "conversion-marketplace-plugins", "marketplace.json", "plugins must be an array.")

    paths: list[Path] = []
    root_absolute = root.absolute()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("source"), dict):
            return [], Finding("error", "conversion-marketplace-entry", "marketplace.json", "Plugin entry has no source object.")
        source = entry["source"]
        if source.get("source") != "local" or not isinstance(source.get("path"), str):
            return [], Finding("error", "conversion-marketplace-source", "marketplace.json", "Only local plugin sources can be converted.")
        candidate = Path(os.path.abspath(root / source["path"]))
        if not candidate.is_relative_to(root_absolute):
            return [], Finding("error", "conversion-marketplace-path", "marketplace.json", "Plugin path escapes the marketplace root.")
        link = _link_in_path(candidate)
        if link is not None:
            return [], Finding("error", "conversion-link", _relative(link, root), "Refusing to traverse a symbolic link.")
        paths.append(candidate)
    return paths, None


def convert_marketplace(path: Path, apply: bool = False, dry_run: bool = False) -> list[ConversionResult]:
    link = _link_in_path(path)
    if link is not None:
        return [
            ConversionResult(
                root=path,
                dry_run=dry_run,
                findings=[Finding("error", "conversion-link", str(link), "Refusing to traverse a symbolic link.")],
            )
        ]
    root = path.resolve(strict=False)
    plugin_paths, finding = _marketplace_paths(root)
    if finding is not None:
        return [ConversionResult(root=root, dry_run=dry_run, findings=[finding])]
    if apply and dry_run:
        return [
            ConversionResult(
                root=root,
                dry_run=True,
                findings=[Finding("error", "conversion-mode", "marketplace.json", "Choose --apply or --dry-run, not both.")],
            )
        ]
    if dry_run:
        return [convert_in_place(plugin_path, dry_run=True) for plugin_path in plugin_paths]
    if apply:
        return [convert_in_place(plugin_path) for plugin_path in plugin_paths]
    return [
        ConversionResult(root=plugin_path, findings=audit_path(plugin_path).findings)
        for plugin_path in plugin_paths
    ]
