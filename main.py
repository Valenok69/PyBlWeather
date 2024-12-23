import logging
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import requests
from typing import Union
import re
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
API_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

cities = {
    "Москва": (55.7558, 37.6173),
    "Санкт-Петербург": (59.9343, 30.3351),
    "Новосибирск": (55.0084, 82.9357),
    "Казань": (55.8304, 49.0661),
    "Екатеринбург": (56.8389, 60.6057),
    "Нижний Новгород": (56.2965, 43.9361),
    "Уфа": (54.7388, 55.9721)
}

class WeatherStates(StatesGroup):
    start_city = State()
    end_city = State()
    days = State()
@router.message(Command("weather"))
async def weather_command(message: types.Message, state: FSMContext):
    await message.answer("Выбери начальную точку маршрута или введи вручную:", reply_markup=city_buttons("start_city"))
    await state.set_state(WeatherStates.start_city)
def get_coordinates(city_name):
    base_url = "https://geocoding-api.open-meteo.com/v1/search"
    request_query = f'?name={city_name}&count=5&language=ru&format=json'

    try:
        response = requests.get(base_url + request_query)
        if response.status_code != 200:
            return None
        else:
            response_json = response.json()
            if 'results' in response_json and len(response_json['results']) != 0:
                lat, lon = response_json['results'][0]['latitude'], response_json['results'][0]['longitude']
                return lat, lon
            else:
                return None
    except Exception as e:
        print("Exception! Error: " + str(e))
        return None

def get_weather(lat, lon, days):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&timezone=auto&forecast_days={days}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return f"Ошибка подключения к API. Код состояния: {response.status_code}"

        try:
            data = response.json()
        except json.JSONDecodeError:
            return "Ошибка обработки данных с сервера. Попробуйте позже."

        if 'daily' not in data:
            return "Ошибка получения данных. Проверьте запрос."

        forecast = data['daily']
        result = []
        for i in range(min(days, len(forecast['time']))):
            date = forecast['time'][i]
            temp_max = forecast['temperature_2m_max'][i]
            temp_min = forecast['temperature_2m_min'][i]
            precipitation = forecast['precipitation_sum'][i]
            windspeed = forecast['windspeed_10m_max'][i]
            result.append(f"""{date}:
            🌡️ Макс. темп: {temp_max}°C
            ❄️ Мин. темп: {temp_min}°C
            🌧️ Осадки: {precipitation} мм
            💨 Ветер: {windspeed} км/ч\n""")
        return "\n".join(result)
    except requests.exceptions.Timeout:
        return "Сервер не отвечает. Проверьте подключение к интернету или попробуйте позже."

    except requests.exceptions.RequestException as e:
        return f"Ошибка сети: {str(e)}"
    except Exception as e:
        return f"Произошла непредвиденная ошибка: {str(e)}"

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Запросить прогноз погоды", callback_data="start_weather")]
        ]
    )
    await message.reply("Привет! Я бот прогноза погоды для маршрута.", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "start_weather")
async def start_weather(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Выбери начальную точку маршрута или введи вручную:",
                                  reply_markup=city_buttons("start_city"))
    await state.set_state(WeatherStates.start_city)
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "📋 **Доступные команды:**\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение с подсказками\n"
        "/weather - узнать прогноз погоды для маршрута\n\n"
        "📍 **Выбор маршрута:**\n"
        "1. Выберите начальную точку.\n"
        "2. Выберите конечную точку.\n"
        "3. Укажите количество дней для прогноза.\n\n"
        "🌦️ **Получение прогноза погоды:**\n"
        "Бот покажет погоду для выбранных точек на заданное количество дней.\n\n"
    )
    await message.answer(help_text, parse_mode="Markdown")

def city_buttons(prefix):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=city, callback_data=f"{prefix}:{city}")] for city in cities]
    )
def days_buttons(prefix):
    return InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text=str(i), callback_data=f"days:{i}")] for i in range(1, 8)]
    )
@router.callback_query(F.data.startswith("start_city:"))
async def set_start_city_callback(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(":")[1]
    coords = cities[city]
    await state.update_data(start_city=(city, coords))
    await callback.message.answer(f"Начальная точка: {city}")
    await callback.message.answer("Выбери конечную точку маршрута:", reply_markup=city_buttons("end_city"))
    await state.set_state(WeatherStates.end_city)

@router.message(WeatherStates.start_city)
async def set_start_city_text(message: types.Message, state: FSMContext):
    city = message.text
    coords = get_coordinates(city)
    if not coords:
        await message.answer("Не удалось найти координаты. Попробуй ещё раз.")
        return
    await state.update_data(start_city=(city, coords))
    await message.answer(f"Начальная точка: {city}")
    await message.answer("Выбери конечную точку маршрута:", reply_markup=city_buttons("end_city"))
    await state.set_state(WeatherStates.end_city)
"""
@router.message(WeatherStates.days)
async def select_days(message: types.Message, state: FSMContext):
    try:
        # Проверяем корректность ввода количества дней
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введи корректное количество дней (целое число больше 0).")
        return

    # Обновляем данные состояния
    await state.update_data(days=days)
    data = await state.get_data()
    start_city, start_coords = data['start_city']
    end_city, end_coords = data['end_city']

    # Получаем прогноз погоды
    start_weather = get_weather(*start_coords, days)
    end_weather = get_weather(*end_coords, days)

    await message.answer(f"Прогноз для {start_city} на {days} дней:\n{start_weather}\n (˵ •̀ ᴗ - ˵ ) ✧")
    await message.answer(f"Прогноз для {end_city} на {days} дней:\n{end_weather}\n(૭ ｡•̀ ᵕ •́｡ )૭")
    await state.clear()
"""
@router.callback_query(F.data.startswith("end_city:"))
async def select_end_city_callback(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(":")[1]
    coords = get_coordinates(city)
    if not coords:
        await callback.message.answer("Не удалось найти координаты для указанного города. Попробуй ещё раз.")
        return
    await state.update_data(end_city=(city, coords))
    await callback.message.answer(f"Конечная точка маршрута: {city}")
    await callback.message.answer("Укажи длительность путешествия (в днях):", reply_markup=days_buttons("days"))
    await state.set_state(WeatherStates.days)
@router.message(WeatherStates.end_city)
async def select_end_city_manual(message: types.Message, state: FSMContext):
    city = message.text
    coords = get_coordinates(city)
    if not coords:
        await message.answer("Не удалось найти координаты для указанного города. Попробуй ещё раз.")
        return
    await state.update_data(end_city=(city, coords))
    await message.answer(f"Конечная точка маршрута: {city}")
    await message.answer("Укажи длительность путешествия (в днях):", reply_markup=days_buttons("days"))
    await state.set_state(WeatherStates.days)
@router.callback_query(F.data.startswith("days:"))
async def set_days_callback(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split(":")[1])
    await process_days_input(callback.message, state, days)

@router.message(WeatherStates.days)
async def set_days_manual(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введи корректное количество дней (целое число больше 0).")
        return
    await process_days_input(message, state, days)

async def process_days_input(message, state, days):
    await state.update_data(days=days)
    data = await state.get_data()
    start_city, start_coords = data['start_city']
    end_city, end_coords = data['end_city']
    start_weather = get_weather(*start_coords, days)
    end_weather = get_weather(*end_coords, days)
    await message.answer(f"Прогноз для {start_city} на {days} дней:\n{start_weather}\n (˵ •̀ ᴗ - ˵ ) ✧")
    await message.answer(f"Прогноз для {end_city} на {days} дней:\n{end_weather}\n(૭ ｡•̀ ᵕ •́｡ )૭")
    await state.clear()
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
