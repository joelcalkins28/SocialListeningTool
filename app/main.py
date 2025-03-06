from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

from app.data.collector import SocialMediaDataCollector
from app.data.processor import SocialMediaDataProcessor
from app.services.sheets_service import GoogleSheetsService
from app.services.gemini_service import GeminiService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Social Listening Tool")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize services
data_collector = SocialMediaDataCollector()
data_processor = SocialMediaDataProcessor()
sheets_service = GoogleSheetsService()
gemini_service = GeminiService()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Renders the main dashboard page.
    """
    logger.debug("Handling request to /")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Social Listening Tool",
            "message": "Welcome to the Social Listening Tool"
        }
    )

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

@app.get("/api/search/{brand_name}")
async def search_brand(brand_name: str):
    """
    Search for a brand and return social media data and insights.
    
    Args:
        brand_name (str): Name of the brand to search for
        
    Returns:
        JSONResponse: Social media data and insights
    """
    try:
        logger.info(f"Processing search request for brand: {brand_name}")
        
        # Collect data
        data = data_collector.collect_data(brand_name)
        if not data:
            raise HTTPException(status_code=404, detail="No data found for the specified brand")
        
        # Process data
        results = data_processor.process_data(data)
        
        # Generate AI insights
        try:
            ai_insights = gemini_service.generate_insights(brand_name, data, results["metrics"])
            if not ai_insights:
                logger.warning("No AI insights generated")
                ai_insights = ["No AI insights available at this time."]
            results["insights"] = ai_insights
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            results["insights"] = ["Unable to generate AI insights at this time."]
        
        # Update Google Sheets
        try:
            sheets_service.update_data_sheet(brand_name, data)
            sheets_service.update_metrics_sheet(brand_name, results)
            sheets_service.create_dashboard_sheet(brand_name)
        except Exception as e:
            logger.error(f"Error updating Google Sheets: {str(e)}")
            # Don't raise the exception, just log it
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error processing brand search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.debug("Starting the application")
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8080)),
        reload=os.getenv("DEBUG", "True").lower() == "true",
        log_level="debug",
    ) 