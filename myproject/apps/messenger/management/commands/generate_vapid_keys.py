"""
Генерирует пару VAPID-ключей (P-256) для Web Push уведомлений messenger.

Выводит ключи в формате base64url (без padding) — именно такой формат ожидают
и pywebpush на сервере, и PushManager.subscribe() на клиенте.
"""

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


class Command(BaseCommand):
    help = 'Генерирует пару VAPID-ключей (P-256) для Web Push в формате base64url'

    def handle(self, *args, **options):
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        private_raw = private_key.private_numbers().private_value.to_bytes(32, 'big')
        public_raw = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

        private_b64 = _b64url(private_raw)
        public_b64 = _b64url(public_raw)

        self.stdout.write(self.style.SUCCESS('Сгенерированы VAPID ключи.'))
        self.stdout.write('')
        self.stdout.write('Добавьте переменные в .env (или в окружение сервера):')
        self.stdout.write('')
        self.stdout.write(f'VAPID_PUBLIC_KEY={public_b64}')
        self.stdout.write(f'VAPID_PRIVATE_KEY={private_b64}')
        self.stdout.write('VAPID_ADMIN_EMAIL=admin@example.ru')
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                'ВАЖНО: приватный ключ хранить как секрет, не коммитить в репозиторий.'
            )
        )
