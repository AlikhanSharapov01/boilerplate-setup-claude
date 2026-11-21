# CLAUDE.md

RV32I single-cycle core for the OSOC course. SystemVerilog, simulated with Icarus, linted with Verilator.

## Rules
- Always discuss the plan before editing anything and wait for my go-ahead.
- Never commit to main.
- Don't add Co-Authored-By lines.
- Keep diffs minimal.

## Project notes
- `rtl/` is synthesizable RTL only; testbenches go in `tb/`.
- Use `always_ff` / `always_comb`, never plain `always`.
- Active-low synchronous reset `rst_n` everywhere.
- Don't touch `build/` (generated).
