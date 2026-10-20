import importlib.util
import json
import os
import stat
from pathlib import Path
import re
import shutil
import time
import uuid
import unittest
import tomllib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("template", ROOT / "scripts/template.py")
template = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template)


class TemplateTests(unittest.TestCase):
    def setUp(self):
        # mkdir inherits workspace ACLs; tempfile's restrictive mode can fail in
        # managed Windows sandboxes even when the workspace itself is writable.
        self.root = ROOT.parent / ("template-test-" + uuid.uuid4().hex)
        self.root.mkdir()
        self.target = self.root / "consumer"

    def tearDown(self):
        resolved = self.root.resolve()
        self.assertEqual(resolved.parent, ROOT.parent.resolve())
        self.assertTrue(resolved.name.startswith("template-test-"))
        for attempt in range(6):
            try:
                shutil.rmtree(resolved, onerror=self._make_writable)
                break
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.5 * (attempt + 1))

    @staticmethod
    def _make_writable(func, path, _exc):
        # git packs are read-only on Windows; clear the flag and retry once
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def install(self, **kw):
        return template.install(ROOT, self.target, ["claude", "codex"], ["base"], **kw)

    def test_catalog_and_native_formats(self):
        config, output = template.render(ROOT, ["claude", "codex"], ["base"])
        self.assertEqual(len(config["roles"]), 28)
        self.assertEqual(len(config["actions"]), 11)
        self.assertEqual(sum(p.startswith(".codex/agents/") for p in output), 28)
        self.assertEqual(sum(p.startswith(".claude/commands/") for p in output), 11)
        for path, data in output.items():
            if path.endswith(".toml"):
                value = tomllib.loads(data.decode())
                if path.startswith(".codex/agents/"):
                    self.assertTrue({"name", "description", "developer_instructions"} <= value.keys())
                    self.assertIn("ALWAYS orchestrates", value["developer_instructions"])
            elif path.endswith(".json"):
                json.loads(data)

    def test_github_projects_board(self):
        _, output = template.render(ROOT, ["claude", "codex"], ["base", "github-projects"])
        contract = output[".engineering/workflow/github-projects.md"].decode()
        for state in ("open", "pending", "in-progress", "in-review", "rejected", "blocked", "completed", "accepted", "closed"):
            self.assertIn(f"| {state} |", contract)
        self.assertIn("Never use Done", contract)
        self.assertIn(".engineering/templates/issue.md", output)
        self.assertIn(".engineering/integrations/github-projects/setup-project.sh", output)
        self.assertFalse(any("integrations/vscode" in p or "workflow/kanban" in p for p in output))
        with self.assertRaisesRegex(ValueError, "renamed to github-projects"):
            template.render(ROOT, ["claude"], ["base", "kanban"])

    def test_dry_run_and_idempotence(self):
        self.install(dry_run=True)
        self.assertFalse(self.target.exists())
        self.assertTrue(self.install()["write"])
        manifest = self.target / ".engineering/manifest.json"
        stamp = manifest.stat().st_mtime_ns
        self.assertEqual(self.install()["write"], [])
        self.assertEqual(manifest.stat().st_mtime_ns, stamp)
        template.check(ROOT, self.target)

    def test_complete_preflight_conflict(self):
        self.target.mkdir()
        (self.target / "CLAUDE.md").write_text("existing rules")
        before = list(self.target.rglob("*"))
        with self.assertRaisesRegex(ValueError, "conflict"):
            self.install()
        self.assertEqual(list(self.target.rglob("*")), before)
        self.assertEqual((self.target / "CLAUDE.md").read_text(), "existing rules")

    def test_existing_codex_config_is_not_merged(self):
        (self.target / ".codex").mkdir(parents=True)
        (self.target / ".codex/config.toml").write_text("[agents]\nenabled = false\n")
        with self.assertRaisesRegex(ValueError, "conflict"):
            self.install()
        self.assertFalse((self.target / "AGENTS.md").exists())

    def test_installed_drift(self):
        self.install()
        (self.target / "AGENTS.md").write_text("manual edit")
        with self.assertRaisesRegex(ValueError, "drift"):
            self.install(sync=True)
        with self.assertRaisesRegex(ValueError, "drift"):
            template.check(ROOT, self.target)

    def test_manifest_traversal(self):
        self.install()
        p = self.target / ".engineering/manifest.json"
        data = json.loads(p.read_text())
        data["files"]["../outside"] = "bad"
        p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "unsafe"):
            self.install(sync=True)

    def test_manifest_cannot_claim_unrelated_or_git_files(self):
        self.install()
        for name in ("unrelated.txt", ".git/config"):
            unrelated = self.target / name
            unrelated.parent.mkdir(parents=True, exist_ok=True)
            unrelated.write_bytes(b"user owned")
            manifest_path = self.target / ".engineering/manifest.json"
            original = manifest_path.read_bytes()
            manifest = json.loads(original)
            manifest["files"][name] = template.digest(unrelated.read_bytes())
            manifest_path.write_bytes(template.json_bytes(manifest))
            before = {p.relative_to(self.target).as_posix(): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
            with self.assertRaisesRegex(ValueError, "ownership"):
                self.install(sync=True)
            after = {p.relative_to(self.target).as_posix(): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            manifest_path.write_bytes(original)

    def test_source_target_overlap_and_profile_traversal(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            template.install(ROOT, ROOT, ["codex"], ["base"])
        with self.assertRaisesRegex(ValueError, "invalid profile"):
            template.render(ROOT, ["codex"], ["../base"])

    def test_workspace_root_may_contain_the_template_checkout(self):
        workspace = self.root / "workspace"
        checkout = workspace / "engineering-template"
        shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns("__pycache__", ".git"))
        before = {p.relative_to(checkout).as_posix(): p.read_bytes() for p in checkout.rglob("*") if p.is_file()}
        result = template.install(checkout, workspace, ["claude", "codex"], ["base"])
        self.assertTrue(result["write"])
        self.assertTrue((workspace / ".engineering/manifest.json").is_file())
        self.assertEqual(before, {p.relative_to(checkout).as_posix(): p.read_bytes() for p in checkout.rglob("*") if p.is_file()})
        template.check(checkout, workspace)
        with self.assertRaisesRegex(ValueError, "separate"):
            template.install(checkout, checkout / "child", ["codex"], ["base"])

    def test_sync_retires_a_file_the_template_stopped_shipping(self):
        source = self.root / "source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns("__pycache__", ".git"))
        self.target.mkdir()
        template.install(source, self.target, ["claude"], ["base"])
        old = ".engineering/templates/install-registry.md"
        (self.target / old).write_bytes(b"legacy template")
        manifest_path = self.target / ".engineering/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["files"][old] = template.digest(b"legacy template")
        manifest_path.write_text(json.dumps(manifest))
        result = template.install(source, self.target, ["claude"], ["base"], sync=True)
        self.assertIn(old, result["remove"])
        self.assertFalse((self.target / old).exists())
        # an unrelated path is still refused
        manifest = json.loads(manifest_path.read_text())
        manifest["files"]["notes.txt"] = template.digest(b"x")
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "ownership"):
            template.check(source, self.target)

    def test_profile_conflicts(self):
        with self.assertRaisesRegex(ValueError, "conflicting profile"):
            template.render(ROOT, ["codex"], ["base", "hosting-managed", "vps-k3s"])

    def test_safe_source_update(self):
        import shutil
        source = self.root / "source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns("__pycache__"))
        template.install(source, self.target, ["codex"], ["base"])
        changed = source / "core/roles/backend.md"
        changed.write_bytes(changed.read_bytes() + b"\nSource update.\n")
        with self.assertRaisesRegex(ValueError, "source update"):
            template.check(source, self.target)
        result = template.install(source, self.target, ["codex"], ["base"], sync=True)
        self.assertIn(".engineering/roles/backend.md", result["write"])
        template.check(source, self.target)

    def test_symlink_ancestor(self):
        real = self.root / "real"
        real.mkdir()
        link = self.root / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation unavailable; Windows junction tested separately")
        with self.assertRaisesRegex(ValueError, "symlink|reparse"):
            template.install(ROOT, link / "child", ["codex"], ["base"])

    def test_junction_ancestor(self):
        import os
        import subprocess
        if os.name != "nt":
            self.skipTest("Windows junction test")
        real = self.root / "real"
        real.mkdir()
        link = self.root / "junction"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(real)], capture_output=True)
        if result.returncode:
            self.skipTest("junction creation unavailable")
        try:
            with self.assertRaisesRegex(ValueError, "reparse"):
                template.install(ROOT, link / "child", ["codex"], ["base"])
        finally:
            link.rmdir()

    def test_package_layout(self):
        _, output = template.render(ROOT, ["claude"], ["base"], package=True)
        self.assertIn(".claude-plugin/plugin.json", output)
        self.assertIn(".claude-plugin/marketplace.json", output)
        self.assertIn("BOOTSTRAP.md", output)
        self.assertNotIn("CLAUDE.md", output)
        self.assertEqual(sum(p.startswith("agents/") for p in output), 28)

    def test_every_native_child_loads_project_context(self):
        for package, providers in ((False, ["claude", "codex"]), (True, ["claude"])):
            _, output = template.render(ROOT, providers, ["base"], package=package)
            children = {p: d for p, d in output.items() if p.startswith((".codex/agents/", ".claude/agents/", "agents/"))}
            self.assertEqual(len(children), 28 if package else 56)
            for path, data in children.items():
                text = data.decode()
                for required in (".engineering/project.json", ".engineering/catalog.json", ".engineering/profiles/<id>.json", "Do not rely on inherited context"):
                    self.assertIn(required, text, path)
            for path, data in output.items():
                if path in ("AGENTS.md", "CLAUDE.md", "BOOTSTRAP.md") or path.startswith(("commands/", ".claude/commands/")) or (path.startswith(".agents/skills/") and "drawio" not in path):
                    self.assertIn(".engineering/catalog.json", data.decode(), path)
                    self.assertIn(".engineering/project.json", data.decode(), path)

    def test_claude_tools_commands_and_metadata(self):
        _, output = template.render(ROOT, ["claude"], ["base"], package=True)
        for name in ("security", "reviewer"):
            text = output[f"agents/{name}.md"].decode()
            tools = next(line for line in text.splitlines() if line.startswith("tools:"))
            self.assertIn("Bash", tools)
            self.assertNotIn("Write", tools)
            self.assertNotIn("Edit", tools)
            self.assertIn("safe non-mutating probes", text)
        architect = output["agents/architect.md"].decode()
        self.assertNotIn("Bash", next(line for line in architect.splitlines() if line.startswith("tools:")))
        for path, data in output.items():
            if path.startswith("commands/"):
                lines = data.decode().splitlines()
                self.assertEqual(lines[0], "---")
                self.assertTrue(lines[1].startswith("name: "))
                self.assertTrue(lines[2].startswith("description: "))
                json.loads(lines[2].removeprefix("description: "))
                self.assertEqual(lines[3], "---")
        self.assertIn("author", json.loads(output[".claude-plugin/plugin.json"]))
        self.assertEqual(len(json.loads(output[".claude-plugin/plugin.json"])["agents"]), 28)
        self.assertIn("description", json.loads(output[".claude-plugin/marketplace.json"]))

    def test_plugin_consumer_onboarding_recipe(self):
        import contextlib
        import io
        from unittest.mock import patch
        plugin = self.root / "plugin"
        consumer = self.root / "consumer-project"
        consumer.mkdir()
        template.install(ROOT, plugin, ["claude"], ["base"], package=True)
        onboarding = (ROOT / "adapters/claude/README.md").read_text(encoding="utf-8")
        generated = (plugin / "BOOTSTRAP.md").read_text(encoding="utf-8")
        self.assertEqual((plugin / "PLUGIN_SETUP.md").read_text(encoding="utf-8"), onboarding)
        self.assertIn("PLUGIN_SETUP.md", generated)
        self.assertNotIn("shutil.copytree", generated)
        # Exercise the exact documented, reviewed recipe without a subprocess
        # or a new runtime feature. Runtime CLI never executes adapter code.
        recipe = onboarding.split("@'\n", 1)[1].split("\n'@", 1)[0]
        with patch("sys.argv", ["onboarding", str(plugin), str(consumer)]), contextlib.redirect_stdout(io.StringIO()):
            exec(compile(recipe, "documented-onboarding", "exec"), {"__name__": "__main__"})
        common = consumer / ".engineering"
        self.assertFalse((common / "manifest.json").exists())
        self.assertTrue((plugin / ".engineering/manifest.json").is_file())
        (consumer / "CLAUDE.md").write_bytes((plugin / "BOOTSTRAP.md").read_bytes())
        self.assertTrue((common / "project.json").is_file())
        self.assertTrue((common / "catalog.json").is_file())
        project = json.loads((common / "project.json").read_text())
        for profile in project["profiles"]:
            self.assertTrue((common / "profiles" / f"{profile}.json").is_file())
        for section in ("workflow", "policies", "roles", "actions", "templates", "skills"):
            self.assertTrue(any((common / section).rglob("*")), section)
        for source in (plugin / ".engineering").rglob("*"):
            if source.is_file() and source.name != "manifest.json":
                self.assertEqual(source.read_bytes(), (common / source.relative_to(plugin / ".engineering")).read_bytes())
        self.assertEqual(len(list((plugin / "agents").glob("*.md"))), 28)
        self.assertFalse((consumer / ".claude/agents").exists())
        before = {p.relative_to(consumer).as_posix(): p.read_bytes() for p in consumer.rglob("*") if p.is_file()}
        with patch("sys.argv", ["onboarding", str(plugin), str(consumer)]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            exec(compile(recipe, "documented-onboarding", "exec"), {"__name__": "__main__"})
        self.assertEqual(before, {p.relative_to(consumer).as_posix(): p.read_bytes() for p in consumer.rglob("*") if p.is_file()})

    def test_model_tiers_rendered_per_role(self):
        config, output = template.render(ROOT, ["claude", "codex"], ["base"])
        tiers = config["model_tiers"]
        self.assertEqual({k: v["claude"] for k, v in tiers.items()}, {"deep": "opus", "standard": "sonnet", "light": "haiku"})
        for role in config["roles"]:
            text = output[f".claude/agents/{role['id']}.md"].decode()
            self.assertIn(f"\nmodel: {tiers[role['tier']]['claude']}\n", text, role["id"])
            codex = tomllib.loads(output[f".codex/agents/{role['id']}.toml"].decode())
            self.assertEqual(codex["model_reasoning_effort"], tiers[role["tier"]]["codex_effort"], role["id"])
        by_id = {r["id"]: r for r in config["roles"]}
        for role in ("architect", "security", "cloud", "devsecops-infra", "privacy-compliance"):
            self.assertEqual(by_id[role]["tier"], "deep", role)
        for role in ("lay-user", "scribe"):
            self.assertEqual(by_id[role]["tier"], "light", role)
        for role in ("qa", "reviewer", "backend", "frontend-senior", "ux-designer", "product-owner"):
            self.assertEqual(by_id[role]["tier"], "standard", role)
        for gate in ("qa", "security", "reviewer", "privacy-compliance"):
            self.assertNotEqual(by_id[gate]["tier"], "light", gate)

    def test_tier_overrides_are_validated_persisted_and_synced(self):
        _, output = template.render(ROOT, ["claude"], ["base"], tiers={"reviewer": "deep", "scribe": "standard"})
        self.assertIn("\nmodel: opus\n", output[".claude/agents/reviewer.md"].decode())
        self.assertIn("\nmodel: sonnet\n", output[".claude/agents/scribe.md"].decode())
        self.assertEqual(json.loads(output[".engineering/project.json"])["tiers"], {"reviewer": "deep", "scribe": "standard"})
        for bad in ({"qa": "light"}, {"privacy-compliance": "light"}, {"nope": "deep"}, {"qa": "ultra"}):
            with self.assertRaises(ValueError, msg=str(bad)):
                template.render(ROOT, ["claude"], ["base"], tiers=bad)
        template.install(ROOT, self.target, ["claude"], ["base"], tiers={"architect": "standard"})
        template.check(ROOT, self.target)
        manifest = json.loads((self.target / ".engineering/manifest.json").read_text())
        self.assertEqual(manifest["tiers"], {"architect": "standard"})
        self.assertIn("\nmodel: sonnet\n", (self.target / ".claude/agents/architect.md").read_text())
        manifest["tiers"] = {"qa": "light"}
        (self.target / ".engineering/manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            template.check(ROOT, self.target)

    def test_product_and_ux_team_roles(self):
        config, output = template.render(ROOT, ["claude", "codex"], ["base", "product-team", "polyrepo"])
        roles = {r["id"]: r for r in config["roles"]}
        for role in ("product-owner", "ux-researcher", "ux-designer", "ui-designer", "brand-strategist", "marketing", "frontend-senior", "privacy-compliance", "lay-user", "scribe"):
            self.assertIn(role, roles)
            self.assertIn(f".engineering/roles/{role}.md", output)
            self.assertTrue(roles[role]["description"].startswith("Use "), role)
        # lay users are read-only, weakest tier, and never given code access
        lay = output[".claude/agents/lay-user.md"].decode()
        tools = next(line for line in lay.splitlines() if line.startswith("tools:"))
        self.assertEqual(tools, "tools: Read, Grep, Glob")
        self.assertIn("model: haiku", lay)
        self.assertEqual(tomllib.loads(output[".codex/agents/lay-user.toml"].decode())["sandbox_mode"], "read-only")
        # authors can write artifacts but cannot run shell; privacy review is diagnostic and read-only
        for role in ("product-owner", "ux-designer", "ui-designer", "brand-strategist", "marketing", "scribe"):
            tools = next(line for line in output[f".claude/agents/{role}.md"].decode().splitlines() if line.startswith("tools:"))
            self.assertIn("Write", tools, role)
            self.assertNotIn("Bash", tools, role)
        privacy = output[".claude/agents/privacy-compliance.md"].decode()
        self.assertNotIn("Write", next(line for line in privacy.splitlines() if line.startswith("tools:")))
        self.assertIn("LEGAL-REVIEW", privacy)
        frontend = next(line for line in output[".claude/agents/frontend-senior.md"].decode().splitlines() if line.startswith("tools:"))
        self.assertIn("Bash", frontend)
        for action in ("story", "usability", "privacy"):
            self.assertIn(f".claude/commands/{action}.md", output)
            self.assertIn(f".agents/skills/{action}/SKILL.md", output)

    def test_management_workflow_policies_and_templates(self):
        _, output = template.render(ROOT, ["claude"], ["base", "product-team", "polyrepo", "github-projects"])
        for path in ("workflow/staffing.md", "workflow/user-stories.md", "workflow/usability.md", "workflow/polyrepo.md",
                     "policies/models.md", "policies/quality-principles.md", "policies/installations.md",
                     "templates/user-story.md", "templates/staffing.md", "templates/persona.md",
                     "templates/usability-report.md", "templates/decision.md", "templates/registro-instalacoes.md"):
            self.assertIn(f".engineering/{path}", output, path)
        stories = output[".engineering/workflow/user-stories.md"].decode()
        for needle in ("Definition of Ready", "Definition of Done", "Given/When/Then", "INVEST", "Assets and links", "Metadata"):
            self.assertIn(needle, stories)
        usability = output[".engineering/workflow/usability.md"].decode()
        for needle in ("exactly two", "LGPD", "Precedence", "LEGAL-REVIEW", "Guardrails", "dark patterns"):
            self.assertIn(needle.lower(), usability.lower())
        models = output[".engineering/policies/models.md"].decode()
        for needle in ("deep", "standard", "light", "Opus", "Sonnet", "Haiku", "Escalate"):
            self.assertIn(needle, models)
        quality = output[".engineering/policies/quality-principles.md"].decode().lower()
        for needle in ("idempotence", "fault tolerance", "scalability", "reuse"):
            self.assertIn(needle, quality)
        self.assertIn("Type | Single select", output[".engineering/workflow/github-projects.md"].decode())
        self.assertIn("Model tier:", output[".engineering/templates/brief.md"].decode())
        for child in (".claude/agents/architect.md", "CLAUDE.md"):
            self.assertIn("policies/models.md", output[child].decode())

    def test_template_is_project_neutral(self):
        banned = re.compile(r"\b(aura|aura-fit|teotonio|allankltsn)\b", re.IGNORECASE)
        offenders = []
        for path in ROOT.rglob("*"):
            rel = path.relative_to(ROOT)
            if ".git" in rel.parts or "__pycache__" in rel.parts or not path.is_file() or path.suffix in (".png", ".pyc"):
                continue
            if rel.as_posix() in ("tests/test_template.py", "integrations/plugins/curated.json"):
                continue
            if banned.search(path.read_text(encoding="utf-8", errors="ignore")):
                offenders.append(rel.as_posix())
        self.assertEqual(offenders, [])

    def test_every_installation_must_be_registered(self):
        _, output = template.render(ROOT, ["claude", "codex"], ["base"])
        path = "docs/operations/registro-instalacoes.md"
        policy = output[".engineering/policies/installations.md"].decode()
        self.assertIn("Mandatory rule", policy)
        self.assertIn(path, policy)
        self.assertIn(".engineering/templates/registro-instalacoes.md", output)
        for name in ("CLAUDE.md", "AGENTS.md", ".claude/agents/backend.md", ".codex/agents/lay-user.toml", ".claude/commands/qa.md"):
            self.assertIn(path, output[name].decode(), name)

    def test_curated_plugins_are_documented_not_installed(self):
        curated = json.loads((ROOT / "integrations/plugins/curated.json").read_text(encoding="utf-8"))
        self.assertEqual(curated["status"], "recommended_not_installed")
        for market in curated["marketplaces"]:
            self.assertTrue(market["repo"].startswith("https://github.com/"))
            self.assertIsInstance(market["stars"], int)
            self.assertTrue(market["add"].startswith("claude plugin marketplace add "))
            for plugin in market["plugins"]:
                self.assertTrue(plugin["install"].startswith("claude plugin install "))
        _, output = template.render(ROOT, ["claude", "codex"], ["base"])
        self.assertFalse(any(p.startswith(".claude/plugins") or "node_modules" in p for p in output))


if __name__ == "__main__":
    unittest.main()
