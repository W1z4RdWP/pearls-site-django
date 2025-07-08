#!/bin/bash

set -e  # Прервать выполнение при ошибке

git pull

source .venv/bin/activate # Активация виртуального окружения
cd myproject # Переход в директорию проекта

if [ -d staticfiles ]; then
    echo "Меняем владельца staticfiles/ на django-user"
    sudo chown django-user:django-user -R staticfiles/

    echo "Удаляем папку staticfiles/"
    sudo rm -rf staticfiles
else
    echo "Папка staticfiles не найдена, пропускаю chown и удаление."
fi

echo "Собираем статику Django"
python manage.py collectstatic --noinput

echo "Меняем владельца staticfiles/ на www-data"
sudo chown www-data:www-data -R staticfiles/

echo "Выполняем миграции"
python manage.py migrate

echo "Проверяем проект Django"
python manage.py check

echo "Готово!"
