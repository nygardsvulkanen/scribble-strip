#!/bin/bash
# Starts the Scribble Monitor's local server (no browser is opened).
# Open http://localhost:8643 yourself in any browser, as many windows as you like.
# It shows Live's status bar messages from the Alias8_Scribble script in big text.
# Keep this window open while you use it; close it (or press Ctrl+C) to stop.

cd "$(dirname "$0")" || exit 1
URL="http://localhost:8643"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No Python 3 found. macOS will offer to install the 'Command Line Developer Tools' -"
  echo "accept that, then double-click this file again."
  python3 --version
  read -r -p "Press Enter to close."
  exit 1
fi

echo "Scribble Monitor running at $URL  (open it in a browser; Ctrl+C or close this window to stop)"
exec python3 scribble_monitor.py
