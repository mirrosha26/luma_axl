from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.dateparse import parse_datetime
from events.luma_api import LumaAPI
from events.models import Event, EventClient
from events.accel_api import AccelOnlineAPI
import time
from events.accel_api import update_axl_contact


class Command(BaseCommand):
    help = 'Получение списка гостей мероприятий Luma'

    def handle(self, *args, **options):
        self._process_guests()
        
    def _process_guests(self):
        luma_client = LumaAPI()
        accel_connect = AccelOnlineAPI()
        accel_connect.login(settings.ACCEL_API_EMAIL, settings.ACCEL_API_PASSWORD)

        events = Event.objects.filter(axl_connect=True, luma_connect=True, is_active=True)

        for event in events:
            self.stdout.write(self.style.SUCCESS(f'\nПолучение гостей для события: {event.title}'))
            guests = luma_client.get_all_event_guests(event.luma_event_id)
            
            if not guests:
                self.stdout.write(self.style.WARNING(f'Нет гостей для события {event.title}'))
                continue

            self.stdout.write(self.style.SUCCESS(f'Получено гостей: {len(guests)}'))
            
            for entry in guests:
                guest = entry['guest']
                if not guest.get('email'):
                    continue

                self._process_single_guest(event, guest, accel_connect)

    def _process_single_guest(self, event, guest, accel_connect):
        """Обработка одного гостя"""
        email = guest.get('email')
        status = guest.get('approval_status')
        
        # Проверяем, нужно ли сохранять не approved записи
        if not event.axl_pending_webinar_connect and status != 'approved':
            # Если запись существует, удаляем её
            event_client = EventClient.objects.filter(event=event, email=email).first()
            if event_client:
                if event_client.axl_id:
                    try:
                        accel_connect.delete_webinar_user(event_client.axl_id)
                        self.stdout.write(self.style.SUCCESS(
                            f"Удален пользователь из Accel Online: {email}"
                        ))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"Ошибка при удалении пользователя из Accel Online: {str(e)}"
                        ))
                event_client.delete()
                self.stdout.write(self.style.WARNING(f'Удалена запись для {email} со статусом {status}'))
            return

        event_client = EventClient.objects.filter(event=event, email=email).first()
        
        if not event_client:
            self._create_guest(event, guest, accel_connect)
        else:
            self._update_guest_status(event_client, status, guest, accel_connect)

    def _create_guest(self, event, guest, accel_connect):
        """Создание нового гостя"""
        ticket_price = guest.get('event_ticket', {}).get('amount', 0) / 100 if guest.get('event_ticket') else 0
        
        event_client = EventClient.objects.create(
            event=event,
            email=guest.get('email'),
            name=guest.get('name', ''),
            approval_status=guest.get('approval_status', 'pending'),
            registered_at=parse_datetime(guest.get('registered_at')) if guest.get('registered_at') else None,
            check_in_qr_code=guest.get('check_in_qr_code'),
            ticket_name=guest.get('event_ticket', {}).get('name', '') if guest.get('event_ticket') else None,
            phone=guest.get('phone_number'),
            utm=guest.get('custom_source'),
            price=ticket_price
        )
        
        self._create_axl_user(event, event_client, accel_connect)
        
        self.stdout.write(f"Создана запись: {event_client.name}")
        self.stdout.write('-' * 50)

    def _update_guest_status(self, event_client, new_status, guest, accel_connect):
        """Обновление статуса существующего гостя"""
        if event_client.approval_status != new_status:
            old_status = event_client.approval_status
            event_client.approval_status = new_status
            
            # Обновляем дополнительные поля
            if guest.get('phone_number'):
                event_client.phone = guest.get('phone_number')
            if guest.get('custom_source'):
                event_client.utm = guest.get('custom_source')
            if guest.get('event_ticket'):
                event_client.ticket_name = guest.get('event_ticket', {}).get('name')
                event_client.price = guest.get('event_ticket', {}).get('amount', 0) / 100
            
            event_client.save()
            
            # Если есть AXL ID, удаляем пользователя из старого вебинара
            if event_client.axl_id:
                try:
                    accel_connect.delete_webinar_user(event_client.axl_id)
                    event_client.axl_id = None
                    event_client.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Удален пользователь из Accel Online: {event_client.email}"
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Ошибка при удалении пользователя из Accel Online: {str(e)}"
                    ))
            
            # Создаем пользователя в новом вебинаре
            self._create_axl_user(event_client.event, event_client, accel_connect)
            self.stdout.write(
                self.style.WARNING(f'Статус гостя {event_client.email} изменен на {new_status}')
            )

    def _create_axl_user(self, event, event_client, accel_connect):
        """Создание пользователя в AXL"""
        webinar_id = None
        if event_client.approval_status == 'approved' and event.axl_connect:
            webinar_id = event.axl_webinar_id
        elif event.axl_pending_webinar_connect:
            webinar_id = event.axl_pending_webinar_id

        if event.axl_connect and webinar_id:
            try:
                response = accel_connect.create_webinar_user(
                    webinar_id=webinar_id,
                    email=event_client.email,
                    first_name=event_client.name.split()[0] if event_client.name else "Гость",
                    last_name=" ".join(event_client.name.split()[1:]) if event_client.name and len(event_client.name.split()) > 1 else "Н/Д"
                )
                event_client.axl_id = response.get('body', '')
                event_client.save()
                self.stdout.write(self.style.SUCCESS(f"Создан пользователь в Accel Online: {event_client.email}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка при создании пользователя в Accel Online: {str(e)}"))

        try:
            update_axl_contact(
                email=event_client.email,
                ticket_name=event_client.ticket_name or "",
                phone=event_client.phone or "",
                status=event_client.approval_status,
                utm=event_client.utm or "",
                price=event_client.price or ""
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при обновлении контакта в AXL: {str(e)}"))