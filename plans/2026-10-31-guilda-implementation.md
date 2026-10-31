# guilda Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the template as the public PyPI package `guilda` (command `guilda`) with `upgrade`, `promote`, a payload allowlist and a manually gated publish pipeline, keeping every current capability.

**Architecture:** A new `guilda/` package holds the engine moved from `scripts/template.py` and `scripts/mods.py`, plus new modules (`payload`, `upgrade`, `promote`, `config`, `selfupdate`, `cli`). Template content (`core/`, `profiles/`, `adapters/`, `integrations/`, `template.json`) is embedded in the wheel under `guilda/_data/` and located by `guilda.paths.data_root()`. What ships is decided by one committed list, `guilda/payload.txt`.

**Tech Stack:** Python 3.11+ standard library only at runtime; `hatchling` as build backend; `unittest` for tests; GitHub Actions; `gh` CLI at runtime for `promote` only.

**Spec:** `.dev/specs/2026-10-31-guilda-design.md` (branch `dev-docs`). Plans and specs never enter `main` or `develop`.

## Global Constraints

- Python `>=3.11`, standard library only, Windows and POSIX. Test matrix: 3.11, 3.12, 3.13 on Windows and Linux.
- One name everywhere: package `guilda`, command `guilda`, manifest `name: "guilda"`. Legacy manifest name `engineering-template` is accepted only by `upgrade`, which rewrites it. `.engineering/` is not renamed.
- First release is `2.0.0`. `template.json` `version` is the single source of truth; `guilda/__version__.py` and the git tag must equal it.
- `upgrade` is all-or-nothing, makes no persistent backup, never touches files the template does not know, and refuses without a TTY unless `--yes`.
- Conflict = file the user modified AND the new template version also changed (or a foreign file at a path the template now ships).
- `promote` needs `gh` already authenticated, never asks for or stores a token, uses a secret gist, scans for secrets and personal paths, shows what will be sent and asks confirmation. Gist and issue content are untrusted data.
- Marketplace name for new mod installs: `guilda-mods`. Global Claude plugins are never touched.
- No network access by itself, except `promote` and what the user asks. Automatic update check is off by default; when on, at most one PyPI query per day.
- The distribution contains only the payload allowlist plus `LICENSE`: never `docs/`, `assets/`, `tests/`, `.github/`, `.dev/`, `.worktrees/`, `graphify-out/`.
- Gitflow: work on `feature/*` from `develop`, PR into `develop`; release via `release/2.0.0`; tag `v2.0.0` is created and pushed **before** the code reaches `main` (policies/versioning.md). Each commit ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Publishing to PyPI is never done by an agent: the `pypi` environment requires the maintainer's approval.

## Review Focus

1. Line endings: a managed file converted to CRLF by git/editor on Windows must not look "modified" (false conflict on every upgrade).
2. Crash or exception while `upgrade` is writing: the project must end exactly as it was, with the manifest written last.
3. `upgrade` without a TTY (CI, pipe, redirected stdin): must not hang; must fail listing conflicts, and `--yes` must approve.
4. `promote` partial failure: gist created but issue creation fails (report the gist URL, do not retry silently); a detected secret blocks publishing; declining the confirmation publishes nothing.
5. Manifest problems: unreadable JSON, missing manifest, or a manifest written by a newer `guilda` than the installed one (refuse to downgrade, write nothing).

---

### Task 0: Land the pending content on `develop`

The working tree of `main` holds uncommitted template work (skills, `assets/`, `docs/diagramas.md`, board and versioning rules, mods installer, `LICENSE`, test exceptions, `.gitignore`). It enters through a feature branch, not `main`.

**Files:** Modify: `.gitignore`. No new code.

**Interfaces:** Produces: `develop` containing all pending content, so later tasks start from a working suite.

- [ ] **Step 1: Branch from `develop` carrying the working tree**

Run: `git switch -c feature/conteudo-pendente develop` (uncommitted changes travel with the switch).
Expected: `git status --short` still lists the pending files; branch is `feature/conteudo-pendente`.

- [ ] **Step 2: Ignore tool output and keep documents out**

