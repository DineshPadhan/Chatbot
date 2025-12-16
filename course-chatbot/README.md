# 🎓 AI Course Recommendation Chatbot

An intelligent Streamlit-based chatbot that recommends Udemy courses using conversational AI, powered by Google Gemini API.

## Features

✨ **Smart Conversational Interface**
- Natural multi-turn conversations
- Progressive information gathering (ask for details progressively)
- Context retention across messages
- Empathetic responses when no courses found

🤖 **AI-Powered Search**
- Gemini-based query parsing and intent classification
- TF-IDF similarity matching with cosine similarity
- Smart filter extraction (level, budget, paid/free)
- AI-generated course descriptions

📚 **Course Recommendations**
- Filter by topic, difficulty level, and budget
- Real-time course matching
- Paginated results with detailed course cards
- Course details page with AI-generated overview

💬 **Natural Conversations**
- Chit-chat handling (greetings, thank you, goodbye)
- Dataset Q&A mode
- Help command for guidance
- Reset capability to start fresh

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Google Gemini API key ([Get one here](https://ai.google.dev))

### Setup

1. **Clone or download the project**
```bash
cd course-chatbot
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the `course-chatbot` directory:
```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

5. **Run the app**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Usage

### Starting a Search
```
User: "I want to learn Python programming"
Bot: "What's your current skill level? Beginner/Intermediate/Advanced?"
User: "Beginner"
Bot: "Perfect! Are you looking for free courses or open to paid ones?"
User: "Free"
Bot: [Shows recommended courses]
```

### Adding Constraints After Search
```
User: "Show me web development courses"
Bot: [Shows results]
User: "My budget is under 100 rupees"
Bot: "Got it! Filtering for courses under ₹100. I found 5 courses..."
```

### Commands
- `help` - See what the chatbot can do
- `reset` - Start fresh conversation
- Click on any course card to see full details with AI-generated description

## Project Structure

```
course-chatbot/
├── app.py                          # Main Streamlit application
├── recommender.py                  # Course recommendation engine
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── DEPLOYMENT.md                   # Deployment guide
├── .gitignore                      # Git ignore rules
├── .streamlit/
│   ├── config.toml                # Streamlit configuration
│   └── secrets.toml.example       # Secrets template
├── utils/
│   ├── gemini_utils.py            # Gemini API helpers
│   ├── conversation_manager.py    # Conversation logic
│   └── prompt_templates.py        # Prompt templates
├── data/
│   └── udemy_courses.csv          # Course dataset
└── __pycache__/
```

## Configuration

### Streamlit Config (`.streamlit/config.toml`)
- Theme customization
- Server settings
- Client preferences
- Browser settings

### Available Settings
- `port`: Server port (default: 8501)
- `maxUploadSize`: Max upload size in MB
- `timeZone`: Server timezone
- `theme.primaryColor`: Main theme color

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |

### For Deployment
- Set `GOOGLE_API_KEY` in Streamlit Cloud Secrets (don't commit `.env`)
- Use `.env` file for local development only

## How It Works

### 1. **Conversational Flow**
- User provides initial query
- Bot asks for missing information (topic, level, budget)
- Each response refines the search criteria

### 2. **Search & Filtering**
- Parse user query with Gemini to extract:
  - Keywords/topics
  - Skill level (beginner/intermediate/advanced)
  - Budget preference (free/paid)
  - Price range (if applicable)
- Match against course database using TF-IDF + cosine similarity
- Return top 10 matching courses with match percentage

### 3. **Context Management**
- Remembers previous searches
- Merges new constraints with existing context
- Clears context only on user request or new topic

### 4. **Course Details**
- Click any course card to view full details
- AI generates engaging course overview
- Shows pricing, duration, subscribers, reviews
- Direct link to course on Udemy

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Start (Streamlit Cloud)
1. Push code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create new app, select your repo
4. Add `GOOGLE_API_KEY` to Secrets
5. Deploy!

## Technologies Used

- **Frontend**: Streamlit
- **AI**: Google Gemini 2.5 Flash
- **Search**: scikit-learn (TF-IDF + Cosine Similarity)
- **Data Processing**: pandas, numpy
- **API**: google-generativeai

## API Usage & Costs

- Free tier: Limited requests per day
- Paid tier: Pay-as-you-go pricing
- Check [Google AI pricing](https://ai.google.dev/pricing) for details

## Known Limitations

- Requires internet connection for Gemini API
- Course data is static (CSV snapshot)
- No user authentication
- Single-session state (resets on page refresh)
- Budget detection works best with explicit amounts

## Future Enhancements

- [ ] User accounts & saved preferences
- [ ] Real-time course data via Udemy API
- [ ] Course reviews & ratings display
- [ ] Wishlist/bookmark functionality
- [ ] Multi-language support
- [ ] Course comparison tool
- [ ] Learning path recommendations

## Troubleshooting

**Issue**: "GOOGLE_API_KEY not found"
- Solution: Set `GOOGLE_API_KEY` in `.env` file or environment variables

**Issue**: No courses found even with valid search
- Solution: Try broader topic or remove filters (budget/level)

**Issue**: Slow responses
- Solution: Might be API rate limiting. Wait a moment and retry

**Issue**: Course descriptions not generating
- Solution: Check Gemini API status and quota limits

## Contributing

Feel free to fork, modify, and improve this project!

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the [Streamlit Docs](https://docs.streamlit.io)
2. Check the [Google Gemini API Docs](https://ai.google.dev/docs)
3. Review the [Troubleshooting](#troubleshooting) section

---

**Made with ❤️ using Streamlit & Gemini AI**
