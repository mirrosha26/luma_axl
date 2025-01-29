import requests

class AccelOnlineAPI:
    def __init__(self, base_url="https://api.accelonline.io"):
        self.base_url = base_url
        self.auth_token = None
        self.refresh_token = None

    def login(self, email: str, password: str, device_id: str = "web-client", device_type: str = "web", remember_me: bool = True) -> dict:
        """Авторизация пользователя"""
        url = f"{self.base_url}/api/v1/authorization/login"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "email": email,
            "password": password,
            "device_id": device_id,
            "device_type": device_type,
            "remember_me": remember_me
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()

        if response_data["success"]:
            self.auth_token = response_data["body"]["accessToken"]
            self.refresh_token = response_data["body"]["refreshToken"]

        return response_data

    def get_webinar(self, webinar_id: str, fields: str = "{ name }") -> dict:
        """Получение информации о вебинаре"""
        url = f"{self.base_url}/api/v1/webinar/{webinar_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }
        params = {"fields": fields}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def create_webinar_user(self, webinar_id: str, email: str, first_name: str,
                          last_name: str, role: str = "guest", send_email: bool = False) -> dict:
        """Создание пользователя вебинара"""
        url = f"{self.base_url}/api/v1/webinar-user"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }
        data = {
            "webinarId": webinar_id,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "role": role,
            "sendEmail": send_email
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def delete_webinar_user(self, user_id: str) -> None:
        """Удаление пользователя вебинара"""
        url = f"{self.base_url}/api/v1/webinar-user/{user_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }
        response = requests.delete(url, headers=headers)
        response.raise_for_status()