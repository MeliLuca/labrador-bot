# Labrador Puppy Assistant Bot

Telegram bot that answers the most common questions from new Labrador puppy owners. The knowledge base is a curated collection of markdown documents. The model is Gemini 2.5 Flash via Google AI Studio (free tier). Deployment runs on Railway.

## Architecture

```
Telegram User
     ↓
Telegram Bot API
     ↓ (long polling)
Python backend on Railway
     ↓ (system instruction + knowledge base + conversation history)
Google Gemini API (gemini-2.5-flash)
     ↓
Response → Telegram → User
```

The knowledge base (folder `docs/`) is loaded into memory at bot startup and injected as `system_instruction` into every Gemini call.

## Prerequisites

- Telegram account
- Google account (for Google AI Studio)
- GitHub account
- Railway account (you can log in with GitHub)
- Python 3.12+ locally (only if you want to test before deploying)

## Project structure

```
labrador-bot/
├── bot.py              # bot entry point
├── docs/               # knowledge base (markdown)
│   ├── 01-first-days.md
│   ├── 02-feeding.md
│   ├── 03-vaccinations.md
│   └── ... (10-15 files)
├── requirements.txt    # Python dependencies
├── Procfile            # Railway start command
├── runtime.txt         # Python version
├── .gitignore
└── README.md           # this file
```

## Step-by-step setup

### 1. Create the Telegram bot

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Choose a display name (e.g. `Labrador Puppy Assistant`)
4. Choose a username ending in `bot` (e.g. `labrador_puppy_bot`)
5. BotFather returns a token like `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`
6. Save it, you will need it as an environment variable

Optional but recommended: configure the bot through BotFather with:
- `/setdescription` for the description shown before `/start`
- `/setabouttext` for the "About" section
- `/setcommands` to register commands:
  ```
  start - Start the bot
  reset - Reset the conversation
  ```

### 2. Get the Gemini API key

1. Go to `https://aistudio.google.com`
2. Log in with your Google account
3. Click "Get API key" in the top right
4. "Create API key" on a new or existing project
5. Copy the key (format `AIza...`)
6. No credit card required for the free tier

Free tier limits for Gemini 2.5 Flash: 1500 requests/day. Plenty for a demo with 1 to 5 users.

### 3. Prepare the repository

1. Create a new private repo on GitHub (e.g. `labrador-bot`)
2. Clone it locally:
   ```bash
   git clone https://github.com/<your-user>/labrador-bot.git
   cd labrador-bot
   ```
3. Copy all project files inside (`bot.py`, `requirements.txt`, `Procfile`, etc.)
4. Create the `docs/` folder and put the knowledge base markdown files inside
5. Create the `.gitignore` file:
   ```
   __pycache__/
   *.pyc
   .env
   .venv/
   venv/
   .DS_Store
   ```
6. Commit and push:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

### 4. Local test (optional)

If you want to try the bot on your machine before deploying:

```bash
python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

pip install -r requirements.txt

export TELEGRAM_TOKEN="123456:ABC..."
export GEMINI_API_KEY="AIza..."

python bot.py
```

Open Telegram, search for your bot by username, send `/start`. If it replies, you are good.

### 5. Deploy to Railway

1. Go to `https://railway.app` and log in with GitHub
2. "New Project" → "Deploy from GitHub repo"
3. Authorize Railway to access your repos, select `labrador-bot`
4. Railway auto-detects Python and starts the build
5. Once the service is running, go to the "Variables" tab and add:
   - `TELEGRAM_TOKEN` = BotFather token
   - `GEMINI_API_KEY` = Google AI Studio key
6. Railway redeploys automatically with the new variables
7. Check the "Deployments" tab → "View logs" to confirm you see `Bot started` and no errors

The bot now runs 24/7. To stop it, pause the service or delete the project.

## Environment variables

| Name | Description | Example |
|------|-------------|---------|
| `TELEGRAM_TOKEN` | Bot token from BotFather | `123456789:ABC...` |
| `GEMINI_API_KEY` | API key from Google AI Studio | `AIza...` |

Never commit them to the repository. Always pass them as environment variables.

## Updating the knowledge base

To add, edit, or remove documents from the knowledge base:

1. Edit files in `docs/` locally
2. Verify they are properly formatted (YAML front matter, headings, etc.)
3. Commit and push:
   ```bash
   git add docs/
   git commit -m "Update vaccinations section"
   git push
   ```
4. Railway detects the push and redeploys the bot automatically
5. All new conversations will use the updated knowledge

Note: the knowledge base is loaded into memory at bot startup. Conversations already in progress will keep using the old knowledge until `/reset` is called or the bot restarts.

## Troubleshooting

### The bot does not respond

1. Check Railway logs ("Deployments" tab → "View logs")
2. Telegram auth error: `TELEGRAM_TOKEN` is wrong or expired
3. Gemini API error: `GEMINI_API_KEY` is invalid or you exceeded the free tier
4. Knowledge base loading error: verify the `docs/` folder exists and contains valid `.md` files

### The bot responds but answers are inconsistent

1. Check that the system instruction in `bot.py` reflects the desired behavior
2. Verify the knowledge base `.md` files are well structured (headings, sections)
3. Lower `temperature` from 0.3 to 0.1 for more deterministic answers
4. If Gemini ignores instructions, add emphasis: repeat the rules at the beginning and end of the system instruction

### "Context length exceeded" error

The knowledge base plus conversation history exceed the context window. Solutions in order of ease:

1. Reduce the history kept in memory (change `history[-20:]` to `history[-10:]`)
2. Shorten the most verbose `.md` files
3. Move to a RAG system (retrieve only relevant chunks instead of the full KB)

### The bot loses conversation history

Expected. History is in memory, not persistent. If Railway restarts the service (deploy, crash, maintenance) it is lost. For real production, replace the `conversations` dict with Redis or a database.

## Estimated costs

| Item | Demo (1-5 users) | Production (100 users/day) |
|------|------------------|----------------------------|
| Gemini API | €0 (free tier) | €5-15/month |
| Railway | €0 (Hobby plan, $5 free credit) | €5/month (Pro plan) |
| Telegram | €0 (always free) | €0 |
| **Total** | **€0** | **€10-20/month** |

For a demo to a single client the spend is effectively zero. The jump to production stays cheap.

## Future improvements

Ideas if the demo goes well and you want to move to production:

- **Conversation persistence**: Redis or Postgres instead of in-memory dict
- **Question logging**: save questions/answers to a DB to analyze what users ask and improve the KB
- **Analytics**: track number of users, most common questions, "I don't know" rate
- **Real RAG**: if the KB grows beyond 50 documents, move to chunks + vector DB instead of stuffing
- **Tool calling**: add tools like "find nearby vet" or "calculate food dose by weight"
- **Multilingual**: automatic language detection and translated KB
- **Switch to Claude Haiku 4.5**: if Gemini quality is not enough, move to Anthropic API (slightly higher costs but better citations and instruction following)
- **Webhooks instead of polling**: more efficient for high traffic

## Tech stack

- **Language**: Python 3.12
- **LLM model**: Google Gemini 2.5 Flash
- **Gemini SDK**: `google-genai`
- **Bot framework**: `python-telegram-bot` v21+
- **Hosting**: Railway
- **Source control**: GitHub

## License

Private project for internal use. Do not distribute without authorization.
