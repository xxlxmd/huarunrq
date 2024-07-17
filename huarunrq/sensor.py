"""Platform for sensor integration."""
from datetime import timedelta
import logging
import requests
import voluptuous as vol
import base64
import time
import random
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_CNO = 'cno'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CNO): vol.Coerce(str),
    vol.Optional(CONF_NAME, default='HuaRunRQ Gas Balance'): vol.Coerce(str),
})

MIN_TIME_BETWEEN_UPDATES = timedelta(hours=1)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    cno = config[CONF_CNO]
    name = config[CONF_NAME]

    add_entities([HuaRunRQSensor(name, cno)], True)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HuaRunRQ sensor based on a config entry."""
    # 从config_entry中获取配置的CNO和传感器名称
    cno = config_entry.data.get(CONF_CNO)
    name = config_entry.title
    # 确保在创建HuaRunRQSensor对象时提供了所有必需的参数
    async_add_entities([HuaRunRQSensor(name, cno)], True)

class HuaRunRQSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, cno):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._cno = cno
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._attributes

    @property
    def device_info(self):
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(self._cno,)},
            name=self._name,
            manufacturer="HuaRunRQ",
            model="Gas Sensor",
            entry_type=DeviceEntryType.SERVICE,
        )

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            # 使用你提供的业务逻辑代码获取所有数据
            data = self.get_data()
            self._state = data["totalGasBalance"]
            self._attributes = data
        except Exception as e:
            _LOGGER.error("Error fetching data: %s", e)
            self._state = None
            self._attributes = {}

    def get_data(self):
        """Get the data from the API."""
        public_key_pem = '''-----BEGIN PUBLIC KEY-----
        MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAIi4Gb8iOGcc05iqNilFb1gM6/iG4fSiECeEaEYN2cxaBVT+6zgp+Tp0TbGVqGMIB034BLaVdNZZPnqKFH4As8UCAwEAAQ==
        -----END PUBLIC KEY-----'''

        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )

        data_to_encrypt = 'e5b871c278a84defa8817d22afc34338#' + str(int(time.time() * 1000)) + '#' + str(random.randint(1000, 9999))

        encrypted_data = public_key.encrypt(
            data_to_encrypt.encode('utf-8'),
            padding.PKCS1v15()
        )

        base64_encrypted_data = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

        request_body = {
            'USER': 'bizH5',
            'PWD': base64_encrypted_data
        }

        base64_encoded_body = base64.urlsafe_b64encode(json.dumps(request_body).encode('utf-8')).decode('utf-8')

        api_url = 'https://mbhapp.crcgas.com/bizonline/api/h5/pay/queryArrears?authVersion=v2&consNo='+self._cno
        headers = {
            'Content-Type': 'application/json, text/plain, */*',
            'Param': base64_encoded_body
        }   
        response = requests.get(api_url, headers=headers)

        # 解析响应中的所有数据
        data = response.json()
        return data["dataResult"]
