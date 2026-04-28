# Simple FastAPI Game Service

A basic FastAPI web server with health check, GET, and POST endpoints using in-memory data.


## Endpoints

- **GET** `/health` - Service health status
- **GET** `/player/{player_id}/stats` - Get player statistics
- **POST** `/player/update` - Update player data

## Example Usage

```bash
curl http://localhost:8000/health
curl http://localhost:8000/player/12345/stats
curl -X POST http://localhost:8000/player/update \
  -H "Content-Type: application/json" \
  -d '{"player_id": "12345", "level": 10, "score": 2500}'
```
