#!/usr/bin/env python3
"""Portable engineering template renderer; Python 3.11+, standard library only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tomllib

SOURCE = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z][a-z0-9-]*\Z")
COMMON = """The main session ALWAYS orchestrates: consult and delegate implementation and specialized judgments. Separate expertise from task function. Never approve your own work. Independent QA, conformity review, technical review and security must report explicitly on the same reproducible snapshot. Return stable finding IDs to the author; require correction evidence and independent confirmation, and revalidate affected gates after every delta. Silence, timeout, disagreement and exhausted budget never approve. Human acceptance is separate. Without delegation, coordinate verified independent sessions or report blocked; the main session never substitutes for specialists. Read .engineering/workflow/ and .engineering/policies/ explicitly relative to the project root before work. Respect actual permissions; textual scope is not a filesystem sandbox."""
COMMON += " Start in the consuming project root. Before any task, explicitly read .engineering/project.json, .engineering/catalog.json, and each .engineering/profiles/<id>.json selected by project.json, then the relevant role/action contracts. Do not rely on inherited context or automatic discovery. For plugin use, the consuming project must have the shared .engineering tree installed or its verified location explicitly supplied; missing project context blocks execution."


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(path):
    """Reject links/reparse points in every existing ancestor, including junctions."""
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(f"symlink forbidden: {item}")
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"reparse point/junction forbidden: {item}")
    return path


def relative(value):
    p = Path(value)
    if not value or p.is_absolute() or ".." in p.parts or "\\" in value or ":" in value:
        raise ValueError(f"unsafe relative path: {value}")
    return p


def load_source(source):
    source = safe_path(source)
    files = {}
    for directory in ("core", "profiles", "adapters", "integrations"):
        root = safe_path(source / directory)
        if directory == "integrations" and not root.exists():
            continue
        if not root.is_dir():
            raise ValueError(f"missing source directory: {root}")
        for current, dirs, names in os.walk(root, followlinks=False):
            for name in dirs + names:
                safe_path(Path(current) / name)
            for name in names:
                p = Path(current) / name
                files[p.relative_to(source).as_posix()] = p.read_bytes()
    config = json.loads(safe_path(source / "template.json").read_text(encoding="utf-8"))
    if config.get("name") != "engineering-template" or not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.-]+)?", str(config.get("version", ""))):
        raise ValueError("unsupported template name/version")
    for kind in ("roles", "actions"):
        ids = [x["id"] for x in config[kind]]
        if len(ids) != len(set(ids)) or any(not ID.fullmatch(x) for x in ids):
            raise ValueError(f"invalid/duplicate {kind} IDs")
    roles = {x["id"] for x in config["roles"]}
    expected_roles = {"architect", "backend", "python", "aws", "hosting", "qa", "security", "kubernetes", "docker", "cicd", "devsecops-infra", "finops", "sre", "cloud", "ingress", "orchestration", "deployment", "reviewer"}
    if roles != expected_roles or len(config["actions"]) != 8:
        raise ValueError("catalog requires all 18 roles and 8 actions")
    for section in ("workflow", "policies", "templates"):
        if not any(p.startswith(f"core/{section}/") and p.endswith(".md") for p in files):
            raise ValueError(f"missing core {section}")
    for role in config["roles"]:
        if role["mode"] not in ("implementer", "qa", "review", "diagnostic"):
            raise ValueError("invalid role mode")
        body = files[f"core/roles/{role['id']}.md"].decode("utf-8")
        if body.startswith("---"):
            raise ValueError("neutral roles must not contain provider frontmatter")
    for action in config["actions"]:
        if action["role"] not in roles:
            raise ValueError("unknown action role")
        files[f"core/actions/{action['id']}.md"]
    for skill in config["skills"]:
        if not ID.fullmatch(skill):
            raise ValueError("invalid skill ID")
        files[f"core/skills/{skill}/SKILL.md"]
    for name, data in files.items():
        if name.endswith(".json"):
            value = json.loads(data)
            if name.startswith("profiles/"):
                profile_id = Path(name).stem
                if not ID.fullmatch(profile_id) or value.get("id") != profile_id or not isinstance(value.get("instructions"), (str, list)):
                    raise ValueError(f"invalid profile: {name}")
                for conflict in value.get("conflicts", []):
                    if not ID.fullmatch(conflict) or f"profiles/{conflict}.json" not in files:
                        raise ValueError(f"invalid profile conflict: {name}")
        if name.endswith(".toml"):
            tomllib.loads(data.decode("utf-8"))
    return source, config, files


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def render(source, providers, profiles, package=False):
    source, config, files = load_source(source)
    if not providers or set(providers) - {"claude", "codex"}:
        raise ValueError("providers must be claude,codex")
    if package and providers != ["claude"]:
        raise ValueError("package supports only claude")
    selected = {}
    for name in profiles:
        if not ID.fullmatch(name):
            raise ValueError("invalid profile ID")
        value = json.loads(files[f"profiles/{name}.json"])
        if value["id"] != name:
            raise ValueError("profile ID mismatch")
        selected[name] = value
    for name, value in selected.items():
        if set(value.get("conflicts", [])) & selected.keys():
            raise ValueError(f"conflicting profile: {name}")
    output = {".engineering/" + name[5:]: data for name, data in files.items() if name.startswith("core/")}
    output[".engineering/catalog.json"] = json_bytes(config)
    for name, data in files.items():
        if name.startswith("integrations/"):
            output[".engineering/" + name] = data
    for name, value in selected.items():
        output[f".engineering/profiles/{name}.json"] = json_bytes(value)
    output[".engineering/project.json"] = json_bytes({"providers": providers, "profiles": profiles})
    bootstrap = ("# Engineering bootstrap\n\nStart this session in the project root.\n\n" + COMMON + "\n\nExplicitly read .engineering/project.json, selected .engineering/profiles/*.json, then the relevant .engineering/roles/<id>.md and .engineering/actions/<id>.md. Do not assume .engineering discovery.\n")
    for provider in providers:
        if not package:
            output["CLAUDE.md" if provider == "claude" else "AGENTS.md"] = bootstrap.encode()
        for role in config["roles"]:
            name = role["id"]
            body = COMMON + "\n\n" + files[f"core/roles/{name}.md"].decode("utf-8")
            if role["mode"] == "qa":
                body += "\nWrite only explicitly authorized probes/tests; workspace-write does not enforce path scope. Do not edit the implementation under review.\n"
            if provider == "codex":
                fields = {"name": name, "description": role["description"], "developer_instructions": body}
                if role["mode"] in ("review", "diagnostic"):
                    fields["sandbox_mode"] = "read-only"
                elif role["mode"] == "qa":
                    fields["sandbox_mode"] = "workspace-write"
                output[f".codex/agents/{name}.toml"] = ("\n".join(f"{k} = {json.dumps(v, ensure_ascii=False)}" for k, v in fields.items()) + "\n").encode()
            else:
                tools = "Read, Grep, Glob"
                if role["mode"] == "diagnostic" or name in ("security", "reviewer"):
                    tools += ", Bash"
                    body += "\nBash is authorized only for read-only inspection and safe non-mutating probes within the brief (for example git diff). Do not mutate implementation, production, configuration or data. This textual restriction is not enforced filesystem isolation.\n"
                elif role["mode"] in ("implementer", "qa"):
                    tools = "Read, Write, Edit, Grep, Glob, Bash"
                prefix = "agents" if package else ".claude/agents"
                output[f"{prefix}/{name}.md"] = (f"---\nname: {name}\ndescription: {json.dumps(role['description'], ensure_ascii=False)}\ntools: {tools}\n---\n\n" + body).encode()
        for action in config["actions"]:
            name = action["id"]
            body = COMMON + "\n\n" + files[f"core/actions/{name}.md"].decode("utf-8")
            if provider == "codex":
                path = f".agents/skills/{name}/SKILL.md"
                body = f"---\nname: {name}\ndescription: {json.dumps(action['description'], ensure_ascii=False)}\n---\n\n" + body
            else:
                path = f"{'commands' if package else '.claude/commands'}/{name}.md"
                body = f"---\nname: {name}\ndescription: {json.dumps(action['description'], ensure_ascii=False)}\n---\n\n" + body
            output[path] = body.encode()
        for name in config["skills"]:
            prefix = "skills" if package else (".claude/skills" if provider == "claude" else ".agents/skills")
            for path, data in files.items():
                marker = f"core/skills/{name}/"
                if path.startswith(marker):
                    output[f"{prefix}/{name}/{path[len(marker):]}"] = data
        if provider == "codex":
            output[".codex/config.toml"] = b"[agents]\nenabled = true\n"
    if package:
        output[".claude-plugin/plugin.json"] = json_bytes({"name": config["name"], "version": config["version"], "description": "Portable engineering specialist contracts", "author": {"name": "Engineering template maintainers"}, "agents": [f"./agents/{r['id']}.md" for r in config["roles"]], "commands": "./commands", "skills": ["./skills"]})
        output[".claude-plugin/marketplace.json"] = json_bytes({"name": "engineering-template-marketplace", "description": "Portable engineering contracts and provider adapters", "owner": {"name": "Engineering template maintainers"}, "plugins": [{"name": config["name"], "source": "./", "description": "Portable engineering specialist contracts"}]})
        output["PLUGIN_SETUP.md"] = files["adapters/claude/README.md"]
        output["BOOTSTRAP.md"] = ("# Plugin runtime precondition\n\nBefore starting work, the consuming project must already contain the complete shared .engineering tree exported from this package, excluding its root manifest.json. First-use onboarding is documented separately in PLUGIN_SETUP.md in the plugin package; these setup steps are not runtime instructions. The exported consumer contracts are not managed by check/sync.\n\n" + bootstrap).encode()
    return config, output


def install(source, target, providers, profiles, dry_run=False, sync=False, package=False):
    source = safe_path(source)
    target = safe_path(target)
    if target == source or source in target.parents or target in source.parents:
        raise ValueError("source and target must be separate, non-nested trees")
    config, output = render(source, providers, profiles, package)
    manifest_path = safe_path(target / ".engineering/manifest.json")
    old = None
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_manifest(source, old)
    if sync and old is None:
        raise ValueError("sync requires installed manifest")
    previous = old.get("files", {}) if old else {}
    for name in set(output) | set(previous):
        relative(name)
        dest = safe_path(target / name)
        if dest.exists():
            if not dest.is_file():
                raise ValueError(f"not a file: {dest}")
            actual = digest(dest.read_bytes())
            if name in previous and actual != previous[name]:
                raise ValueError(f"installed drift: {name}")
            if name not in previous and (name not in output or dest.read_bytes() != output[name]):
                raise ValueError(f"preexisting conflict: {name}")
        elif name in previous:
            raise ValueError(f"missing managed file: {name}")
        for parent in dest.parents:
            if parent == target.parent:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"parent is not directory: {parent}")
    # Complete preflight before any filesystem mutation, including dry run.
    manifest = json_bytes({"name": config["name"], "version": config["version"], "providers": providers, "profiles": profiles, "package": package, "files": {p: digest(v) for p, v in output.items()}})
    changes = [p for p, data in output.items() if not (target / p).exists() or (target / p).read_bytes() != data]
    removals = sorted(set(previous) - set(output))
    if dry_run:
        return {"write": changes, "remove": removals, "dry_run": True}
    for name in removals:
        (target / name).unlink()
    for name in changes:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(output[name])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    if not manifest_path.exists() or manifest_path.read_bytes() != manifest:
        manifest_path.write_bytes(manifest)
    return {"write": changes, "remove": removals, "dry_run": False}


def validate_manifest(source, manifest):
    """Manifest metadata is untrusted and cannot expand managed ownership."""
    if not isinstance(manifest, dict) or manifest.get("name") != "engineering-template":
        raise ValueError("invalid manifest identity")
    if not isinstance(manifest.get("version"), str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.-]+)?", manifest["version"]):
        raise ValueError("invalid manifest version")
    for key in ("providers", "profiles"):
        if not isinstance(manifest.get(key), list) or not all(isinstance(x, str) and ID.fullmatch(x) for x in manifest[key]):
            raise ValueError(f"invalid manifest {key}")
    if not isinstance(manifest.get("package", False), bool):
        raise ValueError("invalid manifest package flag")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("invalid manifest files")
    _, project = render(source, ["claude", "codex"], ["base"])
    _, plugin = render(source, ["claude"], ["base"], package=True)
    allowed = set(project) | set(plugin)
    _, _, source_files = load_source(source)
    allowed.update(".engineering/" + p for p in source_files if p.startswith("profiles/"))
    for name, value in files.items():
        if not isinstance(name, str):
            raise ValueError("invalid manifest path")
        relative(name)
        if name not in allowed:
            raise ValueError(f"manifest ownership violation: {name}")
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise ValueError(f"invalid manifest hash: {name}")
    # Validate selected provider/profile semantics before trusting metadata.
    render(source, manifest["providers"], manifest["profiles"], manifest.get("package", False))


def check(source, target=None):
    config, output = render(source, ["claude", "codex"], ["base"])
    for name, data in output.items():
        if name.endswith(".toml"):
            tomllib.loads(data.decode())
        if name.endswith(".json"):
            json.loads(data)
    if target is not None:
        target = safe_path(target)
        manifest = json.loads(safe_path(target / ".engineering/manifest.json").read_text(encoding="utf-8"))
        validate_manifest(source, manifest)
        for name, expected in manifest["files"].items():
            p = safe_path(target / relative(name))
            if not p.is_file() or digest(p.read_bytes()) != expected:
                raise ValueError(f"installed drift: {name}")
        _, desired = render(source, manifest["providers"], manifest["profiles"], manifest.get("package", False))
        if {p: digest(v) for p, v in desired.items()} != manifest["files"]:
            raise ValueError("source update available; run sync")
    return {"valid": True, "roles": len(config["roles"]), "actions": len(config["actions"])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "sync", "check", "doctor", "package"])
    parser.add_argument("--target", type=Path)
    parser.add_argument("--providers", default="claude,codex")
    parser.add_argument("--provider", choices=["claude"])
    parser.add_argument("--profiles", default="base")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = {"python": sys.version.split()[0], "tools": {name: {"path": shutil.which(name), "state": "detected; version/discovery unverified" if shutil.which(name) else "absent"} for name in ("claude", "codex", "git", "rtk", "serena")}, "note": "No installation or commands executed. Provider trust, discovery and isolation require real session probes."}
        elif args.command == "check":
            result = check(SOURCE, args.target)
        else:
            if args.target is None:
                raise ValueError("--target required")
            providers = ["claude"] if args.command == "package" and args.provider == "claude" else args.providers.split(",")
            if args.command == "package" and args.provider != "claude":
                raise ValueError("package requires --provider claude")
            result = install(SOURCE, args.target, providers, args.profiles.split(","), args.dry_run, args.command == "sync", args.command == "package")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
