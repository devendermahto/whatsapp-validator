import requests
import json


class EvolutionAPI:
    def __init__(self, api_url, instance_name, api_key):
        self.api_url = api_url.rstrip('/')
        self.instance_name = instance_name
        self.api_key = api_key
        self.headers = {
            'apikey': api_key,
            'Content-Type': 'application/json'
        }

    def check_connection(self):
        url = f"{self.api_url}/instance/connectionState/{self.instance_name}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return True, data
            return False, None
        except Exception as e:
            return False, str(e)

    def check_number(self, phone_number):
        url = f"{self.api_url}/chat/whatsappNumbers/{self.instance_name}"
        payload = {"numbers": [phone_number]}
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._parse_response(data, phone_number)
            else:
                return f"<code>{phone_number}</code> ⏳", "error"
        except Exception as e:
            return f"<code>{phone_number}</code> ⏳", "error"

    def _parse_response(self, data, phone_number):
        try:
            results = data.get('response', [])
            if results and len(results) > 0:
                result = results[0]
                exists = result.get('exists', False)
                if exists:
                    return f"<code>{phone_number}</code> ✅", "valid"
                else:
                    return f"<code>{phone_number}</code> ⛔️", "invalid"
            return f"<code>{phone_number}</code> ⛔️", "invalid"
        except Exception:
            return f"<code>{phone_number}</code> ⏳", "error"