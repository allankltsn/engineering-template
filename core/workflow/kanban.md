# Full Kanban registration contract

Board is durable execution/acceptance record when selected. Cards live directly in
configured relative sprint directory, no subfolders by status. Code/evidence/logs
stay in authorized workspace/worktree; any shared board exception is explicit, never
an inherited absolute path. Only principal changes board configuration through an
authorized proposal; never overwrite user settings.

## Exact frontmatter
Use templates/card.md with only id, status, priority, assignee, epic, dueDate,
created, modified, completedAt, labels, order. Extension may delete extra fields.
Keep checklist, time, evidence, IDs, decisions, prior status and postmortem in body.
id equals filename stem. assignee identifies function and portable instance token;
provider ID may be recorded as optional body metadata, never required for handoff.
UTC ISO 8601 timestamps; modified updates on edits.

Read-only participants return complete card updates, reports and sanitized evidence
to the principal instead of writing files or bypassing tool/sandbox restrictions.
The principal persists these records faithfully, retaining the originating instance,
snapshot, timestamps and verdict; persistence never transfers authorship or approval.
Apply this handoff to every registration step below when writes are unavailable.

IDs: task-N, task-N-impl, task-N-impl-cpK, task-N-review, task-N-qa,
task-N-security, task-N-fix. epic groups parent Task N. Labels role:<function>,
task-N, checkpoint; retroativo for explicit retrospective registration, abandonado
for abandoned work. Retroactive records never imply contemporaneous evidence.

## States and authority
| State | Meaning | Who transitions |
|---|---|---|
| open | Planned, not scheduled | Principal |
| pending | Brief ready | Principal |
| in-progress | Work active | Assigned instance before acting |
| in-review | Delivered for validation / validation active | Author submits; validators start |
| rejected | Defect returned for correction | QA/reviewer/security |
| blocked | Impediment or pending user decision | Detector, informing principal |
| completed | Technically verified with evidence; awaiting human acceptance | Principal |
| accepted | Explicitly accepted by user | User or principal recording written decision |
| closed | Sprint-review closure or explicit abandonment | Principal |

Legacy VSCode backlog is not a new canonical state; explicitly map to open on import.
Never use done. Set operational state before the corresponding action. Completion
states follow actual evidence, not advance declarations. Specialist never promotes
own card beyond in-review; rejected/blocked are exception routing states.
Checkpoint execution-finished is body timestamp/checklist and evidence; completedAt
is reserved for principal-verified completed, resolving historical ambiguity.

## Procedure
1. Principal creates parent milestone and participant cards before dispatch, with
   role, permitted paths, criteria and next owner. Ready -> pending; assignee marks
   in-progress before acting.
2. Agent reads card and updates next owner. For a substantial scoped task create
   3-8 capability checkpoints, not micro-steps; proportional simple task may record
   checklist in parent with explicit rationale. Mark active before work.
3. Author stores real sanitized evidence before handing back; fills time/evidence/
   decisions. Checkpoint checklist completion is not self-approval.
4. QA, compliance/technical review and security have separate cards/instances.
   Findings route to responsible fixer, rejected fix card where blocking.
5. Principal reexecutes at least one evidence command, checks snapshot/commit and
   required gates, then moves completed. Divergence returns work in-progress with
   recorded difference. No evidence -> blocked, no invented completion.
6. Accepted requires user identity/date/scope/decision in body. Closed is Sprint
   Review or explicit abandonment with label and reason.

## Severity mapping
Canonical findings: Critical / High / Medium / Low; retain source severity verbatim.
Legacy Critical -> Critical. Legacy Important -> High unless documented impact
justifies Medium; legacy Minor -> Low unless documented impact justifies Medium.
Record rationale and impact when mapping, never silently downgrade. Critical/High
block completion until corrected/revalidated or an explicitly authorized risk
decision where appropriate; all pending findings/recommendations need disposition.

## Mandatory records
- Parent task postmortem: every real problem/decision, cause, solution that worked,
  failed attempts and prevention. Per-card minutes in body.
- Principal event log: UTC, instance, card, type, message and evidence link.
  Types INICIO, MARCO, RED, GREEN, ESCOLHA, DESVIO, RISCO, PROBLEMA, SOLUCAO,
  DECISAO, ALERTA_PERIGO, FIM. At closure summarize log in parent postmortem.
- User decision: blocked with DECISAO prefix, prior status, context/options/
  recommendation/consequence if unanswered; return NEEDS_DECISION and card path.
  Principal informs user; unaffected authorized work continues. On decision record
  applied scope, remove prefix and resume prior appropriate state.
- Dangerous actual action: do not execute, CRITICIDADE ALTA/CRITICA in card,
  assessment and principal notification immediately; log ALERTA_PERIGO.

## Evidence files and coverage
Configured evidence root/sprint/card:
implementer evidence + test-output; infrastructure compose-ps/probe/logs; database
migration-check including applied schema and seed twice only when relevant/authorized;
review report with snapshot/findings/file:line/verdict; QA report + raw output;
security report + coverage; fixer failing-before/passing-after evidence; investigator
findings/cause/confidence; principal verification with command reexecution.
All include exact command/cwd/snapshot/UTC/exit code, raw sanitized output, criterion
mapping and not-verified items. See policies/evidence.md and templates.
RED must represent valid behavior failure, not unavailable prerequisite; check Docker
first only if selected tests need Docker. Do not mandate Docker for every stack.

## Availability, scope and checklist
If inactive for roughly 10 minutes, principal records last activity and investigates
through authorized provider status/logs; portable handoff never depends on private
Claude transcript paths. Pending required permission -> blocked/decision; do not
expand permissions. New required paths go to principal for authorized scope change.
Prefer bounded rg/path searches; avoid unbounded dependency/root recursion.
Shared migrations/lockfiles/root config/compose have one owner. Parallel writes disjoint.

Before return: card exists with role/scope/criteria; active status preceded work;
checkpoints/checklist recorded; real evidence saved; time/postmortem/next owner filled;
decisions/danger/limitations communicated; card not self-approved.
