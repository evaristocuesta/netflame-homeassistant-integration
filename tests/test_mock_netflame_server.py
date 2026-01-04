import importlib.util
import importlib
import os
import sys
import threading
from http.server import HTTPServer

import requests
import time
import pytest

HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(HERE)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

SCRIPT_PATH = os.path.join(PROJECT_ROOT, "scripts", "mock_netflame_server.py")


def _load_mock_module():
    spec = importlib.util.spec_from_file_location("mock_netflame_server", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="function")
def mock_server_module():
    module = _load_mock_module()

    # Speed up scheduled transitions for tests (20s -> 0.1s) by overriding TRANSITION_DELAY
    orig_delay = getattr(module, "TRANSITION_DELAY", None)
    module.TRANSITION_DELAY = 0.1

    server = HTTPServer(("127.0.0.1", 0), module.MockHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://{host}:{port}/"

    yield module, base_url

    # Restore original TRANSITION_DELAY if present
    if orig_delay is not None:
        module.TRANSITION_DELAY = orig_delay

    server.shutdown()
    server.server_close()


def test_status_temperature_and_power_change(mock_server_module):
    module, base_url = mock_server_module

    temps = set()
    powers = set()
    states = set()

    for _ in range(6):
        r = requests.post(base_url, data={"idOperacion": "1002"}, timeout=1)
        r.raise_for_status()
        lines = [l.strip() for l in r.text.splitlines() if l.strip()]
        kv = dict(line.split("=", 1) for line in lines)
        temps.add(float(kv["temperatura"]))
        powers.add(int(kv["consigna_potencia"]))
        states.add(int(kv["estado"]))
        time.sleep(0.05)

    # Temperature should vary across multiple polls (rounded to 1 decimal)
    assert len(temps) >= 2
    assert any(p == 5 for p in powers)
    assert any(s in (0, 1) for s in states)


def test_onoff_sets_and_toggles_state(mock_server_module):
    module, base_url = mock_server_module

    # initial status should be 0
    assert module._STATUS == 0

    # Turn ON: should enter intermediate state 2 immediately, then final 7 shortly
    r = requests.post(base_url, data={"idOperacion": "1013", "on_off": "1"}, timeout=1)
    r.raise_for_status()
    # Response should reflect the intermediate status (2)
    assert "estado=2" in r.text
    assert module._STATUS == 2

    # Wait for the scheduled final transition (fastened to 0.1s in fixture)
    time.sleep(0.2)
    r = requests.post(base_url, data={"idOperacion": "1002"}, timeout=1)
    r.raise_for_status()
    kv = dict(line.split("=", 1) for line in r.text.splitlines() if "=" in line)
    assert int(kv.get("estado", -1)) == 7
    assert module._STATUS == 7

    # Turn OFF: should enter intermediate state 8 immediately, then final 0 shortly
    r = requests.post(base_url, data={"idOperacion": "1013", "on_off": "0"}, timeout=1)
    r.raise_for_status()
    assert "estado=8" in r.text
    assert module._STATUS == 8

    time.sleep(0.2)
    r = requests.post(base_url, data={"idOperacion": "1002"}, timeout=1)
    r.raise_for_status()
    kv = dict(line.split("=", 1) for line in r.text.splitlines() if "=" in line)
    assert int(kv.get("estado", -1)) == 0
    assert module._STATUS == 0

    # Toggle without on_off should schedule the opposite transition depending on current state
    r = requests.post(base_url, data={"idOperacion": "1013"}, timeout=1)
    r.raise_for_status()
    # Since we were 0, toggling should schedule 2 -> 7 and return intermediate 2
    assert "estado=2" in r.text
    assert module._STATUS == 2

    time.sleep(0.2)
    r = requests.post(base_url, data={"idOperacion": "1002"}, timeout=1)
    r.raise_for_status()
    kv = dict(line.split("=", 1) for line in r.text.splitlines() if "=" in line)
    assert int(kv.get("estado", -1)) == 7
    assert module._STATUS == 7


def test_power_sets_value_and_status_reflects_it(mock_server_module):
    module, base_url = mock_server_module

    r = requests.post(base_url, data={"idOperacion": "1004", "potencia": "7"}, timeout=1)
    r.raise_for_status()
    assert r.text.strip() == "OK"
    assert module._POWER == 7

    # Verify via status
    r = requests.post(base_url, data={"idOperacion": "1002"}, timeout=1)
    kv = dict(line.split("=", 1) for line in r.text.splitlines() if "=" in line)
    assert int(kv.get("consigna_potencia", -1)) == 7


def test_alarms_return_two_lines(mock_server_module):
    module, base_url = mock_server_module

    r = requests.post(base_url, data={"idOperacion": "1079"}, timeout=1)
    r.raise_for_status()
    lines = [l.strip() for l in r.text.splitlines() if l.strip()]
    assert len(lines) >= 2
    assert lines[1] == "0"
    if "=" in lines[0]:
        _, val = lines[0].split("=", 1)
    else:
        val = lines[0]
    assert val == "NONE"


def test_unknown_operation_echoes_back(mock_server_module):
    module, base_url = mock_server_module

    r = requests.post(base_url, data={"idOperacion": "9999", "foo": "bar"}, timeout=1)
    r.raise_for_status()
    text = r.text
    assert "foo=bar" in text
    assert "idOperacion=9999" in text