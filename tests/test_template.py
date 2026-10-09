import importlib.util
import json
from pathlib import Path
import shutil
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
        shutil.rmtree(resolved)

    def install(self, **kw):
        return template.install(ROOT, self.target, ["claude", "codex"], ["base"], **kw)

    def test_catalog_and_native_formats(self):
        config, output = template.render(ROOT, ["claude", "codex"], ["base"])
        self.assertEqual(len(config["roles"]), 18)
        self.assertEqual(len(config["actions"]), 8)
        self.assertEqual(sum(p.startswith(".codex/agents/") for p in output), 18)
        self.assertEqual(sum(p.startswith(".claude/commands/") for p in output), 8)
        for path, data in output.items():
            if path.endswith(".toml"):
                value = tomllib.loads(data.decode())
                if path.startswith(".codex/agents/"):
                    self.assertTrue({"name", "description", "developer_instructions"} <= value.keys())
                    self.assertIn("ALWAYS orchestrates", value["developer_instructions"])
            elif path.endswith(".json"):
                json.loads(data)

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
        self.assertEqual(sum(p.startswith("agents/") for p in output), 18)

    def test_every_native_child_loads_project_context(self):
        for package, providers in ((False, ["claude", "codex"]), (True, ["claude"])):
            _, output = template.render(ROOT, providers, ["base"], package=package)
            children = {p: d for p, d in output.items() if p.startswith((".codex/agents/", ".claude/agents/", "agents/"))}
            self.assertEqual(len(children), 18 if package else 36)
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
        self.assertEqual(len(json.loads(output[".claude-plugin/plugin.json"])["agents"]), 18)
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
        self.assertEqual(len(list((plugin / "agents").glob("*.md"))), 18)
        self.assertFalse((consumer / ".claude/agents").exists())
        before = {p.relative_to(consumer).as_posix(): p.read_bytes() for p in consumer.rglob("*") if p.is_file()}
        with patch("sys.argv", ["onboarding", str(plugin), str(consumer)]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            exec(compile(recipe, "documented-onboarding", "exec"), {"__name__": "__main__"})
        self.assertEqual(before, {p.relative_to(consumer).as_posix(): p.read_bytes() for p in consumer.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
