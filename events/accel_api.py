import requests
import json
from django.conf import settings

def create_axl_request(email, ticket_name, phone, status, utm, price):
    payload = {
        "scenarioId": f"{settings.ACCEL_API_SCENARIO_ID}",
        "contactData": {
            "email": email,
        },
        "data": {
            "luma_ticket_name": ticket_name,
            "phone": phone,
            "luma_status": status,
            "luma_utm": utm,
            "luma_ticket_price": price
        }
    }
    
    return payload

def update_axl_contact(email, ticket_name, phone, status, utm, price):
    API_URL = "https://admin.accelonline.io"
    HEADERS = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.ACCEL_API_KEY}'
    }
    
    try:
        payload = create_axl_request(
            email=email,
            ticket_name=ticket_name,
            phone=phone,
            status=status,
            utm=utm,
            price=price
        )
        
        response = requests.post(
            f"{API_URL}/api/v1/scenario/run",
            data=json.dumps(payload),
            headers=HEADERS
        )
        
        response.raise_for_status()
        result = response.json()
        
        if result:
            print(f"Контакт успешно обновлен: {email}")
        return result
        
    except Exception as e:
        print(f"Ошибка при обновлении контакта {email}: {str(e)}")
        return None


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