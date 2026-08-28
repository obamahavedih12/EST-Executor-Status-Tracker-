# Executor Status Bot

Discord bot pulling live executor data from weao.xyz.

---

## Local Setup

```bash
pip install -r requirements.txt
export BOT_TOKEN=your_token_here   # Windows: set BOT_TOKEN=your_token_here
python main.py
```

---

## Railway (24/7 Hosting) — Free

1. Go to https://railway.app and sign up
2. Click **New Project → Deploy from GitHub repo**
   - Push this folder to a GitHub repo first, or use **Deploy from local** via Railway CLI
3. Once deployed, go to your project → **Variables** tab
4. Add variable:
   - Key:   `BOT_TOKEN`
   - Value: `your_regenerated_token`
5. Railway auto-detects `Procfile` and runs `python main.py`
6. Bot stays online 24/7 — no sleep timers on worker dynos

### Railway CLI (faster)
```bash
npm install -g @railway/cli
railway login
railway init
railway up
railway variables set BOT_TOKEN=your_token
```

---

## Commands

| Command | Alias | Description |
|---|---|---|
| `!status` | `!s` | Full executor status board |
| `!check [name]` | `!c` | Single executor detail |
| `!updated` | `!u` | Updated executors only |
| `!updating` | — | Updating executors only |
| `!setrefresh #channel` | — | Auto-refresh channel (admin) |
| `!commands` | `!h` | Command list |

---

## Token Security

**Never paste your token in chat, code files, or anywhere public.**
Token is read exclusively from the `BOT_TOKEN` environment variable.
If exposed: discord.com/developers/applications → Bot → Reset Token
