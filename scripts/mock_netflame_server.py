#!/usr/bin/env python3
"""Lightweight mock server for Netflame.

Usage:
  python scripts/mock_netflame_server.py [--host HOST] [--port PORT]

Default: HOST=0.0.0.0 PORT=11417

The server accepts POST requests and expects form-encoded
parameters like idOperacion and others. It returns plain text responses similar to
what the real Netflame endpoint returns so you can run the integration locally.
"""
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import logging
import threading

LOG = logging.getLogger("mock_netflame")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())

OP_ONOFF = "1013"
OP_STATUS = "1002"
OP_POWER = "1004"
OP_ALARMS = "1079"

import random

# Mutable mock state
_STATUS = 0  # 0 = off, 1 = turning off, 2 = turning on, 3 = on, 
_TEMPERATURE = 23.5
_POWER = 5

# Lock and timer to manage delayed transitions (e.g., 2 -> 3, 1 -> 0)
_STATE_LOCK = threading.Lock()
_transition_timer = None
# Default transition delay in seconds; configurable via CLI --transition-delay
TRANSITION_DELAY = 20.0

def _schedule_transition(intermediate_status, final_status, delay=None):
    """Set intermediate status immediately and schedule final_status after delay seconds.

    If `delay` is None, uses the module-level `TRANSITION_DELAY` value so this
    behavior can be configured at startup.
    """
    global _STATUS, _transition_timer
    if delay is None:
        delay = TRANSITION_DELAY
    with _STATE_LOCK:
        # cancel any pending transition
        if _transition_timer is not None:
            try:
                _transition_timer.cancel()
            except Exception:
                pass
            _transition_timer = None
        _STATUS = intermediate_status
        LOG.info("Scheduled state change: %s -> %s in %s seconds", intermediate_status, final_status, delay)

        def _do_final():
            global _STATUS, _transition_timer
            with _STATE_LOCK:
                _STATUS = final_status
                _transition_timer = None
            LOG.info("State transitioned to %s", final_status)

        _transition_timer = threading.Timer(delay, _do_final)
        _transition_timer.daemon = True
        _transition_timer.start()

class MockHandler(BaseHTTPRequestHandler):
    def _send_text(self, text: str, code: int = 200):
        b = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        LOG.info("POST %s", self.path)

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)
        id_op = data.get("idOperacion", [None])[0]

        LOG.info("idOperacion=%s", id_op)

        # Use globals to persist changes across requests
        global _STATUS, _TEMPERATURE, _POWER

        if id_op == OP_STATUS:
            # Change temperature slightly on each status call
            delta = random.uniform(-0.5, 0.5)
            _TEMPERATURE = round(_TEMPERATURE + delta, 1)
            resp = f"estado={_STATUS}\ntemperatura={_TEMPERATURE}\nconsigna_potencia={_POWER}\n"
            self._send_text(resp)
            return

        if id_op == OP_ONOFF:
            # Expect 'on_off' parameter set to '1' or '0'
            on_off = data.get("on_off", [None])[0]
            if on_off == "0":
                # Transition: set to '1' (turning off) for TRANSITION_DELAY then to '0' (off)
                _schedule_transition(8, 0)
                resp = f"estado={_STATUS}\n"
            elif on_off == "1":
                # Transition: set to '2' (turning on) for TRANSITION_DELAY then to '3' (on)
                _schedule_transition(2, 7)
                resp = f"estado={_STATUS}\n"
            else:
                # Toggle if parameter missing or invalid: schedule opposite transition
                if _STATUS == 7:
                    _schedule_transition(8, 0)
                else:
                    _schedule_transition(2, 7)
                resp = f"estado={_STATUS}\n"
            self._send_text(resp)
            return

        if id_op == OP_POWER:
            potencia = data.get("potencia", [None])[0]
            if potencia is not None:
                try:
                    _POWER = int(potencia)
                except Exception:
                    pass
            resp = "OK\n"
            self._send_text(resp)
            return

        if id_op == OP_ALARMS:
            # First line contains value, second must be '0' per integration's expectations
            resp = "alarma=N\n0\n"
            self._send_text(resp)
            return

        # Unknown operation: echo back keys for debugging
        resp_lines = [f"{k}={v[0]}" for k, v in data.items()]
        self._send_text("\n".join(resp_lines) + "\n")

    def log_message(self, format, *args):
        # Avoid default logging to stderr
        LOG.info(format % args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=11417, type=int)
    parser.add_argument("--transition-delay", type=float, default=None,
                        help="Delay in seconds for intermediate->final state transitions (default: 20)")
    args = parser.parse_args()

    # Allow CLI to override default transition delay
    global TRANSITION_DELAY
    if args.transition_delay is not None:
        TRANSITION_DELAY = float(args.transition_delay)

    server = HTTPServer((args.host, args.port), MockHandler)
    LOG.info("Mock Netflame server running at http://%s:%d/", args.host, args.port)
    LOG.info("Using transition delay: %s seconds", TRANSITION_DELAY)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("Shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
