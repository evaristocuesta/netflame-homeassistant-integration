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
        # keep verify False by default because many Netflame endpoints have old certs;
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

    # Encender / apagar
    def turn_on(self):
        return self._post({"idOperacion": OP_ONOFF, "on_off": "1"})

    def turn_off(self):
        return self._post({"idOperacion": OP_ONOFF, "on_off": "0"})

    # Leer estado (estado, temperatura, potencia)
    def get_status(self) -> dict:
        raw = self._post({"idOperacion": OP_ESTADO})

        estado = None
        temperatura = None
        potencia = None

        for line in raw.split("\n"):
            if line.startswith("estado="):
                try:
                    estado = int(line.replace("estado=", "").strip())
                except Exception:
                    estado = None
            if line.startswith("temperatura="):
                try:
                    temperatura = float(line.replace("temperatura=", "").strip())
                except Exception:
                    temperatura = None
            if line.startswith("consigna_potencia=") or line.startswith("consigna_pot="):
                try:
                    potencia = int(line.split("=")[1].strip())
                except Exception:
                    potencia = None

        return {
            "raw": raw,
            "estado": estado,
            "temperatura": temperatura,
            "potencia": potencia
        }

    # Asignar potencia
    def set_potencia(self, nivel: int):
        if nivel < 1 or nivel > 9:
            raise ValueError("Nivel de potencia debe ser 1..9")
        return self._post({
            "idOperacion": OP_POTENCIA,
            "potencia": str(nivel)
        })

    # Alarmas
    def get_alarmas(self):
        raw = self._post({"idOperacion": OP_ALARMAS})

        # Try to return a short interpreted string if possible
        for line in raw.split("\n"):
            if "alarma" in line or "alarm" in line or "error" in line:
                return line.strip()
        return raw.strip()
