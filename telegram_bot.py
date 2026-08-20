import os
import logging
import requests
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://localhost:8000")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


class ScrapAIBot:
    def __init__(self, token: str, api_url: str = API_URL):
        self.api_url = api_url.rstrip("/")
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("crawl", self.crawl_command))
        self.app.add_handler(CommandHandler("search", self.search_command))
        self.app.add_handler(CommandHandler("answer", self.answer_command))
        self.app.add_handler(CommandHandler("ask", self.answer_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
🕷️ **ScrapAI Bot – Autonomous Knowledge Assistant**

Your offline-ready web scraping and semantic search companion.

**Directives:**
• `/crawl <url>` — Ingest and index a website
• `/search <query>` — Hybrid search over crawled vault
• `/answer <question>` — Extractive QA reasoning with citations
• `/stats` — Real-time telemetry & page counts
• `/help` — Command directory

⚡ Connected to ScrapAI Engine: `{}`
        """.format(self.api_url)
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        
    async def crawl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a URL.\n\nExample: `/crawl https://example.com`",
                parse_mode='Markdown'
            )
            return
            
        url = context.args[0].strip()
        if not url.startswith(('http://', 'https://')):
            url = "https://" + url
            
        try:
            await update.message.chat.send_action(action="typing")
            response = requests.post(
                f"{self.api_url}/api/v1/crawl",
                json={"urls": [url], "max_depth": 1},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                await update.message.reply_text(
                    f"✅ **Target Injected into Queue!**\n\n"
                    f"🌐 URL: `{url}`\n"
                    f"📊 Status: {result.get('message', 'Queued for ingestion')}\n"
                    f"⏳ Total Queued: {result.get('queued', 1)}\n\n"
                    f"Use `/stats` to monitor progress or `/search` to explore.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ API Error ({response.status_code}): {response.text[:200]}")
        except Exception as e:
            await update.message.reply_text(f"❌ Connection error: {str(e)}")
            
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a search query.\n\nExample: `/search artificial intelligence`",
                parse_mode='Markdown'
            )
            return
            
        query = " ".join(context.args)
        try:
            await update.message.chat.send_action(action="typing")
            response = requests.get(
                f"{self.api_url}/api/v1/search",
                params={"q": query, "limit": 5},
                timeout=15
            )
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    text = f"🔍 **Search Results for:** _{query}_\n\n"
                    for i, r in enumerate(results[:5], 1):
                        title = r.get('title') or 'Untitled'
                        url = r.get('url') or ''
                        snippet = r.get('snippet') or r.get('content') or ''
                        score = r.get('score', 0.0)
                        text += f"*{i}. {title}* (Score: `{score}`)\n"
                        text += f"🔗 `{url}`\n"
                        text += f"💬 _{snippet[:140]}..._\n\n"
                    await update.message.reply_text(text, parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"❌ No records found for '{query}'. Try `/crawl <url>` first.")
            else:
                await update.message.reply_text(f"❌ Search failed: HTTP {response.status_code}")
        except Exception as e:
            await update.message.reply_text(f"❌ Search error: {str(e)}")

    async def answer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a question.\n\nExample: `/answer What is machine learning?`",
                parse_mode='Markdown'
            )
            return
            
        query = " ".join(context.args)
        try:
            await update.message.chat.send_action(action="typing")
            response = requests.post(
                f"{self.api_url}/api/v1/query/answer",
                json={"query": query, "limit": 5},
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'No answer synthesized.')
                sources = data.get('sources', [])
                
                text = f"🤖 **Extractive QA Synthesized Answer:**\n\n{answer}\n\n"
                if sources:
                    text += "📚 **Referenced Sources:**\n"
                    for s in sources:
                        text += f"[{s.get('citation_id')}] [{s.get('title') or s.get('url')}]({s.get('url')})\n"
                await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
            else:
                await update.message.reply_text(f"❌ Reasoning engine error: HTTP {response.status_code}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.message.chat.send_action(action="typing")
            response = requests.get(f"{self.api_url}/api/v1/stats", timeout=10)
            if response.status_code == 200:
                s = response.json()
                text = f"""
📊 **ScrapAI Engine Telemetry**

📄 **Indexed Pages:** {s.get('pages', 0)}
✂️ **Text Chunks:** {s.get('chunks', 0)}
🧠 **Embeddings Stored:** {s.get('embeddings', 0)}
⏳ **Active Queue:** {s.get('queued', 0)}
🌐 **Domains Tracked:** {s.get('domains', 0)}
🔍 **Searches Handled:** {s.get('searches', 0)}
                """
                await update.message.reply_text(text, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Could not retrieve stats (HTTP {response.status_code})")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📖 **ScrapAI Bot Command Directory**

• `/crawl <url>` — Enqueue website for crawling & indexing
• `/search <query>` — Search knowledge base with hybrid scoring
• `/answer <query>` — Generate structured answer with citations
• `/stats` — Show system stats & queue metrics
• `/help` — Show this message

💡 *Send any URL directly to quick-crawl it!*
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip() if update.message.text else ""
        if text.startswith(('http://', 'https://')):
            # Quick crawl shortcut
            context.args = [text]
            await self.crawl_command(update, context)
        else:
            await update.message.reply_text(
                "🤖 Send `/help` for commands or `/answer <your question>` to search knowledge.",
                parse_mode='Markdown'
            )
        
    def run(self):
        logger.info(f"🤖 Telegram Bot Starting... Connected to {self.api_url}")
        self.app.run_polling()


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ Warning: TELEGRAM_BOT_TOKEN environment variable not set.")
        print("To run the Telegram bot, set TELEGRAM_BOT_TOKEN and run again.")
    else:
        bot = ScrapAIBot(TELEGRAM_BOT_TOKEN)
        bot.run()
