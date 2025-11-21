import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import aiohttp
import json
from urllib.parse import urlparse

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000")

class ScrapAIBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("crawl", self.crawl_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
🤖 **Scrap AI Bot** - Web Scraping Made Easy

**Commands:**
/crawl <url> - Scrape a single URL
/crawl_multiple - Scrape multiple URLs (send one per line)
/search <query> - Search scraped content
/status - Check scraping status

**Examples:**
/crawl https://example.com
/search artificial intelligence
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📖 **How to Use Scrap AI Bot:**

1. **Scrape a Website:**
   `/crawl https://example.com`

2. **Scrape Multiple Sites:**
   Send: `/crawl_multiple`
   Then send URLs (one per line)

3. **Search Content:**
   `/search machine learning`

4. **Check Status:**
   `/status`

⚡ The bot will extract clean text, generate embeddings, and make it searchable!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def crawl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Please provide a URL. Example: /crawl https://example.com")
            return
            
        url = context.args[0]
        
        # Validate URL
        if not self.is_valid_url(url):
            await update.message.reply_text("❌ Invalid URL format. Please use http:// or https://")
            return
            
        # Send to API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/v1/crawl",
                    json={"urls": [url]}
                ) as response:
                    if response.status == 200:
                        await update.message.reply_text(
                            f"✅ **URL Queued for Scraping!**\n\n"
                            f"🌐 {url}\n"
                            f"⏳ Processing...\n\n"
                            f"Use /status to check progress.",
                            parse_mode='Markdown'
                        )
                    else:
                        await update.message.reply_text("❌ Failed to queue URL. API error.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        
        # Check if it's multiple URLs (for crawl_multiple flow)
        if context.user_data.get('awaiting_urls'):
            urls = [line.strip() for line in text.split('\n') if line.strip()]
            valid_urls = [url for url in urls if self.is_valid_url(url)]
            
            if valid_urls:
                # Send to API
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{API_URL}/api/v1/crawl",
                            json={"urls": valid_urls}
                        ) as response:
                            if response.status == 200:
                                await update.message.reply_text(
                                    f"✅ **{len(valid_urls)} URLs Queued!**\n\n"
                                    f"⏳ Processing...\n"
                                    f"Use /status to check progress.",
                                    parse_mode='Markdown'
                                )
                            else:
                                await update.message.reply_text("❌ Failed to queue URLs.")
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {str(e)}")
            else:
                await update.message.reply_text("❌ No valid URLs found.")
                
            context.user_data['awaiting_urls'] = False
        else:
            await update.message.reply_text(
                "🤖 Send /help to see available commands or /crawl <url> to scrape a website."
            )
            
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Please provide a search query. Example: /search artificial intelligence")
            return
            
        query = " ".join(context.args)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL}/api/v1/search",
                    params={"query": query, "limit": 5}
                ) as response:
                    if response.status == 200:
                        results = await response.json()
                        if results:
                            response_text = "🔍 **Search Results:**\n\n"
                            for i, result in enumerate(results, 1):
                                title = result.get('title', 'No Title')
                                url = result.get('url', 'No URL')
                                snippet = result.get('content', '')[:100] + "..." if result.get('content') else ""
                                
                                response_text += f"{i}. **{title}**\n"
                                response_text += f"   {url}\n"
                                response_text += f"   {snippet}\n\n"
                                
                            await update.message.reply_text(response_text, parse_mode='Markdown')
                        else:
                            await update.message.reply_text("❌ No results found.")
                    else:
                        await update.message.reply_text("❌ Search failed.")
        except Exception as e:
            await update.message.reply_text(f"❌ Search error: {str(e)}")
            
    def is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except:
            return False
            
    def run(self):
        print("🤖 Telegram Bot Starting...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = ScrapAIBot()
    bot.run()
