#!/usr/bin/env python3
"""Scribble Strip.

Listens for the JSON status messages the Alias8_Live script sends over UDP and shows them in a
browser window in big text. Uses only Python's standard library.

    python3 scribble_strip.py            then open http://localhost:8643

The page gets the messages live through Server-Sent Events (/events).
"""

import json
import struct
import os
import queue
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT_UDP = 9877          # must match STATUS_MIRROR_PORT in Alias8_Live/settings.py
PORT_HTTP = 8643         # the viewer page: http://localhost:8643
PORT_CONTROL = 9878      # commands back to the script (must match STATUS_CONTROL_PORT in settings.py)
script_host = ["127.0.0.1"]   # where the script runs (the address its packets come from)
LISTEN_HOST = "127.0.0.1"  # "0.0.0.0" = also accept messages from other computers

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_FILE = os.path.join(HERE, "viewer.html")
SYNTH_DIR = os.path.join(HERE, "synths")   # the synth pictures behind the knobs (settings.py section 14)
IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml"}

clients = []             # one queue per open browser window
clients_lock = threading.Lock()
last_by_type = {}        # the latest message and controller state, sent to a window as soon as it connects


def parse_osc(data):
    """A minimal OSC message reader (address, then string/float/int arguments), for the A8 GR Post
    devices, which send "/a8/gr <track name> <gain reduction in dB>" from Max for Live."""
    def string(pos):
        end = data.index(b"\0", pos)
        return data[pos:end].decode("utf-8", "replace"), (end + 4) & ~3
    address, pos = string(0)
    tags, pos = string(pos)
    args = []
    for t in tags[1:]:
        if t == "s":
            v, pos = string(pos)
        elif t == "f":
            v, pos = struct.unpack(">f", data[pos:pos + 4])[0], pos + 4
        elif t == "i":
            v, pos = struct.unpack(">i", data[pos:pos + 4])[0], pos + 4
        else:
            break
        args.append(v)
    return address, args


def udp_loop(sock):
    while True:
        data, _addr = sock.recvfrom(65535)
        if data[:1] == b"{":
            script_host[0] = _addr[0]
        if data[:1] == b"/":                        # OSC from Max for Live: gain reduction
            try:
                address, args = parse_osc(data)
            except (ValueError, struct.error):
                continue
            if address == "/a8/gr" and len(args) >= 2 and isinstance(args[-1], (int, float)):
                line = json.dumps({"type": "gr", "track": " ".join(str(a) for a in args[:-1]),
                                   "gr": round(float(args[-1]), 1)})
                with clients_lock:
                    for q in list(clients):
                        q.put(line)
            continue
        try:
            msg = json.loads(data.decode("utf-8"))
            if not isinstance(msg, dict) or ("text" not in msg and msg.get("type") not in ("state", "meters")):
                continue
        except ValueError:
            continue
        line = json.dumps(msg)
        if msg.get("type") != "meters":            # levels are only interesting live
            last_by_type[msg.get("type", "message")] = line
        with clients_lock:
            for q in list(clients):
                q.put(line)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html", "/viewer.html"):
            try:
                with open(PAGE_FILE, "rb") as f:
                    body = f.read()
            except OSError:
                self.send_error(404, "viewer.html not found next to scribble_strip.py")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/synths/"):
            from urllib.parse import unquote
            name = os.path.basename(unquote(self.path[len("/synths/"):].split("?")[0]))   # no folders: just a file name
            ext = os.path.splitext(name)[1].lower()
            path = os.path.join(SYNTH_DIR, name)
            if not name or ext not in IMAGE_TYPES or not os.path.isfile(path):
                self.send_error(404)
                return
            with open(path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", IMAGE_TYPES[ext])
            self.send_header("Cache-Control", "max-age=60")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            q = queue.Queue()
            with clients_lock:
                clients.append(q)
            try:
                for line in list(last_by_type.values()):
                    self.wfile.write(("data: %s\n\n" % line).encode("utf-8"))
                self.wfile.flush()
                while True:
                    try:
                        line = q.get(timeout=15)
                        self.wfile.write(("data: %s\n\n" % line).encode("utf-8"))
                    except queue.Empty:
                        self.wfile.write(b": keep-alive\n\n")    # keeps the connection open
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass                                            # the window was closed
            finally:
                with clients_lock:
                    if q in clients:
                        clients.remove(q)
        else:
            self.send_error(404)

    def do_POST(self):
        # the viewer's buttons (e.g. hide the return columns) -> a small JSON command to the script
        if self.path != "/control":
            self.send_error(404)
            return
        try:
            n = min(int(self.headers.get("Content-Length", 0)), 1024)
            cmd = json.loads(self.rfile.read(n).decode("utf-8"))
            if not isinstance(cmd, dict):
                raise ValueError("unknown command")
            if cmd.get("cmd") == "nextrack":            # S / a click on the rack name: the knobs' next rack
                fwd = {"cmd": "nextrack"}
            elif cmd.get("cmd") == "setrack":           # a chip in the rack strip: that rack
                fwd = {"cmd": "setrack", "i": int(cmd.get("i") or 0)}
            elif cmd.get("cmd") == "racktap":           # settings: tap the selected track again = next rack
                fwd = {"cmd": "racktap", "on": bool(cmd.get("on"))}
            elif cmd.get("cmd") == "returns" and cmd.get("page") in ("perform", "track"):
                fwd = {"cmd": "returns", "page": cmd["page"]}
                if cmd.get("cycle"):
                    fwd["cycle"] = True                 # R / the RET button: the next state (all -> ! -> none)
                elif cmd.get("mode") in ("all", "!", "none"):
                    fwd["mode"] = cmd["mode"]
                else:
                    fwd["hide"] = bool(cmd.get("hide"))
            else:
                raise ValueError("unknown command")
            out = json.dumps(fwd).encode("utf-8")
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(out, (script_host[0], PORT_CONTROL))
            s.close()
        except (ValueError, OSError) as e:
            self.send_error(400, str(e))
            return
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        pass                                                    # keep the Terminal window quiet


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((LISTEN_HOST, PORT_UDP))
    except OSError as e:
        print("Can't listen on UDP port %d (is the viewer already running?): %s" % (PORT_UDP, e))
        sys.exit(1)
    threading.Thread(target=udp_loop, args=(sock,), daemon=True).start()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT_HTTP), Handler)
    except OSError as e:
        print("Can't open http://localhost:%d (is the viewer already running?): %s" % (PORT_HTTP, e))
        sys.exit(1)
    server.daemon_threads = True
    print("Scribble Strip: http://localhost:%d  (listening for UDP on port %d)" % (PORT_HTTP, PORT_UDP))
    print("Keep this window open. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
