import telebot
import threading
import random
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
load_dotenv()


db = client["azkar_bot"]
users_db = db["users"]

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

with open ('azkar.txt', 'r', encoding="utf-8") as file:
    azkar = file.readlines()
    azkar = [line.strip() for line in azkar if len(line.strip()) > 0]

users_timers = {}

def save_users(chat_id, amount, unit):
    existing_users = users_db.find_one({'chat_id': chat_id})
    if not existing_users:
        users_db.insert_one({'chat_id': chat_id  , 'azkar_active': False, 'amount': amount, 'unit': unit })

def update_amount(chat_id, amount,unit):
    users_db.update_one({'chat_id': chat_id}, {'$set': {'amount': amount, 'unit': unit}})

def update_users(chat_id, status):
    users_db.update_one({'chat_id': chat_id}, {'$set': {'azkar_active': status}})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'أهلًا انا بوت للأذكار 🤍 .\n حدد لي المدة وأنا اقوم بأرسال ذكر عشوائي بعد انتهاء كل مدة'
                          '\nلمعرفة كيفية استخدامي ارسل /help ')

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, 'قم بكتابة "/تذكير" فقط للبدء ,ثم حدد وحدة القياس بعد كل تذكير (دقائق , ساعات) \n'
                          'استخدم "/قف" لإيقاف التذكيرات \n'
                          '\n استخدم "/تعديل" لتعديل وقت التذكير \n'
                          'منشئ البوت IG : @1dyd')
@bot.message_handler(commands=['تذكير'])
def ask(message):
    bot.reply_to(message, 'كيف تريد ان يكون تذكيرك \n'
                          '**ملاحظة**\n'
                          'اكتب "دقائق" أو "ساعات"')

    bot.register_next_step_handler(message,ask_unit)

def ask_unit(message):
    unit = message.text.strip()
    if unit not in ['ساعات', 'ساعة', 'ساعه', 'دقائق', 'دقايق']:
        bot.reply_to(message,'اكتب "دقائق" أو "ساعات" فقط')
        bot.register_next_step_handler(message,ask_unit)
        return
    bot.reply_to(message,f'حدد العدد المراد بال{unit}')
    bot.register_next_step_handler(message,check_num,unit)

def check_num(message,unit):
     try:

         amount = int(message.text)
         if amount <= 0:
             bot.reply_to(message,"❌ ادخل رقم صحيح اكبر من 0")
             bot.register_next_step_handler(message,check_num,unit)
         else:
             chat_id = message.chat.id
             if unit in ['ساعات', 'ساعة', 'ساعه']:
                 seconds = amount * 3600
             else:
                 seconds = amount * 60

             send_zkr(chat_id, amount,unit)

             timer = threading.Timer(seconds, start_sending, args=(chat_id, seconds))
             timer.start()

             users_timers[chat_id] = timer

             save_users(chat_id,amount, unit)

             update_users(chat_id, True)

     except ValueError:
         bot.reply_to(message,'حاول مره ثانية , أدخل فقط عدد الدقائق')
         bot.register_next_step_handler(message,check_num ,unit)


def send_zkr(chat_id,amount,unit):
    bot.send_chat_action(chat_id, 'typing')
    bot.send_message(chat_id,f' سيتم إرسال اذكار متنوعة كل {amount}{unit} 🤍.')

def start_sending(chat_id,seconds):
    timer = threading.Timer(seconds ,start_sending, args=(chat_id,seconds))
    timer.start()

    zekr = random.choice(azkar)

    bot.send_message(chat_id, zekr)

    users_timers[chat_id] = timer

@bot.message_handler(commands=['تعديل'])
def edit_request(message):
    bot.reply_to(message, 'تفضِل ان يكون تذكيرك الجديد دقائق أو ساعات ؟')

    bot.register_next_step_handler(message,edit_ask)

def edit_ask(message):
    unit = message.text.strip()
    if unit not in ["دقايق" , "دقائق" , "ساعات" , "ساعة" , "ساعه"]:
        bot.reply_to(message,'❌❌ أكتب "دقائق" أو "ساعات"')
        bot.register_next_step_handler(message,edit_ask)
        return
    bot.reply_to(message,f"أكتب رقم ال{unit} الجديد")
    bot.register_next_step_handler(message,edit_timer,unit)

def edit_timer(message, unit):
    try:
        amount = int(message.text)
        if amount <= 0:
            bot.reply_to(message, "❌❌ ارسل رقم صحيح مثل : 15")
            bot.register_next_step_handler(message, edit_timer, unit)
            return

        chat_id = message.chat.id

        if unit in ['ساعات', 'ساعة', 'ساعه']:
            seconds = amount * 3600
        else:
            seconds = amount * 60

        if chat_id in users_timers:
            users_timers[chat_id].cancel()
            users_timers.pop(chat_id)
        else:
            bot.reply_to(message, 'لايوجد تذكير لتعديله')
            return

        timer = threading.Timer(seconds, start_sending, args=(chat_id, seconds))
        timer.start()

        update_amount(chat_id, amount, unit)
        update_users(chat_id, True)
        users_timers[chat_id] = timer

        bot.send_message(chat_id, f'تم تعديل التذكيرات \nسيتم ارسال التذكير كل {amount} {unit} 🤍')

    except ValueError:
        bot.reply_to(message, "❌❌ ارسل رقم صحيح مثل : 15")
        bot.register_next_step_handler(message, edit_timer, unit)


@bot.message_handler(commands=['قف'])
def cancel(message):
    chat_id = message.chat.id
    if chat_id in users_timers:

        users_timers[chat_id].cancel()

        bot.send_message(chat_id, 'تم ايقاف التذكيرات')

        users_timers.pop(chat_id)

        update_users(chat_id, False)
    else:
        bot.reply_to(message,'لا يوجد تذكير لإيقافه')

def restart_timers():
    active_users = users_db.find({'azkar_active': True})
    for user in active_users:

        chat_id = user['chat_id']
        amount = user['amount']
        unit = user['unit']
        if unit in ['ساعات', 'ساعة', 'ساعه']:
            seconds = amount * 3600
        else:
            seconds = amount * 60

        timer = threading.Timer(seconds, start_sending, args=(chat_id, seconds))
        timer.start()

        users_timers[chat_id] = timer

restart_timers()
bot.polling()
