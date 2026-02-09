# AI-Powered Fashion Agent Chatbot

A multilingual NLP-powered chatbot for fashion, beauty, and styling advice.

## Features

✨ **NLP-Powered**: Automatic language detection and intent classification
🌍 **Bilingual**: Supports English and Kannada languages
🎨 **Fashion-Focused**: Strictly answers only fashion, beauty, makeup, and styling questions
📱 **Responsive Design**: Works on desktop and mobile
🚀 **Production-Ready**: Easy to deploy on any web server

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open browser and navigate to:
```
http://localhost:5000
```

## Deployment

### Deploy to AWS EC2:
1. Launch EC2 instance (Ubuntu)
2. Install Python and pip
3. Clone/upload project files
4. Install dependencies: `pip install -r requirements.txt`
5. Run with: `python app.py`
6. Configure security group to allow port 5000

### Deploy to Heroku:
1. Create `Procfile`:
```
web: python app.py
```
2. Push to Heroku:
```bash
heroku create your-fashion-bot
git push heroku main
```

### Deploy to Azure Web Apps:
1. Create Web App in Azure Portal
2. Deploy via Git or ZIP
3. Set startup command: `python app.py`

## Project Structure

```
Fashion bot/
├── app.py                 # Flask backend with NLP
├── templates/
│   └── index.html        # Chatbot UI
├── requirements.txt      # Python dependencies
└── README.md            # Documentation
```

## How It Works

1. **Language Detection**: Uses langdetect library to identify user's language
2. **Intent Classification**: Keyword-based NLP to determine if query is fashion-related
3. **Response Generation**: Context-aware responses in user's language
4. **Out-of-Scope Handling**: Politely declines non-fashion queries

## Supported Languages

- 🇬🇧 **English**: Full fashion, beauty, and styling support
- 🇮🇳 **ಕನ್ನಡ (Kannada)**: Complete fashion consultation in Kannada

## Supported Topics

- Fashion trends & styling
- Clothing & outfits
- Accessories & jewelry
- Makeup & cosmetics
- Skincare & beauty
- Hair styling
- Seasonal fashion
- Designer brands
- Sustainable fashion

## API Endpoint

**POST /chat**
```json
{
  "message": "What are the latest fashion trends?"
}
```

Response:
```json
{
  "response": "Current fashion trends include..."
}
```

## Customization

To add more languages, update `OUT_OF_SCOPE_RESPONSES` in `app.py`:
```python
OUT_OF_SCOPE_RESPONSES = {
    'your_lang_code': "Your translated message"
}
```

To expand fashion keywords, add to `FASHION_KEYWORDS` set in `app.py`.

## License

MIT License
