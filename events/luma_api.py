import requests
from typing import List, Dict, Optional
from django.conf import settings

class LumaAPI:
    """Класс для взаимодействия с API Luma"""
    
    BASE_URL = "https://api.lu.ma/public/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {settings.LUMA_API_KEY}",
            "Content-Type": "application/json"
        })
        
        # Настройка прокси из settings
        self.session.proxies = {
            'http': f'http://{settings.PROXY_USER}:{settings.PROXY_PASS}@{settings.PROXY_HOST}:{settings.PROXY_PORT}',
            'https': f'http://{settings.PROXY_USER}:{settings.PROXY_PASS}@{settings.PROXY_HOST}:{settings.PROXY_PORT}'
        }
    
    def get_event_guests(
        self, 
        event_id: str,
        pagination_limit: Optional[int] = None,
        pagination_cursor: Optional[str] = None,
        approval_status: Optional[str] = None,
        sort_column: Optional[str] = None,
        sort_direction: Optional[str] = None
    ) -> Optional[Dict]:
        
        try:
            params = {"event_api_id": event_id}

            if pagination_limit is not None:
                params["pagination_limit"] = pagination_limit
            if pagination_cursor is not None:
                params["pagination_cursor"] = pagination_cursor
            if approval_status is not None:
                params["approval_status"] = approval_status
            if sort_column is not None:
                params["sort_column"] = sort_column
            if sort_direction is not None:
                params["sort_direction"] = sort_direction
            
            response = self.session.get(
                f"{self.BASE_URL}/event/get-guests",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении гостей: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Код ошибки: {e.response.status_code}")
                print(f"Тело ответа: {e.response.text}")
            return None

    def get_all_event_guests(self, event_id: str):
        """
        Получение полного списка гостей для мероприятия с использованием пагинации
        
        Args:
            event_id: ID мероприятия в Luma
            
        Returns:
            Список словарей с информацией о гостях
        """
        all_guests = []
        pagination_cursor = None
        
        while True:
            response = self.get_event_guests(
                event_id=event_id,
                pagination_limit=100,
                pagination_cursor=pagination_cursor,
                sort_column="created_at",
                sort_direction="desc"
            )
            
            if not response:
                break
                
            if 'entries' not in response:
                break
                
            all_guests.extend(response['entries'])
            
            if not response.get('has_more'):
                break
                
            pagination_cursor = response.get('next_cursor')
            
        return all_guests