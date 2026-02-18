# React + Vite

Для работы программы нужно запустить 3 сервиса:

- django.wsgi (порт 8005 в dev-режиме и порт 8000 в prod-режиме)

- django.asgi (порт 8006 в dev-режиме и порт 8001 в prod-режиме)

- vite (порт 3000)

## Как запустить в dev
**django.wsgi** 

```bash
cd /opt/pearls-site-django/myproject
source ../.venv/bin/activate
python manage.py runserver 0.0.0.0:8005
```

**django.asgi**

```bash
cd /opt/pearls-site-django/myproject
source ../.venv/bin/activate
daphne -b 0.0.0.0 -p 8006 myproject.messenger_asgi:application
```

**vite**
```bash
cd /opt/pearls-site-django/frontend
npm run dev
```

