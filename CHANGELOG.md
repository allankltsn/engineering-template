# Changelog

Formato baseado em Keep a Changelog. Versões seguem `template.json`.

## [1.1.0] - 2026-10-19

Generalização do template (sem nomes de projeto no core) e inclusão de gestão de produto.
Base: tag `v1.0.0` (commit `81ee341`).

### Adicionado
- **Papéis (10 novos, total 28):** product-owner, ux-researcher, ux-designer, ui-designer,
  brand-strategist, marketing, frontend-senior, privacy-compliance, lay-user, scribe.
  Novo modo `author` (sem shell) para papéis que produzem artefatos.
- **Ações:** `/story`, `/privacy`, `/usability` (total 11).
- **Perfis:** `product-team` e `polyrepo` (total 9).
- **Políticas:** `models.md` (camadas deep/standard/light), `installations.md`
  (registro obrigatório de toda instalação), `quality-principles.md` (reuso, idempotência,
  tolerância a falhas, escalabilidade, simplicidade, verificabilidade).
- **Workflows:** `staffing.md`, `user-stories.md` (DoR/DoD), `usability.md`
  (dois usuários leigos simulados + brainstorm de decisão), `polyrepo.md` (hub + repositórios).
- **Templates:** `decision`, `persona`, `registro-instalacoes`, `staffing`,
  `usability-report`, `user-story`.
- **Camadas de modelo por papel:** `model_tiers` e `roles[].tier` em `template.json`;
  adapter Claude grava `model:` no cabeçalho do agente, Codex grava `model_reasoning_effort`.
  Override por projeto via `--tier ROLE=TIER`, registrado em `project.json` e no manifesto.
  Papéis de gate (qa, security, reviewer, privacy-compliance) não podem ficar abaixo de `standard`.
- **`integrations/plugins/`:** curadoria (`curated.json`, README) de plugins/agentes externos;
  o template não instala nada.
- **GitHub Projects:** campos `Type` (epic/story/task/bug/spike) e `Estimate`; labels
  `type:*`, `tier:*` e `role:*` dos novos papéis.
- Validação: papéis base obrigatórios, camadas válidas, rejeição de override inválido.
- Testes ampliados (`tests/test_template.py`): 26 testes, 1 ignorado.
- Este `CHANGELOG.md`.

### Alterado
- `architect`, `backend`, `security`: texto específico de stack (NestJS/MikroORM/AWS) passou
  a ser condicionado ao perfil selecionado; o core não cita projeto nem stack fixa.
- `workflow/engineering.md`: fluxo começa em história com DoR; seção de deveres de gestão
  do principal; gates incluem conformidade de design, privacidade e rodada de usabilidade.
- `workflow/github-projects.md`: títulos `[S-NNN]`/`[E-NN]`, histórias como sub-issues de
  épicos, tarefas como sub-issues de histórias.
- `templates/brief.md`: campos `Model tier` e `Staffing plan`.
- `policies/integrations.md`: modelos agora seguem camadas lógicas, não mais "herdar".
- `scripts/template.py`: `install` aceita a pasta-raiz do workspace que contém o checkout do
  template (rejeita só sobrescrita de arquivos do próprio template); `retired_paths`
  permite ao `sync` aposentar arquivos antigos; manifesto passa a guardar `tiers`.
- `README.md`, `core/catalog.md`, `docs/compatibility.md`, `docs/validation.md`,
  `integrations/voltagent/README.md`, `integrations/github-projects/*`: atualizados para
  28 papéis, 11 ações, 9 perfis e as novas regras.

### Removido
- Premissa de que adapters Codex omitem `model`; o limite fixo de exatamente 18 papéis e 8 ações.

### Não verificado
- Efeito dos campos `model`/`model_reasoning_effort` gerados em runtime real, execução paralela
  de dois usuários leigos e rodada de usabilidade completa (ver `docs/validation.md`).
  Popularidade em `curated.json` foi lida na data de curadoria.

## [1.0.0]

Estado da `main` em `81ee341` (tag `v1.0.0`): template portátil com 18 especialistas,
8 ações, 7 perfis, adapters Claude/Codex e workflow com GitHub Projects no lugar do
Kanban Markdown.
