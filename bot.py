import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sqlite3
import requests
import json
from datetime import datetime

# تنظیمات - توکن از environment variables گرفته میشه
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GITHUB_PREDICTIONS_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/predictions.json"

# دیتابیس
conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, username TEXT, subscription_end DATE, plan TEXT)''')

class PredictionManager:
    def get_today_predictions(self):
        """دریافت پیش‌بینی‌های امروز از گیت‌هاب"""
        try:
            response = requests.get(GITHUB_PREDICTIONS_URL)
            predictions_data = response.json()
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if today in predictions_data:
                return self.format_predictions(predictions_data[today])
            else:
                return "❌ امروز پیش‌بینی‌ای موجود نیست."
                
        except Exception as e:
            return f"⚠️ خطا در دریافت پیش‌بینی‌ها: {str(e)}"
    
    def format_predictions(self, today_data):
        """قالب‌بندی پیش‌بینی‌ها"""
        text = f"🎯 **پیش‌بینی‌های آور ۲.۵ - {today_data['date']}** ⚽\n\n"
        
        for i, pred in enumerate(today_data['predictions'], 1):
            text += f"━━━━━━━━━━━━━━━━━━━━\n"
            text += f"🏆 **{pred['league']}**\n"
            text += f"⚽ {pred['match']}\n"
            text += f"⏰ {pred['time']} | 📊 اطمینان: {pred['confidence']}%\n"
            text += f"💰 Odds: {pred['odds']} | {pred['prediction']}\n\n"
            
            text += f"📈 **دلایل:**\n"
            for reason in pred['reasons']:
                text += f"• {reason}\n"
            text += f"\n"
        
        text += "⚠️ شرط‌بندی با مسئولیت خودتان"
        return text

# منوها
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎯 دریافت پیش‌بینی امروز", callback_data='predict')],
        [InlineKeyboardButton("💳 خرید اشتراک", callback_data='subscribe')],
        [InlineKeyboardButton("ℹ️ درباره ربات", callback_data='about')],
        [InlineKeyboardButton("🎫 پشتیبانی", callback_data='support')]
    ]
    return InlineKeyboardMarkup(keyboard)

def subscribe_menu():
    keyboard = [
        [InlineKeyboardButton("۱ روز آزمایشی - ۱۰ دلار", callback_data='sub_1day')],
        [InlineKeyboardButton("۱ ماه کامل - ۱۰۰ دلار", callback_data='sub_30day')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# دستورات
def start(update: Update, context):
    welcome_text = """
🤖 **خوش آمدید به ربات پیش‌بینی آور ۲.۵** ⚽

🎯 **پیش‌بینی‌های حرفه‌ای مسابقات فوتبال**
💰 **سیگنال‌های با odds عالی**

💎 **برای شروع روی «دریافت پیش‌بینی امروز» کلیک کنید**
    """
    update.message.reply_text(welcome_text, reply_markup=main_menu())

def button_handler(update: Update, context):
    query = update.callback_query
    query.answer()
    
    if query.data == 'predict':
        predict_command(update, context)
    elif query.data == 'subscribe':
        subscribe_command(update, context)
    elif query.data == 'about':
        about_command(update, context)
    elif query.data == 'support':
        support_command(update, context)
    elif query.data in ['sub_1day', 'sub_30day']:
        payment_command(update, context, query.data)
    elif query.data == 'back_main':
        query.edit_message_text("منوی اصلی:", reply_markup=main_menu())

def predict_command(update: Update, context):
    query = update.callback_query
    
    if not check_subscription(query.from_user.id):
        text = """
❌ **اشتراک شما فعال نیست!**

برای دریافت پیش‌بینی‌های امروز، لطفا ابتدا اشتراک خود را تهیه کنید.

💎 **پلن‌های اشتراک:**
• ۱ روز آزمایشی: ۱۰ دلار
• ۳۰ روز کامل: ۱۰۰ دلار
        """
        keyboard = [
            [InlineKeyboardButton("💳 خرید اشتراک", callback_data='subscribe')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_main')]
        ]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        prediction_manager = PredictionManager()
        predictions_text = prediction_manager.get_today_predictions()
        query.edit_message_text(predictions_text, reply_markup=main_menu())

def subscribe_command(update: Update, context):
    query = update.callback_query
    text = """
💎 **پلن‌های اشتراک:**

• ۱ روز آزمایشی - ۱۰ دلار
• ۳۰ روز کامل - ۱۰۰ دلار

💰 **پرداخت با TON یا USDT**
    """
    query.edit_message_text(text, reply_markup=subscribe_menu())

def about_command(update: Update, context):
    query = update.callback_query
    text = """
🤖 **درباره ربات Over 2.5**

🎯 **تخصص:** پیش‌بینی مسابقات فوتبال با تمرکز روی آور ۲.۵ گل

📊 **روش تحلیل:**
• بررسی آمار گل‌زنی تیم‌ها
• تاریخچه مسابقات مستقیم
• وضعیت بازیکنان کلیدی

💎 **برای شروع اشتراک خود را انتخاب کنید**
    """
    query.edit_message_text(text, reply_markup=main_menu())

def support_command(update: Update, context):
    query = update.callback_query
    text = """
🎫 **پشتیبانی**

📞 برای ارتباط با پشتیبانی:
@YourSupportUsername

⏰ پاسخگویی ۲۴ ساعته
    """
    query.edit_message_text(text, reply_markup=main_menu())

def payment_command(update: Update, context, plan_type):
    query = update.callback_query
    
    plans = {
        'sub_1day': {'name': '۱ روزه', 'price': 10},
        'sub_30day': {'name': '۱ ماهه', 'price': 100}
    }
    
    plan = plans[plan_type]
    text = f"""
💳 **خرید اشتراک {plan['name']}**

💰 مبلغ: {plan['price']} دلار

💎 **روش پرداخت:**
۱. مبلغ را به آدرس زیر واریز کنید:
`UQD-jmuwkZ9hlKiu84uGK8fv-QUFF2T9pkQ6gzNcWlqCsT-b`

۲. رسید پرداخت را برای پشتیبانی ارسال کنید

۳. پس از تایید، اشتراک شما فعال میشود

📞 پشتیبانی: @Over25Predict_supportBot
    """
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data='subscribe')]
    ]
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def check_subscription(user_id):
    """بررسی وضعیت اشتراک کاربر"""
    c.execute("SELECT subscription_end FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if result and datetime.strptime(result[0], '%Y-%m-%d') > datetime.now():
        return True
    return False

def main():
    if not BOT_TOKEN:
        logging.error("توکن ربات تنظیم نشده!")
        return
    
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler, pattern='.*'))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
