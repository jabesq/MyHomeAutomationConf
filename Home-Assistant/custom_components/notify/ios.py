"""
iOS platform for notify component. Should be put into ~/.homeassistant/custom_components/notify/ios.py.

(Yes, actually notify/ios.py, even though the filename on Gist is notify_ios.py).
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/notify.ios/
"""
import logging

import requests

from homeassistant.components.notify import (
    ATTR_TARGET, ATTR_TITLE, ATTR_TITLE_DEFAULT, ATTR_MESSAGE,
    ATTR_DATA, DOMAIN, BaseNotificationService)

_LOGGER = logging.getLogger(__name__)

PUSH_URL = "https://mj28d17jwj.execute-api.us-west-2.amazonaws.com/prod/push"

# DEPENDENCIES = ["ios"]

def get_service(hass, config):
    """Get the iOS notification service."""
    message = config.get(ATTR_MESSAGE)
    target = config.get(ATTR_TARGET)
    title = config.get(ATTR_TITLE)

    return iOSNotificationService(message, title, target)


# pylint: disable=too-few-public-methods, too-many-arguments
class iOSNotificationService(BaseNotificationService):
    """Implement the notification service for iOS."""

    def __init__(self, message, title, target):
        """Initialize the service."""
        self._message = message
        self._title = title
        self._target = target

    def send_message(self, message="", title=None, target=None, **kwargs):
        """Send a message to the Lambda APNS gateway."""
        data = {
            ATTR_MESSAGE: message,
            ATTR_TARGET: target
        }

        """Don't send the default title because
           it makes Apple Watch notifications look bad"""
        if title != ATTR_TITLE_DEFAULT:
            data[ATTR_TITLE] = title
        elif title == ATTR_TITLE_DEFAULT and self._title is not None:
            data[ATTR_TITLE] = self._title

        if target is None:
            data[ATTR_TARGET] = self._target

        if kwargs.get(ATTR_DATA) is not None:
            data[ATTR_DATA] = kwargs.get(ATTR_DATA)

        response = requests.put(PUSH_URL, json=data, timeout=10)

        if response.status_code not in (200, 201):
            _LOGGER.exception(
                "Error sending message. Response %d: %s:",
                response.status_code, response.reason)