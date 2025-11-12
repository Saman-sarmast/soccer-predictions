import requests
import json
from datetime import datetime

class PredictionManager:
    def __init__(self):
        self.github_url = "https://raw.githubusercontent.com/Saman-sarmast/soccer-predictions/refs/heads/main/predictions.json"
    
    def get_today_predictions(self):
        try:
            response = requests.get(self.github_url)
            predictions_data = response.json()
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if today in predictions_data:
                return self.format_predictions(predictions_data[today])
            else:
                return "❌ امروز پیش‌بینی‌ای موجود نیست."
                
        except Exception as e:
            return f"⚠️ خطا در دریافت پیش‌بینی‌ها: {str(e)}"
    
    def format_predictions(self, today_data):
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
