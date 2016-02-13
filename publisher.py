import requests
from ipaddress import ip_address, ip_network
from itertools import chain

class Publisher:

    @staticmethod
    def __fetchgithubips():
        jsonResponse = requests.get("https://api.github.com/meta", auth=("KentonCountyLibrary-Cincypy", "CincyPyCoders2000"))
        ipranges = jsonResponse.json()["hooks"]

        ipranges = [list(ip_network(ip).hosts()) for ip in ipranges]

        # Flatten the matrix to and array
        flat_range = list(chain.from_iterable(ipranges))
        return flat_range

    def in_ip_address_range(self):
        return self.ip in Publisher.__fetchgithubips()

    def __init__(self, ip, sourcebranch, payload):
        # use https://api.github.com/meta to get github ipaddresses
        self.sourcebranch = sourcebranch
        self.payload = payload
        self.ip = ip_address(ip)
