from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_overview import router as overview_router
from api.routes_lifecycle import router as lifecycle_router

app = FastAPI(title="IP Optimization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview_router, prefix="/overview", tags=["Overview"])
app.include_router(lifecycle_router, prefix="/lifecycle", tags=["Lifecycle"])

@app.get("/")
def root():
    return {"message": "IP Optimization API is running"}