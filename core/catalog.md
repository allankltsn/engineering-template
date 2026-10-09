# Preservation matrix
Source paths relative to original checkout; targets relative to core. Every
substantive role body is retained with provider frontmatter removed, project values
parameterized and explicit profile/authorization/independence conditioning.
No installed-version/runtime/parity claim follows from source presence.

| Source | Canonical target | Preservation |
|---|---|---|
| .claude/agents/architect.md | roles/architect.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/aws.md | roles/aws.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/backend.md | roles/backend.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/cicd.md | roles/cicd.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/cloud.md | roles/cloud.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/deployment.md | roles/deployment.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/devsecops-infra.md | roles/devsecops-infra.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/docker.md | roles/docker.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/finops.md | roles/finops.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/hosting.md | roles/hosting.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/ingress.md | roles/ingress.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/kubernetes.md | roles/kubernetes.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/orchestration.md | roles/orchestration.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/python.md | roles/python.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/qa.md | roles/qa.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/security.md | roles/security.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/sre.md | roles/sre.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| New requirement | roles/reviewer.md | Independent compliance and technical review, qualified expertise required |
| .claude/commands/{qa,security,aws,hosting,kubernetes,sre,cicd,devsecops-infra}.md | actions/<same-id>.md | All eight intents/arguments/results; corrected snapshot/base handling |
| CLAUDE.md | policies, workflow, profiles | Stack knowledge, routing, Superpowers phases, security/approval and independent gates |
| docs/sprints/board-workflow.md | workflow/kanban.md, templates | Exact frontmatter, states, ownership, checkpoints, evidence, logs/time, decisions, verification, postmortem |
| skills/drawio-diagram/SKILL.md | skills/drawio-diagram/SKILL.md | XML skeleton, nodes/edges/groups, styles/fallback, context and output; paths/inputs parameterized |
| .claude-plugin/{plugin,marketplace}.json | Adapter distribution responsibility | Metadata/package structure; personal identity/repo excluded from core |
| .claude/settings.local.json | policies/integrations.md | Permission/worktree awareness, eight Voltagent packs; personal allowlists not copied |
| .serena/project.yml | policies/integrations.md | Language/backend/workspace/ignore/tools/modes; no memory/state copied |
| .vscode/settings.json | workflow/kanban.md, policies/integrations.md | Relative board path/columns/colors, optional extension settings; personal Python settings excluded |

QA owns functional/contract/regression and incidental auth failures; security owns
systematic IDOR; devsecops-infra owns IaC; cloud selects services, AWS implements.
Ingress covers Nginx/Traefik/ALB/Gateway API; hosting is profile-conditioned.
Orchestration is service mesh; principal coordinates AI agents.
Main-thread fixing and repeated per-turn approval are removed. Historical
cost/plan/limit/threshold claims require verification. Board absolute paths/private
transcripts are not defaults; execution-finished differs from approval.
Original severities retained with explicit mapping; legacy backlog maps explicitly.
Text never proves enforcement; external plugin installation is not inferred.
