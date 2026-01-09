from fastapi import FastAPI

from routes.my_hikes import router as my_hikes_router
from routes.trails import router as trails_router
from routes.parks import router as parks_router

app = FastAPI(title="Hike Tracker API")

# 👇 ADD THIS ROOT ROUTE
@app.get("/")
def root():
    return {"status": "Hike Tracker API is running"}

app.include_router(my_hikes_router)
app.include_router(trails_router)
app.include_router(parks_router)
