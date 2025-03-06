from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import logging
from textblob import TextBlob
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

class SocialMediaDataProcessor:
    def __init__(self):
        self.metrics = {
            "total_posts": 0,
            "total_engagement": 0,
            "platform_stats": {},
            "sentiment_stats": {},
            "daily_engagement": {},
            "raw_data": []
        }
        self.gemini_service = GeminiService()
    
    def process_data(self, data):
        """Process the collected social media data and generate metrics."""
        if not data:
            logger.warning("No data provided for processing")
            return {
                "metrics": {
                    "total_posts": 0,
                    "total_engagement": 0,
                    "platform_stats": {},
                    "sentiment_stats": {},
                    "daily_engagement": {},
                    "raw_data": []
                },
                "insights": ["No data available for analysis."]
            }

        # Store raw data for reference
        self.metrics["raw_data"] = data

        # Convert data to DataFrame for easier processing
        df = pd.DataFrame(data)

        # Calculate total posts
        self.metrics["total_posts"] = len(df)

        # Calculate total engagement
        total_engagement = 0
        for _, row in df.iterrows():
            engagement = row["engagement"]
            total_engagement += engagement["likes"] + engagement["comments"] + engagement["shares"]
        self.metrics["total_engagement"] = total_engagement

        # Calculate platform statistics
        platform_stats = {}
        for platform in df["platform"].unique():
            platform_df = df[df["platform"] == platform]
            platform_engagement = 0
            for _, row in platform_df.iterrows():
                engagement = row["engagement"]
                platform_engagement += engagement["likes"] + engagement["comments"] + engagement["shares"]
            
            platform_stats[platform] = {
                "total_engagement": platform_engagement,
                "posts": len(platform_df),
                "avg_engagement": platform_engagement / len(platform_df) if len(platform_df) > 0 else 0
            }
        self.metrics["platform_stats"] = platform_stats

        # Calculate sentiment statistics
        sentiment_stats = {}
        for sentiment in df["sentiment"].unique():
            sentiment_df = df[df["sentiment"] == sentiment]
            sentiment_stats[sentiment] = {
                "count": len(sentiment_df),
                "percentage": (len(sentiment_df) / len(df)) * 100
            }
        self.metrics["sentiment_stats"] = sentiment_stats

        # Calculate daily engagement
        daily_engagement = {}
        for _, row in df.iterrows():
            date = row["date"].split()[0]  # Get just the date part
            engagement = row["engagement"]
            total = engagement["likes"] + engagement["comments"] + engagement["shares"]
            
            if date in daily_engagement:
                daily_engagement[date] += total
            else:
                daily_engagement[date] = total
        
        # Sort daily engagement by date
        self.metrics["daily_engagement"] = dict(sorted(daily_engagement.items()))

        # Generate insights using Gemini
        insights = self.gemini_service.generate_insights("Yankee Candle", data, self.metrics)

        # Convert all metrics to native Python types
        self.metrics["total_posts"] = int(self.metrics["total_posts"])
        self.metrics["total_engagement"] = int(self.metrics["total_engagement"])
        
        for platform, stats in self.metrics["platform_stats"].items():
            stats["total_engagement"] = int(stats["total_engagement"])
            stats["posts"] = int(stats["posts"])
            stats["avg_engagement"] = float(stats["avg_engagement"])
        
        for sentiment, stats in self.metrics["sentiment_stats"].items():
            stats["count"] = int(stats["count"])
            stats["percentage"] = float(stats["percentage"])

        return {
            "metrics": self.metrics,
            "insights": insights
        }
    
    def _generate_insights(self, df: pd.DataFrame) -> List[str]:
        """
        Generate insights from the processed data.
        
        Args:
            df (pd.DataFrame): Processed data
            
        Returns:
            List[str]: List of insights
        """
        insights = []
        
        # Platform performance
        if self.metrics["platform_stats"]:
            best_platform = max(self.metrics["platform_stats"].items(), key=lambda x: x[1]["total_engagement"])[0]
            insights.append(f"Best performing platform: {best_platform}")
        
        # Sentiment analysis
        if self.metrics["sentiment_stats"]:
            sentiment_distribution = self.metrics["sentiment_stats"]
            insights.append(f"Sentiment distribution: {sentiment_distribution}")
        
        # Engagement trends
        if len(self.metrics["daily_engagement"]) > 1:
            recent_days = list(self.metrics["daily_engagement"].items())[-2:]
            if recent_days[1][1] > recent_days[0][1]:
                insights.append("Engagement is trending upward")
            else:
                insights.append("Engagement is trending downward")
        
        return insights 