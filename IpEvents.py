import requests

with open("IpToken.txt", "r") as f:
    TOKEN = f.read().strip()


class IpInfo:
    def __init__(self, ip=None):
        self.ip = ip

    def get_ip_info(self):
        if self.ip:
            url = f"https://ipinfo.io/{self.ip}?token={TOKEN}"
        else:
            url = f"https://ipinfo.io?token={TOKEN}"

        response = requests.get(url)
        response.raise_for_status()

        return response.json()