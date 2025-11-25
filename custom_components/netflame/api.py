import requests
import logging

from .const import (
    BASE_URL,
    OP_ONOFF,
    OP_ESTADO,
    OP_POTENCIA,
    OP_ALARMAS,
)

_LOGGER = logging.getLogger(__name__)

class NetflameApi:
    def __init__(self, username: str, password: str, session: requests.Session = None):
        self.username = username
        self.password = password
        self.session = session or requests.Session()
        # Keep verify False by default because many Netflame endpoints have old certs;
        # administrators should change to True and provide certs if possible.
        self.session.verify = False

    def _post(self, data: dict) -> str:
        try:
            r = self.session.post(
                BASE_URL,
                auth=(self.username, self.password),
                data=data,
                timeout=10
            )
            r.raise_for_status()
            return r.text
        except Exception as e:
            _LOGGER.exception("Netflame POST error: %s", e)
            raise

    # Turn on/off
    def turn_on(self):
        return self._post({"idOperacion": OP_ONOFF, "on_off": "1"})

    def turn_off(self):
        return self._post({"idOperacion": OP_ONOFF, "on_off": "0"})

    # Read status (state, temperature, power)
    def get_status(self) -> dict:
        raw = self._post({"idOperacion": OP_ESTADO})

        status = None
        temperature = None
        power = None

        for line in raw.split("\n"):
            if line.startswith("estado="):
                try:
                    status = int(line.replace("estado=", "").strip())
                except Exception:
                    status = None
            if line.startswith("temperatura="):
                try:
                    temperature = float(line.replace("temperatura=", "").strip())
                except Exception:
                    temperature = None
            if line.startswith("consigna_potencia=") or line.startswith("consigna_pot="):
                try:
                    power = int(line.split("=")[1].strip())
                except Exception:
                    power = None

        return {
            "raw": raw,
            "status": status,
            "temperature": temperature,
            "power": power
        }

    # Set power level
    def set_potencia(self, nivel: int):
        if nivel < 1 or nivel > 9:
            raise ValueError("Power level must be 1..9")
        return self._post({
            "idOperacion": OP_POTENCIA,
            "potencia": str(nivel)
        })

    # Get alarms
    def get_alarms(self):
        raw = self._post({"idOperacion": OP_ALARMAS})

        # Split by lines
        lines = [l.strip() for l in raw.split("\n") if l.strip()]

        # Reproduce eliminarErrores() from the original JavaScript
        fixed_data = [l for l in lines if "error" not in l.lower()]

        # We need at least two clean lines
        if len(fixed_data) < 2:
            return None

        # datos_correctos[1] must be "0"
        if fixed_data[1] != "0":
            return None

        # Get value after "=" in the first correct line
        if "=" in fixed_data[0]:
            return fixed_data[0].split("=", 1)[1].strip()

        return fixed_data[0].strip()
