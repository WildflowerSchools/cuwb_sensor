import requests

from cuwb_sensor.tools.logging import logger


class API(object):
    def __init__(self, hostname="10.22.0.170:5000"):
        self.BASE_URL = f"http://{hostname}"

    def _request(self, endpoint, method="GET", json=None):
        url = "/".join([self.BASE_URL, endpoint])
        return requests.request(url=url,
                                method=method,
                                json=json,
                                timeout=3)

    def _get(self, endpoint):
        return self._request(endpoint, "GET")

    def _post(self, endpoint, json=None):
        if json is None:
            json = dict()

        return self._request(endpoint, "POST", json=json)

    def get_networks(self):
        res = self._get("cuwbnets")
        return res.json()

    def start_network(self, name):
        res = self._post(endpoint="/".join(["cuwbnets", name]),
                         json={"action": "start"})

        return res.json().get("status") == "success"

    def stop_network(self, name):
        res = self._post(endpoint="/".join((["cuwbnets", name])),
                         json={"action": "stop"})
        return res.json().get("status") == "success"

    def is_network_running(self, name):
        res = self._get("/".join((["cuwbnets", name])))
        cuwbnets = res.json().get("cuwbnets")
        if cuwbnets:
            return cuwbnets[0].get("running")
        return False

    def get_devices(self, name):
        res = self._get("/".join((["cuwbnets", name, "devices"])))
        return res.json().get("devices")

    def get_anchors(self, name):
        devices = self.get_devices(name)

        anchors = []
        for d in devices:
            try:
                if d.get("interfaces")[0].get("roles")[0].get("name") == "SEEDER":
                    anchors.append(d)
            except Exception as e:
                logger.error("Failed parsing devices: {}".format(e))

        return anchors

    def get_tags(self, name):
        devices = self.get_devices(name)

        tags = []
        for d in devices:
            try:
                if d.get("interfaces")[0].get("roles")[0].get("name") == "DEFAULT TAG":
                    tags.append(d)
            except Exception as e:
                logger.error("Failed parsing devices: {}".format(e))

        return tags
