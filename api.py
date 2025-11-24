import requests
import logging

from .const import BASE_URL, OP_ONOFF, OP_ESTADO

_LOGGER = logging.getLogger(__name__)


class NetflameApi:
    def __init__(self, username: str, password: str, session: requests.Session = None):
        self.username = username
        self.password = password
        self.session = session or requests.Session()
        self.session.verify = False  # Certificado viejo

    def _post(self, data: dict) -> str:
        try:
            r = self.session.post(
                BASE_URL,
                auth=(self.username, self.password),
                data=data,
                timeout=5
            )
            r.raise_for_status()
            return r.text
        except Exception as e:
            _LOGGER.error("Netflame POST error: %s", e)
            raise

    def turn_on(self):
        return self._post({"idOperacion": OP_ONOFF, "on_off": "1"})

    def turn_off(self):
        return self._post({"idOperacion": OP_ONOFF, "on_off": "0"})

    def get_status(self) -> dict:
        raw = self._post({"idOperacion": OP_ESTADO})
        estado = None

        for line in raw.split("\n"):
            if line.startswith("estado="):
                estado = int(line.replace("estado=", "").strip())

        return {
            "raw": raw,
            "estado": estado
        }
