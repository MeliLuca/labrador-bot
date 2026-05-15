import os
import logging
from pathlib import Path
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Carica knowledge base una volta sola all'avvio
KB_DIR = Path(__file__).parent / "docs"
knowledge = "\n\n---\n\n".join(
    f"# FILE: {f.name}\n\n{f.read_text(encoding='utf-8')}"
    for f in sorted(KB_DIR.glob("*.md"))
)
log.info(f"Caricati {len(list(KB_DIR.glob('*.md')))} documenti dalla knowledge base")

SYSTEM_INSTRUCTION = f"""Sei un assistente per padroni di cuccioli di labrador alle prime armi.

REGOLE:
- Rispondi SOLO basandoti sui documenti qui sotto.
- Se la domanda non è coperta, dillo e rimanda al veterinario.
- Non inventare dosaggi, farmaci, diagnosi.
- Per sintomi o emergenze, rimanda sempre al veterinario.
- Cita il file da cui prendi l'info, es. "(fonte: 03-vaccinazioni.md)".
- Tono pratico, chiaro, rassicurante. Max 200 parole.
- Niente tabelle o formattazione complessa: questa è una chat Telegram.
- Rispondi nella stessa lingua della domanda.

=== KNOWLEDGE BASE ===

{knowledge}
"""

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash"

# Storia conversazioni in memoria, per chat_id
conversations: dict[int, list] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conversations[chat_id] = []
    await update.message.reply_text(
        "Ciao! Sono l'assistente per padroni di cuccioli di labrador. "
        "Chiedimi qualsiasi cosa sul tuo cucciolo: alimentazione, "
        "vaccinazioni, addestramento, comportamento. "
        "Per emergenze rivolgiti sempre al veterinario."
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conversations[chat_id] = []
    await update.message.reply_text("Conversazione resettata.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_msg = update.message.text

    history = conversations.setdefault(chat_id, [])
    history.append({"role": "user", "parts": [{"text": user_msg}]})

    # Tieni ultimi 20 turni
    history_trimmed = history[-20:]

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        response = client.models.generate_content(
            model=MODEL,
            contents=history_trimmed,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=500,
                temperature=0.3,
            ),
        )

        reply = response.text
        history.append({"role": "model", "parts": [{"text": reply}]})

        await update.message.reply_text(reply)

    except Exception as e:
        log.exception("Errore Gemini")
        await update.message.reply_text(
            "Mi dispiace, c'è stato un problema. Riprova tra qualche secondo."
        )

def main():
    app = Application.builder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Bot avviato")
    app.run_polling()

if __name__ == "__main__":
    main()