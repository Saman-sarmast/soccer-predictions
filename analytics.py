import sqlite3
from datetime import datetime

def show_detailed_stats():
    conn = sqlite3.connect('subscriptions.db')
    c = conn.cursor()
    
    print("=" * 60)
    print("📊 **آمار دقیق کاربران ربات**")
    print("=" * 60)
    
    # لیست تمام کاربران
    c.execute("SELECT user_id, username, subscription_end FROM users ORDER BY subscription_end DESC")
    users = c.fetchall()
    
    print(f"👥 تعداد کل کاربران: {len(users)}")
    print("\n📋 لیست کاربران:")
    print("-" * 60)
    
    for user_id, username, subscription_end in users:
        status = "✅ فعال" if subscription_end and datetime.strptime(subscription_end, '%Y-%m-%d') > datetime.now() else "❌ غیرفعال"
        print(f"🆔 آیدی: {user_id}")
        print(f"👤 یوزرنیم: @{username}" if username else "👤 یوزرنیم: ندارد")
        print(f"📅 اشتراک تا: {subscription_end}")
        print(f"🔸 وضعیت: {status}")
        print("-" * 40)
    
    # آمار پرداخت‌ها
    c.execute("SELECT COUNT(*), SUM(amount) FROM payments WHERE status = 'completed'")
    payment_count, total_income = c.fetchone()
    total_income = total_income or 0
    
    print(f"💰 پرداخت‌های موفق: {payment_count}")
    print(f"💵 مجموع درآمد: {total_income} TON")
    print("=" * 60)

if __name__ == '__main__':
    show_detailed_stats()
