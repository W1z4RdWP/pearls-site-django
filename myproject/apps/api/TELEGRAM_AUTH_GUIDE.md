# Руководство по авторизации через Telegram с JWT токенами

## Обзор

Система авторизации через Telegram использует JWT токены для безопасной передачи учетных данных. Токены имеют ограниченное время жизни (10 минут) и содержат зашифрованные данные пользователя.

## API Endpoints

### 1. Генерация токена авторизации

**URL:** `POST /api/telegram/token/`

**Параметры:**
```json
{
    "email": "user@example.com",
    "password": "userpassword"
}
```

**Ответ при успехе:**
```json
{
    "success": true,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in_minutes": 10,
    "auth_url": "https://yourdomain.com/api/telegram/auth/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Ответ при ошибке:**
```json
{
    "error": "Неверный email или пароль"
}
```

### 2. Автоматическая авторизация

**URL:** `GET /api/telegram/auth/?token=JWT_TOKEN`

**Поведение:**
- При успешной авторизации: перенаправление на `/users/profile/`
- При ошибке: перенаправление на `/users/login/` с сообщением об ошибке

## Использование в Telegram боте

### Python (python-telegram-bot)

```python
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Конфигурация
DJANGO_API_URL = "https://yourdomain.com/api/telegram"
USER_CREDENTIALS = {
    "user1": {"email": "user1@example.com", "password": "password1"},
    "user2": {"email": "user2@example.com", "password": "password2"}
}

async def generate_auth_link(email, password):
    """Генерирует ссылку для авторизации"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/token/",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('auth_url')
        else:
            error_data = response.json()
            return f"Ошибка: {error_data.get('error', 'Неизвестная ошибка')}"
            
    except requests.RequestException as e:
        return f"Ошибка соединения: {str(e)}"

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /login для авторизации"""
    user_id = str(update.effective_user.id)
    
    if user_id not in USER_CREDENTIALS:
        await update.message.reply_text("У вас нет доступа к авторизации.")
        return
    
    credentials = USER_CREDENTIALS[user_id]
    auth_url = await generate_auth_link(credentials["email"], credentials["password"])
    
    if auth_url.startswith("https://"):
        await update.message.reply_text(
            f"Нажмите на ссылку для входа в систему:\n\n{auth_url}",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(auth_url)

# Регистрация обработчика
application = Application.builder().token("YOUR_BOT_TOKEN").build()
application.add_handler(CommandHandler("login", login_command))
```

### Node.js (node-telegram-bot-api)

```javascript
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const bot = new TelegramBot('YOUR_BOT_TOKEN', {polling: true});
const DJANGO_API_URL = 'https://yourdomain.com/api/telegram';

const USER_CREDENTIALS = {
    '123456789': {email: 'user1@example.com', password: 'password1'},
    '987654321': {email: 'user2@example.com', password: 'password2'}
};

async function generateAuthLink(email, password) {
    try {
        const response = await axios.post(`${DJANGO_API_URL}/token/`, {
            email: email,
            password: password
        });
        
        return response.data.auth_url;
    } catch (error) {
        if (error.response) {
            return `Ошибка: ${error.response.data.error}`;
        }
        return `Ошибка соединения: ${error.message}`;
    }
}

bot.onText(/\/login/, async (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from.id.toString();
    
    if (!USER_CREDENTIALS[userId]) {
        bot.sendMessage(chatId, 'У вас нет доступа к авторизации.');
        return;
    }
    
    const credentials = USER_CREDENTIALS[userId];
    const authUrl = await generateAuthLink(credentials.email, credentials.password);
    
    if (authUrl.startsWith('https://')) {
        bot.sendMessage(chatId, `Нажмите на ссылку для входа в систему:\n\n${authUrl}`);
    } else {
        bot.sendMessage(chatId, authUrl);
    }
});
```

### PHP (Telegram Bot API)

```php
<?php
require_once 'vendor/autoload.php';

use Telegram\Bot\Api;

$telegram = new Api('YOUR_BOT_TOKEN');
$djangoApiUrl = 'https://yourdomain.com/api/telegram';

$userCredentials = [
    '123456789' => ['email' => 'user1@example.com', 'password' => 'password1'],
    '987654321' => ['email' => 'user2@example.com', 'password' => 'password2']
];

function generateAuthLink($email, $password) {
    global $djangoApiUrl;
    
    $data = [
        'email' => $email,
        'password' => $password
    ];
    
    $options = [
        'http' => [
            'header' => "Content-type: application/json\r\n",
            'method' => 'POST',
            'content' => json_encode($data)
        ]
    ];
    
    $context = stream_context_create($options);
    $result = file_get_contents($djangoApiUrl . '/token/', false, $context);
    
    if ($result === FALSE) {
        return 'Ошибка соединения';
    }
    
    $response = json_decode($result, true);
    
    if (isset($response['auth_url'])) {
        return $response['auth_url'];
    } else {
        return 'Ошибка: ' . ($response['error'] ?? 'Неизвестная ошибка');
    }
}

$update = $telegram->getWebhookUpdates();

if ($update->getMessage() && $update->getMessage()->getText() === '/login') {
    $chatId = $update->getMessage()->getChat()->getId();
    $userId = $update->getMessage()->getFrom()->getId();
    
    if (!isset($userCredentials[$userId])) {
        $telegram->sendMessage([
            'chat_id' => $chatId,
            'text' => 'У вас нет доступа к авторизации.'
        ]);
        return;
    }
    
    $credentials = $userCredentials[$userId];
    $authUrl = generateAuthLink($credentials['email'], $credentials['password']);
    
    if (strpos($authUrl, 'https://') === 0) {
        $telegram->sendMessage([
            'chat_id' => $chatId,
            'text' => "Нажмите на ссылку для входа в систему:\n\n{$authUrl}"
        ]);
    } else {
        $telegram->sendMessage([
            'chat_id' => $chatId,
            'text' => $authUrl
        ]);
    }
}
?>
```

## Безопасность

### Рекомендации:

1. **Храните учетные данные в безопасном месте** - используйте переменные окружения или зашифрованные конфигурационные файлы
2. **Ограничьте доступ** - проверяйте ID пользователей Telegram перед выдачей ссылок
3. **Мониторинг** - все попытки авторизации логируются в audit.log
4. **Время жизни токенов** - токены действительны только 10 минут
5. **HTTPS** - используйте только HTTPS для передачи токенов

### Настройка JWT секретного ключа:

Добавьте в `.env` файл:
```
JWT_SECRET_KEY=your-very-secure-secret-key-here
```

## Тестирование

### Тест генерации токена:
```bash
curl -X POST https://yourdomain.com/api/telegram/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword"}'
```

### Тест авторизации:
```bash
curl "https://yourdomain.com/api/telegram/auth/?token=YOUR_JWT_TOKEN"
```

## Обработка ошибок

Система возвращает следующие типы ошибок:

- **400** - Неполные данные (отсутствует email или password)
- **401** - Неверные учетные данные
- **403** - Аккаунт не подтвержден администратором
- **404** - Профиль пользователя не найден
- **500** - Внутренняя ошибка сервера

Все ошибки логируются в audit.log с указанием IP адреса и времени.
