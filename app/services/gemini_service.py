import os
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_insights(self, brand_name: str, data: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[str]:
        """
        Generate AI-powered insights using the Gemini API.
        
        Args:
            brand_name (str): Name of the brand
            data (List[Dict[str, Any]]): Raw social media data
            metrics (Dict[str, Any]): Processed metrics
            
        Returns:
            List[str]: List of AI-generated insights
        """
        try:
            # Prepare the prompt
            prompt = self._create_analysis_prompt(brand_name, data, metrics)
            
            # Generate response with safety settings
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            response = self.model.generate_content(
                contents=prompt,
                safety_settings=safety_settings,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            # Parse and format insights
            insights = self._parse_insights(response.text)
            
            logger.info(f"Generated AI insights for {brand_name}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            raise  # Re-raise to trigger retry
    
    def _create_analysis_prompt(self, brand_name: str, data: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        """
        Create a prompt for the Gemini API.
        
        Args:
            brand_name (str): Name of the brand
            data (List[Dict[str, Any]]): Raw social media data
            metrics (Dict[str, Any]): Processed metrics
            
        Returns:
            str: Formatted prompt
        """
        # Extract key metrics
        total_posts = metrics["total_posts"]
        total_engagement = metrics["total_engagement"]
        platform_stats = metrics["platform_stats"]
        sentiment_stats = metrics["sentiment_stats"]
        
        # Create platform summary
        platform_summary = []
        for platform, stats in platform_stats.items():
            platform_summary.append(f"- {platform}: {stats['posts']} posts, {stats['total_engagement']:,} total engagement")
        platform_summary_text = "\n".join(platform_summary)
        
        # Create sentiment summary
        sentiment_summary = []
        for sentiment, stats in sentiment_stats.items():
            sentiment_summary.append(f"- {sentiment}: {stats['count']} posts ({stats['percentage']:.1f}%)")
        sentiment_summary_text = "\n".join(sentiment_summary)
        
        # Calculate engagement rate
        engagement_rate = (total_engagement / total_posts) if total_posts > 0 else 0
        
        prompt = f"""As a social media analytics expert, analyze the following data for {brand_name} and provide actionable insights.

Key Performance Indicators:
- Total Posts: {total_posts:,}
- Total Engagement: {total_engagement:,}
- Average Engagement Rate: {engagement_rate:.2f} per post

Platform Performance:
{platform_summary_text}

Sentiment Distribution:
{sentiment_summary_text}

Please provide 3-5 actionable insights about:
1. Overall brand performance and engagement trends
2. Platform-specific recommendations for improvement
3. Sentiment analysis and brand perception
4. Content strategy recommendations
5. Opportunities for growth and engagement

Format each insight as a clear, concise statement with specific recommendations where applicable. Focus on actionable insights that can drive improvement. Do not use markdown formatting or special characters."""

        return prompt
    
    def _parse_insights(self, response_text: str) -> List[str]:
        """
        Parse the Gemini API response into a list of insights.
        
        Args:
            response_text (str): Raw response from the API
            
        Returns:
            List[str]: List of formatted insights
        """
        # Split response into lines and clean up
        insights = [line.strip() for line in response_text.split('\n') if line.strip()]
        
        # Remove any numbering or bullet points
        insights = [insight.lstrip('1234567890.*- ') for insight in insights]
        
        # Filter out any empty or very short insights
        insights = [insight for insight in insights if len(insight) > 10]
        
        # Ensure each insight starts with a capital letter and ends with a period
        insights = [insight[0].upper() + insight[1:] if insight else insight for insight in insights]
        insights = [insight + '.' if not insight.endswith('.') else insight for insight in insights]
        
        # Format insights with bullet points
        formatted_insights = []
        for insight in insights[:5]:  # Limit to top 5 insights
            formatted_insights.append(f"• {insight}")
        
        return formatted_insights 