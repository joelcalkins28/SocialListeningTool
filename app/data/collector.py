import json
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class SocialMediaDataCollector:
    def __init__(self):
        self.platforms = ["Instagram", "Facebook", "X"]
        self.sentiment_options = ["positive", "negative", "neutral"]
        
    def generate_simulated_data(self, brand_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Generate simulated social media data for a given brand.
        
        Args:
            brand_name (str): Name of the brand to generate data for
            days (int): Number of days of data to generate
            
        Returns:
            List[Dict[str, Any]]: List of social media posts with engagement metrics
        """
        logger.debug(f"Generating simulated data for brand: {brand_name}")
        
        data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            # Generate 1-5 posts per day
            posts_per_day = random.randint(1, 5)
            
            for _ in range(posts_per_day):
                post = {
                    "platform": random.choice(self.platforms),
                    "date": current_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "content": f"Sample post about {brand_name}",
                    "engagement": {
                        "likes": random.randint(100, 10000),
                        "comments": random.randint(10, 500),
                        "shares": random.randint(5, 200)
                    },
                    "sentiment": random.choice(self.sentiment_options),
                    "url": f"https://example.com/{brand_name.lower().replace(' ', '-')}/{random.randint(1000, 9999)}"
                }
                data.append(post)
            
            current_date += timedelta(days=1)
        
        return data
    
    def save_data_to_json(self, data: List[Dict[str, Any]], filename: str) -> None:
        """
        Save the collected data to a JSON file.
        
        Args:
            data (List[Dict[str, Any]]): The data to save
            filename (str): Name of the file to save to
        """
        try:
            # Ensure the data directory exists
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            filepath = data_dir / filename
            logger.debug(f"Saving data to {filepath}")
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            
            logger.info(f"Successfully saved data to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving data to file: {str(e)}")
            # Don't raise the exception, just log it
    
    def collect_data(self, brand_name: str) -> List[Dict[str, Any]]:
        """
        Main method to collect data for a brand.
        Currently uses simulated data, but will be extended to use real APIs.
        
        Args:
            brand_name (str): Name of the brand to collect data for
            
        Returns:
            List[Dict[str, Any]]: Collected social media data
        """
        logger.info(f"Starting data collection for brand: {brand_name}")
        
        try:
            # Generate simulated data
            data = self.generate_simulated_data(brand_name)
            
            # Save to JSON file
            filename = f"{brand_name.lower().replace(' ', '_')}_data.json"
            self.save_data_to_json(data, filename)
            
            logger.info(f"Completed data collection for {brand_name}")
            return data
            
        except Exception as e:
            logger.error(f"Error collecting data: {str(e)}")
            return []  # Return empty list instead of raising 