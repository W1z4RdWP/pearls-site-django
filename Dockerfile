# Базовый образ, необходим python версии>=3.12
FROM python:3.12-slim

# Задает рабочую диркторию внутри контейнера
WORKDIR /app

# Создает директорию для логов
RUN mkdir -p /var/log/django

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libffi-dev \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
  && rm -rf /var/lib/apt/lists/*


# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 

# переносит файл со списком зависимостей 
COPY ./myproject/requirements.txt /app

# обновляет пипку
RUN pip install --upgrade pip

# загружает зависимости
RUN pip install -r requirements.txt

# Удаляем build-зависимости, чтобы уменьшить размер образа
RUN apt-get purge -y --auto-remove \
    build-essential \
    pkg-config \
    libcairo2-dev \
    libffi-dev \
  && rm -rf /var/lib/apt/lists/*

# переносит содержимое репозитория pearls-site-django в контейнер в директорию /app/
COPY . .

# Задает рабочей директорией myproject
WORKDIR /app/myproject/

### Не используется (нужно задать права и можно применять)
# COPY ./scripts/entrypoint.sh /entrypoint.sh
# ENTRYPOINT ["/entrypoint.sh"]

# Требование на проброс порта 8005
EXPOSE 8005

### Прописано в compose
#CMD ["python", "myproject/manage.py", "runserver", "0.0.0.0:8005"]