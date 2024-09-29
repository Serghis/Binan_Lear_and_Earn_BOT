import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import telebot
from telebot.types import BotCommand
from keep_alive import keep_alive

# Usa variables de entorno para las credenciales
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

bot = telebot.TeleBot(BOT_TOKEN)

def load_previous_data(filename='binance_courses.json'):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_data(data, filename='binance_courses.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def compare_data(old_data, new_data):
    new_courses = [course for course in new_data if course not in old_data]
    return new_courses

def scrape_binance_with_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://academy.binance.com/es/learn-and-earn?utm_source=binance_announce")
    driver.implicitly_wait(5)

    courses = driver.find_elements(By.CLASS_NAME, "course-card")
    scraped_data = []

    for course in courses:
        title = course.find_element(By.CLASS_NAME, "course-name").text
        description = course.find_element(By.CLASS_NAME, "css-62w6gh").text
        status = course.find_element(By.CLASS_NAME, "css-0").text
        link = course.find_element(By.TAG_NAME, 'a').get_attribute('href')

        course_data = {
            'title': title,
            'description': description,
            'status': status,
            'link': link
        }
        scraped_data.append(course_data)

    driver.quit()
    return scraped_data

def send_telegram_message(message):
    bot.send_message(CHAT_ID, message, parse_mode='Markdown')

def check_for_updates():
    previous_data = load_previous_data()
    new_data = scrape_binance_with_selenium()

    new_courses = compare_data(previous_data, new_data)
    if new_courses:
        print("Se han detectado nuevos cursos. Enviando notificación por Telegram...")
        for course in new_courses:
            message = f"*Nuevo curso disponible:*\n\n"
            message += f"*Título:* {course['title']}\n"
            message += f"*Descripción:* {course['description']}\n"
            message += f"*Estado:* {course['status']}\n"
            message += f"*Enlace:* {course['link']}"
            send_telegram_message(message)
        
        save_data(new_data)
    else:
        print("No se han detectado nuevos cursos.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Bienvenido al bot de Binance Learn and Earn. Usa /check para verificar manualmente los cursos.")

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.reply_to(message, "Verificando manualmente los cursos de Binance Learn and Earn...")
    check_for_updates()
    bot.reply_to(message, "Verificación manual completada.")

def main():
    bot.set_my_commands([
        BotCommand("start", "Iniciar el bot"),
        BotCommand("help", "Mostrar ayuda"),
        BotCommand("check", "Verificar manualmente los cursos")
    ])
    
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    keep_alive()  # Mantiene el bot activo
    while True:
        try:
            check_for_updates()
            time.sleep(3600)  # Espera una hora entre cada comprobación
        except Exception as e:
            print(f"Error en el bot: {e}")
            time.sleep(15)

if __name__ == "__main__":
    main()