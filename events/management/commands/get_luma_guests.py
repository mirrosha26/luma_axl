from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.dateparse import parse_datetime
from events.luma_api import LumaAPI
from events.models import Event, Client, EventClient
from events.accel_api import AccelOnlineAPI
import time


class Command(BaseCommand):
    help = 'Получение списка гостей мероприятий Luma'

    def handle(self, *args, **options):
        self._process_guests()

    def _process_guests(self):
        luma_client = LumaAPI()
        accel_client = AccelOnlineAPI()
        accel_client.login(settings.ACCEL_API_EMAIL, settings.ACCEL_API_PASSWORD)

        events = Event.objects.filter(axl_connect=True, luma_connect=True, is_active=True)

        for event in events:
            self.stdout.write(self.style.SUCCESS(f'\nПолучение гостей для события: {event.title}'))
            guests = luma_client.get_all_event_guests(event.luma_event_id)
            
            if guests:
                self.stdout.write(self.style.SUCCESS(f'Получено гостей: {len(guests)}'))
                
                # Собираем информацию о всех гостях из Luma
                luma_guests_status = {}
                for entry in guests:
                    guest = entry['guest']
                    if guest.get('email'):
                        luma_guests_status[guest.get('email')] = guest.get('approval_status')

                # Собираем emails всех актуальных гостей
                current_guest_emails = set()
                
                # Обрабатываем только approved гостей
                for entry in guests:
                    guest = entry['guest']
                    
                    # Пропускаем гостей без email или не со статусом approved
                    if not guest.get('email') or guest.get('approval_status') != 'approved':
                        continue
                        
                    current_guest_emails.add(guest.get('email'))
                    
                    # Создаем или обновляем клиента только для approved гостей
                    client, created = Client.objects.update_or_create(
                        email=guest.get('email'),
                        defaults={
                            'name': guest.get('name', 'Н/Д'),
                        }
                    )
                    
                    # Создаем или обновляем связь клиента с событием
                    event_client, ec_created = EventClient.objects.update_or_create(
                        event=event,
                        client=client,
                        defaults={
                            'approval_status': guest.get('approval_status', 'pending'),
                            'registered_at': parse_datetime(guest.get('registered_at')) if guest.get('registered_at') else None,
                            'check_in_qr_code': guest.get('check_in_qr_code'),
                            'ticket_name': guest.get('event_ticket', {}).get('name', 'Н/Д') if guest.get('event_ticket') else None,
                        }
                    )
                    
                    # Если связь создана впервые, создаем пользователя в Accel Online
                    if ec_created and event.axl_webinar_id:
                        try:
                            response = accel_client.create_webinar_user(
                                webinar_id=event.axl_webinar_id,
                                email=client.email,
                                first_name=client.name.split()[0] if client.name else "Гость",
                                last_name=" ".join(client.name.split()[1:]) if client.name and len(client.name.split()) > 1 else "Н/Д"
                            )
                            # Изменяем доступ к ID пользователя в ответе
                            print(response)
                            event_client.client.axl_id = response.get('body', '')
                            event_client.client.save()
                            self.stdout.write(self.style.SUCCESS(f"Создан пользователь в Accel Online: {client.email}"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Ошибка при создании пользователя в Accel Online: {str(e)}"))
                    status = 'Создан' if created else 'Обновлен'
                    ec_status = 'Создана' if ec_created else 'Обновлена'
                    
                    self.stdout.write(f"Клиент {status}: {client.name}")
                    self.stdout.write(f"Связь с событием {ec_status}")
                    self.stdout.write('-' * 50)

                # Находим записи, где статус изменился с approved на другой
                event_clients = EventClient.objects.filter(
                    event=event,
                    client__email__isnull=False,
                    approval_status='approved'
                )
                
                for ec in event_clients:
                    # Проверяем, изменился ли статус в Luma
                    luma_status = luma_guests_status.get(ec.client.email)
                    if luma_status is None or luma_status != 'approved':
                        # Если статус изменился или гостя больше нет в списке
                        if ec.client.axl_id and event.axl_webinar_id:
                            try:
                                accel_client.delete_webinar_user(ec.client.axl_id)
                                self.stdout.write(self.style.SUCCESS(
                                    f"Удален пользователь из Accel Online: {ec.client.email}"
                                ))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(
                                    f"Ошибка при удалении пользователя из Accel Online: {str(e)}"
                                ))
                        ec.delete()
                        self.stdout.write(
                            self.style.WARNING(f'Удалена связь с гостем {ec.client.email} (статус изменился или гость удален)')
                        )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Нет гостей для события {event.title}')
                )