# Career API

FastAPI service for managing career paths and guidance.

## Running the service

```bash
pip install -r requirements.txt
cd app
python main.py
```

The service will be available at http://localhost:8001

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /career-paths` - Get all career paths
- `GET /career-paths/{path_id}` - Get specific career path
- `POST /career-paths/{path_id}/recommend` - Get personalized recommendations