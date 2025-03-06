import os
import json
from typing import List, Dict, Any
import logging
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import pandas as pd
import base64

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        try:
            # Get credentials from environment variables
            private_key = os.getenv("GOOGLE_PRIVATE_KEY")
            if private_key:
                try:
                    # Try to decode if it's base64 encoded
                    private_key = base64.b64decode(private_key).decode('utf-8')
                except:
                    # If not base64, use as is
                    pass
                
                # Clean up the private key
                private_key = private_key.strip()
                private_key = private_key.replace('\\n', '\n')
                private_key = private_key.replace('\\"', '"')
                
                # Ensure proper formatting
                if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                    private_key = f"-----BEGIN PRIVATE KEY-----\n{private_key}"
                if not private_key.endswith('-----END PRIVATE KEY-----'):
                    private_key = f"{private_key}\n-----END PRIVATE KEY-----"
                if not private_key.endswith('\n'):
                    private_key += '\n'
                
                # Log key structure (safely)
                logger.debug("Private key validation:")
                logger.debug(f"Starts with correct header: {private_key.startswith('-----BEGIN PRIVATE KEY-----')}")
                end_marker = '-----END PRIVATE KEY-----\n'
                logger.debug(f"Ends with correct footer: {private_key.endswith(end_marker)}")
                newline_count = private_key.count('\n')
                logger.debug(f"Number of newlines in key: {newline_count}")
                
                # Additional debug info
                key_parts = private_key.split('\n')
                logger.debug(f"Number of key parts: {len(key_parts)}")
                logger.debug(f"Key structure valid: {len(key_parts) > 2 and key_parts[0].startswith('-----BEGIN') and key_parts[-2].endswith('-----')}")
            
            credentials = {
                "type": "service_account",
                "project_id": os.getenv("GOOGLE_PROJECT_ID"),
                "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
                "private_key": private_key,
                "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL")
            }
            
            # Log environment variables status for debugging
            logger.info("Checking environment variables...")
            for key, value in credentials.items():
                if key != "private_key":  # Don't log the actual private key
                    logger.info(f"{key}: {'set' if value else 'not set'}")
            
            # Validate required fields
            required_fields = ["project_id", "private_key_id", "private_key", "client_email", "client_id", "client_x509_cert_url"]
            missing_fields = [field for field in required_fields if not credentials.get(field)]
            if missing_fields:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
            
            self.scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Create credentials from the dictionary
            try:
                logger.debug("Attempting to create credentials...")
                # Log the structure of credentials (safely)
                safe_creds = {k: ('set' if v else 'not set') for k, v in credentials.items()}
                logger.debug(f"Credentials structure: {json.dumps(safe_creds, indent=2)}")
                
                self.credentials = Credentials.from_service_account_info(
                    credentials,
                    scopes=self.scope
                )
                logger.debug("Credentials created successfully")
                
                logger.debug("Attempting to authorize with gspread...")
                self.client = gspread.authorize(self.credentials)
                logger.debug("gspread authorization successful")
                
                self.spreadsheet = None
                logger.info("Successfully initialized Google Sheets service")
            except Exception as e:
                logger.error(f"Failed to initialize credentials: {str(e)}")
                if hasattr(e, '__dict__'):
                    logger.error(f"Error details: {e.__dict__}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error details: {e.__dict__}")
            raise
    
    def create_or_get_spreadsheet(self, brand_name: str) -> gspread.Spreadsheet:
        """
        Create a new spreadsheet for a brand or get an existing one.
        
        Args:
            brand_name (str): Name of the brand
            
        Returns:
            gspread.Spreadsheet: The spreadsheet object
        """
        try:
            # Try to find existing spreadsheet
            spreadsheet_name = f"Social Listening - {brand_name}"
            try:
                self.spreadsheet = self.client.open(spreadsheet_name)
                logger.info(f"Found existing spreadsheet for {brand_name}")
            except gspread.SpreadsheetNotFound:
                # Create new spreadsheet
                self.spreadsheet = self.client.create(spreadsheet_name)
                logger.info(f"Created new spreadsheet for {brand_name}")
            
            return self.spreadsheet
        
        except Exception as e:
            logger.error(f"Error creating/getting spreadsheet: {str(e)}")
            raise
    
    def update_data_sheet(self, brand_name: str, data: List[Dict[str, Any]]) -> None:
        """
        Update the data sheet with new social media data.
        
        Args:
            brand_name (str): Name of the brand
            data (List[Dict[str, Any]]): Social media data
        """
        try:
            spreadsheet = self.create_or_get_spreadsheet(brand_name)
            
            # Convert data to DataFrame for easier manipulation
            df = pd.DataFrame(data)
            
            # Prepare data for sheets
            headers = ["Date", "Platform", "Content", "Likes", "Comments", "Shares", "Sentiment", "URL"]
            rows = [headers]
            
            for _, row in df.iterrows():
                rows.append([
                    row["date"],
                    row["platform"],
                    row["content"],
                    row["engagement"]["likes"],
                    row["engagement"]["comments"],
                    row["engagement"]["shares"],
                    row["sentiment"],
                    row["url"]
                ])
            
            # Update or create the data sheet
            try:
                sheet = spreadsheet.worksheet("Raw Data")
            except gspread.WorksheetNotFound:
                sheet = spreadsheet.add_worksheet("Raw Data", len(rows), len(headers))
            
            sheet.clear()  # Clear existing data
            sheet.update(rows)
            
            # Format the sheet
            sheet.format("A1:H1", {"textFormat": {"bold": True}})
            sheet.freeze(rows=1)
            
            logger.info(f"Updated data sheet for {brand_name}")
            
        except Exception as e:
            logger.error(f"Error updating data sheet: {str(e)}")
            raise
    
    def update_metrics_sheet(self, brand_name: str, metrics: Dict[str, Any]) -> None:
        """
        Update the metrics sheet with processed data and insights.
        
        Args:
            brand_name (str): Name of the brand
            metrics (Dict[str, Any]): Processed metrics and insights
        """
        try:
            spreadsheet = self.create_or_get_spreadsheet(brand_name)
            
            # Log the incoming metrics for debugging
            logger.debug(f"Received metrics for {brand_name}: {json.dumps(metrics, indent=2)}")
            
            # Ensure required metrics exist with default values
            metrics = {
                "total_posts": metrics.get("total_posts", 0),
                "total_engagement": metrics.get("total_engagement", 0),
                "platform_stats": metrics.get("platform_stats", {}),
                "sentiment_stats": metrics.get("sentiment_stats", {}),
                "raw_data": metrics.get("raw_data", []),
                "insights": metrics.get("insights", [])
            }
            
            # Validate insights
            if not isinstance(metrics["insights"], list):
                logger.warning(f"Insights is not a list: {metrics['insights']}")
                metrics["insights"] = []
            
            # Log the processed metrics
            logger.debug(f"Processed metrics for {brand_name}: {json.dumps(metrics, indent=2)}")
            
            # Prepare metrics data
            metrics_data = [
                ["Metrics", "Value"],
                ["Total Posts", metrics["total_posts"]],
                ["Total Engagement", metrics["total_engagement"]],
                ["Average Engagement Rate", f"{metrics['total_engagement'] / metrics['total_posts']:.2f}" if metrics['total_posts'] > 0 else "0"],
                ["", ""],
                ["Platform Statistics", ""],
                ["Platform", "Total Engagement", "Posts", "Avg. Engagement"]
            ]
            
            # Add platform statistics
            for platform, engagement in metrics["platform_stats"].items():
                platform_posts = sum(1 for post in metrics.get("raw_data", []) if post["platform"] == platform)
                avg_engagement = engagement / platform_posts if platform_posts > 0 else 0
                metrics_data.append([platform, engagement, platform_posts, f"{avg_engagement:.2f}"])
            
            metrics_data.extend([
                ["", ""],
                ["Sentiment Distribution", ""],
                ["Sentiment", "Count", "Percentage"]
            ])
            
            # Add sentiment statistics
            total_posts = metrics["total_posts"]
            for sentiment, count in metrics["sentiment_stats"].items():
                percentage = (count / total_posts) * 100 if total_posts > 0 else 0
                metrics_data.append([sentiment, count, f"{percentage:.1f}%"])
            
            metrics_data.extend([
                ["", ""],
                ["AI-Generated Insights", ""]
            ])
            
            # Add insights with validation
            if metrics["insights"]:
                for insight in metrics["insights"]:
                    if isinstance(insight, str):
                        metrics_data.append([insight, ""])
                    else:
                        logger.warning(f"Invalid insight format: {insight}")
                        metrics_data.append([str(insight), ""])
            else:
                logger.warning("No insights available")
                metrics_data.append(["No insights available", ""])
            
            # Log the final metrics data
            logger.debug(f"Final metrics data for {brand_name}: {json.dumps(metrics_data, indent=2)}")
            
            # Update or create the metrics sheet
            try:
                sheet = spreadsheet.worksheet("Metrics")
            except gspread.WorksheetNotFound:
                sheet = spreadsheet.add_worksheet("Metrics", len(metrics_data), 3)
            
            sheet.clear()  # Clear existing data
            sheet.update(metrics_data)
            
            # Format the sheet
            sheet.format("A1:B1", {"textFormat": {"bold": True}})
            sheet.format("A6:C6", {"textFormat": {"bold": True}})
            sheet.format("A12:C12", {"textFormat": {"bold": True}})
            sheet.format("A16:B16", {"textFormat": {"bold": True}})
            
            # Format sentiment percentages with background colors
            sentiment_start_row = 13
            for i, (sentiment, count) in enumerate(metrics["sentiment_stats"].items()):
                row = sentiment_start_row + i
                percentage = (count / total_posts) * 100 if total_posts > 0 else 0
                
                # Set background color based on percentage
                if percentage > 50:
                    color = {"red": 0.8, "green": 1, "blue": 0.8}  # Light green
                elif percentage > 25:
                    color = {"red": 1, "green": 1, "blue": 0.8}  # Light yellow
                else:
                    color = {"red": 1, "green": 0.8, "blue": 0.8}  # Light red
                
                sheet.format(f"C{row}", {"backgroundColor": color})
            
            logger.info(f"Updated metrics sheet for {brand_name}")
            
        except Exception as e:
            logger.error(f"Error updating metrics sheet: {str(e)}")
            raise
    
    def create_dashboard_sheet(self, brand_name: str) -> None:
        """
        Create a dashboard sheet with charts and visualizations.
        
        Args:
            brand_name (str): Name of the brand
        """
        try:
            spreadsheet = self.create_or_get_spreadsheet(brand_name)
            
            # Create dashboard sheet
            try:
                dashboard = spreadsheet.worksheet("Dashboard")
            except gspread.WorksheetNotFound:
                dashboard = spreadsheet.add_worksheet("Dashboard", 100, 20)
            
            # Add dashboard title and description
            dashboard.update("A1", [[f"Social Media Dashboard - {brand_name}"]])
            dashboard.update("A2", [[f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])
            
            # Add chart placeholders
            dashboard.update("A4", [["Platform Performance"]])
            dashboard.update("A20", [["Sentiment Distribution"]])
            dashboard.update("A36", [["Engagement Trends"]])
            
            # Format the dashboard
            dashboard.format("A1", {"textFormat": {"bold": True, "fontSize": 16}})
            dashboard.format("A2", {"textFormat": {"italic": True}})
            dashboard.format("A4", {"textFormat": {"bold": True, "fontSize": 14}})
            dashboard.format("A20", {"textFormat": {"bold": True, "fontSize": 14}})
            dashboard.format("A36", {"textFormat": {"bold": True, "fontSize": 14}})
            
            # Add instructions for Data Studio
            dashboard.update("A50", [[
                "To view interactive visualizations, click the link below to open in Google Data Studio:"
            ]])
            
            # Create Data Studio link
            data_studio_url = f"https://datastudio.google.com/reporting/create?ds=spreadsheets&spreadsheetId={spreadsheet.id}"
            dashboard.update("A51", [[f"=HYPERLINK(\"{data_studio_url}\", \"Open in Google Data Studio\")"]])
            
            logger.info(f"Created dashboard sheet for {brand_name}")
            
        except Exception as e:
            logger.error(f"Error creating dashboard sheet: {str(e)}")
            raise 