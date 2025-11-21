import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Your WORKING API URL - use the exact one from your tests
API_URL = "https://scrapai-2.onrender.com"  # ⚠️ This is your LIVE API!
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class ScrapAIBot:
    def __init__(self, token: str):
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("crawl", self.crawl_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("search", self.search_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
🤖 **Scrap AI Bot - NOW LIVE!** 🎉

Your personal web scraping assistant is ready!

**Commands:**
/crawl <url> - Scrape any website
/search <query> - Search scraped content  
/stats - Check scraping status
/help - Get instructions

**Examples:**
/crawl https://example.com
/search artificial intelligence
/stats

⚡ Powered by your live ScrapAI API!
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        
    async def crawl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a URL\n\n"
                "Example: /crawl https://example.com\n"
                "Example: /crawl https://httpbin.org/html"
            )
            return
            
        url = context.args[0]
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ Please use a valid URL starting with http:// or https://")
            return
            
        try:
            # Show typing indicator
            await update.message.chat.send_action(action="typing")
            
            # Call your LIVE API
            response = requests.post(
                f"{API_URL}/api/v1/crawl",
                json={"urls": [url]},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                await update.message.reply_text(
                    f"✅ **URL Queued Successfully!**\n\n"
                    f"🌐 {url}\n"
                    f"📊 {result.get('message', 'Added to crawl queue')}\n\n"
                    f"Use /stats to check progress or /search to find content.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ API Error: {response.status_code}\n\nTry again in a moment.")
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Connection Error**\n\n"
                f"Error: {str(e)}\n\n"
                f"The API might be waking up (free tier). Try again in 30 seconds.",
                parse_mode='Markdown'
            )
            
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.message.chat.send_action(action="typing")
            
            response = requests.get(f"{API_URL}/api/v1/stats", timeout=30)
            
            if response.status_code == 200:
                stats = response.json()
                
                stats_text = f"""
📊 **ScrapAI Statistics**

📄 **Pages Scraped:** {stats.get('pages', 0)}
⏳ **URLs Queued:** {stats.get('queued', 0)}
✅ **Total Processed:** {stats.get('total', 0)}

💡 **Tip:** Use /crawl to add more URLs
                """
                await update.message.reply_text(stats_text, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Could not fetch statistics. API might be waking up.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a search term\n\n"
                "Example: /search artificial intelligence\n"
                "Example: /search example domain"
            )
            return
            
        query = " ".join(context.args)
        
        try:
            await update.message.chat.send_action(action="typing")
            
            response = requests.get(
                f"{API_URL}/api/v1/search",
                params={"q": query},
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                
                if results:
                    response_text = f"🔍 **Search Results for '{query}':**\n\n"
                    
                    for i, result in enumerate(results[:5], 1):  # Show first 5 results
                        title = result.get('title', 'No Title')[:50]
                        url = result.get('url', 'No URL')[:50]
                        content_preview = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                        
                        response_text += f"{i}. **{title}**\n"
                        response_text += f"   `{url}`\n"
                        response_text += f"   {content_preview}\n\n"
                    
                    await update.message.reply_text(response_text, parse_mode='Markdown')
                else:
                    await update.message.reply_text(
                        f"❌ No results found for '{query}'\n\n"
                        f"Try /crawl to add some websites first!"
                    )
            else:
                await update.message.reply_text("❌ Search failed. API might be waking up.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Search error: {str(e)}")
            
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📖 **ScrapAI Bot Help**

**Available Commands:**
/crawl <url> - Scrape a website
/search <query> - Search scraped content
/stats - Show scraping statistics
/help - This message

**Examples:**
• /crawl https://example.com
• /search machine learning
• /stats

**Features:**
• Extract clean text from websites
• Search through scraped content  
• Real-time statistics
• Fast and efficient

⚡ **Your API is LIVE and working!**
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        
        # If someone sends a URL directly
        if text.startswith(('http://', 'https://')):
            await update.message.reply_text(
                f"🌐 **URL Detected!**\n\n"
                f"To scrape: {text}\n\n"
                f"Use: /crawl {text}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "🤖 Send /help to see available commands\n"
                "Or use /crawl <url> to scrape a website"
            )
        
    def run(self):
        print("🤖 Telegram Bot Starting...")
        print(f"🌐 Connected to API: {API_URL}")
        self.app.run_polling()

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Missing TELEGRAM_BOT_TOKEN environment variable")
        exit(1)
        
    bot = ScrapAIBot(TELEGRAM_BOT_TOKEN)
    bot.run()
