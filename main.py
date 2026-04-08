import telebot
import re
import time
import random
import os
from telebot import types
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

import database

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env file!")

bot = telebot.TeleBot(API_TOKEN, parse_mode="HTML")

database.init_db()


def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔗 Connect API", callback_data="connect_api"),
        types.InlineKeyboardButton("📲 Start Checker", callback_data="start_checker")
    )
    return markup


def api_connected_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📲 Start Checker", callback_data="start_checker"),
        types.InlineKeyboardButton("🗑 Reset API", callback_data="reset_api")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 Back", callback_data="main_menu")
    )
    return markup


def restart_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔁 Start New Check", callback_data="main_menu"))
    return markup


def chunk_list(lst, size=50):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user = database.get_user(cid)
    if not user:
        database.update_user_api(cid, "", "", "")
    
    msg = (
        "<b>🚀 WhatsApp Validator Bot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔗 Connect your Evolution API\n"
        "📲 Validate WhatsApp numbers\n\n"
        "Click below to get started:"
    )
    bot.send_message(cid, msg, reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    cid = call.message.chat.id
    user = database.get_user(cid)

    if call.data == "main_menu":
        database.update_state(cid, "IDLE")
        send_welcome(call.message)

    elif call.data == "connect_api":
        if user and user.get('api_url') and user.get('instance_name') and user.get('api_key'):
            api = EvolutionAPI(user['api_url'], user['instance_name'], user['api_key'])
            connected, _ = api.check_connection()
            if connected:
                msg = (
                    "<b>🟢 API Already Connected</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "Instance: <code>{instance}</code>\n\n"
                    "Ready to start checking!"
                ).format(instance=user['instance_name'])
                bot.send_message(cid, msg, reply_markup=api_connected_menu())
                return
        database.update_state(cid, "AWAITING_CREDENTIALS")
        bot.send_message(
            cid,
            "<b>🔗 Connect API</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Send credentials in this format:\n"
            "<code>URL, InstanceName, APIKey</code>\n\n"
            "Example:\n"
            "<code>http://192.168.1.100:8080, myinstance, abc123xyz</code>"
        )

    elif call.data == "start_checker":
        if not user or not user.get('api_url') or not user.get('instance_name') or not user.get('api_key'):
            bot.answer_callback_query(call.id, "❌ API not connected! Click Connect API first.", show_alert=True)
            return
        
        api = EvolutionAPI(user['api_url'], user['instance_name'], user['api_key'])
        connected, _ = api.check_connection()
        if not connected:
            bot.answer_callback_query(call.id, "❌ API not reachable! Check your connection.", show_alert=True)
            return
        
        database.update_state(cid, "AWAITING_NUMBERS")
        bot.send_message(
            cid,
            "<b>📲 Ready to Check</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Send me phone numbers to validate.\n"
            "You can send single numbers or bulk text.\n\n"
            "Example:\n"
            "<code>1234567890</code>\n"
            "or\n"
            "<code>1234567890 9876543210 5551234567</code>"
        )

    elif call.data == "reset_api":
        database.update_user_api(cid, "", "", "")
        database.update_state(cid, "IDLE")
        bot.send_message(cid, "🗑️ <b>API Reset</b>\n\nClick Connect API to set up again.", reply_markup=main_menu())


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    cid = message.chat.id
    user = database.get_user(cid)
    
    if not user:
        send_welcome(message)
        return

    state = user.get('state', 'IDLE')

    if state == "AWAITING_CREDENTIALS":
        parts = message.text.split(',')
        if len(parts) != 3:
            bot.reply_to(message, "⚠️ Invalid format!\n\nSend as: <code>URL, InstanceName, APIKey</code>")
            return
        
        api_url = parts[0].strip()
        instance_name = parts[1].strip()
        api_key = parts[2].strip()

        from evolution_api import EvolutionAPI
        api = EvolutionAPI(api_url, instance_name, api_key)
        connected, resp = api.check_connection()
        
        if connected:
            database.update_user_api(cid, api_url, instance_name, api_key)
            database.update_state(cid, "IDLE")
            bot.reply_to(
                message,
                "<b>✅ API Connected Successfully!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"Instance: <code>{instance_name}</code>\n\n"
                "Click Start Checker to begin.",
                reply_markup=api_connected_menu()
            )
        else:
            bot.reply_to(message, f"❌ <b>Connection Failed</b>\n\nCould not connect to API.\nCheck your URL and credentials.")

    elif state == "AWAITING_NUMBERS":
        numbers = re.findall(r'\d{10,15}', message.text)
        if not numbers:
            bot.reply_to(message, "❌ No valid numbers found!\n\nNumbers must be 10-15 digits.")
            return

        numbers = list(set(numbers))
        total = len(numbers)
        bot.send_message(cid, f"⏳ Received {total} numbers...\nProcessing in batches of 50...")

        all_results = []
        counts = {"valid": 0, "invalid": 0, "error": 0}
        failed_numbers = []

        batches = list(chunk_list(numbers, 50))
        
        for batch_idx, batch in enumerate(batches, 1):
            bot.send_message(cid, f"⚙️ Processing batch {batch_idx}/{len(batches)} ({len(batch)} numbers)...")
            
            from evolution_api import EvolutionAPI
            api = EvolutionAPI(user['api_url'], user['instance_name'], user['api_key'])
            
            results = []
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {executor.submit(api.check_number, num): num for num in batch}
                
                for future in as_completed(futures):
                    text, category = future.result()
                    results.append(text)
                    counts[category] += 1
                    
                    if category in ("invalid", "error"):
                        num = re.sub(r"\D", "", text)
                        if num:
                            failed_numbers.append(num)
                    
                    time.sleep(random.uniform(2.5, 5.5))
            
            all_results.extend(results)
            
            if batch_idx < len(batches):
                bot.send_message(cid, "😴 <b>Resting to prevent bans...</b>\n3 minute cooldown between batches.")
                time.sleep(180)

        summary = (
            "<b>📊 Results Summary</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Valid: {valid}\n"
            "⛔️ Invalid: {invalid}\n"
            "⏳ Errors: {error}\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ).format(**counts)

        bot.send_message(cid, summary)

        result_text = "\n".join(all_results)
        if len(result_text) > 4000:
            for i in range(0, len(all_results), 50):
                bot.send_message(cid, "\n".join(all_results[i:i+50]))
        else:
            bot.send_message(cid, result_text)

        if failed_numbers:
            file_path = f"failed_{cid}_{int(time.time())}.txt"
            with open(file_path, "w") as f:
                f.write("\n".join(sorted(set(failed_numbers))))
            
            with open(file_path, "rb") as f:
                bot.send_document(cid, f, caption="📎 Failed/Invalid numbers")
            
            os.remove(file_path)

        bot.send_message(
            cid,
            "<b>✅ Processing Complete!</b>",
            reply_markup=restart_keyboard()
        )
        database.update_state(cid, "IDLE")

    else:
        send_welcome(message)


if __name__ == "__main__":
    print("🤖 Bot started. Press Ctrl+C to stop.")
    bot.infinity_polling()