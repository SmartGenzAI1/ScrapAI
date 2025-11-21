# In telegram_bot.py - remove aiohttp, use requests
import requests
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

API_URL = os.getenv("API_URL", "http://localhost:8000")

class ScrapAIBot:
    def __init__(self, token: str):
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("crawl", self.crawl_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 Scrap AI Bot\n\n"
            "Commands:\n"
            "/crawl <url> - Scrape website\n"
            "/stats - Show status\n"
            "/help - Get help"
        )
        
    async def crawl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /crawl https://example.com")
            return
            
        url = context.args[0]
        
        try:
            response = requests.post(f"{API_URL}/api/v1/crawl", json={"urls": [url]})
            if response.status_code == 200:
                await update.message.reply_text(f"✅ Queued: {url}")
            else:
                await update.message.reply_text("❌ Failed to queue URL")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = requests.get(f"{API_URL}/api/v1/stats")
            if response.status_code == 200:
                stats = response.json()
                await update.message.reply_text(
                    f"📊 Stats:\n"
                    f"Pages: {stats['pages']}\n"
                    f"Queued: {stats['queued']}\n"
                    f"Processed: {stats['processed']}"
                )
            else:
                await update.message.reply_text("❌ Could not get stats")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Help:\n"
            "- /crawl <url> - Scrape website\n"
            "- /stats - Show statistics\n"
            "- Works with most simple websites"
        )
        
    def run(self):
        print("🤖 Telegram bot running...")
        self.app.run_polling()

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Missing TELEGRAM_BOT_TOKEN")
        exit(1)
        
    bot = ScrapAIBot(token)
    bot.run()