Append to `.gitignore`: `core/graphify-out/`, `graphify-out/`, `.worktrees/`, `.dev/`, `docs/resume.md` is **not** ignored (maintainer decides). Then `git status --short | grep graphify` must print nothing.

- [ ] **Step 3: Run the full suite**

Run: `python -m unittest tests.test_template`
Expected: `OK (skipped=1)`, 35 tests.

- [ ] **Step 4: Commit in logical groups** (skills; assets and docs; board + versioning rules; mods installer; license and tests), then `git push -u origin feature/conteudo-pendente` and `gh pr create --base develop`. The maintainer merges.

---

### Task 1: Package skeleton, data root, version

**Files:**
- Create: `pyproject.toml`, `guilda/__init__.py`, `guilda/__version__.py`, `guilda/paths.py`, `guilda/__main__.py`
- Test: `tests/test_guilda_package.py`

**Interfaces:**
- Produces: `guilda.paths.data_root() -> pathlib.Path` (the directory containing `template.json`, `core/`, `profiles/`, `adapters/`, `integrations/`); `guilda.__version__: str`.

- [ ] **Step 1: Write the failing tests** in `tests/test_guilda_package.py`:
  - `test_version_matches_template_json`: `guilda.__version__ == json.load(template.json)["version"]`.
  - `test_data_root_in_checkout_is_repo_root`: `(data_root() / "template.json").is_file()` and `(data_root() / "core").is_dir()`.
  - `test_data_root_prefers_embedded_data`: with a temp package dir containing `_data/template.json`, `paths._resolve(package_dir=tmp)` returns `tmp / "_data"`.

- [ ] **Step 2: Run to confirm failure** — `python -m unittest tests.test_guilda_package` → `ModuleNotFoundError: guilda`.

- [ ] **Step 3: Implement.** `paths.py`: `_resolve(package_dir: Path) -> Path` returns `package_dir/"_data"` if it holds `template.json`, else `package_dir.parent`; `data_root()` calls it with this file's directory. `__version__.py` holds `__version__ = "1.3.0"` for now (Task 11 bumps it). `pyproject.toml`: `[project] name="guilda"`, `requires-python=">=3.11"`, license `Apache-2.0`, `dynamic=["version"]` read by hatch from `guilda/__version__.py`, `[project.scripts] guilda="guilda.cli:main"`; `[tool.hatch.build.targets.wheel]` packages `guilda`, with `force-include` mapping `core`, `profiles`, `adapters`, `integrations` and `template.json` to `guilda/_data/...` and `LICENSE` included. `__main__.py` calls `guilda.cli.main` (created in Task 6; guard with `if __name__ == "__main__"`).

- [ ] **Step 4: Run to confirm pass** — same command → `OK`.

- [ ] **Step 5: Commit** — `feat(pacote): esqueleto do pacote guilda e raiz de dados`.

---

### Task 2: Move the engine into the package

**Files:**
- Move: `scripts/template.py` → `guilda/engine.py`; `scripts/mods.py` → `guilda/mods.py` (`git mv`)
- Create: `scripts/template.py`, `scripts/mods.py` (shims)
- Modify: `install.py`, `tests/test_template.py:14-18`
- Test: existing `tests/test_template.py`

**Interfaces:**
- Consumes: `guilda.paths.data_root()`.
- Produces: `guilda.engine` with the current public names unchanged (`render`, `install`, `check`, `validate_manifest`, `load_source`, `digest`, `main`) and `SOURCE = data_root()`; `guilda.mods` with `install_mod(name, scope, target, dry_run=False, home=None, run=subprocess.run, platform=None)` and `SOURCE = data_root()`.

