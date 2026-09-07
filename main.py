import telebot
import threading
import random
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client["azkar_bot"]
users_db = db["users"]

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

with open ('azkar.txt', 'r', encoding="utf-8") as file:
    azkar = file.readlines()
    azkar = [line.strip() for line in azkar if len(line.strip()) > 0]

users_timers = {}



@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'أهلًا انا بوت للأذكار 🤍 .\n حدد لي المدة وأنا اقوم بأرسال ذكر عشوائي بعد انتهاء كل مدة'
                          '\nلمعرفة كيفية استخدامي ارسل /help ')

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message,'قم بكتابة /تذكير للبدء ,ثم ادخل عدد الدقائق بعد كل تذكير \n'
                         'استخدم /قف لإيقاف التذكيرات \n'
                         'منشئ البوت IG : @1dyd')
@bot.message_handler(commands=['تذكير'])
def ask(message):
    bot.reply_to(message,'حدد المدة بالدقائق .'
                         '\n مثل "15"')
    bot.register_next_step_handler(message,check_num)

def check_num(message):
     try:

         interval = int(message.text)
         if interval <= 0:
             bot.reply_to(message,"❌ ادخل رقم صحيح اكبر من 0")
             bot.register_next_step_handler(message,check_num)
         else:
             chat_id = message.chat.id
             send_zkr(chat_id, interval)
             timer = threading.Timer(interval * 60, start_sending, args=(chat_id, interval))
             timer.start()
             users_timers[chat_id] = timer

     except ValueError:
         bot.reply_to(message,'حاول مره ثانية , أدخل فقط عدد الدقائق')
         bot.register_next_step_handler(message,check_num)


def send_zkr(chat_id,interval):
    bot.send_chat_action(chat_id, 'typing')
    bot.send_message(chat_id,f'سيتم ارسال اذكار متنوعة كل {interval} دقيقة 🤍')

def start_sending(chat_id,interval):
    timer = threading.Timer(interval * 60 ,start_sending, args=(chat_id,interval))
    timer.start()

    zekr = random.choice(azkar)

    bot.send_message(chat_id, zekr)

    users_timers[chat_id] = timer

@bot.message_handler(commands=['تعديل'])
def edit_request(message):
    bot.reply_to(message, 'أدخل الوقت الجديد لإرسال التذكيرات')


    bot.register_next_step_handler(message,edit_timer)

def edit_timer(message):
    try:
        interval = int(message.text)
        if interval <= 0:
            bot.reply_to(message, "❌❌ ارسل رقم صحيح مثل : 15")
            bot.register_next_step_handler(message,edit_timer)
            return

        chat_id = message.chat.id

        if chat_id in users_timers:
            users_timers[chat_id].cancel()
            users_timers.pop(chat_id)
        else:
            bot.reply_to(message,'لايوجد تذكير لتعديله')
            return 


        timer = threading.Timer(interval * 60, start_sending, args=(chat_id, interval))
        timer.start()

        users_timers[chat_id] = timer

        bot.send_message(chat_id,f'تم تعديل التذكيرات \n'
                             f'سيتم ارسال التذكير كل {interval} دقيقة 🤍')

    except ValueError:
        bot.reply_to(message,"❌❌ ارسل رقم صحيح مثل : 15")
        bot.register_next_step_handler(message,edit_timer)

@bot.message_handler(commands=['قف'])
def cancel(message):
    chat_id = message.chat.id
    if chat_id in users_timers:
        users_timers[chat_id].cancel()
        bot.send_message(chat_id, 'تم ايقاف التذكيرات')
        users_timers.pop(chat_id)
    else:
        bot.reply_to(message,'لا يوجد تذكير لإيقافه')


bot.polling()
