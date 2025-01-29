import requests

event_id = "evt-CuR8M2YCz3sSXFr"
LUMA_API_KEY = 'secret-DnXl6Pynj6kVK0oj7oqGZ5mHK'


def get_guests_page(event_id, LUMA_API_KEY, page_cursor=None):
    url = "https://api.lu.ma/public/v1/event/get-guests"

    params = {
        "event_api_id": event_id,
        "pagination_limit": 100,
        "sort_column": "created_at",
        "sort_direction": "desc"
    }

    if page_cursor:
        params["pagination_cursor"] = page_cursor

    headers = {
        "Authorization": f"Bearer {LUMA_API_KEY}",
        "Content-Type": "application/json"
    }

    # Настройка прокси с аутентификацией
    proxy_host = "45.153.20.239"
    proxy_port = "11534"
    proxy_user = "3Sd0K6"
    proxy_pass = "W7yGsP"

    proxies = {
        'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
    }

    try:
        response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None

# Использование:
page_cursor = None
page_num = 1

while True:
    page_data = get_guests_page(event_id, LUMA_API_KEY, page_cursor)

    if not page_data:
        break

    print(f"\nСтраница {page_num}")
    print("-" * 50)

    if 'entries' in page_data:
        for entry in page_data['entries']:
            guest = entry['guest']
            print(f"Гость: {guest['name']} - {guest['email']}")
            print(f"Статус: {guest['approval_status']}")
            print(f"Зарегистрирован: {guest['registered_at']}")
            print(f"QR код: {guest['check_in_qr_code']}")
            print("Билет:", guest['event_ticket']['name'])
            print("-" * 50)

    if not page_data.get('has_more'):
        break

    page_cursor = page_data.get('next_cursor')
    page_num += 1