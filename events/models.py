from django.db import models
from django.conf import settings
from .accel_api import AccelOnlineAPI
from .luma_api import LumaAPI

class Event(models.Model):
    title = models.CharField('Название', max_length=255)
    luma_event_id = models.CharField('ID мероприятия Luma', max_length=255)
    axl_webinar_id = models.CharField('ID вебинара в AXL', max_length=255)
    axl_pending_webinar_id = models.CharField('ID вебинара в AXL (ожидание)', max_length=255, null=True, blank=True)
    is_active = models.BooleanField('Активно', default=False)
    axl_connect = models.BooleanField('Подключение к AXL', default=False)
    axl_pending_webinar_connect = models.BooleanField('Подключение к AXL (ожидание)', default=False)
    luma_connect = models.BooleanField('Подключение к Luma', default=False)
    
    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.axl_webinar_id:
            try:
                accel_client = AccelOnlineAPI()
                accel_client.login(settings.ACCEL_API_EMAIL, settings.ACCEL_API_PASSWORD)

                response = accel_client.get_webinar(self.axl_webinar_id)
                if response.get("success"):
                    self.axl_connect = True
                else:
                    self.axl_connect = False
            except Exception:
                self.axl_connect = False

        if self.axl_pending_webinar_id:
            try:
                accel_client = AccelOnlineAPI()
                accel_client.login(settings.ACCEL_API_EMAIL, settings.ACCEL_API_PASSWORD)

                response = accel_client.get_webinar(self.axl_pending_webinar_id)
                if response.get("success"):
                    self.axl_pending_webinar_connect = True
                else:
                    self.axl_pending_webinar_connect = False
            except Exception:
                self.axl_pending_webinar_connect = False
        else:
            self.axl_pending_webinar_connect = False

        if self.luma_event_id:
            try:
                luma_client = LumaAPI()
                response = luma_client.get_event_guests(
                    event_id=self.luma_event_id,
                    pagination_limit=100
                )
                if isinstance(response, dict) and response.get('message') == 'No access to event':
                    self.luma_connect = False
                else:
                    self.luma_connect = response is not None
            except Exception:
                self.luma_connect = False
        
        super().save(*args, **kwargs)



class EventClient(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('approved', 'Подтвержден'),
        ('pending_approval', 'Ожидает'),
        ('waitlist', 'Лист ожидания'),
        ('declined', 'Отменен'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name='Событие')
    
    # Поля клиента
    name = models.CharField('ФИО', max_length=255)
    email = models.EmailField('Email')
    axl_id = models.CharField('ID в AXL', max_length=255, blank=True, null=True)
    
    # Поля события
    approval_status = models.CharField('Статус', max_length=20, choices=APPROVAL_STATUS_CHOICES)
    registered_at = models.DateTimeField('Дата регистрации', null=True, blank=True)
    check_in_qr_code = models.CharField('QR код', max_length=255, null=True, blank=True)
    ticket_name = models.CharField('Название билета', max_length=255, null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Участник события'
        verbose_name_plural = 'Участники событий'
        unique_together = ['event', 'email']

    def __str__(self):
        return f"{self.name} - {self.event.title}"