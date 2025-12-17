# SE RASNA Mirror Backend

FastAPI backend for sales call evaluation SaaS MVP.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Calls

- `POST /api/v1/calls/` - Upload call audio with context
- `GET /api/v1/calls/` - List all calls
- `GET /api/v1/calls/{call_id}` - Get call details
- `POST /api/v1/calls/{call_id}/transcribe` - Trigger transcription
- `POST /api/v1/calls/{call_id}/evaluate` - Trigger RASNA evaluation
- `DELETE /api/v1/calls/{call_id}` - Delete call

## Architecture

```
backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── core/         # Config and database
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── repositories/ # Data access layer
└── storage/          # Local file storage
```

## TODO

- [ ] Implement transcription service (Whisper/AssemblyAI)
- [ ] Implement RASNA evaluation logic
- [ ] Add background job processing (Celery/RQ)
- [ ] Add authentication
- [ ] Add file streaming for large audio files
- [ ] Add audio format validation
- [ ] Add comprehensive error handling
- [ ] Add logging
- [ ] Add tests
- [ ] Configure for production deployment
