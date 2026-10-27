# Agent Instructions & Guidelines

## Remote Work Notes Rule

This environment is usually accessed through SSH. Do not assume that local Obsidian notes are available here.

When doing debugging, setup, deployment, or system administration work, leave a concise work note under:

`~/work-notes/`

Use this filename format:

`YYYY-MM-DD-HHMM-topic.md`

The note should include:

### Context
- Hostname:
- Working directory:
- Project:
- Device / server role:
- Date:

### Goal
Briefly describe what the user wanted to accomplish.

### Commands Run
List important commands that were executed.

### Files Changed
List modified files and why they changed.

### Findings
Record symptoms, error messages, root causes, and useful observations.

### Resolution
Explain what fixed the issue, or what was attempted if unresolved.

### Follow-up
List remaining tasks, risks, or list things to verify later.

### Sensitive Data Policy
Do not write secrets, passwords, API keys, private keys, full tokens, or private customer data into the note.
Use aliases such as robot01, training-server, or internal-registry instead of exposing sensitive details.
