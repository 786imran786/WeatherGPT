# WeatherGPT

An AI-powered conversational weather forecasting platform.

## Project Structure

```
weathergpt/
├── frontend/           # Vanilla HTML/CSS/JS dashboard
│   ├── index.html
│   ├── styles.css
│   ├── app.js          # UI logic and rendering
│   └── api.js          # API layer (talks to backend)
└── backend/            # Python FastAPI backend
    ├── app/
    │   ├── main.py             # FastAPI app + compat routes
    │   ├── core/
    │   │   ├── config.py       # Settings (env vars)
    │   │   └── logging.py      # Logging setup
    │   ├── api/v1/
    │   │   ├── router.py       # V1 API router
    │   │   └── endpoints/
    │   │       ├── health.py
    │   │       ├── locations.py
    │   │       ├── weather.py
    │   │       └── chat.py
    │   ├── schemas/            # Pydantic models
    │   │   ├── location.py
    │   │   ├── weather.py
    │   │   └── chat.py
    │   ├── services/           # Business logic
    │   │   ├── weather_service.py
    │   │   ├── location_service.py
    │   │   └── chat_service.py
    │   ├── integrations/weather/
    │   │   ├── base.py         # Provider interface
    │   │   └── open_meteo.py   # Open-Meteo adapter
    │   └── tests/
    │       └── test_api.py
    ├── requirements.txt
    ├── .env.example
    └── pytest.ini
```

## Quick Start

### 1. Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy and edit environment config
copy .env.example .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**.  
Interactive docs: **http://localhost:8000/docs**

### 2. Frontend

Open `frontend/index.html` in a browser, or serve it with any static file server:

```bash
# Using Python's built-in server (from project root)
cd frontend
python -m http.server 5500
```

Then open **http://localhost:5500** — the dashboard will fetch real weather data from the backend.

## API Endpoints

### Frontend-Compatible Routes (used by `api.js`)

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/weather` | `city` | Current weather by city name |
| GET | `/api/forecast` | `city` | Hourly + daily forecast by city |
| GET | `/api/alerts` | `region` | Weather alerts (stub) |
| GET | `/api/locations` | — | Popular locations with current temps |
| POST | `/api/chat` | `{message, city, language}` | Chat with weather context |

### V1 API Routes

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/v1/health` | — | Health check |
| GET | `/api/v1/locations/search` | `q` | Geocoding search |
| GET | `/api/v1/weather/current` | `latitude`, `longitude` | Current weather by coords |
| GET | `/api/v1/weather/forecast` | `latitude`, `longitude` | Forecast by coords |
| POST | `/api/v1/chat` | `{message, city, language}` | Chat |

### Example Requests

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Search locations
curl "http://localhost:8000/api/v1/locations/search?q=Phagwara"

# Current weather by coordinates
curl "http://localhost:8000/api/v1/weather/current?latitude=31.22&longitude=75.77"

# Forecast by coordinates
curl "http://localhost:8000/api/v1/weather/forecast?latitude=31.22&longitude=75.77"

# Current weather by city (frontend compat)
curl "http://localhost:8000/api/weather?city=Phagwara"

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather today?", "city": "Phagwara", "language": "en"}'
```

## Running Tests

```bash
cd backend
pytest app/tests/ -v
```

## Weather Data Provider

Uses [Open-Meteo](https://open-meteo.com/) — a free, open-source weather API.  
No API key required. Subject to their usage terms.

## Architecture Decisions

- **Provider adapter pattern**: Weather logic is isolated behind `WeatherProviderBase`. Swapping to another provider requires implementing a single class.
- **Frontend compatibility**: The backend exposes both proper v1 REST endpoints *and* the exact routes the existing `api.js` expects, so the dashboard works without any frontend changes.
- **No fabricated data**: All weather data comes from Open-Meteo. The chat service uses real API calls, never invented conditions.
- **Modular structure**: Routes → Services → Integrations. Each layer has a single responsibility.

## Future Roadmap

- [ ] LLM integration (OpenAI / Gemini) for natural-language weather queries
- [ ] PostgreSQL + SQLAlchemy for saved locations and chat history
- [ ] Redis caching layer
- [ ] Real weather alerts integration
- [ ] Historical weather data
- [ ] Docker containerisation
- [ ] Voice input support
