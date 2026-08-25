from __future__ import annotations

import ipaddress
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

from frontmatter import audit_frontmatter
from models import AuditReport, Finding


PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
PLUGIN_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
AUTHOR_FIELDS = {"name", "email", "url"}
PLUGIN_NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
EXTENSION_NAMESPACE_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$"
)
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
CLIENT_ONLY_NAMES = {
    ".claude-plugin",
    ".codex-plugin",
    "agents",
    "commands",
    "hooks",
    "lsp",
    "ui",
}
SECRET_HEADER_NAMES = {
    "api-key",
    "authorization",
    "cookie",
    "proxy-authorization",
    "token",
    "x-api-key",
}


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _symlink_component(path: Path, root: Path) -> Path | None:
    root_absolute = root.absolute()
    candidate = path.absolute()
    try:
        relative = candidate.relative_to(root_absolute)
    except ValueError:
        return None
    current = root_absolute
    if current.is_symlink():
        return current
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return current
    return None


def _read_json(path: Path) -> tuple[Any | None, Finding | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except OSError as exc:
        return None, Finding("error", "json-read", path.as_posix(), str(exc))
    except json.JSONDecodeError as exc:
        return None, Finding(
            "error",
            "json-syntax",
            path.as_posix(),
            f"Invalid JSON: {exc.msg}.",
            exc.lineno,
        )


def detect_source_types(root: Path) -> tuple[str, ...]:
    types: list[str] = []
    manifest = root / "plugin.json"
    if _symlink_component(manifest, root) is None and manifest.is_file():
        data, _ = _read_json(manifest)
        if isinstance(data, dict) and data.get("$schema") == PLUGIN_SCHEMA:
            types.append("agent-plugin")
        else:
            types.append("legacy-root")
    codex_manifest = root / ".codex-plugin" / "plugin.json"
    if _symlink_component(codex_manifest, root) is None and codex_manifest.is_file():
        types.append("codex")
    claude_manifest = root / ".claude-plugin" / "plugin.json"
    if _symlink_component(claude_manifest, root) is None and claude_manifest.is_file():
        types.append("claude")
    skill = root / "SKILL.md"
    if _symlink_component(skill, root) is None and skill.is_file():
        types.append("agent-skill")
    return tuple(types)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False


def _iter_package_entries(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in {".git", "__pycache__"})
        current_path = Path(current)
        for name in directories:
            yield current_path / name
        for name in sorted(files):
            yield current_path / name


def _audit_containment(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_package_entries(root):
        link = _symlink_component(path, root)
        if link is not None:
            findings.append(
                Finding(
                    "error",
                    "package-link",
                    _relative(link, root),
                    "Refusing to traverse a symbolic link in the package.",
                )
            )
            if not _inside(path, root):
                findings.append(
                    Finding(
                        "error",
                        "package-path-escape",
                        _relative(path, root),
                        "Resolved package path escapes the plugin root.",
                    )
                )
        elif not _inside(path, root):
            findings.append(
                Finding(
                    "error",
                    "package-path-escape",
                    _relative(path, root),
                    "Resolved package path escapes the plugin root.",
                )
            )
    return findings


def _audit_manifest(root: Path, path: Path, data: Any) -> tuple[str | None, list[Finding]]:
    rel = _relative(path, root)
    findings: list[Finding] = []
    if not isinstance(data, dict):
        return None, [Finding("error", "manifest-type", rel, "plugin.json must contain a JSON object.")]

    unknown = sorted(set(data) - PLUGIN_FIELDS)
    for field in unknown:
        findings.append(
            Finding("error", "manifest-unknown-field", rel, f"Unknown portable manifest field: {field}.")
        )

    if data.get("$schema") != PLUGIN_SCHEMA:
        findings.append(
            Finding("error", "manifest-schema", rel, f"$schema must be {PLUGIN_SCHEMA}.")
        )

    name = data.get("name")
    if not isinstance(name, str) or not (1 <= len(name) <= 64) or not PLUGIN_NAME_RE.fullmatch(name):
        findings.append(
            Finding("error", "manifest-name", rel, "Plugin name does not meet Agent Plugins 1.0.0 rules.")
        )
        plugin_name = None
    else:
        plugin_name = name

    for field in ("version", "description", "homepage", "repository", "license"):
        if field in data and not isinstance(data[field], str):
            findings.append(
                Finding("error", "manifest-field-type", rel, f"Manifest field '{field}' must be a string.")
            )

    author = data.get("author")
    if "author" in data:
        if not isinstance(author, dict):
            findings.append(Finding("error", "manifest-author-type", rel, "Author must be an object."))
        else:
            for field in sorted(set(author) - AUTHOR_FIELDS):
                findings.append(
                    Finding("error", "manifest-author-field", rel, f"Unknown author field: {field}.")
                )
            if any(not isinstance(value, str) for value in author.values()):
                findings.append(
                    Finding("error", "manifest-author-type", rel, "Every author value must be a string.")
                )

    keywords = data.get("keywords")
    if "keywords" in data and (
        not isinstance(keywords, list) or any(not isinstance(value, str) for value in keywords)
    ):
        findings.append(
            Finding("error", "manifest-keywords-type", rel, "Keywords must be an array of strings.")
        )

    extensions = data.get("extensions")
    if "extensions" in data:
        if not isinstance(extensions, dict):
            findings.append(Finding("error", "manifest-extensions-type", rel, "Extensions must be an object."))
        else:
            for namespace, value in extensions.items():
                if not isinstance(namespace, str) or not EXTENSION_NAMESPACE_RE.fullmatch(namespace):
                    findings.append(
                        Finding(
                            "error",
                            "manifest-extension-namespace",
                            rel,
                            f"Extension namespace '{namespace}' is not a reverse-domain identifier.",
                        )
                    )
                if not isinstance(value, dict):
                    findings.append(
                        Finding(
                            "error",
                            "manifest-extension-value",
                            rel,
                            f"Extension '{namespace}' must contain an object.",
                        )
                    )
    return plugin_name, findings


def _link_target(raw: str) -> str | None:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        value = value[1 : value.index(">")]
    elif " " in value:
        value = value.split(" ", 1)[0]
    value = unquote(value).strip()
    if not value or value.startswith("#"):
        return None
    parsed = urlparse(value)
    if parsed.scheme or value.startswith("//"):
        return None
    return value.split("#", 1)[0].split("?", 1)[0]


def _audit_skill_links(skill_dir: Path, plugin_root: Path) -> list[Finding]:
    skill_path = skill_dir / "SKILL.md"
    rel = _relative(skill_path, plugin_root)
    try:
        text = skill_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return [Finding("error", "skill-read", rel, str(exc))]
    findings: list[Finding] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        target_text = _link_target(match.group(1))
        if target_text is None:
            continue
        target = skill_dir / target_text.replace("/", os.sep)
        if not _inside(target, skill_dir):
            findings.append(
                Finding("error", "skill-link-escape", rel, f"Local link escapes the skill directory: {target_text}.")
            )
        elif not target.exists():
            findings.append(
                Finding("error", "skill-link-missing", rel, f"Local link does not exist: {target_text}.")
            )
    return findings


def _audit_skills(root: Path) -> list[Finding]:
    skills = root / "skills"
    link = _symlink_component(skills, root)
    if link is not None:
        return [Finding("error", "package-link", _relative(link, root), "Refusing to traverse a symbolic link in the package.")]
    if not skills.exists():
        return []
    if not skills.is_dir():
        return [Finding("error", "skills-kind", "skills", "skills must be a directory.")]

    findings: list[Finding] = []
    discovered: set[Path] = set()
    for child in sorted(skills.iterdir(), key=lambda path: path.name.lower()):
        skill_path = child / "SKILL.md"
        link = _symlink_component(child, root) or _symlink_component(skill_path, root)
        if link is not None:
            findings.append(
                Finding("error", "package-link", _relative(link, root), "Refusing to traverse a symbolic link in the package.")
            )
            continue
        if child.is_dir() and skill_path.is_file():
            discovered.add(skill_path)
            findings.extend(audit_frontmatter(child, root))
            findings.extend(_audit_skill_links(child, root))
            try:
                line_count = len(skill_path.read_text(encoding="utf-8-sig").splitlines())
            except (OSError, UnicodeError):
                line_count = 0
            if line_count > 500:
                findings.append(
                    Finding(
                        "warning",
                        "skill-length",
                        _relative(skill_path, root),
                        f"SKILL.md has {line_count} lines; Agent Skills recommends fewer than 500.",
                    )
                )

    for skill_path in sorted(skills.rglob("SKILL.md")):
        if skill_path not in discovered:
            findings.append(
                Finding(
                    "error",
                    "nested-skill",
                    _relative(skill_path, root),
                    "Agent Plugins discovers skills only in immediate child directories of skills/.",
                )
            )
    return findings


def _valid_plugin_relative(value: str, root: Path) -> bool:
    if not value.startswith("./"):
        return False
    return _inside(root / value[2:].replace("/", os.sep), root)


def _valid_placeholder_path(value: str, root: Path) -> bool:
    if value.startswith("./"):
        return _valid_plugin_relative(value, root)
    for placeholder in ("${PLUGIN_ROOT}", "${PLUGIN_DATA}"):
        if value == placeholder:
            return True
        prefix = placeholder + "/"
        if value.startswith(prefix):
            remainder = value[len(prefix) :]
            return ".." not in PurePosixPath(remainder).parts
    return False


def _is_loopback(hostname: str | None) -> bool:
    if hostname == "localhost":
        return True
    if hostname is None:
        return False
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def _audit_stdio_server(root: Path, rel: str, name: str, server: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    allowed = {"type", "command", "args", "env", "cwd"}
    for field in sorted(set(server) - allowed):
        findings.append(
            Finding("error", "mcp-server-field", rel, f"MCP server '{name}' has unknown field '{field}'.")
        )
    command = server.get("command")
    if not isinstance(command, str) or not command or any(char.isspace() for char in command):
        findings.append(
            Finding("error", "mcp-command", rel, f"MCP server '{name}' command must be one executable token.")
        )
    elif command.startswith("./"):
        if not _valid_plugin_relative(command, root):
            findings.append(
                Finding("error", "mcp-command-path", rel, f"MCP server '{name}' command escapes the plugin root.")
            )
    elif "/" in command or "\\" in command or command.startswith("."):
        findings.append(
            Finding("error", "mcp-command", rel, f"MCP server '{name}' command must be bare or start with './'.")
        )

    args = server.get("args")
    if "args" in server and (not isinstance(args, list) or any(not isinstance(value, str) for value in args)):
        findings.append(Finding("error", "mcp-args", rel, f"MCP server '{name}' args must be strings."))
    env = server.get("env")
    if "env" in server:
        if not isinstance(env, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in env.items()):
            findings.append(Finding("error", "mcp-env", rel, f"MCP server '{name}' env must map strings to strings."))
        elif {"PLUGIN_ROOT", "PLUGIN_DATA"} & set(env):
            findings.append(
                Finding("error", "mcp-env-reserved", rel, f"MCP server '{name}' cannot set PLUGIN_ROOT or PLUGIN_DATA.")
            )
    cwd = server.get("cwd")
    if "cwd" in server and (not isinstance(cwd, str) or not _valid_placeholder_path(cwd, root)):
        findings.append(
            Finding("error", "mcp-cwd", rel, f"MCP server '{name}' cwd is not a valid portable path.")
        )
    return findings


def _audit_http_server(rel: str, name: str, server: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    allowed = {"type", "url", "headers"}
    for field in sorted(set(server) - allowed):
        findings.append(
            Finding("error", "mcp-server-field", rel, f"MCP server '{name}' has unknown field '{field}'.")
        )
    url = server.get("url")
    parsed = urlparse(url) if isinstance(url, str) else None
    if parsed is None or parsed.scheme not in {"http", "https"} or not parsed.hostname:
        findings.append(Finding("error", "mcp-url", rel, f"MCP server '{name}' URL must be absolute HTTP or HTTPS."))
    else:
        if parsed.username is not None or parsed.password is not None or parsed.fragment:
            findings.append(
                Finding("error", "mcp-url", rel, f"MCP server '{name}' URL cannot contain credentials or a fragment.")
            )
        if parsed.scheme == "http" and not _is_loopback(parsed.hostname):
            findings.append(
                Finding("error", "mcp-url-https", rel, f"MCP server '{name}' must use HTTPS outside loopback.")
            )

    headers = server.get("headers")
    if "headers" in server:
        if not isinstance(headers, dict) or any(
            not isinstance(key, str) or not isinstance(value, str) for key, value in headers.items()
        ):
            findings.append(
                Finding("error", "mcp-headers", rel, f"MCP server '{name}' headers must map strings to strings.")
            )
        else:
            lowered = [key.lower() for key in headers]
            if len(lowered) != len(set(lowered)):
                findings.append(
                    Finding("error", "mcp-header-duplicate", rel, f"MCP server '{name}' repeats a header name.")
                )
            if any("\r" in key or "\n" in key or "\r" in value or "\n" in value for key, value in headers.items()):
                findings.append(
                    Finding("error", "mcp-header-format", rel, f"MCP server '{name}' has an invalid header field.")
                )
            if SECRET_HEADER_NAMES & set(lowered):
                findings.append(
                    Finding("error", "mcp-secret-header", rel, f"MCP server '{name}' embeds a credential header.")
                )
    return findings


def _audit_mcp(root: Path) -> list[Finding]:
    path = root / "mcp.json"
    link = _symlink_component(path, root)
    if link is not None:
        return [Finding("error", "package-link", _relative(link, root), "Refusing to traverse a symbolic link in the package.")]
    if not path.exists():
        return []
    rel = _relative(path, root)
    if not path.is_file():
        return [Finding("error", "mcp-kind", rel, "mcp.json must be a regular file.")]
    data, read_finding = _read_json(path)
    if read_finding is not None:
        return [Finding(read_finding.severity, read_finding.code, rel, read_finding.message, read_finding.line)]
    if not isinstance(data, dict):
        return [Finding("error", "mcp-type", rel, "mcp.json must contain a JSON object.")]

    findings: list[Finding] = []
    for field in sorted(set(data) - {"$schema", "mcpServers"}):
        findings.append(Finding("error", "mcp-top-field", rel, f"Unknown mcp.json field: {field}."))
    if data.get("$schema") != MCP_SCHEMA:
        findings.append(Finding("error", "mcp-schema", rel, f"$schema must be {MCP_SCHEMA}."))
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        findings.append(Finding("error", "mcp-servers-type", rel, "mcpServers must be an object."))
        return findings

    for name, server in servers.items():
        if not isinstance(name, str) or not isinstance(server, dict):
            findings.append(Finding("error", "mcp-server-type", rel, "Each MCP server must be a named object."))
            continue
        transport = server.get("type")
        if transport == "stdio":
            findings.extend(_audit_stdio_server(root, rel, name, server))
        elif transport in {"streamable-http", "sse"}:
            findings.extend(_audit_http_server(rel, name, server))
        else:
            findings.append(
                Finding("error", "mcp-transport", rel, f"MCP server '{name}' has an unsupported transport.")
            )
    return findings


def _client_only_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for name in sorted(CLIENT_ONLY_NAMES):
        path = root / name
        link = _symlink_component(path, root)
        if link is not None:
            findings.append(
                Finding("error", "package-link", _relative(link, root), "Refusing to traverse a symbolic link in the package.")
            )
            continue
        if path.exists():
            findings.append(
                Finding(
                    "info",
                    "client-only-artifact",
                    _relative(path, root),
                    f"'{name}' is a client compatibility artifact, not an Agent Plugins v1 component.",
                )
            )
    return findings


def _name_from_compatibility_manifest(root: Path, source_types: tuple[str, ...]) -> str | None:
    candidates: list[Path] = []
    if "codex" in source_types:
        candidates.append(root / ".codex-plugin" / "plugin.json")
    if "claude" in source_types:
        candidates.append(root / ".claude-plugin" / "plugin.json")
    for path in candidates:
        data, _ = _read_json(path)
        if isinstance(data, dict) and isinstance(data.get("name"), str):
            return data["name"]
    return None


def audit_path(path: Path) -> AuditReport:
    root = path.resolve(strict=False)
    if not root.is_dir():
        return AuditReport(
            root=root,
            source_types=(),
            findings=[Finding("error", "root-kind", str(root), "Audit target must be a directory.")],
        )

    source_types = detect_source_types(root)
    findings: list[Finding] = []
    plugin_name: str | None = None

    if not source_types:
        findings.append(
            Finding("error", "unrecognized-source", ".", "No Agent Plugin, Codex plugin, Claude plugin, or Agent Skill was found.")
        )

    manifest = root / "plugin.json"
    manifest_link = _symlink_component(manifest, root)
    if manifest_link is not None:
        findings.append(
            Finding("error", "package-link", _relative(manifest_link, root), "Refusing to traverse a symbolic link in the package.")
        )
    elif manifest.exists():
        if not manifest.is_file():
            findings.append(Finding("error", "manifest-kind", "plugin.json", "plugin.json must be a regular file."))
        else:
            data, read_finding = _read_json(manifest)
            if read_finding is not None:
                findings.append(
                    Finding(read_finding.severity, read_finding.code, "plugin.json", read_finding.message, read_finding.line)
                )
            else:
                plugin_name, manifest_findings = _audit_manifest(root, manifest, data)
                findings.extend(manifest_findings)
    elif any(kind in source_types for kind in ("codex", "claude")):
        findings.append(
            Finding("error", "missing-portable-manifest", "plugin.json", "Portable Agent Plugin manifest is missing.")
        )
        plugin_name = _name_from_compatibility_manifest(root, source_types)

    if source_types == ("agent-skill",):
        findings.extend(audit_frontmatter(root, root))
    else:
        findings.extend(_audit_skills(root))
        findings.extend(_audit_mcp(root))
        findings.extend(_client_only_findings(root))
        findings.extend(_audit_containment(root))

    findings.sort(key=lambda item: (item.path.lower(), item.line or 0, item.severity, item.code))
    return AuditReport(root=root, source_types=source_types, findings=findings, plugin_name=plugin_name)
