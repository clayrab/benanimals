# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Baby Animal Keyboard — a fullscreen pygame app for toddlers. Pressing a letter key displays the letter, an animal name, and speaks it aloud via `espeak`. Input is grabbed to prevent toddlers from triggering OS shortcuts.

## Running

```bash
./run
# or equivalently:
nix-shell -p python3 python3Packages.pygame espeak --run "python ~/baby-animals.py"
```

Dependencies (provided via nix-shell): Python 3, pygame, espeak.

## Architecture

Single-file app (`benanimals.py`). No tests, no build system.

- `ANIMALS` dict maps each letter to (animal_name, color)
- `speak()` calls `espeak` via subprocess
- `draw_animal()` renders letter + animal name + decorative circles
- `main()` runs the pygame event loop in fullscreen with input grab
- Exit: Ctrl+Shift+Q held 2 seconds, Ctrl+Shift+Escape, or 10-minute inactivity timeout
