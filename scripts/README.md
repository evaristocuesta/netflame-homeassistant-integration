# Mock Netflame Server 🔧

Simple local mock server to emulate the Netflame `recepcion_datos_4.cgi` endpoint.

## Run

```bash
python scripts/mock_netflame_server.py --host 127.0.0.1 --port 11417
```

By default it runs on `0.0.0.0:11417`.

## Usage with the integration

In `custom_components/netflame/const.py` comment out the original `BASE_URL` line that points to the production server and add a local URL. Example:

```python
# BASE_URL = "https://easynet9.netflamehome.com:11417/recepcion_datos_4.cgi"  # original production URL (commented during local dev)
BASE_URL = "http://127.0.0.1:11417/recepcion_datos_4.cgi"  # local mock
```

The component will POST to the mock server instead of the remote one.
## Behavior

The mock recognizes these `idOperacion` values and returns simple, predictable responses:

- `1002` (status): returns lines `estado=1`, `temperatura=23.5`, `consigna_potencia=5`
- `1013` (on/off): returns `OK` (see state transition details below)
- `1004` (set power): returns `OK`
- `1079` (alarms): returns `alarma=NONE` and `0` on the following line (to match `get_alarms()` expectations)

If an unknown operation is sent, the mock echoes back the form keys and values for debugging.

## State transition delay

The mock simulates *intermediate* states when the device is turned on or off:

- Turning **on** (`on_off=1`): the mock sets `estado=2` (turning on) for a configurable delay, then transitions to `estado=3` (on).
- Turning **off** (`on_off=0`): the mock sets `estado=1` (turning off) for a configurable delay, then transitions to `estado=0` (off).

The default delay is **20 seconds** to emulate realistic device behavior. You can override the delay at startup using the `--transition-delay` CLI option (value in seconds):

```bash
python scripts/mock_netflame_server.py --transition-delay 5
```

This is useful for quicker local testing; for example, the test suite uses a short delay (`0.1`) to speed up assertions:

```bash
python scripts/mock_netflame_server.py --transition-delay 0.1
```

The chosen delay is logged at startup (e.g. `Using transition delay: 0.1 seconds`).

---

If you want the mock to return other values, edit `scripts/mock_netflame_server.py` or re-run with a different port.

## Running automated tests

Install pytest (recommended in a virtualenv):

```bash
pip install pytest
```

Run the test suite:

```bash
pytest .\tests\test_mock_netflame_server.py -q
```

The tests start the mock server in-process and exercise `NetflameApi` methods (`get_status`, `turn_on`, `turn_off`, `set_power`, `get_alarms`).
