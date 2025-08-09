from fastapi import FastAPI
from src.routes import router
from app.flow import check_authenticity

app = FastAPI()
app.include_router(router, prefix="/api")
@app.post("/api/checkAuthenticity")
async def check_authenticity_endpoint(request_data: dict):
    url = request_data.get("url")
    log = request_data.get("log", False)
    return check_authenticity(url, log)
