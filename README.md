# Telegram Weather Bot

## Описание
Этот бот предоставляет прогноз погоды для заданных пользователем точек маршрута на определённое количество дней. Он использует API Open-Meteo для получения данных о погоде и поддерживает инлайн-кнопки для интерактивного взаимодействия с пользователем.

---

## Функционал
1. **Команды**:
   - `/start` — Начать работу с ботом и выбрать начальную точку маршрута.
   - `/help` — Получить информацию о командах и возможностях бота.
   - `/weather` — Получить прогноз погоды для маршрута, указав количество дней.

2. **Интерактивные кнопки**:
   - Выбор начальной и конечной точек маршрута с помощью кнопок или текстового ввода.

3. **Обработка ошибок**:
   - Сообщения о проблемах с подключением к API или некорректных данных.

---

## Установка и запуск

1. **Клонирование репозитория**:
```
git clone https://github.com/Valenok69/PyBlWeather
cd weather-bot
```

2. **Установка зависимостей**:
```
python -m venv venv
source venv/bin/activate   # Для Linux/MacOS
venv\Scripts\activate      # Для Windows
pip install -r requirements.txt
```

3. **Запуск бота**:
```
python main.py
```

---

## Конфигурация
1. **Переменные окружения**:
   - Создайте файл `.env` в корневой директории.
   - Добавьте в него ваш токен Telegram-бота:
```
BOT_TOKEN=your_token_here
```

2. **Настройка API**: 
   - Open-Meteo API используется без ключа.

---

## Обработка ошибок
Если API недоступен или возникают сетевые проблемы, бот корректно уведомляет пользователя о возникшей ошибке.

---

## Команда /help
Команда `/help` предоставляет краткую информацию о доступных командах и их функциях:
- `/start` — Запуск бота и начало работы.
- `/help` — Просмотр доступных команд.
- `/weather` — Получение прогноза погоды для заданного маршрута.

