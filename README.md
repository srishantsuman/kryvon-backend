# KRYVON — Trading Journal

Professional trading journal with FastAPI backend, React frontend, PostgreSQL database, JWT auth, Google OAuth, and OTP password reset.

---

## 🚀 Run with Docker (recommended — one command)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Steps

```bash
# 1. Clone / enter the project
cd kryvon

# 2. Start everything
docker compose up --build

# That's it. Open:
#   Frontend  →  http://localhost:5173
#   API docs  →  http://localhost:8000/docs
#   pgAdmin   →  http://localhost:5050  (run with --profile tools)
```

> First build takes ~2 min. Subsequent starts take ~10 seconds.

---

## 🔧 Run without Docker (local dev)

### Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL locally, then copy and edit the env file
cp .env.example .env
# Edit .env — set DATABASE_URL to your local Postgres

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API runs at **http://localhost:8000**
Interactive docs at **http://localhost:8000/docs**

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy and edit env
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000/api/v1

# Start dev server
npm run dev
```

Frontend runs at **http://localhost:5173**

---

## ⚙️ Configuration

### Required for full functionality

| Feature | What to set |
|---|---|
| Core auth | `SECRET_KEY` — generate with `openssl rand -hex 32` |
| Google OAuth | `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` from [Google Cloud Console](https://console.cloud.google.com) |
| Password reset email | `SMTP_USER` + `SMTP_PASSWORD` (use Gmail App Password) |

### Google OAuth setup (5 min)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID (Web application)
4. Add authorized redirect URI: `http://localhost:5173/auth/callback`
5. Copy Client ID and Secret into `backend/.env` and `frontend/.env`

### Gmail App Password (for OTP email)

1. Enable 2FA on your Google account
2. Go to myaccount.google.com → Security → App passwords
3. Generate a password for "Mail"
4. Set `SMTP_USER=your@gmail.com` and `SMTP_PASSWORD=the-16-char-app-password`

---

## 📁 Project structure

```
kryvon/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app entry point
│   │   ├── api/v1/endpoints/    ← auth, trades, dashboard, analytics
│   │   ├── core/                ← config, JWT/bcrypt security
│   │   ├── db/                  ← SQLAlchemy session
│   │   ├── models/              ← User, Trade ORM models
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   ├── services/            ← business logic (auth, trades, analytics)
│   │   └── utils/               ← email, JWT dependency
│   ├── alembic/                 ← database migrations
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── api/                 ← client.ts, auth.ts, trades.ts, analytics.ts
    │   ├── app/
    │   │   ├── context/         ← AuthContext, TradeContext (real API)
    │   │   ├── pages/           ← Dashboard, Journal, Analytics, CalendarView
    │   │   ├── components/      ← AddTradeModal, DayDetailModal, ui/
    │   │   ├── layouts/         ← DashboardLayout
    │   │   └── routes.tsx
    │   └── styles/
    ├── package.json
    └── Dockerfile
```

---

## 🔌 API reference

All endpoints are prefixed with `/api/v1`. Protected endpoints require `Authorization: Bearer <token>`.

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register with email + password |
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/refresh` | Get new access token via cookie |
| POST | `/auth/logout` | Clear refresh token cookie |
| GET | `/auth/me` | Current user info |
| POST | `/auth/forgot-password` | Send OTP to email |
| POST | `/auth/reset-password` | Verify OTP + set new password |
| POST | `/auth/google` | Exchange Google OAuth code for JWT |

### Trades

| Method | Endpoint | Description |
|---|---|---|
| GET | `/trades?page=1&symbol=AAPL&tag=FOMO` | List trades (paginated, filterable) |
| POST | `/trades` | Create trade |
| PATCH | `/trades/{id}` | Update trade |
| DELETE | `/trades/{id}` | Delete trade |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard` | Stats + daily PnL chart data |
| GET | `/calendar?year=2026&month=3` | Monthly calendar data + streaks |
| GET | `/analytics` | Full analytics: tags, symbols, hourly, distribution |

---

## 🗄️ Database migrations

```bash
cd backend

# After changing a model, create a migration
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## 🚢 Deploy to production

### Render / Railway / Fly.io (easiest)

1. Push to GitHub
2. Connect repo to [Render](https://render.com) or [Railway](https://railway.app)
3. Set environment variables in their dashboard
4. They auto-detect Dockerfile and deploy

### VPS (DigitalOcean / Hetzner)

```bash
# On your server
git clone your-repo && cd kryvon

# Edit docker-compose.yml — change ENVIRONMENT=production, set real SECRET_KEY
# Then:
docker compose up -d --build

# Optional: put Nginx in front for SSL (Let's Encrypt)
```

### Production checklist
- [ ] Set `SECRET_KEY` to a strong random value (`openssl rand -hex 32`)
- [ ] Set `ENVIRONMENT=production` (disables /docs endpoint)
- [ ] Use real SMTP credentials (not test values)
- [ ] Set `FRONTEND_URL` to your actual domain
- [ ] Enable HTTPS (via Nginx + Certbot or your host's SSL)

---

## 📝 Example API request/response

### Create a trade

```bash
curl -X POST http://localhost:8000/api/v1/trades \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-04-01",
    "symbol": "AAPL",
    "entry_price": 175.50,
    "exit_price": 180.00,
    "quantity": 10,
    "trade_type": "buy",
    "notes": "Breakout above resistance",
    "tags": ["FOMO"]
  }'
```

Response:
```json
{
  "id": 1,
  "date": "2026-04-01",
  "symbol": "AAPL",
  "entry_price": "175.5000",
  "exit_price": "180.0000",
  "quantity": "10.0000",
  "trade_type": "buy",
  "pnl": "45.0000",
  "notes": "Breakout above resistance",
  "tags": ["fomo"],
  "created_at": "2026-04-01T10:30:00Z"
}
```

> Notice: PnL is **calculated server-side** — the client never sends it.