- [ ] **Step 1: Point the existing tests at the package** — in `tests/test_template.py` replace the two `spec_from_file_location` blocks with `import guilda.engine as template` and `import guilda.mods as mods` (add repo root to `sys.path` as needed).
- [ ] **Step 2: Run to confirm failure** — `python -m unittest tests.test_template` → import error.
- [ ] **Step 3: `git mv` both files, replace `SOURCE = Path(__file__).resolve().parents[1]` with `SOURCE = paths.data_root()` in each**, make `scripts/template.py` and `scripts/mods.py` shims that insert the repo root in `sys.path` and call `guilda.engine.main` / re-export `guilda.mods`, and make `install.py` import `guilda.engine`/`guilda.mods` instead of loading by path.
- [ ] **Step 4: Run to confirm pass** — `python -m unittest tests.test_template` → `OK (skipped=1)`; and `python scripts/template.py check` prints `"valid": true`.
- [ ] **Step 5: Commit** — `refactor(pacote): move o motor para guilda/engine e guilda/mods`.

---

### Task 3: Payload allowlist

**Files:**
- Create: `guilda/payload.py`, `guilda/payload.txt`
- Modify: `guilda/engine.py` (`load_source`)
- Test: `tests/test_guilda_payload.py`

**Interfaces:**
- Produces: `payload.FORBIDDEN: tuple[str, ...] = ("graphify-out", "docs/superpowers", "plans/", "specs/", ".worktrees", ".dev", "__pycache__")`; `payload.read(root: Path) -> list[str]` (relative posix paths from `payload.txt`, sorted, validated); `payload.generate(root: Path) -> list[str]` (tracked files under `core/ profiles/ adapters/ integrations/` plus `template.json`, from `git ls-files`); CLI `python -m guilda.payload --write | --check`.
- Consumes: `engine.load_source` now iterates `payload.read(source)` instead of `os.walk`.

- [ ] **Step 1: Write the failing tests:**
  - `test_payload_has_no_forbidden_paths`: no entry contains any `FORBIDDEN` fragment.
  - `test_payload_matches_git_tracked_files`: `payload.read(ROOT) == payload.generate(ROOT)` (skip if not a git checkout).
  - `test_every_payload_file_exists`.
  - `test_load_source_ignores_untracked_noise`: create `core/graphify-out/x.json` in a temp copy of the repo and assert it never appears in `engine.render(...)` output.
- [ ] **Step 2: Run to confirm failure** — `ModuleNotFoundError: guilda.payload`.
- [ ] **Step 3: Implement** `payload.py` per the interfaces; `generate` raises `ValueError` if a tracked path matches `FORBIDDEN`; `load_source` raises `ValueError("file outside payload: ...")` for any file it is asked to read that is not listed. Generate `payload.txt` with `python -m guilda.payload --write` and commit it.
- [ ] **Step 4: Run to confirm pass** — new tests plus `tests.test_template` → `OK`.
- [ ] **Step 5: Commit** — `feat(pacote): lista de permitidos do payload e vigia contra vazamentos`.

---

### Task 4: Name `guilda` and legacy manifest handling

**Files:**
- Modify: `template.json` (`name`), `guilda/engine.py` (`load_source`, `validate_manifest`, `check`, `install`), `guilda/mods.py` (`MARKETPLACE`)
- Test: `tests/test_guilda_migration.py`; adjust assertions in `tests/test_template.py` that expect `engineering-template`

**Interfaces:**
- Produces: `engine.TEMPLATE_NAME = "guilda"`, `engine.LEGACY_NAMES = ("engineering-template",)`; `engine.validate_manifest(source, manifest, allow_legacy=False)`; `engine.read_manifest(target: Path) -> dict` (raises `ValueError("manifest unreadable: <path>")` and `ValueError("no manifest: run guilda init")`).
- Consumed by Task 5.

- [ ] **Step 1: Write the failing tests:**
  - `test_new_manifest_name_is_guilda` (init writes `"name": "guilda"`).
  - `test_legacy_manifest_rejected_by_check_and_sync`: message contains `run guilda upgrade`.
  - `test_legacy_manifest_accepted_with_allow_legacy`.
  - `test_unreadable_manifest_is_clear_error` and `test_missing_manifest_points_to_init` (Review Focus 5).
  - `test_new_mod_marketplace_is_guilda_mods`.
