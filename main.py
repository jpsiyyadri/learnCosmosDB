import uvicorn
from fastapi import FastAPI

from plants_routes import lifespan, plants_router

app = FastAPI(lifespan=lifespan)

app.include_router(plants_router, prefix="/plants", tags=["plants"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
