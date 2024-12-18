# Двухпользовательский Wordle-бот для Telegram

Этот бот позволяет двум пользователям играть в игру по типу Wordle. Один игрок загадывает слово длиной от 4 до 8 букв, а второй пытается его угадать. У игрока есть **6 попыток**, чтобы угадать слово.

## Функциональность

- **Команда `/start`**: Начать взаимодействие с ботом.
- **Команда `/new_game`**: Создать новую игру.
- **Команда `/cancel`**: Отменить текущую игру.

## Важно

Оба игрока **должны** начать диалог с ботом, отправив ему команду `/start`. Иначе бот не сможет отправить личное сообщение угадывающему игроку.

## Установка и запуск без Docker

Следуйте инструкциям ниже, чтобы запустить бота на вашем локальном компьютере или сервере без использования Docker.

### 1. Создайте бота в Telegram

- Откройте Telegram и найдите бот [@BotFather](https://telegram.me/BotFather).
- Отправьте команду `/newbot` и следуйте инструкциям для создания нового бота.
- После создания вы получите **токен API**. Сохраните его — он понадобится позже.

### 2. Установите Python

Убедитесь, что у вас установлен Python 3.7 или выше. Проверить версию Python можно командой:

```bash
python3 --version
```

### 3. Создайте виртуальное окружение (необязательно, но рекомендуется)

```bash
python3 -m venv venv
source venv/bin/activate  # Для Linux/Mac
# or
venv\Scripts\activate  # Для Windows
```

### 4. Установите необходимые зависимости

Установите библиотеку `python-telegram-bot` версии 20 или выше:

```bash
pip install python-telegram-bot --upgrade
```

### 5. Сохраните код бота

- Создайте файл `main.py` и скопируйте в него код бота (см. выше).
- Замените `'YOUR_TELEGRAM_BOT_TOKEN'` на ваш токен, полученный от `@BotFather`.

```python
application = ApplicationBuilder().token('YOUR_TELEGRAM_BOT_TOKEN').build()
```

### 6. Запустите бота

```bash
python3 main.py
```

Если всё настроено правильно, бот запустится и будет ждать сообщений в Telegram.

### 7. Начните игру

- **Оба игрока** должны найти бота в Telegram и отправить ему команду `/start`.
- Первый игрок (загадчик) отправляет команду `/new_game`.
- Следуйте инструкциям бота:
  - Укажите `@username` второго игрока.
  - Задайте слово из 5 букв.
- Второй игрок (угадывающий) получит сообщение от бота и сможет начать угадывать слово.

## Правила игры

- У вас есть **6 попыток**, чтобы угадать слово.
- После каждой попытки бот покажет вам:
  - Номер текущей попытки.
  - Вашу догадку (слово).
  - Строку с цветными квадратами:
    - 🟩 — буква на правильном месте.
    - 🟨 — буква есть в слове, но на другой позиции.
    - ⬜ — буквы нет в слове.
- Если вы угадали слово, получите поздравительное сообщение с эмодзи 🎉.
- Если не смогли угадать за 6 попыток, игра заканчивается, и бот сообщит вам загаданное слово.

## Примечания

- При каждой попытке ваша текущая попытка будет отображаться в чате.
- Загадавший игрок будет получать уведомления о ваших попытках с подробностями.
- Если угадывающий игрок правильно угадает слово, бот уведомит об этом загадывающего игрока.

## Дополнительная информация

- **Остановка бота**: Для остановки бота нажмите `Ctrl+C` в окне терминала, где он запущен.
- **Логирование**: Бот настроен на вывод логов уровня INFO, что полезно для отладки.

## Возможные улучшения

- Хранение активных игр в базе данных для сохранения между перезапусками бота.
- Расширение функционала для поддержки одновременных игр с несколькими пользователями.
- Добавление словаря для проверки допустимости слов и предотвращения ввода несуществующих слов.

## Поддержка

Если у вас возникли вопросы или проблемы с запуском бота, пожалуйста, откройте тему на GitHub или свяжитесь с разработчиком.

## Установка и запуск с использованием Docker

Для удобства развертывания и запуска бота вы можете использовать Docker. Следуйте инструкциям ниже:

### 1. Подготовка к запуску

1. Убедитесь, что у вас установлены:
   - Docker
   - Docker Compose

2. Создайте файл `.env` в корневой директории проекта:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```
   Замените `your_bot_token_here` на ваш токен от @BotFather.

### 2. Сборка и запуск

1. Соберите Docker образ:
   ```bash
   docker-compose build
   ```

2. Запустите контейнер:
   ```bash
   docker-compose up -d
   ```

#### 3. Управление контейнером

- Просмотр логов:
  ```bash
  docker-compose logs -f
  ```

- Остановка бота:
  ```bash
  docker-compose down
  ```

- Перезапуск бота:
  ```bash
  docker-compose restart
  ```

### Мониторинг и обслуживание

#### Логи
Логи бота сохраняются в директории `logs/`. Вы можете найти их:
- При запуске без Docker: в локальной директории `logs/`
- При запуске с Docker: внутри volume `./logs:/app/logs`
