from django.apps import AppConfig
from django.core.management import call_command
import threading


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'

    def ready(self):
        # Избегаем двойного запуска при использовании автоперезагрузки
        import os
        if os.environ.get('RUN_MAIN', None) != 'true':
            # Запускаем в отдельном потоке, чтобы не блокировать запуск Django
            thread = threading.Thread(
                target=call_command,
                args=('get_luma_guests',)
            )
            thread.daemon = True 
            thread.start()
