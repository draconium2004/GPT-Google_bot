import openai
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv

# Load environment variables from a .env file (for local development)
load_dotenv()

# Read API keys from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Check if all environment variables are set
if not all([TELEGRAM_TOKEN, OPENAI_API_KEY, GOOGLE_API_KEY, GOOGLE_CSE_ID]):
    raise ValueError("One or more environment variables are missing!")

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

# Function to handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    # If the user wants to perform a Google search, detect command-based triggers
    if user_input.lower().startswith(("search:", "google:", "find:")):
        query = user_input.split(":", 1)[1].strip()
        search_results = fetch_google_cse_results(query)
        await update.message.reply_text(search_results)
    else:
        # Otherwise, process the prompt with ChatGPT
        chat_response = ask_chatgpt(user_input)
        await update.message.reply_text(chat_response)

# Function to get a ChatGPT response with enhanced error handling
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # You can switch to "gpt-3.5-turbo" if preferred
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,       # Limits the number of tokens in the response
            temperature=0.7,      # Controls the randomness of the output
        )
        return response.choices[0].message["content"].strip()

    except openai.error.RateLimitError:
        return "Error: Rate limit exceeded. Please try again later."
    except openai.error.AuthenticationError:
        return "Error: Authentication failed. Please check your API key."
    except openai.error.APIError as e:
        return f"Error with the OpenAI API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Function to fetch Google Custom Search Engine results
def fetch_google_cse_results(query):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query
        }
        res = requests.get(url, params=params)
        res.raise_for_status()  # Raise exception for HTTP errors
        data = res.json()
        items = data.get("items", [])

        if not items:
            return "No search results found."

        # Format the top 5 results as "Title\nURL"
        formatted = "\n\n".join([f"{item['title']}\n{item['link']}" for item in items[:5]])
        return f"Top Google Results:\n\n{formatted}"

    except requests.exceptions.RequestException as e:
        return f"Google Search Error: {e}"
    except KeyError:
        return "Error processing the search results."
    except Exception as e:
        return f"An unexpected error occurred during search: {e}"

# Start the Telegram bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    app.run_polling()