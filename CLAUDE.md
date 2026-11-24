# Scribble Strip – notes for Claude

Big-text browser display for Ableton Live: shows which track, parameter and value the controller is moving, the rack's 16 macros, sends, meters, gain reduction, a Colour EQ curve and a picture of the synth. Formerly "Alias 8 status viewer" (renamed 2026-11-22, because more controllers are coming: a Novation Launch Control next).
Owner: Daniel (writes in Swedish; answer in Swedish, keep code/comments/docs in English).

## Layout
- `scribble_strip.py` – local server: http://127.0.0.1:8643 serves `viewer.html` and `/synths/<file>`; listens on UDP 9877 for JSON from the Live script; POST /control → UDP 9878 back to the script (`returns`, `nextrack`, `setrack`, `racktap`).
- `viewer.html` – all UI in one file (always dark; Settings key "," with tabs Knobs, Racks, Meters, Window; keys S/←/→ racks, R returns, L layout, B tint).
- `synths/*.jpg` – Daniel's own 1200×1920 pictures (protein, sh4d, s4, modelcycles, gr1, returns, bus, audio, externalinstrument, abletoninstrument).
- `Start Scribble Strip.command` – double-click starter (macOS).

## Protocol (sender today: ../alias8-scribble, script folder Alias8_Live)
- `{type:"message", text:"Alias 8: <track> - <macro> <value>", control, target, pickup, macro:[n, owner], targets}` per knob/fader step.
- `{type:"state", page, pages, cols:[{name, rgb, kind, selected, vol, …}], macros:{kind, groups, gr, gcolors, racks, rack_n, rack_count, rack_path, voice, page, pages, pstyle, eq}}` whenever the controller state changes (≤0.1 s after a knob step).
- Keep the protocol controller-neutral when adding a second sender (Launch Control): prefer new optional fields over Alias-specific ones; the "Alias 8:" text prefix should become a field.

## Working rules
- Test: run `scribble_strip.py`, open the page with Playwright, call `showState(st)` then `show(msg)`; screenshot at several sizes incl. portrait 1080×1920 (Daniel's main view). `node --check` the extracted `<script>`.
- Role icons: iterate on a standalone page rendering `roleSvg()` at 96/48/24 px, then paste into viewer.html. When inserting CSS by string search, make sure the anchor isn't inside another selector.
- Pictures are cached ~60 s by the viewer (Cmd+Shift+R). Restart the server when `scribble_strip.py` changes.
- Every change: a line in `CHANGES.md`, commit.
