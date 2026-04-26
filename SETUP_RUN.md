# Запуск Lunch Bot

## 1. Что нужно подготовить

1. Telegram Bot Token из BotFather.
2. Google таблица.
3. Service Account JSON для Google Sheets API.
4. Telegram ID админа.

## 2. Google таблица

Бот сам создаёт листы:

- `bot_data` — записи об обедах
- `logs` — лог действий

В таблице нужно дать доступ email сервисного аккаунта, который есть в JSON-файле Google.

## 3. Локальный запуск

Создать файл `.env`:

```env
BOT_TOKEN=токен_бота
SPREADSHEET_ID=id_таблицы
GOOGLE_CREDENTIALS_FILE=service_account.json
TIMEZONE=Europe/Kyiv
ADMIN_IDS=telegram_id_админа
LUNCH_DURATION_MINUTES=45
SLOT_CAPACITY=2
REMINDER_MINUTES=15
```

Потом:

```bash
pip install -r requirements.txt
python bot.py
```

## 4. Render

В Render Environment Variables добавить:

```env
BOT_TOKEN=...
SPREADSHEET_ID=...
GOOGLE_SERVICE_ACCOUNT_JSON={...весь json сервисного аккаунта...}
TIMEZONE=Europe/Kyiv
ADMIN_IDS=123456789
LUNCH_DURATION_MINUTES=45
SLOT_CAPACITY=2
REMINDER_MINUTES=15
```

Команда запуска уже есть в `render.yaml`.

## 5. Проверка

1. Админ пишет боту `/start`.
2. Новый пользователь пишет `/start` и подаёт заявку.
3. Админ получает заявку и подтверждает.
4. Оператор бронирует обед.
5. Запись появляется в листе `bot_data`.
