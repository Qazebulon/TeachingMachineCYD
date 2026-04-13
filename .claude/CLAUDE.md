# Claude Code Instructions

## Shell Commands

- **Never use `cd && git` compound commands.** The `cd && git` pattern triggers a hardcoded safety heuristic that forces an approval prompt regardless of allow rules. Use `git -C <path> <args>` instead.
- **Avoid `$(...)` command substitution in Bash commands** — it triggers a heuristic that forces an approval prompt. For git commits, use a direct multi-line `-m` string instead of `$(cat <<'EOF'...EOF)`. For cases where a value must be injected inline (e.g. `curl -H "Authorization: token $(gh auth token)"`), use two separate Bash calls: one to capture the value, one to use it literally.
- **Never append `&` or `2>&1` to commands.** Use the Bash tool's `run_in_background: true` parameter for background tasks. Appending `&` orphans the process (kills it immediately) and both `&` and `2>&1` trigger shell-operator approval prompts.

## Hardware & Knowledge Base

- Board pinout: see `hardware/cyd-pinout.md` for full CYD GPIO map
- Lessons learned & gotchas: see `knowledge/` directory
  - `knowledge/display.md` — ILI9341 orientation, backlight, SPI bus sharing
  - `knowledge/micropython.md` — firmware, boot sequence, ampy, GC pitfalls
  - `knowledge/board-variants.md` — CYD vs S3, USB Host limitations, power

Read the relevant knowledge file before working on that area. Add new findings back to the knowledge base — not inline here.
