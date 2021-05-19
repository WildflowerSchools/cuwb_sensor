from tenacity import retry, stop_after_attempt, wait_random_exponential

from cuwb_sensor.network_api import API
from cuwb_sensor.tools.logging import logger


class FailedToStartException(Exception):

    def __init__(self, name):
        super().__init__(f"Failed to start `{name}` cuwbnet")


class FailedToStopException(Exception):

    def __init__(self, name):
        super().__init__(f"Failed to stop `{name}` cuwbnet")


class AnchorsDegradedException(Exception):

    def __init__(self, name, error_messages):
        self.error_messages = error_messages
        super().__init__(f"Anchors at '{name}' in degraded state: {error_messages}")


class Contract(object):
    def __init__(self, network_name):
        self.name = network_name

    @retry(wait=wait_random_exponential(multiplier=1, max=10))
    def ensure_network_is_running(self):
        api = API()
        if not api.is_network_running(self.name):
            api.start_network(self.name)
            if not api.is_network_running(self.name):
                raise FailedToStartException(self.name)

    @retry(wait=wait_random_exponential(multiplier=1, max=10))
    def ensure_network_is_stopped(self):
        api = API()
        if api.is_network_running(self.name):
            api.stop_network(self.name)
            if api.is_network_running(self.name):
                raise FailedToStopException(self.name)

    @retry(wait=wait_random_exponential(multiplier=2, max=10),
           stop=stop_after_attempt(3),
           reraise=True)
    def check_network_health(self):
        logger.info("Checking '{}' network health...".format(self.name))

        api = API()
        anchors = api.get_anchors(self.name)

        degraded_state_errors = []

        if len(anchors) == 0:
            degraded_state_errors.append("No anchors found in CUWB network")

        for a in anchors:
            anchor_name = a.get("name", "UNKNOWN")
            connectivity = a.get("connectivity_state", "")
            synchronization = a.get("synchronization_state", "")

            if not connectivity.lower() == "ethernet and uwb connected":
                degraded_state_errors.append("Anchor '{}' reporting bad connectivity - `{}`".format(anchor_name, connectivity))

            if not synchronization.lower() == "rx and tx synced":
                degraded_state_errors.append("Anchor '{}' reporting bad synchronization - `{}`".format(anchor_name, synchronization))

        if len(degraded_state_errors) > 0:
            logger.error("'{}' network health degraded: {}".format(self.name, degraded_state_errors))
            raise AnchorsDegradedException(self.name, degraded_state_errors)
