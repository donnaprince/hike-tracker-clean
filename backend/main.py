from fastapi import FastAPI
from backend.routes.my_hikes import router as my_hikes_router
from backend.routes.trails import router as trails_router
from backend.routes.parks import router as parks_router

app = FastAPI(title="Hike Tracker API")

app.include_router(my_hikes_router)
app.include_router(trails_router)
app.include_router(parks_router)
