from fastapi import FastAPI
from crop_monitoring import CropMonitoringSystem

app = FastAPI()
cms = CropMonitoringSystem()

@app.get("/")
def read_root():
    return {"message": "Crop Monitoring API is running."}
