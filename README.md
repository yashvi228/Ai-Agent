# Chatbot (Flask + DeepSeek)

## Quickstart

1. Create `.env` in project root:

```
SECRET_KEY=change-me
CORS_ORIGINS=http://localhost:5000
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
MAX_HISTORY=20
REQUEST_TIMEOUT_SEC=60
```

2. Install and run (local):

```
python3 -m venv myvenv && source myvenv/bin/activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000

## Docker

```
docker build -t chatbot .
docker run -p 5000:5000 --env-file .env chatbot
```

## Notes
- Streaming responses implemented via chunked JSON containing `chunks: [{ delta: "..." }]`.
- Conversation memory stored in Flask session (trimmed to `MAX_HISTORY`).
- Rate limiting: 60/min, 600/hour per IP.
- Markdown rendered client-side with `marked`.
- For production, place behind a reverse proxy (Nginx) and use HTTPS.

