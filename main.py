import telebot
import re

import Config
import random
import wikipedia
from telebot import types
import sqlite3

bot = telebot.TeleBot(Config.bot)


num = False
admins = [6681334561]
clients = []
text = ""
link = ""
wiki = False

conn = sqlite3.connect("users_db", check_same_thread=False)

cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INT);")
conn.commit()

@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.id in admins:
        help(message)
    else:
        info = cur.execute("SELECT * FROM users WHERE id=?", (message.chat.id,)).fetchone()
        if not info:
            cur.execute("INSERT INTO users (id) VALUES (?)", (message.chat.id,))
            conn.commit()
            bot.reply_to(message, "who are you")

def help(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("редактировать текст"))
    markup.add(types.KeyboardButton("редактировать ссылку"))
    markup.add(types.KeyboardButton("показать текст"))
    markup.add(types.KeyboardButton("начать рассылку"))
    markup.add(types.KeyboardButton("помощь"))
    bot.send_message(message.chat.id,"команды для бота: \n"
                                    "/edit_text - редактировать текст. \n"
                                    "/edit_link - редактировать ссылку. \n"
                                    "/show_message - показать текст. \n"
                                    "/send or /send_message - начать рассылку. \n"
                                    "/help - помощь.", reply_markup=markup)


@bot.message_handler(commands=["show_message"])
def show_message(message):
    if message.chat.id in admins:
        bot.send_message(message.chat.id, f"Текущий текст: \n"
                                          f"{text}"
                                          f"{link}")

@bot.message_handler(commands=["edit_text"])
def edit_text(message):
    m = bot.send_message(message.chat.id, "Введите сообщение для рассылки")
    bot.register_next_step_handler(m, save_text)

def save_text(message):
    global text
    if message.text not in ["Изменить текст", "Изменить ссылку"]:
        text = message.text
        bot.send_message(message.chat.id, f"Я сохранил текст: {text}")
    else:
        bot.send_message(message.chat.id, "текст некорректный.")


@bot.message_handler(commands=["edit_link"])
def edit_link(message):
    m = bot.send_message(message.chat.id, "Введите ссылку для рассылки")
    bot.register_next_step_handler(m, save_link)

def save_link(message):
    global link
    regex = re.compile(
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # проверка dot
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # проверка ip 
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if message.text is not None and regex.search(message.text):
        link = message.text
        bot.send_message(message.chat.id, f"Я сохранил link: {link}")
    else:
        m = bot.send_message(message.chat.id, "Ссылка некорректная,введи еще раз")
        bot.register_next_step_handler(m, save_link)


@bot.message_handler(commands=["send", "send_message"])
def send_message(message):
    global text, link
    if message.chat.id in admins:
        if text != "":
            if link != "":
                cur.execute("SELECT id FROM users")
                massive = cur.fetchall()
                print(massive)
                for client in massive:
                    id = client[0]
                    sending(id)
                else:
                    text = ""
                    link = ""
            else:
                bot.send_message(message.chat.id, "ссылка не приложена")
        else:
            bot.send_message(message.chat.id, "ссылка не приложена")
def sending(id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Click me", url=link))
    bot.send_message(id, text, reply_markup=markup)




@bot.message_handler(commands=["greet"])
def test(message):
    bot.send_message(message.chat.id, "Bot you send message")

@bot.message_handler(commands=["play"])
def bot_play_games(message):
    markup_inline = types.InlineKeyboardMarkup() # 1- Создать клавиатуру
    btn_y = types.InlineKeyboardButton(text="yes", callback_data="yes") # 2- создать кнопки для клав.
    btn_n = types.InlineKeyboardButton(text="no", callback_data="no")
    markup_inline.add(btn_y, btn_n)
    bot.send_message(message.chat.id, "You want to play games?", reply_markup=markup_inline)

@bot.callback_query_handler(func=lambda call:True)
def callback_buttons(call):
    if call.data == "yes":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Угадайка")
        btn2 = types.KeyboardButton("Википедия")
        markup.add(btn1, btn2)
        bot.send_message(call.message.chat.id, "Выбери, что хочешь?", reply_markup=markup)
    elif call.data == "no":
        pass


@bot.message_handler(content_types=["text"])
def type_text(message):
    global game, wiki
    text = message.text.lower()
    if wiki:
        bot.send_message(message.chat.id, get_wiki(text))
    if text == "привет":
        bot.send_message(message.chat.id, "Hello, how are you?")
    elif text == "угадайка":
        game_random_number(message)
        game = True
    elif text == str(num) and text in ["1", "2", "3"] and game:
        game = False
        bot.send_message(message.chat.id, "Угадал!")
    elif text == "википедия":
        bot.send_message(message.chat.id, "Что тебе найти в википедии?")
        wiki = True
    elif text == "редактировать текст":
        edit_text(message)
    elif text == "редактировать ссылку":
        edit_link(message)



def game_random_number(message):
    global num
    num = random.randint(1, 3)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("1"))
    markup.add(types.KeyboardButton("2"))
    markup.add(types.KeyboardButton("3"))
    bot.send_message(message.chat.id, "Загадал число, угадай.", reply_markup=markup)

wikipedia.set_lang("ru")
def get_wiki(word):
    try:
        w = wikipedia.page(word)
        wikitext = w.content[:1000]
        wikimas = wikitext.split(".")
        wikimas = wikimas[:-1] # Убирает последний элемент из списка

        wiki_result = ""
        for i in wikimas:
            if not ("==" in i):
                wiki_result = wiki_result + i + "."
            else:
                break

        wiki_result = re.sub('\([^()]*\)', '', wiki_result)

        return wiki_result
    except Exception as error:
        return f"Ничего не нашел {error}"

print(get_wiki("Москва"))

bot.infinity_polling() # контролирует когда приходят боту сообщения и позволяет раб.
# коду
# def game(message):
#     print("STart")
#     markup_inline = types.InlineKeyboardMarkup()
#     b1 = types.InlineKeyboardButton(text= "начать", callback_data="game")
#     markup_inline.add(b1)
#     bot.send_message(message.chat.id, "хочешь поугадывать числа?", reply_markup=markup_inline)
#
# def answer(call):
#     if call.data == "game":
#         global num
#         markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
#         n1 = types.KeyboardButton("1")
#         n2 = types.KeyboardButton("2")
#         n3 = types.KeyboardButton("3")
#         n4 = types.KeyboardButton("4")
#         n5 = types.KeyboardButton("5")
#         num = random.randint( 1, 5)
#         print(num)
#         markup_reply.add(n5, n4, n2, n1, n3)
#         bot.send_message(call.message.chat.id, "Я загадал, какое?", reply_markup=markup_reply)



@bot.message_handler(content_types=["text"])
def type_text(message):
    text = message.text.lower()
    if text == "слизь":
        bot.send_message(message.chat.id, "да здеесь я")
    if "иди нахуй" in text:
        bot.send_message(message.chat.id, "боже чел ливай из жизни такие оскорбления только пятилетка выдавить может")


bot.infinity_polling()
