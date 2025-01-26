from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import uvicorn
from typing import Dict, Any
from analysis import analyze_and_forecast, inventory_analysis  # Fix import path

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for results
latest_results = {
    "forecast": None,
    "status": None,
    "recommendations": None
}

@app.post("/run-analysis")
async def run_analysis():
    try:
        # Run full analysis pipeline
        forecast_df = analyze_and_forecast()
        status_df, recommendations_df = inventory_analysis(forecast_df)
        
        # Store results in memory
        latest_results.update({
            "forecast": forecast_df.to_dict(orient="records"),
            "status": status_df.to_dict(orient="records"),
            "recommendations": recommendations_df.to_dict(orient="records")
        })
        
        return {"message": "Analysis completed successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast")
async def get_forecast():
    if not latest_results["forecast"]:
        raise HTTPException(status_code=404, detail="No forecast data available")
    return latest_results["forecast"]

@app.get("/inventory-status")
async def get_inventory_status():
    if not latest_results["status"]:
        raise HTTPException(status_code=404, detail="No status data available")
    return latest_results["status"]

@app.get("/recommendations")
async def get_recommendations():
    if not latest_results["recommendations"]:
        raise HTTPException(status_code=404, detail="No recommendations available")
    return latest_results["recommendations"]

@app.get("/item-details/{item_id}")
async def get_item_details(item_id: str):
    try:
        return {
            "forecast": [x for x in latest_results["forecast"] if x["item_id"] == item_id],
            "status": [x for x in latest_results["status"] if x["item_id"] == item_id],
            "recommendations": [x for x in latest_results["recommendations"] if x["item_id"] == item_id]
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)