import asyncio
import platform
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import g4f
import html

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BOT_TOKEN = ''

bot = telebot.TeleBot(BOT_TOKEN)

chat_contexts = {}

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="End the conversation"))
    return keyboard

def split_long_message(message, chunk_size=4096):
    return [message[i:i + chunk_size] for i in range(0, len(message), chunk_size)]

@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "Hello! I am your assistant GPT-4 🤖.\n\n"
        " Ask me any questions — I'm always happy to help! \n",
        reply_markup=get_main_keyboard()
    )

    chat_contexts[chat_id] = [{"role": "system",
                               "content": "Please use the usual mathematical symbols and signs instead of HTML formatting. For example, use *, /, ^, ≤, ≥, ≠, ∑, ∏, √ and other characters directly."}]

@bot.message_handler(func=lambda msg: msg.text == "End the conversation")
def end_chat(message):
    chat_id = message.chat.id
    if chat_id in chat_contexts:
        chat_contexts.pop(chat_id)
    bot.send_message(chat_id, "The conversation is over. You can start a new conversation by simply asking a question.")
    chat_contexts[chat_id] = [{"role": "system",
                               "content": "Please use the usual mathematical symbols and signs instead of HTML formatting. For example, use *, /, ^, ≤, ≥, ≠, ∑, ∏, √ and other characters directly."}]

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    chat_id = message.chat.id
    user_input = message.text.strip()

    if chat_id not in chat_contexts:
        chat_contexts[chat_id] = [
            {"role": "system", "content": "Please answer the user's question clearly and clearly."}]

    chat_contexts[chat_id].append({"role": "user", "content": user_input})

    bot.send_chat_action(chat_id, "typing")

    prompt = f"The user asked: '{user_input}'. Answer his question clearly and clearly."
    prompt += "\nConversation history:\n" + "\n".join([item["content"] for item in chat_contexts[chat_id]])

    try:
        # Генерация ответа через g4f
        response = g4f.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )

        if isinstance(response, dict) and 'choices' in response:
            assistant_message = response['choices'][0]['message']['content']
        else:
            assistant_message = str(response)

    except Exception as e:
        assistant_message = f"An error occurred when generating the response: {str(e)}"

    chat_contexts[chat_id].append({"role": "assistant", "content": assistant_message})

    decoded_response = html.unescape(assistant_message)
    split_messages = split_long_message(decoded_response)

    for msg in split_messages:
        bot.send_message(chat_id, msg)

if __name__ == '__main__':
    print("The bot is running!")
    bot.infinity_polling()