- [ ] **Step 2: Run to confirm failure.**
- [ ] **Step 3: Implement** the constants and parameter; `check` and `install(sync=True)` raise `ValueError("legacy manifest name; run guilda upgrade")` when `name in LEGACY_NAMES`; update `template.json`, the plugin/marketplace names rendered for `package=True`, and `mods.MARKETPLACE = "guilda-mods"`.
- [ ] **Step 4: Run to confirm pass** — `python -m unittest tests.test_template tests.test_guilda_migration`.
- [ ] **Step 5: Commit** — `feat(nome): renomeia o manifesto para guilda e isola o nome legado`.

---

### Task 5: `upgrade` engine

**Files:**
- Create: `guilda/upgrade.py`
- Test: `tests/test_guilda_upgrade.py`

**Interfaces:**
- Consumes: `engine.render`, `engine.read_manifest`, `engine.validate_manifest(..., allow_legacy=True)`, `engine.digest`, `engine.json_bytes`, `engine.safe_path`.
- Produces:
  - `@dataclass(frozen=True) class Plan: write: list[str]; remove: list[str]; keep: list[str]; conflicts: list[str]; migrate_name: bool`
  - `class UpgradeRefused(Exception)` (carries `.plan`)
  - `plan_upgrade(source: Path, target: Path) -> Plan` — pure, writes nothing
  - `apply_upgrade(source: Path, target: Path, plan: Plan, approved: bool) -> dict` returning `{"write": [...], "remove": [...], "kept": [...], "migrated": bool}`
  - `same_text(a: bytes, b: bytes) -> bool` — equal after `\r\n`→`\n`.
- File classification, per managed path: user file == manifest hash (or `same_text` with the installed version) and unchanged in new render → nothing; unchanged by user, changed by template → `write`; user-modified and template unchanged → `keep`; user-modified and template changed → `conflicts`; path now shipped but present as a foreign file with different content → `conflicts`; path retired by the template → `remove` (conflict if user-modified). Files not in the manifest and not in the new render are never listed.

- [ ] **Step 1: Write the failing tests** (build a project with `engine.install`, then mutate):
  - `test_untouched_project_has_empty_plan`.
  - `test_template_change_is_written` / `test_user_edit_is_kept_when_template_unchanged` / `test_user_edit_plus_template_change_is_conflict`.
  - `test_user_added_file_never_touched`: a file `.claude/skills/mine/SKILL.md` survives byte-identical.
  - `test_crlf_conversion_is_not_a_modification`: rewrite a managed file with `\r\n` → plan has no conflict, no keep (Review Focus 1).
  - `test_conflicts_without_approval_write_nothing`: `apply_upgrade(..., approved=False)` raises `UpgradeRefused` and every file hash is unchanged, including non-conflicting ones (all-or-nothing).
  - `test_approved_overwrites_conflicts_without_backup`: conflict file replaced, no `*.bak` or backup dir created.
  - `test_failure_mid_apply_restores_project` (Review Focus 2): monkeypatch the writer to raise on the 3rd file; assert every file and the manifest are byte-identical to before.
  - `test_manifest_written_last`: record write order; manifest is the final write.
  - `test_legacy_name_migrates_in_same_operation`: manifest ends with `"name": "guilda"` and new hashes.
  - `test_newer_manifest_version_refused` (Review Focus 5): manifest `version` greater than the engine's → `ValueError` mentioning "newer", nothing written.
  - `test_dry_run_plan_has_no_side_effects`.
- [ ] **Step 2: Run to confirm failure.**
- [ ] **Step 3: Implement** the interfaces. Reuse providers, profiles and tiers from the manifest. `apply_upgrade` preflights, keeps originals of every file it will touch in memory only, writes, writes the manifest last, and on any exception restores from memory then re-raises; memory is dropped on success. Compare versions with a small `_parse_version(str) -> tuple[int, int, int]`.
- [ ] **Step 4: Run to confirm pass** — `python -m unittest tests.test_guilda_upgrade`.
- [ ] **Step 5: Commit** — `feat(upgrade): atualização tudo ou nada com migração do nome legado`.

---

### Task 6: `guilda` CLI

**Files:**
- Create: `guilda/cli.py`
- Modify: `guilda/__main__.py`, `install.py`
- Test: `tests/test_guilda_cli.py`

