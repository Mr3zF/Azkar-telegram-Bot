import telebot
from telebot import types
import threading
import random
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())


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

def main_menu():

    inline = types.InlineKeyboardMarkup()
    tzkeer_bt = types.InlineKeyboardButton(text='تذكير جديد', callback_data='tzkeer+')
    edit_bt = types.InlineKeyboardButton(text='تعديل وقت التذكير', callback_data='edit/')
    cancel_bt = types.InlineKeyboardButton(text='إيقاف التذكير', callback_data='cancel-')
    creator_bt = types.InlineKeyboardButton(text='منشئ البوت', url='www.instagram.com/1dyd/')


    inline.add(tzkeer_bt)
    inline.add(edit_bt)
    inline.add(cancel_bt)
    inline.add(creator_bt)
    return inline

@bot.callback_query_handler(func=lambda call : call.data == 'back2main')
def back2main(call):
    keyboard = main_menu()
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    bot.edit_message_text(chat_id=chat_id,message_id=message_id,text='كيف أساعدك ؟',reply_markup=keyboard)
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['start'])
def send_welcome(message):

    keyboard = main_menu()

    bot.reply_to(message, 'أهلًا , أنا بوت للأذكار , كيف أساعدك ؟',reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call : call.data == 'tzkeer+')
def new_zkr(call):
    inline = types.InlineKeyboardMarkup()

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    hours_bt = types.InlineKeyboardButton(text='بالساعات',callback_data='hours+')
    minutes_bt = types.InlineKeyboardButton(text= 'بالدقائق', callback_data='minutes+')

    inline.add(hours_bt)
    inline.add(minutes_bt)

    bot.edit_message_text(chat_id=chat_id,message_id=message_id,text="هل تريد أن يكون التذكير بالدقائق أو الساعات ؟" , reply_markup=inline)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call : call.data in ['hours+' , 'minutes+'])
