import os
import stripe
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

from app.settings.database import database
from app.settings.environment import settings
from app.settings.routers import routers

env_path = os.path.join(".", ".env")
load_dotenv(dotenv_path=env_path)

app = FastAPI()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
  
@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


prefix = "/api"
[app.include_router(router, prefix=prefix) for router in routers]

if __name__ == "__main__":
    port = settings.get("app").get("port")
    uvicorn.run(app, host="0.0.0.0", port=port)