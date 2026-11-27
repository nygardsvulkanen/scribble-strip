# Scribble Monitor – changes

- 2026-11-22: Renamed from "Alias 8 status viewer" and moved out of the Alias8_Live folder into its own repo (`status_viewer.py` → `scribble_strip.py`, `Start status viewer.command` → `Start Scribble Strip.command`, page title "Scribble Strip"). Same ports and protocol. Earlier history: `Docs/CHANGES.md` in alias8-live.
- 2026-11-23: Added an MIT license (`LICENSE`).
- 2026-11-23: Screenshots in the README (`screenshots/`).
- 2026-11-24: Links point to alias8-scribble (the Alias8_Live script repo was renamed).
- 2026-11-26: Opening `viewer.html` straight from Finder (file://) now jumps to http://localhost:8643, or says to start the server, instead of hanging on "connecting…".
- 2026-11-26: Landscape: rack name, rack strip and page strip share one line above the knobs; the knobs may shrink to 40 % (was 60 %); an empty device-parameter line keeps no space in short windows. All 16 knobs now fit on a 16:10 laptop screen. Portrait unchanged.
- 2026-11-26: The Colour EQ curve only shows when the turned macro really moves an EQ device (`targets_eq` from the script); an older script without that field behaves as before.
- 2026-11-26: EQ curve: `targets_eq: null` (not known yet) hides it too; it shows on `true` (sent again ~0.1 s after the step) or when the field is missing (older script).
- 2026-11-26: EQ curve decided by the macro name instead of `targets_eq` (Live never reports the values of macro-mapped parameters, so the script cannot see what a macro moves): only EQ-like names (not Drive/Saturation/Tape/Phaser or unknown names), and only with an EQ Eight on the track. `COLOUR_EQ` can set a type or "off" per name.
- 2026-11-26: Mouse control: drag a macro knob up/down to turn it (Shift = fine, ~200 px = full range), or use the scroll wheel over it; a click on a column of the 8-track strip or a box in the Tracks / Returns overview selects that track in Live. New commands `knob` {n, v, end} and `selecttrack` {col | track | ret} (needs the matching Alias8_Live script and a restart of `scribble_strip.py`). While dragging, state packets from Live don't pull the knob back. Double-click on a knob no longer toggles full screen.
- 2026-11-27: Renamed to **Scribble Monitor** (`scribble_strip.py` → `scribble_monitor.py`, `Start Scribble Strip.command` → `Start Scribble Monitor.command`, page title "Scribble Monitor"). The sending script is now `Alias8_Scribble` (was `Alias8_Live`). Same ports and protocol; the GitHub repo is now `scribble-monitor` (the local folder is still `scribble-strip`).
- 2026-11-27: Landscape: the big text (track, macro, value), hint, GR bar and the long pickup meter take only the left third of the window, with font sizes to match; the Colour EQ curve sits just right of them. Portrait unchanged.
