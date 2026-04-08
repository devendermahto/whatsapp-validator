\## 📄 Product Requirements Document (PRD)



\### 1. Product Overview

\*\*Name:\*\* Self-Hosted WhatsApp Validator Bot

\*\*Purpose:\*\* A Telegram bot that validates whether phone numbers are active on WhatsApp. It uses a self-hosted Evolution API (running via Docker on Unraid) to bypass third-party subscription costs and improve data privacy.

\*\*Target Environment:\*\* Unraid Server (Evolution API in Docker) + Python backend.



\### 2. System Architecture

\* \*\*Frontend UI:\*\* Telegram App (via `pyTelegramBotAPI`).

\* \*\*Backend Logic:\*\* Python 3.10+.

\* \*\*Database:\*\* SQLite (to store user sessions, API URLs, and API Keys persistently without losing them on server restarts).

\* \*\*WhatsApp Gateway:\*\* Evolution API (Self-Hosted).



\### 3. Core Features

\* \*\*Instance Connection:\*\* Users can link their Evolution API instance by providing the Server URL, Instance Name, and Global API Key via Telegram.

\* \*\*Smart Regex Extraction:\*\* The bot must extract all valid phone numbers (10 to 15 digits) from any pasted text block.

\* \*\*Batch Processing:\*\* Large lists must be broken into configurable chunks (e.g., 50 numbers per batch).

\* \*\*Status Classification:\*\* \* ✅ \*\*Valid:\*\* Number exists on WhatsApp.

&#x20;   \* ⛔️ \*\*Invalid/Not Found:\*\* Number does not have a WhatsApp account.

&#x20;   \* ⏳ \*\*Error:\*\* API timeout or failure.

\* \*\*Report Generation:\*\* After processing, the bot sends a summary text message and attaches a `.txt` file containing the numbers that failed or are invalid.



\### 4. Anti-Ban \& Safety Mechanisms

\* \*\*Human-like Delays:\*\* Randomized wait times (e.g., 2.5 to 7.2 seconds) between individual number checks.

\* \*\*Batch Cooldowns:\*\* A mandatory 3-to-5 minute pause after processing a batch of 50 numbers.

\* \*\*Concurrency Limits:\*\* Maximum of 2 concurrent workers per user to prevent overwhelming the local Evolution API container or triggering Meta's DDoS protections.



\*\*\*



\## 🤖 AI Agent Prompt

\*Copy everything below this line and paste it into your AI coding tool.\*



\*\*Context:\*\*

Act as an expert Python developer. I need you to build a Telegram Bot that validates WhatsApp numbers using a self-hosted Evolution API. You must write production-ready, clean, and well-documented code.



\*\*Tech Stack:\*\*

\* Python 3.10+

\* `pyTelegramBotAPI` (Telebot)

\* `requests`

\* `sqlite3` (Standard library)

\* `python-dotenv`

\* `concurrent.futures`



\*\*Project Structure:\*\*

Create the following files:

1\. `.env` (Template for BOT\_TOKEN)

2\. `database.py` (SQLite logic)

3\. `evolution\_api.py` (API wrapper for Evolution API)

4\. `main.py` (Telegram bot logic and execution)



\*\*Requirement 1: Database (`database.py`)\*\*

\* Use SQLite to create a `users` table.

\* Columns: `chat\_id` (Primary Key), `api\_url` (Text), `instance\_name` (Text), `api\_key` (Text), `state` (Text), `last\_activity` (Timestamp).

\* Create functions to: `init\_db()`, `get\_user(chat\_id)`, `update\_user\_api(chat\_id, url, instance, key)`, `update\_state(chat\_id, state)`.



\*\*Requirement 2: Evolution API Wrapper (`evolution\_api.py`)\*\*

\* Create a class `EvolutionAPI` initialized with `api\_url`, `instance\_name`, and `api\_key`.

\* Headers must include: `apikey: {api\_key}`.

\* Write a method `check\_connection()` that hits the `/instance/connectionState/{instance\_name}` endpoint to verify the API is online.

\* Write a method `check\_number(phone\_number)` that hits the `/chat/whatsappNumbers/{instance\_name}` endpoint. 

\* The payload for `check\_number` is `{"numbers": \[phone\_number]}`.

\* Parse the response to return a tuple: `(formatted\_text\_result, category)`. Categories should be "valid", "invalid", or "error".



\*\*Requirement 3: Main Bot Logic (`main.py`)\*\*

\* Initialize the Telebot with `BOT\_TOKEN` from `.env`.

\* Implement Inline Keyboards for the Main Menu: "🔗 Connect API" and "📲 Start Checker".

\* State Machine:

&#x20;   \* If user clicks "Connect API", update state to `AWAITING\_CREDENTIALS`. Ask them to send credentials in format: `URL, InstanceName, APIKey`.

&#x20;   \* If user clicks "Start Checker", verify credentials exist in SQLite. If yes, update state to `AWAITING\_NUMBERS` and ask for numbers.

\* When receiving text in `AWAITING\_NUMBERS`:

&#x20;   \* Use Regex `\\d{10,15}` to extract all numbers.

&#x20;   \* Split the extracted numbers into batches of 50.

\* \*\*CRITICAL Anti-Ban Logic (Implement strictly):\*\*

&#x20;   \* Use `ThreadPoolExecutor` with `max\_workers=2`.

&#x20;   \* After every single number check, implement `time.sleep(random.uniform(2.5, 5.5))`.

&#x20;   \* After every batch of 50 is completed, implement a cooldown: `time.sleep(180)` (3 minutes) and notify the user via Telegram that the bot is "resting to prevent bans".

\* After all batches complete, send a final summary message detailing counts of Valid, Invalid, and Errors.

\* Generate a `.txt` file containing all "invalid" and "error" numbers, send it as a document to the user, and then delete the file from the local OS.



\*\*Constraints:\*\*

\* Do not use async telebot; stick to standard synchronous Telebot with standard threading.

\* Handle all `requests` exceptions gracefully with timeouts (e.g., `timeout=10`) so the bot does not crash if the Unraid server is slow.

\* Ensure all database calls are thread-safe (e.g., using `check\_same\_thread=False` for SQLite if shared, or instantiating connections per thread).



Please generate the complete code for `database.py`, `evolution\_api.py`, and `main.py`.


References:
https://maytapi.com/whatsapp-api-pricing
https://maytapi.com/whatsapp-api-documentation
https://maytapi.com/changelog
references: https://github.com/lohithasan07-hub/WHATSAPP_CHECKER/blob/main/main.py