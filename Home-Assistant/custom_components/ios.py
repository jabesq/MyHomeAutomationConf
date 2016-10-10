"""
Native Home Assistant iOS app component. Should be put into ~/.homeassistant/custom_components/ios.py.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/ios/
"""
import os
import json
import logging
import requests

import homeassistant.loader as loader

from homeassistant.const import (
    EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP)

from homeassistant.components.notify import (ATTR_TARGET, ATTR_TITLE,
                                             ATTR_MESSAGE, ATTR_DATA)

from homeassistant.components.http import HomeAssistantView

_LOGGER = logging.getLogger(__name__)

PUSH_URL = "https://mj28d17jwj.execute-api.us-west-2.amazonaws.com/prod/push"

DOMAIN = "ios"

DEPENDENCIES = ["http"]

DEVICES_FILE = "ios_devices.conf"

DEVICE_IDENTIFIED = "device_identified"

DEVICES = None

PUSH_CONFIGURATION = None

def config_from_file(filename, config=None):
    """Small configuration file management function."""
    if config:
        # We"re writing configuration
        try:
            with open(filename, "w") as fdesc:
                fdesc.write(json.dumps(config))
        except IOError as error:
            _LOGGER.error("Saving config file failed: %s", error)
            return False
        return True
    else:
        # We"re reading config
        if os.path.isfile(filename):
            try:
                with open(filename, "r") as fdesc:
                    return json.loads(fdesc.read())
            except IOError as error:
                _LOGGER.error("Reading config file failed: %s", error)
                # This won"t work yet
                return False
        else:
            return {}


def setup(hass, config):

    DEVICES = config_from_file(hass.config.path(DEVICES_FILE))

    app_config = config[DOMAIN]
    push_categories = app_config.get("push_categories", [])
    
    discovery = loader.get_component("discovery")
    device_tracker = loader.get_component("device_tracker")
    zeroconf = loader.get_component("zeroconf")
    zeroconf.setup(hass, config)

    hass.wsgi.register_view(iOSAppPushConfigView(hass, push_categories))

    hass.wsgi.register_view(iOSAppIdentifyDeviceView(hass))

    def device_identified(event):
        print("DEVICE IDENTIFIED EVENT FIRED", event)
        permanentID = event.data.get("device").get("permanentID")
        DEVICES[permanentID] = event.data
        if not config_from_file(hass.config.path(DEVICES_FILE), DEVICES):
            _LOGGER.error("failed to save config file")

    hass.bus.listen(DEVICE_IDENTIFIED, device_identified)

    return True

def notify(title="", message="", target=""):
    data = {ATTR_MESSAGE: message, ATTR_TITLE: title, ATTR_TARGET: target}

    response = requests.put(PUSH_URL, json=data, timeout=10)

    if response.status_code != 200:
        _LOGGER.exception("Error sending message. Response %d: %s:",
                          response.status_code, response.reason)

class iOSAppPushConfigView(HomeAssistantView):
    requires_auth = False
    url = "/api/ios/push"
    name = "api:ios:push"

    def __init__(self, hass, push_categories):
        super().__init__(hass)
        self.push_categories = push_categories

    def get(self, request):
        return self.json(self.push_categories)

class iOSAppIdentifyDeviceView(HomeAssistantView):
    requires_auth = False
    url = "/api/ios/identify"
    name = "api:ios:identify"

    def __init__(self, hass):
        super().__init__(hass)

    def post(self, request):
        print("IDENTIFY DEVICE DATA", request.json)
        self.hass.bus.fire(DEVICE_IDENTIFIED, request.json)
        return self.json({"status": "ok"})