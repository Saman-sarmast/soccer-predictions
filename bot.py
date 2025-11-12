import os
import logging
import asyncio
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# تنظیمات
BOT_TOKEN = os.environ.get('BOT_TOKEN')
TON_API_URL = "https://toncenter.com/api/v2/"
YOUR_TON_ADDRESS = "UQAtexOWAeOYuq8mUf2HNgJ3gsBBKpqk29svAyHw5U-pbKCX"

# دیتابیس
conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, username TEXT, subscription_end DATE)''')
c.execute('''CREATE TABLE IF NOT EXISTS payments
             (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, 
              tx_hash TEXT, status TEXT, created_date TIMESTAMP)''')

class TONPaymentChecker:
    async def check_payment(self, user_id: int, amount: float):
        """بررسی پرداخت کاربر از TON API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{TON_API_URL}getTransactions?address={YOUR_TON_ADDRESS}&limit=20"
                async with session.get(url) as response:
                    data = await response.json()
                    
                    for tx in data.get('result', []):
                        tx_value = int(tx['in_msg']['value']) / 10**9
                        tx_comment = tx['in_msg'].get('message', '')
                        tx_hash = tx['transaction_id']['hash']
                        
                        # تحمل ۰.۵ TON اختلاف (بدون اطلاع به کاربر)
                        if (abs(tx_value - amount) <= 0.5 and  
                            (str(user_id) in tx_comment or tx_comment == '')):
                            
                            # چک کردن duplicate
                            c.execute("SELECT id FROM payments WHERE tx_hash = ?", (tx_hash,))
                            if not c.fetchone():
                                # ذخیره پرداخت
                                c.execute("INSERT INTO payments (user_id, amount, tx_hash, status, created_date) VALUES (?, ?, ?, ?, ?)",
                                         (user_id, tx_value, tx_hash, 'completed', datetime.now()))
                                
                                # فعال‌سازی اشتراک
                                if amount == 3:  # ۱ روزه
                                    end_date = datetime.now() + timedelta(days=1)
                                else:  # ۱ ماهه
                                    end_date = datetime.now() + timedelta(days=30)
                                    
                                c.execute("INSERT OR REPLACE INTO users (user_id, username, subscription_end) VALUES (?, ?, ?)",
                                         (user_id, "user", end_date.strftime('%Y-%m-%d')))
                                conn.commit()
                                return True
                    return False
        except Exception as e:
            logging.error(f"خطا در بررسی پرداخت: {e}")
            return False

# منوها
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎯 دریافت پیش‌بینی امروز", callback_data='predict')],
        [InlineKeyboardButton("💳 خرید اشتراک", callback_data='subscribe')],
        [InlineKeyboardButton("ℹ️ راهنمایی", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def subscribe_menu():
    keyboard = [
        [InlineKeyboardButton("۱ روز آزمایشی - ۳ TON", callback_data='sub_1day')],
        [InlineKeyboardButton("۱ ماه کامل - ۳۹ TON", callback_data='sub_30day')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# دستورات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 **خوش آمدید به ربات پیش‌بینی آور ۲.۵** ⚽

🎯 **پیش‌بینی‌های حرفه‌ای مسابقات فوتبال**
💰 **پرداخت اتوماتیک با TON**

👇 برای شروع از دکمه‌های زیر استفاده کنید:
    """
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'predict':
        await predict_command(update, context)
    elif query.data == 'subscribe':
        await subscribe_command(update, context)
    elif query.data == 'help':
        await help_command(update, context)
    elif query.data in ['sub_1day', 'sub_30day']:
        await payment_command(update, context, query.data)
    elif query.data == 'back_main':
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())
    elif query.data.startswith('check_'):
        plan_type = query.data.replace('check_', '')
        await check_payment_command(update, context, plan_type)

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not check_subscription(user_id):
        text = """
❌ **اشتراک شما فعال نیست!**

برای دریافت پیش‌بینی‌های امروز، لطفا ابتدا اشتراک خود را تهیه کنید.
        """
        keyboard = [
            [InlineKeyboardButton("💳 خرید اشتراک", callback_data='subscribe')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_main')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # دریافت پیش‌بینی‌ها از گیت‌هاب
        from prediction_manager import PredictionManager
        prediction_manager = PredictionManager()
        predictions_text = prediction_manager.get_today_predictions()
        await query.edit_message_text(predictions_text, reply_markup=main_menu())

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = """
💎 **پلن‌های اشتراک:**

• ۱ روز آزمایشی - ۳ TON
• ۳۰ روز کامل - ۳۹ TON

💰 **پرداخت اتوماتیک با TON**
    """
    await query.edit_message_text(text, reply_markup=subscribe_menu())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = """
📖 **راهنمایی**

💳 **روش پرداخت:**
۱. پلن مورد نظر را انتخاب کنید
۲. مبلغ TON را به آدرس داده شده واریز کنید
۳. سیستم به طور خودکار پرداخت را بررسی می‌کند
۴. اشتراک شما فعال می‌شود

⚠️ در صورت مشکل در پرداخت، ۵ دقیقه منتظر بمانید سپس دوباره بررسی کنید
    """
    await query.edit_message_text(text, reply_markup=main_menu())

async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type):
    query = update.callback_query
    user_id = query.from_user.id
    
    plans = {
        'sub_1day': {'name': '۱ روزه', 'price': 3},
        'sub_30day': {'name': '۱ ماهه', 'price': 39}
    }
    
    plan = plans[plan_type]
    
    text = f"""
💳 **خرید اشتراک {plan['name']}**

💰 مبلغ: **دقیقاً {plan['price']} TON**

🏦 **آدرس TON:**
`{YOUR_TON_ADDRESS}`

⚠️ **توجه مهم:**
• فقط **یک تراکنش** با مقدار **دقیق {plan['price']} TON** واریز کنید
• پرداخت‌های چندتایی تأیید **نمی‌شوند**
• مبالغ کمتر یا بیشتر **تأیید نمی‌شوند**

🔄 پس از پرداخت دقیق، روی «بررسی پرداخت» کلیک کنید
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 بررسی پرداخت", callback_data=f'check_{plan_type}')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='subscribe')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def check_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type):
    query = update.callback_query
    user_id = query.from_user.id
    
    plans = {
        'sub_1day': {'name': '۱ روزه', 'price': 3},
        'sub_30day': {'name': '۱ ماهه', 'price': 39}
    }
    
    plan = plans[plan_type]
    
    # بررسی پرداخت
    payment_checker = TONPaymentChecker()
    payment_received = await payment_checker.check_payment(user_id, plan['price'])
    
    if payment_received:
        text = f"""
✅ **پرداخت شما تأیید شد!**

🎉 اشتراک {plan['name']} شما فعال شد.

اکنون می‌توانید از منوی اصلی پیش‌بینی‌های امروز را دریافت کنید.
        """
        await query.edit_message_text(text, reply_markup=main_menu())
    else:
        text = f"""
❌ **پرداختی یافت نشد**

لطفاً:
۱. مطمئن شوید **دقیقاً {plan['price']} TON** واریز کرده‌اید
۲. ۵ دقیقه منتظر بمانید (تأخیر شبکه)
۳. سپس دوباره بررسی کنید

🏦 آدرس: `{YOUR_TON_ADDRESS}`
        """
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 بررسی مجدد", callback_data=f'check_{plan_type}')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='subscribe')]
        ]))

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
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.run_polling()

if __name__ == '__main__':
    main()