**Interfaces:**
- Consumes: `engine.*`, `upgrade.*`, `mods.install_mod`.
- Produces: `main(argv: list[str] | None = None) -> int`; `confirm(prompt: str, stdin=None, stdout=None) -> bool` (returns `False` without reading when `stdin` is not a TTY); subcommands `init`, `sync`, `check`, `doctor`, `package`, `install`, `upgrade`, `mod`, `promote`, `self-update`, with the current flags unchanged (`--target`, `--providers`, `--provider`, `--profiles`, `--tier`, `--dry-run`). `install <projeto>` equals today's `install.py`. `upgrade <projeto>` takes `--dry-run` and `--yes`. `install.py` becomes a thin call to `cli.main(["install", *argv])`.

- [ ] **Step 1: Write the failing tests:**
  - `test_init_sync_check_doctor_package_behave_as_before` (same outputs as `scripts/template.py`).
  - `test_upgrade_without_tty_fails_listing_conflicts` and `test_upgrade_yes_approves` (Review Focus 3): stdin replaced by a non-TTY stream; first returns `1` with the conflict list on stderr and no writes; second returns `0`.
  - `test_upgrade_prompt_shows_files_and_warns_data_loss`: with a fake TTY answering `n`, output lists each conflict, says local changes will be lost, suggests `guilda promote`, and nothing is written; answering `y` applies.
  - `test_upgrade_dry_run_prints_plan_and_writes_nothing`.
  - `test_install_command_matches_install_py`.
- [ ] **Step 2: Run to confirm failure.**
- [ ] **Step 3: Implement** with `argparse` subparsers; `upgrade` calls `plan_upgrade`, prompts only when `plan.conflicts` is non-empty and `--yes` is absent, then `apply_upgrade`. Exit code `1` with a message on `ValueError`/`UpgradeRefused`.
- [ ] **Step 4: Run to confirm pass** — `python -m unittest tests.test_guilda_cli tests.test_template`; also `python -m guilda check`.
- [ ] **Step 5: Commit** — `feat(cli): comando guilda com upgrade, install e mod`.

---

### Task 7: `promote`

**Files:**
- Create: `guilda/promote.py`, `.github/ISSUE_TEMPLATE/proposta.yml`
- Modify: `guilda/cli.py` (wire `promote`)
- Test: `tests/test_guilda_promote.py`

**Interfaces:**
- Consumes: `engine.read_manifest`, `engine.digest`, `engine.render`.
- Produces:
  - `changed_files(source: Path, target: Path) -> dict[str, bytes]` — files added or modified versus the manifest, only under managed directories; excludes `.engineering/manifest.json`.
  - `@dataclass(frozen=True) class Finding: path: str; line: int; kind: str`
  - `scan(files: dict[str, bytes]) -> list[Finding]` — kinds: `secret` (private-key blocks, `ghp_`/`github_pat_`/`AKIA`/`xox[bp]-`/`sk-` tokens, `password|secret|token\s*[:=]\s*\S{8,}`), `personal-path` (`C:\Users\<name>`, `/home/<name>`, `/Users/<name>`), `binary`, `too-large` (over 1 MiB).
  - `build_issue(title: str, description: str, gist_url: str, paths: list[str], version: str) -> tuple[str, str]` — body lists changed paths, the follow-up work (catalog, tests, changelog, README), the gist link, and the contribution acceptance sentence.
  - `promote(source, target, title, description, assume_yes=False, runner=subprocess.run, stdin=None, stdout=None) -> dict` returning `{"gist": url, "issue": url}`.
- Flow: `gh auth status` must succeed → collect and scan → any finding aborts with the list → print every file to be sent and ask confirmation (declined or non-TTY without `--yes` publishes nothing) → `gh gist create` (secret) → `gh issue create` against `allankltsn/guilda`.

