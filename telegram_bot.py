import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Get config from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Use your ACTUAL Render URL - replace with your exact URL
API_URL = "https://scrapai-2.onrender.com"  # ⚠️ CHANGE THIS TO YOUR EXACT URL

class SimpleScrapAIBot:
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
            "🤖 Scrap AI Bot - NOW WORKING!\n\n"
            "Commands:\n"
            "/crawl <url> - Scrape a website\n"
            "/stats - Show status\n"
            "/help - Get help"
        )
        
    async def crawl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Please provide a URL. Example: /crawl https://example.com")
            return
            
        url = context.args[0]
        
        try:
            print(f"🔄 Attempting to call API: {API_URL}/api/v1/crawl")
            response = requests.post(
                f"{API_URL}/api/v1/crawl", 
                json=[url],
                timeout=30  # Add timeout
            )
            print(f"📡 API Response: {response.status_code}")
            
            if response.status_code == 200:
                await update.message.reply_text(f"✅ URL queued: {url}")
            else:
                await update.message.reply_text(f"❌ API returned {response.status_code}")
        except Exception as e:
            error_msg = f"❌ Error connecting to API: {str(e)}"
            print(error_msg)
            await update.message.reply_text(error_msg)
            
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            print(f"🔄 Getting stats from: {API_URL}/api/v1/stats")
            response = requests.get(f"{API_URL}/api/v1/stats", timeout=30)
            print(f"📊 Stats response: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                await update.message.reply_text(
                    f"📊 Stats:\n"
                    f"Pages scraped: {stats.get('pages', 0)}\n"
                    f"URLs queued: {stats.get('queued', 0)}\n"
                    f"Total URLs: {stats.get('total', 0)}"
                )
            else:
                await update.message.reply_text(f"❌ Stats API returned {response.status_code}")
        except Exception as e:
            error_msg = f"❌ Error getting stats: {str(e)}"
            print(error_msg)
            await update.message.reply_text(error_msg)
            
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Help:\n"
            "- /crawl <url> - Scrape a website\n"
            "- /stats - Show statistics\n"
            "- /start - Show welcome message"
        )
        
    def run(self):
        print(f"🤖 Telegram bot starting...")
        print(f"🌐 API URL: {API_URL}")
        self.app.run_polling()

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Missing TELEGRAM_BOT_TOKEN environment variable")
        exit(1)
        
    bot = SimpleScrapAIBot(TELEGRAM_BOT_TOKEN)
    bot.run()