def time_check(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == 'hours+':
        unit = 'ساعات'
        bot.edit_message_text(chat_id=chat_id,message_id=message_id,text="أكتب عدد الساعات 'بالأرقام فقط'")
        bot.register_next_step_handler(call.message,check_num,unit)

    elif call.data == 'minutes+':
        unit = 'دقائق'
        bot.edit_message_text(chat_id=chat_id,message_id=message_id,text="أكتب عدد الدقائق 'بالأرقام فقط'")
        bot.register_next_step_handler(call.message,check_num,unit)
    bot.answer_callback_query(call.id)


def check_num(message, unit):
    try:

        amount = int(message.text)
        if amount <= 0:
            bot.reply_to(message, "❌ ادخل رقم صحيح اكبر من 0")
            bot.register_next_step_handler(message, check_num, unit)
        else:
            chat_id = message.chat.id
            if chat_id in users_timers:
                users_timers[chat_id].cancel()

            if unit in ['ساعات', 'ساعة', 'ساعه']:
                seconds = amount * 3600
            else:
                seconds = amount * 60

            send_zkr(chat_id, amount, unit)

            timer = threading.Timer(seconds, start_sending, args=(chat_id, seconds))
            timer.start()

            users_timers[chat_id] = timer
            save_users(chat_id, amount, unit)
            update_users(chat_id, True)
            update_amount(chat_id, amount, unit)





    except ValueError:
        bot.reply_to(message, 'حاول مره ثانية , أدخل فقط عدد الدقائق')
        bot.register_next_step_handler(message, check_num, unit)


def send_zkr(chat_id,amount,unit):
    bot.send_chat_action(chat_id, 'typing')
    back2main = types.InlineKeyboardButton(text='العودة للقائمة الرئيسية',callback_data='back2main')
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(back2main)
    if amount == 1 and unit == 'ساعات':
        bot.send_message(chat_id, ' سيتم إرسال أذكار متنوعة كل ساعة 🤍.',reply_markup=keyboard)
    elif amount == 2 and unit == 'ساعات':
        bot.send_message(chat_id, ' سيتم إرسال أذكار متنوعة كل ساعتين 🤍.',reply_markup=keyboard)
    elif amount in range(3,11) and unit == 'ساعات':
        bot.send_message(chat_id, f' سيتم إرسال اذكار متنوعة كل {amount}ساعات 🤍.',reply_markup=keyboard)
    elif amount >= 11 and unit == 'ساعات':
        bot.send_message(chat_id, f' سيتم إرسال اذكار متنوعة كل {amount}ساعة 🤍.',reply_markup=keyboard)
    elif amount == 1 and unit == 'دقائق':
        bot.send_message(chat_id, ' سيتم إرسال أذكار متنوعة كل دقيقة 🤍.',reply_markup=keyboard)
    elif amount == 2 and unit == 'دقائق':
        bot.send_message(chat_id, ' سيتم إرسال أذكار متنوعة كل دقيقتين 🤍.',reply_markup=keyboard)
    elif amount in range(3,11) and unit == 'دقائق':
        bot.send_message(chat_id, f' سيتم إرسال اذكار متنوعة كل {amount}دقايق 🤍.',reply_markup=keyboard)
    elif amount >= 11 and unit == 'دقائق':
        bot.send_message(chat_id, f' سيتم إرسال اذكار متنوعة كل {amount}دقيقة 🤍.',reply_markup=keyboard)

def start_sending(chat_id,seconds):
    timer = threading.Timer(seconds ,start_sending, args=(chat_id,seconds))
    timer.start()

    zekr = random.choice(azkar)

    bot.send_message(chat_id, zekr)

    users_timers[chat_id] = timer

@bot.callback_query_handler(func=lambda call : call.data == 'edit/')
def edit_ask(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    inline = types.InlineKeyboardMarkup()

    hours_bt = types.InlineKeyboardButton(text='بالساعات',callback_data='hours/')
    minutes_bt = types.InlineKeyboardButton(text= 'بالدقائق', callback_data='minutes/')

    inline.add(hours_bt)
    inline.add(minutes_bt)

    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="هل تريد أن يكون التذكير بالدقائق أو الساعات ؟",
                          reply_markup=inline)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call : call.data in ['hours/','minutes/'])
def edit_tzkeer(call):
    keyboard = types.InlineKeyboardMarkup()
    back2main = types.InlineKeyboardButton(text='العودة للقائمة الرئيسية',callback_data='back2main')
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    keyboard.add(back2main)
    if chat_id in users_timers:

        if call.data == 'hours/':
            unit = 'ساعات'
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="أكتب عدد الساعات 'بالأرقام فقط'")
            bot.register_next_step_handler(call.message, check_num, unit)

        elif call.data == 'minutes/':
            unit = 'دقائق'
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="أكتب عدد الدقائق 'بالأرقام فقط'")
            bot.register_next_step_handler(call.message, check_num, unit)
    else:
        bot.edit_message_text(chat_id=chat_id,message_id=message_id,text='لايوجد تذكير لتعديله', reply_markup=keyboard)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call : call.data == 'cancel-')
def cancel(call):
    keyboard = types.InlineKeyboardMarkup()

    back2main = types.InlineKeyboardButton(text='العودة للقائمة الرئيسية',callback_data='back2main')

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if chat_id in users_timers:

        users_timers[chat_id].cancel()
        keyboard.add(back2main)
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='تم إيقاف التذكيرات',
                              reply_markup=keyboard)
        update_users(chat_id,False)
        users_timers.pop(chat_id)

    else:
        keyboard.add(back2main)
        bot.edit_message_text(chat_id=chat_id,message_id=message_id, text='لايوجد تذكير لإيقافه',reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['احصائيات'])
def show_stats(message):
    total_users = users_db.count_documents({})
    active_users = users_db.count_documents({'azkar_active': True})
    bot.reply_to(message, f'إجمالي المستخدمين: {total_users}\nالمستخدمين النشطين حالياً: {active_users}')

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
