# Social Listening Tool

A web application for analyzing social media data and generating insights using AI.

## Features

- Social media data collection and analysis
- Real-time metrics visualization
- AI-powered insights generation
- Google Sheets integration for data storage
- Interactive dashboard

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file with your Google API credentials
   - Add your Google Sheets API credentials
4. Run the development server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8080
   ```

## Deployment

This application is configured for deployment on Render.com:

1. Create a Render.com account
2. Connect your GitHub repository
3. Create a new Web Service
4. Configure environment variables:
   - Add your Google API credentials
   - Set up Google Sheets API access
5. Deploy!

## Environment Variables

Required environment variables:
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google API credentials file
- `GOOGLE_SHEETS_ID`: Your Google Sheets document ID

## License

MIT License 