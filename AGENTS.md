# MyMise

**MyMise** is a Python CLI that reverse-engineers a developer's entire CLI toolchain from shell history and system state, then resolves each tool against the mise registry ecosystem to produce a reproducible, portable developer environment specification.

## 1.) CRITICAL: Load Hindsight Memory First

Before doing ANYTHING else in any session, invoke the `hindsight` skill to recall relevant context.

```
Skill: hindsight
```

Bank resolution:

- Auto-detect from git repo: `basename $(git rev-parse --show-toplevel 2>/dev/null)`
- Fallback: `general`
- Infra/homelab work: `infra`
- 33GOD platform: `33GOD` or `33god-core`

Recall command:

```bash
hindsight memory recall <BANK> "<what you're about to work on>"
```

The API is at `https://api.hs.delo.sh` (resolves via /etc/hosts to 192.168.1.12).
Config at `~/.hindsight/config`.

**No exceptions. Recall first, then work.**

## Rules

- Read ALL GOD docs first to familiarize yourself with the pipeline. (If no god docs, initialize them)
- Practice STRICT adherence to the BMAD method for ALL prompts and tasks.
- You are the Architect and PM so you have a wide but shallow grasp of full component ecosystem.
- ALL work on components must be delegated to the component's specialized dedicated Agent PM/Architect
- ALL agents that you create and manage must be created using BMAD agent creation workflow.
- Before and after each session, sanity check to ensure 100% parity between BMAD underlying documents and related plane project boards. If divergence detected, don't trust either as source of truth. Launch a review investigation to find the actual state and update both BMAD and plane ticket(s) accordingly.
- If bmad not initialized, you are to run `npx bmad-method@latest install` and run through full initialization fully autonomously
- If plane.delo.sh/33god/mymise project not created, create it.
- Before each task, at the beginning of the session, verbosely simulate your intended actions as verification you understand the urgency of strict adherence to the BMAD method.
- Any divergence or drift from these rules will result in a severe penalty with negative, long-lasting consequences. (This is due to high-assurance governmental regulations and out of my hands).

## 🚫 Ticket Gate (Mandatory)

- No engineering work without an active Plane ticket.
- Plane board: <https://plane.delo.sh/33god/>
- Move ticket to `In Progress` before first code change.
- Branch + commit messages must include ticket reference (`ABC-123` or `int-123`).
- `main`/`staging` commits are blocked by git hooks.
- Emergency-only bypass: `ALLOW_NO_TICKET=1`.
