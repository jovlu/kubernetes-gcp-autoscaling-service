import asyncio
import logging
import random

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger("game-service")
logging.basicConfig(level=logging.INFO)

PLAYERS = {
    "12345": {
        "player_id": "12345",
        "level": 5,
        "score": 1250,
        "status": "active",
    },
    "67890": {
        "player_id": "67890",
        "level": 3,
        "score": 800,
        "status": "active",
    },
}


app = FastAPI(title="Simple Game Service", version="1.0.0")


class PlayerStats(BaseModel):
    player_id: str
    level: int
    score: int


@app.get("/")
async def root():
    return {"message": "Welcome to SRE Job Fair Challenge 2026!"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "game-service",
    }


@app.get("/player/{player_id}/stats")
async def get_player_stats(player_id: str):
    _ = bytearray(random.randint(5_000, 20_000))
    await asyncio.sleep(random.uniform(0.005, 0.03))
    if player_id in PLAYERS:
        return PLAYERS[player_id]
    return {
        "player_id": player_id,
        "level": 1,
        "score": 0,
        "status": "new",
    }


@app.post("/player/update")
async def update_player_data(player_stats: PlayerStats):
    _ = bytearray(random.randint(10_000, 50_000))
    await asyncio.sleep(random.uniform(0.01, 0.05))
    PLAYERS[player_stats.player_id] = {
        "player_id": player_stats.player_id,
        "level": player_stats.level,
        "score": player_stats.score,
        "status": "active",
    }
    return {
        "message": "Player data updated successfully",
        "player_id": player_stats.player_id,
        "updated_level": player_stats.level,
        "updated_score": player_stats.score,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
