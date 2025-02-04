import os
import time
import datetime

import telebot
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from utils import main_keyboard, make_back_inline_button_markup, make_connect_markup, make_pay_markup, make_help_markup, make_buy_inline_button_markup

load_dotenv()

engine = create_engine(f"postgresql+psycopg2://{os.environ['SQL_USER']}:{os.environ['SQL_PASS']}@{os.environ['SQL_HOST']}/{os.environ['SQL_DATABASE']}")

bot = telebot.TeleBot(token=os.environ["TELEBOT_API"])
prices = [
    telebot.types.LabeledPrice(label='1 месяц', amount=1), 
    telebot.types.LabeledPrice(label='4 месяц', amount=4), 
    telebot.types.LabeledPrice(label='12 месяц', amount=12), 
]


@bot.message_handler(commands=["start"])
def handle_start(message):
    text_to_print = """Мы обеспечиваем сверх-быстрое и защищенное соединение, используя передовые технологии VPN 

Стабильная работа Instagram и YouTube в 4K без рекламы, интернет банкинг остается рабочий. Доступно на всех устройствах: смартфонах, ноутбуках, планшетах и телевизорах. Больше никаких надоедающих Вкл/Выкл VPN.

Для новых пользователей доступен пробный период — 10 дней, чтобы вы могли оценить все преимущества сервиса.

Поддержка 24/7: @ledger_vpn_support

Нажмите ⚡️Подключиться ↓ для начала работы
"""
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
    user_id = message.from_user.id
    if not is_active_user(user_id):
        response = "У вас нет активной подписки"
    else:
        with engine.begin() as connection:
            sql_query = f"""
                SELECT * 
                FROM subs 
                WHERE subs_id = {user_id}
            """
            df = pd.read_sql_query(sql_query, connection)
        end_time = df['date_end'][0]
        response = f'Ваша подписка закончится `{end_time}`'
    markup = make_back_inline_button_markup()
    bot.send_message(message.chat.id, response, reply_markup=markup)


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
    markup = make_buy_inline_button_markup()
    bot.edit_message_text(
        chat_id=query.from_user.id,
        text=f"Выберете тип оплаты:",
        message_id=query.message.id,
        reply_markup=markup
    )


@bot.callback_query_handler(lambda query: query.data == "buy_tg_stars")
def handle_buy(query):
    bot.send_invoice(
        chat_id=query.from_user.id, 
        title='Оплата в TG Stars', 
        description='Выберете срок оплаты',
        invoice_payload='subscription',
        currency='XTR',
        prices=prices,
        provider_token=None,
    )


def is_active_user(user_id):
    with engine.begin() as conn:
        query = f"""
            SELECT * 
            FROM subs 
            WHERE subs_id = {user_id}
                AND date_end > '{datetime.datetime.now()}'
        """
        df = pd.read_sql_query(query, conn)
    return not df.empty


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Произошла ошибка.")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    response = "Вы оплатили подписку ✅"
    user_id = message.from_user.id
    if not is_active_user(user_id):
        with engine.begin() as connection:
            connection.execute(text(f'DELETE FROM subs WHERE subs_id = {user_id}'))
            connection.commit()

        with engine.begin() as connection:
            start = datetime.datetime.now()
            end = start + datetime.timedelta(days=30)
            parameters = {
                "subs_id": user_id,
                "date_start": start.strftime("%Y-%m-%d %H:%M:%S"),
                "date_end": end.strftime("%Y-%m-%d %H:%M:%S"),
            }
            connection.execute(text('INSERT INTO subs (subs_id, date_start, date_end) VALUES (:subs_id, :date_start, :date_end)'), parameters)
            connection.commit()
    else:
        with engine.begin() as connection:
            update_query = f"""
                UPDATE subs 
                SET date_end = date_end + INTERVAL'30 days'
                WHERE subs_id = {user_id}
            """
            connection.execute(text(update_query))
            connection.commit()
    
    with engine.begin() as connection:
        query = f"""
            SELECT * 
            FROM subs 
            WHERE subs_id = {user_id}
        """
        df = pd.read_sql_query(query, connection)
    end_time = df['date_end'][0]

    response += '\n' + f'Ваша подписка закончится `{end_time}`'
    markup = telebot.types.InlineKeyboardMarkup()
    itembtn_str = telebot.types.InlineKeyboardButton("Главное меню", callback_data="menu")
    markup.add(itembtn_str)

    bot.send_message(
        chat_id=message.chat.id,
        text=response,
        reply_markup=markup,
        parse_mode="Markdown",
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
