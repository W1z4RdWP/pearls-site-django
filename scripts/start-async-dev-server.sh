source .venv/bin/activate
cd myproject
daphne -b 0.0.0.0 -p 8005 myproject.messenger_asgi:application