- [ ] **Step 1: Write the failing tests** (a fake `runner` records calls):
  - `test_changed_files_lists_added_and_modified_only`.
  - `test_scan_flags_token_private_key_and_personal_paths`, `test_scan_flags_binary_and_oversize`.
  - `test_secret_blocks_publishing_and_calls_nothing` (Review Focus 4): runner never invoked after `gh auth status`.
  - `test_declined_confirmation_publishes_nothing` (Review Focus 4).
  - `test_gh_not_authenticated_is_clear_error`.
  - `test_issue_creation_failure_reports_gist_url` (Review Focus 4): fake runner fails on `issue create`; result/exception names the gist URL and does not retry.
  - `test_issue_body_contains_gist_link_paths_and_acceptance`.
  - `test_gist_is_secret`: the `gist create` argv does not contain `--public`.
- [ ] **Step 2: Run to confirm failure.**
- [ ] **Step 3: Implement** the interfaces. The issue form `proposta.yml` has required fields (description, what changed, acceptance checkbox "I grant the maintainer a license to use and relicense this contribution") and applies label `proposta`.
- [ ] **Step 4: Run to confirm pass** — `python -m unittest tests.test_guilda_promote`.
- [ ] **Step 5: Commit** — `feat(promote): proposta de feature por gist secreto e issue`.

---

### Task 8: Config and `self-update`

**Files:**
- Create: `guilda/config.py`, `guilda/selfupdate.py`
- Modify: `guilda/cli.py`
- Test: `tests/test_guilda_selfupdate.py`

**Interfaces:**
- Produces:
  - `config.path() -> Path` (`%APPDATA%\guilda\config.json` on Windows, `$XDG_CONFIG_HOME/guilda/config.json` or `~/.config/guilda/config.json` elsewhere); `config.load() -> dict` with defaults `{"update_check": "off", "last_check": null}`; `config.save(data: dict) -> None`. `update_check` is `"off" | "notify" | "auto"`.
  - `selfupdate.latest_version(opener=urllib.request.urlopen) -> str` (PyPI JSON for `guilda`).
  - `selfupdate.check_if_due(now: datetime, cfg: dict, opener=...) -> str | None` — `None` when `off` or checked within 24 h; otherwise the newer version or `None`.
  - `selfupdate.upgrade_self(runner=subprocess.run) -> int` running `python -m pip install --upgrade guilda` (or `uv tool upgrade guilda` when installed by uv).
- `guilda self-update` always runs `upgrade_self`; `check_if_due` runs at CLI start only when `update_check != "off"`.

- [ ] **Step 1: Write the failing tests:**
  - `test_default_is_off_and_makes_no_network_call`: opener raises if called; `check_if_due` returns `None`.
  - `test_notify_checks_at_most_once_per_day`; `test_auto_runs_upgrade_self_once`.
  - `test_pre_release_versions_are_ignored`.
  - `test_cli_never_touches_network_when_off`.
  - `test_config_path_per_platform`.
- [ ] **Step 2: Run to confirm failure.**
- [ ] **Step 3: Implement.** Compare with the same `_parse_version`; ignore pre-releases.
- [ ] **Step 4: Run to confirm pass.**
- [ ] **Step 5: Commit** — `feat(self-update): atualização global opcional e desligada por padrão`.

---

### Task 9: CI

**Files:**
- Create: `.github/workflows/ci.yml`, `tests/test_guilda_wheel.py`

**Interfaces:**
- Produces: workflow `CI` (names fixed: job `test`, job `payload-guard`, job `build`).

- [ ] **Step 1: Write `tests/test_guilda_wheel.py`** — builds the wheel with `python -m build --wheel` (skipped when `build` is not installed) and asserts the wheel namelist contains `guilda/_data/template.json`, `guilda/_data/core/`, `LICENSE`, and contains none of `docs/`, `assets/`, `tests/`, `.github/`, `graphify-out`, `.dev`, `.worktrees`, `plans/`, `specs/`.
- [ ] **Step 2: Run to confirm it fails or skips** — `python -m unittest tests.test_guilda_wheel`.
- [ ] **Step 3: Write `ci.yml`**: triggers on PRs to `develop` and `main` and on pushes to `feature/**`, `release/**`; job `test` runs `python -m unittest discover -s tests` on a matrix of `ubuntu-latest` and `windows-latest` × Python 3.11, 3.12, 3.13; job `payload-guard` runs `python -m guilda.payload --check` and fails when `git ls-files` shows `docs/superpowers/`, `plans/`, `specs/`, `graphify-out/` or `.worktrees/`; job `build` installs `build`, builds sdist and wheel, runs `tests.test_guilda_wheel`.
- [ ] **Step 4: Verify** — push the feature branch, open the PR into `develop`, and confirm all three jobs green with `gh pr checks`.
- [ ] **Step 5: Commit** — `ci: testes, vigia do payload e conferência da distribuição`.

