# Session diary <YYYY-MM-DD> (append-only; one line per event)
Path: docs/operations/session-diary-<YYYY-MM-DD>.md. Only append; never rewrite or reorder.
Format: `time | event | handoff or file path`. No prompt text, tool output, secrets or personal data.
Fixed points: before dispatching an agent (intent + brief), when an agent report arrives
(verdict + handoff), when a gate opens or closes, at token milestones, at a resume.

- HH:MM | dispatch <role>/<tier>: <short intent> | <brief path>
- HH:MM | report <role>: <verdict or state> | <handoff path>
- HH:MM | gate <name> opened|closed on <snapshot hash>: <verdict> | <report path>
- HH:MM | milestone <N>k reached: <user choice> | <continuation prompt path, if any>
- HH:MM | resume after interruption: <what was found> | <live-state path>
