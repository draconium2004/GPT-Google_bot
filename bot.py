import openai
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import os

# Read API keys from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

openai.api_key = OPENAI_API_KEY

# Handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    if user_input.lower().startswith(("search:", "google:", "find:")):
        query = user_input.split(":", 1)[1].strip()
        search_results = fetch_google_cse_results(query)
        await update.message.reply_text(search_results)
    else:
        chat_response = ask_chatgpt(user_input)
        await update.message.reply_text(chat_response)

# ChatGPT response
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ChatGPT Error: {e}"

# Google Search via CSE
def fetch_google_cse_results(query):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query
        }
        res = requests.get(url, params=params).json()
        items = res.get("items", [])
        if not items:
            return "No search results found."

        formatted = "\n\n".join([f"{item['title']}\n{item['link']}" for item in items[:5]])
        return f"Top Google Results:\n\n{formatted}"
    except Exception as e:
        return f"Search Error: {e}"

# Start the bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