---

### Task 10: Release pipeline with a manual gate

**Files:**
- Create: `.github/workflows/release.yml`, `tests/test_guilda_release.py`

**Interfaces:**
- Produces: workflow file named exactly `release.yml` (registered on PyPI as the trusted publisher together with environment `pypi`, owner `allankltsn`, repository `guilda`); `scripts/check_release.py` with `check(tag: str, root: Path) -> list[str]` returning problems.

- [ ] **Step 1: Write the failing tests** (`tests/test_guilda_release.py`):
  - `test_check_release_ok`: tag `v2.0.0`, `template.json` and `__version__` both `2.0.0` → `[]`.
  - `test_check_release_reports_each_mismatch`: tag vs template.json, template.json vs `__version__`, malformed tag (`2.0`, `v2.0.0-rc.1`).
  - `test_release_workflow_is_gated`: parse `release.yml` text; the job that runs `gh-action-pypi-publish` has `environment: pypi`, `permissions: id-token: write`, `needs` the build job, and the workflow triggers only on `push: tags: ["v*"]`.
- [ ] **Step 2: Run to confirm failure.**
- [ ] **Step 3: Implement** `scripts/check_release.py` (stdlib; `main()` reads `GITHUB_REF_NAME`) and `release.yml` with jobs: `verify` (runs `check_release.py`, confirms `git merge-base --is-ancestor $GITHUB_SHA origin/main`, runs the suite), `build` (artifact upload), `publish` (`environment: pypi`, `id-token: write`, `pypa/gh-action-pypi-publish`). Because the tag is pushed before the code, `verify` waits for the commit to be on `main` by failing with a clear message; the maintainer re-runs the workflow after merging.
- [ ] **Step 4: Run to confirm pass** — `python -m unittest tests.test_guilda_release`.
- [ ] **Step 5: Commit** — `ci(release): publicação com aprovação manual do mantenedor`.

---

### Task 11: Docs, version 2.0.0 and release

**Files:**
- Modify: `template.json` (`version` → `2.0.0`), `guilda/__version__.py`, `README.md`, `CHANGELOG.md`, `docs/compatibility.md`, `docs/validation.md`, `tests/test_template.py` (version assertions)
- Test: `tests/test_guilda_package.py::test_version_matches_template_json`

- [ ] **Step 1: Update the failing assertions** — change the `1.3.0` expectation in `tests/test_template.py` and the version test to `2.0.0`; run them to see them fail.
- [ ] **Step 2: Bump** `template.json` and `__version__.py` to `2.0.0`.
- [ ] **Step 3: Docs** — README gets `pip install guilda` / `uv tool install guilda`, the command table (`init`, `upgrade`, `promote`, `self-update`, the rest), the migration steps for projects with the old name (`guilda upgrade --dry-run`, then `guilda upgrade`), and a link to the maintainer's contribution flow (issues only). CHANGELOG gets a `2.0.0` entry listing the breaking changes (manifest name, entry point, payload allowlist, marketplace `guilda-mods`). The old `python install.py` instructions stay as the checkout path.
- [ ] **Step 4: Full verification** — `python -m unittest discover -s tests` → all green; `python -m build` produces a wheel; install it in a fresh virtualenv and run `guilda check`, `guilda init --target <tmp> --dry-run`.
- [ ] **Step 5: Release (human-gated)** — `git switch -c release/2.0.0 develop`; PR into `main`. Following policies/versioning.md: create and push the annotated tag `v2.0.0` on the release commit **before** merging into `main`; merge; merge back into `develop`; re-run the `release` workflow if `verify` was waiting; the maintainer approves the `publish` job in GitHub. An agent never approves it.
- [ ] **Step 6: Commit** — `chore(release): 2.0.0`.
