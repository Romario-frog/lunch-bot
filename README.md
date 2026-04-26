# 🍽️ Lunch Bot

Telegram-бот для керування обідами через Google Sheets.

## Що вже зроблено

- ролі: `operator` і `admin`;
- обіди зберігаються в Google таблиці на листі `bot_data`;
- максимум 2 людини на один час;
- оператор може керувати тільки своїм обідом;
- адмін має доступ до логів;
- нагадування за 15 хвилин у ЛС;
- статистика: хто зараз на обіді і скільки обідів сьогодні;
- логи дій у `data/logs.json` і на листі `logs` у Google Sheets.

## Структура Google таблиці

У Google Sheets треба мати або дозволити боту створити лист:

```text
bot_data
```

Колонки:

```text
date | user_id | username | full_name | start_time | end_time | status | created_by | updated_at
```

Приклад:

```text
26.04.2026 | 123456 | roma | Roma | 15:00 | 15:45 | active | Roma | 2026-04-26T15:00:00
```

> Візуальну таблицю для людей можна залишити як є. Бот працює з `bot_data`, щоб не ламати поточний вигляд.

## Налаштування

1. Створи Telegram bot через BotFather і отримай `BOT_TOKEN`.
2. Створи Google Cloud service account.
3. Завантаж JSON-ключ і назви його `service_account.json`.
4. Дай service account доступ до Google таблиці як Editor.
5. Скопіюй `.env.example` у `.env`.
6. Заповни:

```env
BOT_TOKEN=...
SPREADSHEET_ID=...
GOOGLE_CREDENTIALS_FILE=service_account.json
TIMEZONE=Europe/Kyiv
ADMIN_IDS=111111111,222222222
LUNCH_DURATION_MINUTES=45
SLOT_CAPACITY=2
REMINDER_MINUTES=15
```

## Запуск локально

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

Для Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Render

На Render краще запускати як **Worker**, не Web Service.

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
python bot.py
```

Environment Variables:

```text
BOT_TOKEN
SPREADSHEET_ID
TIMEZONE
ADMIN_IDS
LUNCH_DURATION_MINUTES
SLOT_CAPACITY
REMINDER_MINUTES
```

`service_account.json` на Render напряму файлом не зручно. Найпростіше на старті залити файл у репозиторій приватно, але краще не комітити ключі. Правильний варіант — зберегти JSON у Secret File Render або зробити env-змінну з JSON і потім дописати читання з неї.

## Меню

Оператор:

- 🍽 Запланувати обід
- 🔁 Перенести обід
- ❌ Скасувати обід
- 👀 Мій обід
- 📋 Хто зараз на обіді
- 📊 Статистика
- ℹ️ Правила

Адмін:

- усе меню оператора;
- 📝 Логи.

## Як оновити GitHub

Якщо папка вже підключена до GitHub:

```bash
cd шлях/до/lunch-bot
git status
git add .
git commit -m "update lunch bot with google sheets logic"
git push origin main
```

Якщо скачав цей архів окремо, але репозиторій уже є на GitHub:

```bash
git clone https://github.com/Romario-frog/lunch-bot.git
```

Потім скопіюй файли з архіву в цю папку з заміною і виконай:

```bash
cd lunch-bot
git add .
git commit -m "update lunch bot structure"
git push origin main
```
