# Deployment Guide - Course Chatbot

## Overview
This is a Streamlit-based AI course recommendation chatbot powered by Google Gemini API.

## Prerequisites
- Python 3.8+
- Google Gemini API key
- Streamlit Cloud account (for cloud deployment)

## Local Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file in the course-chatbot directory:
```
GOOGLE_API_KEY=your_api_key_here
```

### 3. Run Locally
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Cloud Deployment (Streamlit Cloud)

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Connect to Streamlit Cloud
1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Click "New app"
3. Select your GitHub repository
4. Set main file path: `course-chatbot/app.py`
5. Click Deploy

### 3. Add Secrets
In Streamlit Cloud:
1. Go to Settings → Secrets
2. Add your API key:
```toml
GOOGLE_API_KEY = "your_api_key_here"
```

## Production Deployment (Other Platforms)

### Using Heroku
```bash
heroku login
heroku create your-app-name
git push heroku main
```

Add environment variable:
```bash
heroku config:set GOOGLE_API_KEY=your_key
```

### Using Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "course-chatbot/app.py", "--server.port=8501"]
```

## File Structure
```
course-chatbot/
├── app.py                 # Main Streamlit app
├── recommender.py         # Recommendation engine
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── .env                  # Environment variables (local only)
├── utils/
│   ├── gemini_utils.py
│   ├── conversation_manager.py
│   └── prompt_templates.py
├── data/
│   └── udemy_courses.csv
└── README.md
```

## Environment Variables
- `GOOGLE_API_KEY`: Your Google Gemini API key (required)

## Troubleshooting

### API Key Issues
- Ensure your API key is valid and has Gemini API enabled
- Check rate limits on your Google Cloud project

### Data Loading Issues
- Ensure `data/udemy_courses.csv` is in the correct path
- For cloud deployment, consider uploading to cloud storage (S3, GCS)

### Performance
- Add caching for large operations
- Use `@st.cache_data` decorator for data loading
- Optimize Gemini API calls

## Support
For issues, check:
- [Streamlit Docs](https://docs.streamlit.io)
- [Google Gemini API Docs](https://ai.google.dev/docs)
