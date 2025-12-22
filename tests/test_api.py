import importlib.util
import importlib
import os
import sys
import time
import pytest
import threading
from http.server import HTTPServer

# Make project package importable during tests
HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(HERE)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the const and api modules by path to avoid executing package-level Home Assistant imports
CONST_PATH = os.path.join(PROJECT_ROOT, "custom_components", "netflame", "const.py")
spec_const = importlib.util.spec_from_file_location("custom_components.netflame.const", CONST_PATH)
const_mod = importlib.util.module_from_spec(spec_const)
spec_const.loader.exec_module(const_mod)
# Ensure the const module is importable by its package-style name for relative imports
import sys
sys.modules["custom_components.netflame.const"] = const_mod

API_PATH = os.path.join(PROJECT_ROOT, "custom_components", "netflame", "api.py")
spec = importlib.util.spec_from_file_location("custom_components.netflame.api", API_PATH)
api_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_mod)

NetflameApi = api_mod.NetflameApi
OP_ONOFF = api_mod.OP_ONOFF
OP_POWER = api_mod.OP_POWER
OP_ALARMS = api_mod.OP_ALARMS
OP_STATUS = api_mod.OP_STATUS


# Helpers to start the mock server in-process (duplicate of tests/test_mock_netflame_server fixture helpers)
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "scripts", "mock_netflame_server.py")


def _load_mock_module():
    spec = importlib.util.spec_from_file_location("mock_netflame_server", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DummyResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


class DummySession:
    def __init__(self, response_text="OK"):
        self.response_text = response_text
        self.last = None
        self.verify = True

    def post(self, url, auth=None, data=None, timeout=None):
        self.last = dict(url=url, auth=auth, data=data, timeout=timeout)
        return DummyResponse(self.response_text)


def test_turn_on_off_posts_correct_payload():
    sess = DummySession()
    api = NetflameApi("u", "p", session=sess)

    r = api.turn_on()
    assert sess.last["data"] == {"idOperacion": OP_ONOFF, "on_off": "1"}

    r = api.turn_off()
    assert sess.last["data"] == {"idOperacion": OP_ONOFF, "on_off": "0"}


def test_get_status_parsing_various_fields():
    import math

    raw = "estado=3\ntemperatura=24.5\nconsigna_potencia=7\n"
    sess = DummySession(response_text=raw)
    api = NetflameApi("u", "p", session=sess)

    res = api.get_status()
    assert res["status"] == 3
    assert res["temperature"] == 24.5
    assert res["power"] == 7

    # Accept alternative key name 'consigna_pot'
    raw2 = "estado=0\ntemperatura=20.0\nconsigna_pot=4\n"
    sess2 = DummySession(response_text=raw2)
    api2 = NetflameApi("u", "p", session=sess2)
    res2 = api2.get_status()
    assert res2["power"] == 4

    # Invalid numbers fallback to None or NaN for temperature
    raw3 = "estado=notanint\ntemperatura=NaN\nconsigna_pot=bad\n"
    sess3 = DummySession(response_text=raw3)
    api3 = NetflameApi("u", "p", session=sess3)
    res3 = api3.get_status()
    assert res3["status"] is None
    # float('NaN') is not None, assert that it's NaN
    assert math.isnan(res3["temperature"])
    assert res3["power"] is None


def test_set_power_validation_and_payload():
    sess = DummySession()
    api = NetflameApi("u", "p", session=sess)

    with pytest.raises(ValueError):
        api.set_power(0)
    with pytest.raises(ValueError):
        api.set_power(10)

    api.set_power(5)
    assert sess.last["data"] == {"idOperacion": OP_POWER, "potencia": "5"}


def test_get_alarms_parsing():
    # Normal case
    sess = DummySession(response_text="alarma=NONE\n0\n")
    api = NetflameApi("u", "p", session=sess)
    assert api.get_alarms() == "NONE"

    # Second line not 0 -> None
    sess2 = DummySession(response_text="alarma=NONE\n1\n")
    api2 = NetflameApi("u", "p", session=sess2)
    assert api2.get_alarms() is None

    # Filter out error lines
    sess3 = DummySession(response_text="error: something\nalarma=FOO\n0\n")
    api3 = NetflameApi("u", "p", session=sess3)
    assert api3.get_alarms() == "FOO"


def test_uses_custom_base_url():
    sess = DummySession()
    custom = "http://example.test/recepcion_datos_4.cgi"
    api = NetflameApi("u", "p", session=sess, base_url=custom)
    api.get_status()
    assert sess.last["url"] == custom


@pytest.fixture(scope="function")
def mock_server_module_local():
    # Duplicate of the mock_server_module fixture used elsewhere so this test file can use it
    module = _load_mock_module()
    server = HTTPServer(("127.0.0.1", 0), module.MockHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Speed up scheduled transitions for tests (20s -> 0.1s)
    orig_delay = getattr(module, "TRANSITION_DELAY", None)
    module.TRANSITION_DELAY = 0.1

    base_url = f"http://{host}:{port}/recepcion_datos_4.cgi"

    yield module, base_url

    # Restore original TRANSITION_DELAY if present
    if orig_delay is not None:
        module.TRANSITION_DELAY = orig_delay

    server.shutdown()
    server.server_close()


def test_integration_with_mock_server_status_and_power(mock_server_module_local):
    module, base_url = mock_server_module_local
    # Monkeypatch BASE_URL in the api module loaded above
    orig_base = api_mod.BASE_URL
    api_mod.BASE_URL = base_url

    api = NetflameApi("u", "p")

    # get_status should reflect mock server initial data
    st = api.get_status()
    assert "status" in st

    # set_power should affect subsequent status calls
    api.set_power(7)
    st2 = api.get_status()
    assert st2["power"] == 7

    # turn_on should schedule intermediate 2 then final 3; fixture fastens delay
    module._STATUS = 1
    api.turn_on()
    st3 = api.get_status()
    assert st3["status"] == 2
    time.sleep(0.2)
    st4 = api.get_status()
    assert st4["status"] == 3

    # Restore BASE_URL
    api_mod.BASE_URL = orig_base