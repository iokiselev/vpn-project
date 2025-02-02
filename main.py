import os
import time

import telebot
from dotenv import load_dotenv

from utils import main_keyboard, make_back_inline_button_markup, make_connect_markup, make_pay_markup, make_help_markup

load_dotenv()

bot = telebot.TeleBot(token=os.environ["TELEBOT_API"])


@bot.message_handler(commands=["start"])
def handle_start(message):
    text_to_print = "Добро пожаловать в VPN бота"
    keyboard = main_keyboard()
    bot.send_message(message.chat.id, text=text_to_print, reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    bot.delete_message(message.chat.id, message.id)

    if message.text == 'Статус':
        _status(message)
        
    elif message.text == 'Подключиться':
        _connect(message)

    elif message.text == 'Оплатить':
        _pay(message)

    elif message.text == 'Помощь':
        _help(message)


def _status(message):
    markup = make_back_inline_button_markup()
    bot.send_message(message.chat.id, 'Статус подписки', reply_markup=markup)


def _connect(message):
    markup = make_connect_markup()
    text = """
    Подключение к VPN происходит в 2 шага:  

    1. Кнопка "Скачать" - для загрузки приложения
    2. Кнопка "Подключить" - для добавления локаций"""
    bot.send_message(message.chat.id, text, reply_markup=markup)


def _pay(message):
    markup = make_pay_markup()
    bot.send_message(message.chat.id, 'Заплатить', reply_markup=markup)


def _help(message):
    markup = make_help_markup()
    bot.send_message(message.chat.id, 'Помощь', reply_markup=markup)


@bot.callback_query_handler(lambda query: query.data == 'make_config')
def make_config(query):
    bot.edit_message_text(
        chat_id=query.from_user.id,
        text=f"Делаю конфиг",
        message_id=query.message.id,
    )


@bot.callback_query_handler(lambda query: query.data.split("_")[0] == "pay")
def pay_n_month(query):
    n = int(query.data.split("_")[-1])
    bot.edit_message_text(
        chat_id=query.from_user.id,
        text=f"Оплата за {n} времени",
        message_id=query.message.id,
    )


@bot.callback_query_handler(lambda query: query.data == 'back')
def handle_start_trading(query):
    bot.delete_message(query.from_user.id, query.message.id)


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(15)
