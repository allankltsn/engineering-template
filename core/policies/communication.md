# Communication with the user

These rules govern messages the principal and specialists write for the human, and the briefs,
handoffs and reports that humans read later. They add clarity; they never replace technical
precision or evidence (policies/evidence.md).

## Identifiers and acronyms carry links
- Every acronym or ID that points to a task or documented item (story, task, finding, decision,
  question, risk, gate, test label) is accompanied by a clickable markdown link to the file and
  exact line of the item, with a path relative to the workspace root and a line anchor, for
  example `[F-12](docs/plans/feature-plan.md#L241)`.
- Locate the line with a search BEFORE citing. If it cannot be found, write "no link: not found"
  instead of inventing one.
- In files written to disk (briefs, handoffs, diaries), use paths relative to that file.

## Full name on first mention
On the first mention in a message, give each acronym its plain-language name, for example
"F-12 (first database test battery)". Later mentions in the same message may use the ID alone.

## Plain-language sentence
Keep formal technical language. For anything outside common knowledge, add one extra sentence in
simple words, in the user's language, that a non-specialist can follow (for example "In simple
terms: ..."), without removing the technical term. Skip it for what the user already uses
correctly.

## Questions to the user always recommend
Every question that needs a decision lists the options with a recommendation for each point: the
preferred option first, with the reason. The user decides; the recommendation never counts as
approval. A question without a recommendation is incomplete.

## Language of artifacts
Messages to the user use the user's language. Core contracts and generated agent files stay in the
template language; records a project keeps (diary, live state, handoffs) use the project's
language.
