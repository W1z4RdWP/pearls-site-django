source .venv/bin/activate
cd myproject
daphne -b 0.0.0.0 -p 8005 myproject.asgi:application
# python manage.py runserver 0.0.0.0:8005