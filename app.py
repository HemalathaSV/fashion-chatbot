from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from langdetect import detect
import re
import secrets

import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

conversation_memory = {}
conversation_context = {}  # Stores last topic/intent/keywords
shown_images = {}
session_timestamps = {}  # Track session activity

# Enhanced memory capacity with instance-level boosting
MAX_MEMORY_SIZE = 15000  # Increased from 10000
CONTEXT_WINDOW = 300  # Increased from 200
MAX_KEYWORDS = 75  # Increased from 50
MAX_SESSIONS = 1000  # Maximum concurrent sessions

# Memory optimization settings
MEMORY_CLEANUP_THRESHOLD = 0.8  # Cleanup when 80% full
INACTIVE_SESSION_TIMEOUT = 3600  # 1 hour in seconds

FASHION_KEYWORDS = {
    # English keywords - Clothing & Outfits
    'fashion', 'trends', 'clothing', 'outfits', 'styling', 'wardrobe', 'apparel',
    'dress', 'shirt', 'pants', 'jeans', 'skirt', 'style', 'wear', 'outfit', 'look',
    'saree', 'lehenga', 'kurta', 'kurti', 'salwar', 'kameez', 'churidar', 'palazzo',
    'blazer', 'jacket', 'coat', 'sweater', 'cardigan', 'top', 'blouse', 'tunic',
    'shorts', 'trousers', 'gown', 'jumpsuit', 'romper', 'suit', 'tuxedo',
    
    # Occasions
    'wedding', 'bride', 'groom', 'bridal', 'marriage', 'reception', 'engagement',
    'office', 'work', 'formal', 'casual', 'party', 'professional', 'business',
    'festival', 'celebration', 'event', 'ceremony', 'function', 'gathering',
    'date', 'dinner', 'lunch', 'brunch', 'cocktail', 'evening', 'night', 'day',
    
    # Accessories & Jewelry
    'accessories', 'shoes', 'bags', 'jewelry', 'jewellery', 'necklace', 'earrings',
    'bracelet', 'ring', 'bangles', 'anklet', 'chain', 'pendant', 'brooch',
    'watch', 'belt', 'scarf', 'stole', 'dupatta', 'shawl', 'hat', 'cap',
    'sunglasses', 'glasses', 'clutch', 'purse', 'handbag', 'wallet',
    'heels', 'flats', 'sandals', 'boots', 'sneakers', 'loafers', 'pumps',
    
    # Makeup & Beauty
    'makeup', 'cosmetics', 'skincare', 'beauty', 'hair', 'nail', 'manicure', 'pedicure',
    'foundation', 'concealer', 'powder', 'blush', 'bronzer', 'highlighter', 'contour',
    'lipstick', 'lipgloss', 'lipliner', 'eyeshadow', 'eyeliner', 'mascara', 'kajal',
    'eyebrow', 'brow', 'primer', 'setting', 'spray', 'perfume', 'fragrance',
    'hairstyle', 'haircut', 'haircolor', 'hairdo', 'bun', 'ponytail', 'braid',
    
    # Colors
    'color', 'colour', 'red', 'blue', 'green', 'yellow', 'pink', 'purple', 'orange',
    'black', 'white', 'grey', 'gray', 'brown', 'beige', 'navy', 'maroon', 'burgundy',
    'gold', 'silver', 'bronze', 'copper', 'cream', 'ivory', 'peach', 'coral', 'mint',
    
    # Styles & Attributes
    'traditional', 'modern', 'contemporary', 'vintage', 'retro', 'classic', 'trendy',
    'ethnic', 'western', 'indo-western', 'fusion', 'bohemian', 'boho', 'chic',
    'elegant', 'sophisticated', 'glamorous', 'minimalist', 'edgy', 'sporty',
    'overall', 'complete', 'full', 'entire', 'whole', 'perfect', 'ideal',
    'smart', 'sharp', 'polished', 'sleek', 'stylish', 'fashionable',
    
    # Fabrics & Materials
    'silk', 'cotton', 'linen', 'wool', 'chiffon', 'georgette', 'velvet', 'satin',
    'denim', 'leather', 'suede', 'lace', 'net', 'organza', 'crepe', 'rayon',
    
    # Brands & Shopping
    'brand', 'designer', 'boutique', 'store', 'shop', 'buy', 'purchase', 'price',
    'budget', 'affordable', 'expensive', 'luxury', 'premium', 'collection',
    
    # Action words
    'tips', 'advice', 'idea', 'suggestion', 'recommend', 'help', 'need', 'want',
    'settled', 'something', 'anything', 'show', 'tell', 'give', 'find', 'choose',
    
    # Kannada keywords
    'ಫ್ಯಾಷನ್', 'ಮೇಕಪ್', 'ಸೌಂದರ್ಯ', 'ವಸ್ತ್ರ', 'ಬಟ್ಟೆ', 'ಸೀರೆ', 'ಮದುವೆ', 'ಶೈಲಿ', 'ಆಭರಣ',
    'ಕೂದಲು', 'ಚರ್ಮ', 'ಸುಗಂಧ', 'ಬಣ್ಣ', 'ಕೆಂಪು', 'ನೀಲಿ', 'ಹಸಿರು', 'ಹಳದಿ', 'ಕಪ್ಪು', 'ಬಿಳಿ',
    'ಚಪ್ಪಲಿ', 'ಬೂಟು', 'ಕೈಚೀಲ', 'ಉಂಗುರ', 'ಕಿವಿಯೋಲೆ', 'ಕೊರಳು', 'ಬಳೆ',
    'ಆಫೀಸ್', 'ಪಾರ್ಟಿ', 'ಕಾರ್ಯ', 'ಔಪಚಾರಿಕ', 'ಅನೌಪಚಾರಿಕ',
    
    # Transliterated/Mixed keywords
    'ನೀಡ್', 'ವೆಡ್ಡಿಂಗ್', 'ಸಂಥಿಂಗ್', 'ಐ', 'ಫಾರ್', 'ಲುಕ್', 'ಸ್ಟೈಲ್'
}

GREETING_KEYWORDS = {
    'hi', 'hello', 'hey', 'greetings', 'namaste'
}

GRATITUDE_KEYWORDS = {
    'thank', 'thanks', 'thankyou', 'thank you', 'thx', 'tq', 'appreciate', 'grateful',
    'धन्यवाद', 'ಧನ್ಯವಾದ', 'ಧನ್ಯವಾದಗಳು'
}

OUT_OF_SCOPE_RESPONSES = {
    'en': "Sorry, I am a fashion agent and I can only answer questions related to fashion, makeup, and beauty trends.",
    'kn': "ಕ್ಷಮಿಸಿ, ನಾನು ಫ್ಯಾಷನ್ ಏಜೆಂಟ್ ಮತ್ತು ನಾನು ಫ್ಯಾಷನ್, ಮೇಕಪ್ ಮತ್ತು ಸೌಂದರ್ಯ ಟ್ರೆಂಡ್ಗಳಿಗೆ ಸಂಬಂಧಿಸಿದ ಪ್ರಶ್ನೆಗಳಿಗೆ ಮಾತ್ರ ಉತ್ತರಿಸಬಲ್ಲೆ."
}

def detect_language(text):
    try:
        lang = detect(text)
        return lang
    except:
        return 'en'

def is_greeting(text):
    text_lower = text.lower().strip()
    return any(greeting in text_lower for greeting in GREETING_KEYWORDS)

def is_gratitude(text):
    text_lower = text.lower().strip()
    return any(gratitude in text_lower for gratitude in GRATITUDE_KEYWORDS)

def extract_intent(text, context_data):
    """Extract user intent from message and context"""
    text_lower = text.lower()
    
    # Enhanced context checking - look at previous keywords
    prev_keywords = context_data.get('keywords', [])
    last_intent = context_data.get('last_intent', '')
    
    # Extract current keywords and find links
    current_keywords = extract_keywords(text)
    keyword_links = find_keyword_links(current_keywords, prev_keywords)
    
    # Check for gender specification with context
    if any(word in text_lower for word in ['men', 'man', 'male', 'groom', 'boy', 'guy', 'gentleman']):
        if last_intent in ['formal_office', 'casual_office', 'office', 'outfit_general'] or 'office' in keyword_links:
            return 'men_office'
        if last_intent in ['wedding'] or 'wedding' in keyword_links:
            return 'men_wedding'
        if last_intent in ['party'] or 'party' in keyword_links:
            return 'men_party'
        if last_intent in ['casual_wear'] or 'casual' in keyword_links:
            return 'men_casual'
        # If just "men" or "for men" after any fashion context
        if last_intent in ['formal_office', 'casual_office', 'office', 'wedding', 'party', 'outfit_general']:
            return 'men_' + last_intent.replace('_office', '_office')
    
    # Check for color combination queries with office context
    if last_intent in ['formal_office', 'casual_office', 'office', 'outfit_general'] or 'office' in keyword_links:
        color_words = ['red', 'black', 'white', 'blue', 'green', 'grey', 'navy', 'burgundy', 'pink', 'yellow']
        if any(color in text_lower for color in color_words) and len(text_lower.split()) <= 15:
            return 'color_styling_office'
    
    # Check for single-word formal/casual queries with office context
    if last_intent in ['formal_office', 'casual_office', 'office', 'outfit_general'] or 'office' in keyword_links:
        if text_lower.strip() in ['formal', 'casual', 'smart casual', 'professional', 'smart']:
            if 'formal' in text_lower or 'professional' in text_lower:
                return 'formal_office'
            elif 'casual' in text_lower or 'smart' in text_lower:
                return 'casual_office'
    
    # Check for single-word queries with wedding context
    if last_intent in ['wedding', 'wedding_makeup'] or 'wedding' in keyword_links:
        if text_lower.strip() in ['makeup', 'ಮೇಕಪ್', 'cosmetic', 'beauty']:
            return 'wedding_makeup'
        if text_lower.strip() in ['outfit', 'dress', 'wear', 'clothes', 'ವಸ್ತ್ರ']:
            return 'wedding'
    
    # Check for single-word queries with party context
    if last_intent in ['party', 'party_makeup'] or 'party' in keyword_links:
        if text_lower.strip() in ['makeup', 'ಮೇಕಪ್', 'cosmetic', 'beauty']:
            return 'party_makeup'
        if text_lower.strip() in ['outfit', 'dress', 'wear', 'clothes']:
            return 'party'
    
    # Check for color-only queries with saree context
    if last_intent in ['saree', 'kanchipuram_saree'] or 'saree' in keyword_links:
        color_keywords = ['red', 'green', 'blue', 'yellow', 'pink', 'purple', 'orange', 'black', 'white', 'gold', 'silver', 'maroon', 'navy']
        if any(color in text_lower for color in color_keywords) and len(text_lower.split()) <= 3:
            return 'saree_color_change'
    
    # Smart continuation detection - if previous context exists
    if last_intent and len(text_lower.split()) <= 10:
        continuation_words = ['yes', 'yeah', 'ok', 'sure', 'need', 'want', 'tell', 'show', 'give', 'something', 'anything', 'more', 'also', 'ನೀಡ್', 'ಸಂಥಿಂಗ್', 'ಐ', 'ಫಾರ್']
        if any(word in text_lower for word in continuation_words):
            # Check if it relates to previous topic
            if any(kw in text_lower for kw in prev_keywords[-5:]):
                return last_intent + '_continue'
            # Check for wedding/party/office context
            if 'wedding' in last_intent or 'ಮದುವೆ' in ' '.join(prev_keywords[-5:]):
                if any(word in text_lower for word in ['wedding', 'bridal', 'ಮದುವೆ', 'ವೆಡ್ಡಿಂಗ್']):
                    return 'wedding'
            if 'office' in last_intent:
                if any(word in text_lower for word in ['office', 'work', 'professional']):
                    return last_intent
    
    # Check for formal/casual outfit queries
    if any(word in text_lower for word in ['formal', 'professional']) and any(word in text_lower for word in ['outfit', 'dress', 'wear', 'look']):
        return 'formal_office'
    
    # Check for specific intents
    if any(word in text_lower for word in ['makeup', 'cosmetic', 'foundation', 'lipstick', 'eyeshadow', 'ಮೇಕಪ್']):
        if any(word in text_lower for word in ['wedding', 'bridal', 'traditional', 'settled', 'ಮದುವೆ', 'ವೆಡ್ಡಿಂಗ್']):
            return 'wedding_makeup'
        elif any(word in text_lower for word in ['party', 'evening', 'night']):
            return 'party_makeup'
        else:
            return 'makeup'
    
    if any(word in text_lower for word in ['kanchipuram', 'kanchi', 'kanjivaram']):
        return 'kanchipuram_saree'
    
    if any(word in text_lower for word in ['overall', 'complete', 'full', 'entire', 'whole']):
        if any(word in text_lower for word in ['look', 'style', 'outfit']):
            if any(word in text_lower for word in ['casual', 'office', 'work']):
                return 'complete_office_look'
            elif any(word in text_lower for word in ['wedding', 'bridal', 'ಮದುವೆ', 'ವೆಡ್ಡಿಂಗ್']):
                return 'complete_wedding_look'
            return 'complete_look'
    
    if any(word in text_lower for word in ['office', 'work', 'professional']):
        if any(word in text_lower for word in ['casual', 'smart']):
            return 'casual_office'
        return 'formal_office'
    
    if any(word in text_lower for word in ['wedding', 'bridal', 'ಮದುವೆ', 'ವೆಡ್ಡಿಂಗ್']):
        return 'wedding'
    
    if any(word in text_lower for word in ['party', 'celebration', 'event']):
        return 'party'
    
    if any(word in text_lower for word in ['festival', 'festive', 'ಹಬ್ಬ', 'ಉತ್ಸವ']):
        return 'festival'
    
    if any(word in text_lower for word in ['vacation', 'holiday', 'travel', 'trip', 'beach', 'resort']):
        return 'vacation'
    
    if 'casual' in text_lower and 'wear' in text_lower:
        return 'casual_wear'
    
    if any(word in text_lower for word in ['saree', 'sari', 'ಸೀರೆ']):
        return 'saree'
    
    if any(word in text_lower for word in ['outfit', 'dress', 'wear', 'ವಸ್ತ್ರ', 'clothes']):
        return 'outfit_general'
    
    # Check context for continuation
    if last_intent:
        if any(word in text_lower for word in ['yes', 'yeah', 'ok', 'sure', 'need', 'want', 'tell', 'show', 'give', 'something', 'anything', 'ನೀಡ್', 'ಸಂಥಿಂಗ್']):
            return last_intent + '_continue'
    
    return 'general'

def extract_keywords(text):
    """Extract important keywords from user message"""
    text_lower = text.lower()
    keywords = []
    
    # Expanded important words list
    important_words = [
        # Occasions
        'wedding', 'party', 'office', 'casual', 'formal', 'bridal', 'reception', 'engagement',
        'festival', 'ceremony', 'function', 'date', 'dinner', 'cocktail', 'business',
        # Clothing
        'saree', 'lehenga', 'dress', 'outfit', 'kurta', 'kurti', 'salwar', 'palazzo',
        'blazer', 'jacket', 'shirt', 'pants', 'jeans', 'skirt', 'gown', 'jumpsuit',
        # Makeup & Beauty
        'makeup', 'cosmetic', 'beauty', 'lipstick', 'foundation', 'eyeshadow', 'mascara',
        'hairstyle', 'haircut', 'skincare', 'perfume', 'nail', 'manicure',
        # Accessories
        'jewelry', 'necklace', 'earrings', 'bracelet', 'bangles', 'ring', 'watch',
        'shoes', 'heels', 'flats', 'sandals', 'boots', 'bag', 'clutch', 'purse',
        # Styles
        'traditional', 'modern', 'ethnic', 'western', 'fusion', 'vintage', 'chic',
        'elegant', 'glamorous', 'minimalist', 'trendy', 'classic', 'contemporary',
        # Attributes
        'work', 'professional', 'smart', 'style', 'look', 'complete', 'overall', 'full',
        # Colors
        'red', 'green', 'blue', 'yellow', 'pink', 'purple', 'orange', 'black', 'white',
        'gold', 'silver', 'maroon', 'navy', 'burgundy', 'beige', 'brown', 'grey',
        # Fabrics
        'silk', 'cotton', 'chiffon', 'georgette', 'velvet', 'satin', 'denim', 'lace',
        # Kannada
        'ಮದುವೆ', 'ಪಾರ್ಟಿ', 'ಆಫೀಸ್', 'ಸೀರೆ', 'ಮೇಕಪ್', 'ವಸ್ತ್ರ', 'ವೆಡ್ಡಿಂಗ್',
        'ಬಣ್ಣ', 'ಕೆಂಪು', 'ನೀಲಿ', 'ಹಸಿರು', 'ಶೈಲಿ', 'ಆಭರಣ', 'ಕೂದಲು',
        # Brands
        'kanchipuram', 'banarasi', 'kanchi', 'designer', 'brand'
    ]
    
    for word in text_lower.split():
        if word in important_words or any(kw in word for kw in important_words):
            keywords.append(word)
    
    return keywords

def find_keyword_links(current_keywords, prev_keywords):
    """Find connections between current and previous keywords"""
    links = []
    
    # Expanded keyword relationships
    keyword_groups = {
        'office': ['office', 'work', 'professional', 'formal', 'casual', 'smart', 'business', 'ಆಫೀಸ್', 'ಕಾರ್ಯ'],
        'wedding': ['wedding', 'bridal', 'marriage', 'bride', 'groom', 'reception', 'engagement', 'ಮದುವೆ', 'ವೆಡ್ಡಿಂಗ್', 'traditional'],
        'party': ['party', 'celebration', 'event', 'cocktail', 'ಪಾರ್ಟಿ', 'evening', 'night', 'function', 'gathering'],
        'saree': ['saree', 'sari', 'ಸೀರೆ', 'kanchipuram', 'silk', 'kanchi', 'banarasi', 'georgette', 'chiffon'],
        'lehenga': ['lehenga', 'choli', 'ghagra', 'chaniya'],
        'kurta': ['kurta', 'kurti', 'salwar', 'kameez', 'churidar', 'palazzo', 'ethnic'],
        'makeup': ['makeup', 'cosmetic', 'ಮೇಕಪ್', 'beauty', 'lipstick', 'foundation', 'eyeshadow', 'mascara', 'kajal'],
        'hair': ['hair', 'hairstyle', 'haircut', 'ಕೂದಲು', 'bun', 'ponytail', 'braid', 'hairdo'],
        'jewelry': ['jewelry', 'jewellery', 'ಆಭರಣ', 'necklace', 'earrings', 'bracelet', 'bangles', 'ring', 'ಬಳೆ'],
        'outfit': ['outfit', 'dress', 'wear', 'clothes', 'ವಸ್ತ್ರ', 'ಬಟ್ಟೆ', 'look', 'style', 'attire', 'ensemble'],
        'shoes': ['shoes', 'heels', 'flats', 'sandals', 'boots', 'sneakers', 'footwear', 'ಚಪ್ಪಲಿ', 'ಬೂಟು'],
        'accessories': ['accessories', 'bag', 'clutch', 'purse', 'handbag', 'scarf', 'belt', 'watch', 'ಕೈಚೀಲ'],
        'color': ['red', 'green', 'blue', 'yellow', 'pink', 'purple', 'color', 'colour', 'ಬಣ್ಣ', 'ಕೆಂಪು', 'ನೀಲಿ', 'ಹಸಿರು',
                  'orange', 'black', 'white', 'gold', 'silver', 'maroon', 'navy', 'burgundy', 'beige'],
        'style': ['traditional', 'modern', 'ethnic', 'western', 'fusion', 'vintage', 'chic', 'elegant', 'trendy', 'ಶೈಲಿ']
    }
    
    # Find which groups current and previous keywords belong to
    for current_kw in current_keywords:
        for prev_kw in prev_keywords[-15:]:  # Check last 15 keywords (increased from 10)
            for group_name, group_words in keyword_groups.items():
                if any(gw in current_kw for gw in group_words) and any(gw in prev_kw for gw in group_words):
                    links.append(group_name)
                    break
    
    return list(set(links))  # Remove duplicates

def is_fashion_related(text, context=[]):
    text_lower = text.lower()
    
    # Enhanced context checking with keyword memory
    if context:
        last_messages = ' '.join(context[-CONTEXT_WINDOW:]).lower()
        if any(keyword in last_messages for keyword in ['outfit', 'wear', 'style', 'dress', 'fashion', 'makeup', 'beauty', 'wedding', 'party', 'office', 'saree', 'ಮದುವೆ', 'ವಸ್ತ್ರ', 'ಮೇಕಪ್']):
            if len(text_lower.split()) <= 30:
                return True
    
    return any(keyword in text_lower for keyword in FASHION_KEYWORDS)

def cleanup_inactive_sessions():
    """Remove inactive sessions to free memory"""
    current_time = time.time()
    inactive_sessions = []
    
    for session_id, last_active in session_timestamps.items():
        if current_time - last_active > INACTIVE_SESSION_TIMEOUT:
            inactive_sessions.append(session_id)
    
    for session_id in inactive_sessions:
        if session_id in conversation_memory:
            del conversation_memory[session_id]
        if session_id in conversation_context:
            del conversation_context[session_id]
        if session_id in session_timestamps:
            del session_timestamps[session_id]
    
    return len(inactive_sessions)

def optimize_memory():
    """Optimize memory usage when threshold reached"""
    total_sessions = len(conversation_memory)
    
    if total_sessions > MAX_SESSIONS * MEMORY_CLEANUP_THRESHOLD:
        cleanup_inactive_sessions()
        
        # If still over threshold, remove oldest sessions
        if len(conversation_memory) > MAX_SESSIONS:
            sorted_sessions = sorted(session_timestamps.items(), key=lambda x: x[1])
            sessions_to_remove = sorted_sessions[:len(sorted_sessions) // 4]  # Remove oldest 25%
            
            for session_id, _ in sessions_to_remove:
                if session_id in conversation_memory:
                    del conversation_memory[session_id]
                if session_id in conversation_context:
                    del conversation_context[session_id]
                if session_id in session_timestamps:
                    del session_timestamps[session_id]

def get_out_of_scope_message(lang):
    return OUT_OF_SCOPE_RESPONSES.get(lang, OUT_OF_SCOPE_RESPONSES['en'])

def get_greeting_response(lang):
    responses = {
        'en': "Hello! 👋 I'm your fashion consultant. How can I help you with fashion, styling, or beauty today?",
        'kn': "ನಮಸ್ಕಾರ! 👋 ನಾನು ನಿಮ್ಮ ಫ್ಯಾಷನ್ ಸಲಹೆಗಾರ. ಇಂದು ಫ್ಯಾಷನ್, ಸ್ಟೈಲಿಂಗ್ ಅಥವಾ ಸೌಂದರ್ಯದಲ್ಲಿ ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
    }
    return responses.get(lang, responses['en'])

def get_gratitude_response(lang):
    responses = {
        'en': "You're welcome! 😊 Feel free to ask if you need more fashion advice, styling tips, or beauty recommendations. Happy to help!",
        'kn': "ನಿಮಗೆ ಸ್ವಾಗತ! 😊 ಹೆಚ್ಚಿನ ಫ್ಯಾಷನ್ ಸಲಹೆ, ಸ್ಟೈಲಿಂಗ್ ಸಲಹೆಗಳು ಅಥವಾ ಸೌಂದರ್ಯ ಶಿಫಾರಸುಗಳು ಬೇಕಾದರೆ ಕೇಳಲು ಮುಕ್ತವಾಗಿರಿ. ಸಹಾಯ ಮಾಡಲು ಸಂತೋಷ!"
    }
    return responses.get(lang, responses['en'])

def generate_fashion_response(query, lang, session_id):
    query_lower = query.lower()
    context = conversation_memory.get(session_id, [])
    context_data = conversation_context.get(session_id, {})
    
    # Extract keywords from current query
    current_keywords = extract_keywords(query)
    
    # Extract intent with enhanced context
    intent = extract_intent(query, context_data)
    
    # Handle color change for sarees
    if intent == 'saree_color_change':
        color = None
        for c in ['green', 'blue', 'pink', 'yellow', 'purple', 'maroon', 'gold', 'orange']:
            if c in query_lower:
                color = c
                break
        
        if color:
            responses = {
                'en': f"**{color.title()} Kanchipuram Saree - Beautiful Choice!** ✨\n\n**About:**\n• Pure silk from Kanchipuram, Tamil Nadu\n• Rich {color} color with gold zari work\n• Traditional temple borders and pallu designs\n• Perfect for weddings, festivals\n\n**Styling:**\n• Jewelry: Gold temple jewelry, antique gold necklace, jhumkas, gold bangles (6-8)\n• Blouse: Gold, contrast color, or matching\n• Makeup: Complement the {color} saree with matching tones\n• Hair: Traditional bun with gajra\n\n**Where to Buy:**\n• Nalli, Pothys, RMKV (Chennai)\n• Taneira, FabIndia\n• Price: ₹5,000 - ₹50,000+\n\nYou'll look absolutely stunning! 👑",
                'kn': f"**{color.title()} ಕಾಂಚೀಪುರಂ ಸೀರೆ - ಸುಂದರ ಆಯ್ಕೆ!** ✨\n\n**ಬಗ್ಗೆ:**\n• ಕಾಂಚೀಪುರಂ, ತಮಿಳುನಾಡಿನಿಂದ ಶುದ್ಧ ರೇಷ್ಮೆ\n• ಚಿನ್ನದ ಜರಿ ಕೆಲಸದೊಂದಿಗೆ ಶ್ರೀಮಂತ {color} ಬಣ್ಣ\n• ಸಾಂಪ್ರದಾಯಿಕ ದೇವಾಲಯ ಗಡಿಗಳು ಮತ್ತು ಪಲ್ಲು ವಿನ್ಯಾಸಗಳು\n• ಮದುವೆಗಳು, ಹಬ್ಬಗಳಿಗೆ ಪರಿಪೂರ್ಣ\n\n**ಸ್ಟೈಲಿಂಗ್:**\n• ಆಭರಣಗಳು: ಚಿನ್ನದ ದೇವಾಲಯ ಆಭರಣಗಳು, ಪುರಾತನ ಚಿನ್ನದ ಹಾರ, ಝುಮ್ಕಾಗಳು, ಚಿನ್ನದ ಬಳೆಗಳು\n• ಬ್ಲೌಸ್: ಚಿನ್ನ, ಕಾಂಟ್ರಾಸ್ಟ್ ಬಣ್ಣ, ಅಥವಾ ಹೊಂದಾಣಿಕೆ\n• ಮೇಕಪ್: ಸೀರೆಯೊಂದಿಗೆ ಹೊಂದಾಣಿಕೆಯ ಟೋನ್ಗಳು\n• ಹೇರ್: ಗಜ್ರಾದೊಂದಿಗೆ ಸಾಂಪ್ರದಾಯಿಕ ಬನ್\n\n**ಎಲ್ಲಿ ಖರೀದಿಸಬೇಕು:**\n• ನಲ್ಲಿ, ಪೋತೀಸ್, RMKV (ಚೆನ್ನೈ)\n• ತನೀರಾ, ಫ್ಯಾಬ್ಇಂಡಿಯಾ\n• ಬೆಲೆ: ₹5,000 - ₹50,000+\n\nನೀವು ಸಂಪೂರ್ಣವಾಗಿ ಅದ್ಭುತವಾಗಿ ಕಾಣುತ್ತೀರಿ! 👑"
            }
            # Update context with keywords
            if session_id not in conversation_context:
                conversation_context[session_id] = {}
            conversation_context[session_id]['last_intent'] = 'kanchipuram_saree'
            conversation_context[session_id]['keywords'] = context_data.get('keywords', []) + current_keywords
            conversation_context[session_id]['keywords'] = conversation_context[session_id]['keywords'][-MAX_KEYWORDS:]  # Keep last 50 keywords
            return responses.get(lang, responses['en'])
    
    # Store intent and keywords for next interaction
    if session_id not in conversation_context:
        conversation_context[session_id] = {}
    conversation_context[session_id]['last_intent'] = intent
    conversation_context[session_id]['last_query'] = query_lower
    # Accumulate keywords and find links
    prev_keywords = context_data.get('keywords', [])
    all_keywords = (prev_keywords + current_keywords)[-MAX_KEYWORDS:]  # Keep last 50 keywords (increased from 20)
    conversation_context[session_id]['keywords'] = all_keywords
    conversation_context[session_id]['keyword_links'] = find_keyword_links(current_keywords, prev_keywords)
    
    # Color styling advice for office
    if intent == 'color_styling_office':
        if 'red' in query_lower and ('black' in query_lower or 'red' in query_lower):
            responses = {
                'en': "**Red & Black Office Styling:** 🔴⚫✨\n\n**Great choice! Here's how to style it professionally:**\n\n**Option 1: Red Top + Black Bottom**\n• Red blouse/shirt with black trousers\n• Black blazer (optional for formal look)\n• Black heels or flats\n• Minimal gold or silver jewelry\n• Keep makeup subtle (nude lips, light eyes)\n\n**Option 2: Black Top + Red Bottom**\n• Black blouse with red trousers/skirt\n• Red should be deep/burgundy for office\n• Black accessories\n\n**Pro Tips:**\n• Choose muted/deep red (burgundy, maroon) over bright red\n• Keep one color dominant, other as accent\n• Avoid all-red outfit for office\n• Add neutral blazer if too bold\n\n**Accessories:** Black bag, watch, simple earrings\n\nPowerful and professional! 💼",
                'kn': "**ಕೆಂಪು & ಕಪ್ಪು ಆಫೀಸ್ ಸ್ಟೈಲಿಂಗ್:** 🔴⚫✨\n\n**ಉತ್ತಮ ಆಯ್ಕೆ! ಇದನ್ನು ವೃತ್ತಿಪರವಾಗಿ ಹೇಗೆ ಸ್ಟೈಲ್ ಮಾಡುವುದು:**\n\n**ಆಯ್ಕೆ 1: ಕೆಂಪು ಟಾಪ್ + ಕಪ್ಪು ಬಾಟಮ್**\n• ಕಪ್ಪು ಪ್ಯಾಂಟ್ಸ್ನೊಂದಿಗೆ ಕೆಂಪು ಬ್ಲೌಸ್/ಶರ್ಟ್\n• ಕಪ್ಪು ಬ್ಲೇಜರ್ (ಫಾರ್ಮಲ್ ಲುಕ್ಗಾಗಿ)\n• ಕಪ್ಪು ಹೀಲ್ಸ್ ಅಥವಾ ಫ್ಲಾಟ್ಸ್\n• ಮಿನಿಮಲ್ ಚಿನ್ನ ಅಥವಾ ಬೆಳ್ಳಿ ಆಭರಣಗಳು\n\n**ಆಯ್ಕೆ 2: ಕಪ್ಪು ಟಾಪ್ + ಕೆಂಪು ಬಾಟಮ್**\n• ಕೆಂಪು ಪ್ಯಾಂಟ್ಸ್/ಸ್ಕರ್ಟ್ನೊಂದಿಗೆ ಕಪ್ಪು ಬ್ಲೌಸ್\n• ಆಫೀಸ್ಗಾಗಿ ಡೀಪ್/ಬರ್ಗಂಡಿ ಕೆಂಪು\n\n**ಪ್ರೊ ಟಿಪ್ಸ್:**\n• ಪ್ರಕಾಶಮಾನ ಕೆಂಪಿಗಿಂತ ಮ್ಯೂಟೆಡ್/ಡೀಪ್ ಕೆಂಪು\n• ಒಂದು ಬಣ್ಣ ಪ್ರಧಾನ, ಇನ್ನೊಂದು ಆಕ್ಸೆಂಟ್\n\n**ಆಕ್ಸೆಸರೀಸ್:** ಕಪ್ಪು ಬ್ಯಾಗ್, ವಾಚ್\n\nಪವರ್ಫುಲ್ ಮತ್ತು ಪ್ರೊಫೆಷನಲ್! 💼"
            }
            return responses.get(lang, responses['en'])
    
    # Office/Work outfit queries
    if intent == 'men_office' or (any(word in query_lower for word in ['office', 'work', 'professional']) and any(word in query_lower for word in ['men', 'man', 'male', 'groom', 'guy'])):
        responses = {
            'en': "**Professional Office Look for Men:** 💼✨\n\n**Formal Office:**\n• Tailored suit (navy, charcoal, black)\n• Dress shirt (white, light blue, striped)\n• Formal trousers with belt\n• Tie (solid or subtle pattern)\n• Blazer with dress pants\n\n**Smart Casual:**\n• Chinos with button-down shirt\n• Blazer with jeans (dark wash)\n• Polo shirt with trousers\n• Oxford shoes or loafers\n\n**Footwear:** Oxford shoes, brogues, loafers, formal shoes\n**Accessories:** Watch, leather belt, tie, cufflinks, laptop bag\n**Grooming:** Clean shave or well-trimmed beard, neat haircut\n\n**Brands:** Van Heusen, Allen Solly, Peter England, Raymond, Louis Philippe\n\nSharp and professional!",
            'kn': "**ಪುರುಷರಿಗೆ ಪ್ರೊಫೆಷನಲ್ ಆಫೀಸ್ ಲುಕ್:** 💼✨\n\n**ಫಾರ್ಮಲ್ ಆಫೀಸ್:**\n• ಟೈಲರ್ಡ್ ಸೂಟ್ (ನೇವಿ, ಚಾರ್ಕೋಲ್, ಕಪ್ಪು)\n• ಡ್ರೆಸ್ ಶರ್ಟ್ (ಬಿಳಿ, ಹಗುರ ನೀಲಿ, ಸ್ಟ್ರೈಪ್ಡ್)\n• ಬೆಲ್ಟ್ನೊಂದಿಗೆ ಫಾರ್ಮಲ್ ಪ್ಯಾಂಟ್ಸ್\n• ಟೈ (ಸಾಲಿಡ್ ಅಥವಾ ಸಬ್ಟಲ್ ಪ್ಯಾಟರ್ನ್)\n• ಡ್ರೆಸ್ ಪ್ಯಾಂಟ್ಸ್ನೊಂದಿಗೆ ಬ್ಲೇಜರ್\n\n**ಸ್ಮಾರ್ಟ್ ಕ್ಯಾಶುಯಲ್:**\n• ಬಟನ್-ಡೌನ್ ಶರ್ಟ್ನೊಂದಿಗೆ ಚಿನೋಸ್\n• ಜೀನ್ಸ್ನೊಂದಿಗೆ ಬ್ಲೇಜರ್\n• ಪ್ಯಾಂಟ್ಸ್ನೊಂದಿಗೆ ಪೋಲೋ ಶರ್ಟ್\n• ಆಕ್ಸ್ಫರ್ಡ್ ಶೂಸ್ ಅಥವಾ ಲೋಫರ್ಸ್\n\n**ಪಾದರಕ್ಷೆ:** ಆಕ್ಸ್ಫರ್ಡ್ ಶೂಸ್, ಬ್ರೋಗ್ಸ್, ಲೋಫರ್ಸ್\n**ಆಕ್ಸೆಸರೀಸ್:** ವಾಚ್, ಲೆದರ್ ಬೆಲ್ಟ್, ಟೈ, ಕಫ್ಲಿಂಕ್ಸ್\n**ಗ್ರೂಮಿಂಗ್:** ಕ್ಲೀನ್ ಶೇವ್ ಅಥವಾ ಟ್ರಿಮ್ಡ್ ಬಿಯರ್ಡ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** Van Heusen, Allen Solly, Peter England, Raymond\n\nಶಾರ್ಪ್ ಮತ್ತು ಪ್ರೊಫೆಷನಲ್!"
        }
        return responses.get(lang, responses['en'])
    
    if any(word in query_lower for word in ['office', 'work', 'professional']):
        if any(word in query_lower for word in ['casual', 'smart casual']):
            responses = {
                'en': "**Smart Casual Office Look:** 💼✨\n\n**For Women:**\n• Well-fitted trousers or chinos with blouse\n• Midi skirt with tucked-in shirt\n• Blazer with jeans (dark wash)\n• Sheath dress with cardigan\n• Colors: Navy, black, grey, white, pastels\n\n**Footwear:** Loafers, ballet flats, low heels, ankle boots\n**Accessories:** Simple watch, small earrings, tote bag\n**Makeup:** Natural, professional (nude lips, light eyes)\n**Hair:** Neat bun, ponytail, or loose waves\n\n**Brands:** Zara, H&M, Marks & Spencer, Westside\n\nProfessional yet comfortable!",
                'kn': "**ಸ್ಮಾರ್ಟ್ ಕ್ಯಾಶುಯಲ್ ಆಫೀಸ್ ಲುಕ್:** 💼✨\n\n**ಮಹಿಳೆಯರಿಗೆ:**\n• ಬ್ಲೌಸ್ನೊಂದಿಗೆ ಚೆನ್ನಾಗಿ ಹೊಂದಿಕೊಂಡ ಪ್ಯಾಂಟ್ಸ್ ಅಥವಾ ಚಿನೋಸ್\n• ಶರ್ಟ್ನೊಂದಿಗೆ ಮಿಡಿ ಸ್ಕರ್ಟ್\n• ಜೀನ್ಸ್ನೊಂದಿಗೆ ಬ್ಲೇಜರ್ (ಡಾರ್ಕ್ ವಾಶ್)\n• ಕಾರ್ಡಿಗನ್ನೊಂದಿಗೆ ಶೀತ್ ಡ್ರೆಸ್\n• ಬಣ್ಣಗಳು: ನೇವಿ, ಕಪ್ಪು, ಬೂದು, ಬಿಳಿ, ಪೇಸ್ಟಲ್ಸ್\n\n**ಪಾದರಕ್ಷೆ:** ಲೋಫರ್ಸ್, ಬ್ಯಾಲೆ ಫ್ಲಾಟ್ಸ್, ಲೋ ಹೀಲ್ಸ್, ಆಂಕಲ್ ಬೂಟ್ಸ್\n**ಆಕ್ಸೆಸರೀಸ್:** ಸಿಂಪಲ್ ವಾಚ್, ಸ್ಮಾಲ್ ಇಯರ್ರಿಂಗ್ಸ್, ಟೋಟ್ ಬ್ಯಾಗ್\n**ಮೇಕಪ್:** ನ್ಯಾಚುರಲ್, ಪ್ರೊಫೆಷನಲ್ (ನ್ಯೂಡ್ ಲಿಪ್ಸ್, ಲೈಟ್ ಐಸ್)\n**ಹೇರ್:** ನೀಟ್ ಬನ್, ಪೋನಿಟೇಲ್, ಅಥವಾ ಲೂಸ್ ವೇವ್ಸ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** Zara, H&M, Marks & Spencer, Westside\n\nಪ್ರೊಫೆಷನಲ್ ಆದರೂ ಆರಾಮದಾಯಕ!"
            }
            return responses.get(lang, responses['en'])
        else:
            responses = {
                'en': "**Professional Office Look:** 💼✨\n\n**For Women:**\n• Tailored blazer with dress pants\n• Pencil skirt with button-down shirt\n• Formal sheath dress\n• Pantsuit (matching blazer & trousers)\n• Colors: Navy, black, grey, white, burgundy\n\n**Footwear:** Closed-toe heels, pumps, formal flats\n**Accessories:** Minimal jewelry (studs, simple watch), structured bag\n**Makeup:** Professional (nude/pink lips, subtle eyes)\n**Hair:** Neat bun, low ponytail, sleek straight\n\n**Brands:** Van Heusen, Allen Solly, Marks & Spencer\n\nConfident and professional!",
                'kn': "**ಪ್ರೊಫೆಷನಲ್ ಆಫೀಸ್ ಲುಕ್:** 💼✨\n\n**ಮಹಿಳೆಯರಿಗೆ:**\n• ಡ್ರೆಸ್ ಪ್ಯಾಂಟ್ಸ್ನೊಂದಿಗೆ ಟೈಲರ್ಡ್ ಬ್ಲೇಜರ್\n• ಬಟನ್-ಡೌನ್ ಶರ್ಟ್ನೊಂದಿಗೆ ಪೆನ್ಸಿಲ್ ಸ್ಕರ್ಟ್\n• ಫಾರ್ಮಲ್ ಶೀತ್ ಡ್ರೆಸ್\n• ಪ್ಯಾಂಟ್ಸೂಟ್ (ಮ್ಯಾಚಿಂಗ್ ಬ್ಲೇಜರ್ & ಟ್ರೌಸರ್ಸ್)\n• ಬಣ್ಣಗಳು: ನೇವಿ, ಕಪ್ಪು, ಬೂದು, ಬಿಳಿ, ಬರ್ಗಂಡಿ\n\n**ಪಾದರಕ್ಷೆ:** ಕ್ಲೋಸ್ಡ್-ಟೋ ಹೀಲ್ಸ್, ಪಂಪ್ಸ್, ಫಾರ್ಮಲ್ ಫ್ಲಾಟ್ಸ್\n**ಆಕ್ಸೆಸರೀಸ್:** ಮಿನಿಮಲ್ ಜ್ಯುವೆಲರಿ (ಸ್ಟಡ್ಸ್, ಸಿಂಪಲ್ ವಾಚ್), ಸ್ಟ್ರಕ್ಚರ್ಡ್ ಬ್ಯಾಗ್\n**ಮೇಕಪ್:** ಪ್ರೊಫೆಷನಲ್ (ನ್ಯೂಡ್/ಪಿಂಕ್ ಲಿಪ್ಸ್, ಸಬ್ಟಲ್ ಐಸ್)\n**ಹೇರ್:** ನೀಟ್ ಬನ್, ಲೋ ಪೋನಿಟೇಲ್, ಸ್ಲೀಕ್ ಸ್ಟ್ರೈಟ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** Van Heusen, Allen Solly, Marks & Spencer\n\nಆತ್ಮವಿಶ್ವಾಸ ಮತ್ತು ಪ್ರೊಫೆಷನಲ್!"
            }
            return responses.get(lang, responses['en'])
    
    # Casual wear queries
    if 'casual' in query_lower and 'wear' in query_lower:
        responses = {
            'en': "**Casual Wear Guide:** 👕✨\n\n**For Women:**\n• Jeans with stylish top/t-shirt\n• Casual dress or maxi dress\n• Shorts with tank top (summer)\n• Leggings with long tunic\n• Denim jacket or cardigan\n\n**Footwear:** Sneakers, flats, sandals, ankle boots\n**Accessories:** Crossbody bag, sunglasses, simple jewelry\n**Makeup:** Natural, minimal (tinted lip balm, mascara)\n**Hair:** Loose, ponytail, messy bun\n\n**Brands:** Zara, H&M, Forever 21, Westside\n\nComfortable and stylish!",
            'kn': "**ಕ್ಯಾಶುಯಲ್ ವೇರ್ ಗೈಡ್:** 👕✨\n\n**ಮಹಿಳೆಯರಿಗೆ:**\n• ಸ್ಟೈಲಿಶ್ ಟಾಪ್/ಟಿ-ಶರ್ಟ್ನೊಂದಿಗೆ ಜೀನ್ಸ್\n• ಕ್ಯಾಶುಯಲ್ ಡ್ರೆಸ್ ಅಥವಾ ಮ್ಯಾಕ್ಸಿ ಡ್ರೆಸ್\n• ಟ್ಯಾಂಕ್ ಟಾಪ್ನೊಂದಿಗೆ ಶಾರ್ಟ್ಸ್ (ಬೇಸಿಗೆ)\n• ಲಾಂಗ್ ಟ್ಯೂನಿಕ್ನೊಂದಿಗೆ ಲೆಗ್ಗಿಂಗ್ಸ್\n• ಡೆನಿಮ್ ಜಾಕೆಟ್ ಅಥವಾ ಕಾರ್ಡಿಗನ್\n\n**ಪಾದರಕ್ಷೆ:** ಸ್ನೀಕರ್ಸ್, ಫ್ಲಾಟ್ಸ್, ಸ್ಯಾಂಡಲ್ಸ್, ಆಂಕಲ್ ಬೂಟ್ಸ್\n**ಆಕ್ಸೆಸರೀಸ್:** ಕ್ರಾಸ್ಬಾಡಿ ಬ್ಯಾಗ್, ಸನ್ಗ್ಲಾಸ್, ಸಿಂಪಲ್ ಜ್ಯುವೆಲರಿ\n**ಮೇಕಪ್:** ನ್ಯಾಚುರಲ್, ಮಿನಿಮಲ್ (ಟಿಂಟೆಡ್ ಲಿಪ್ ಬಾಮ್, ಮಸ್ಕಾರಾ)\n**ಹೇರ್:** ಲೂಸ್, ಪೋನಿಟೇಲ್, ಮೆಸ್ಸಿ ಬನ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** Zara, H&M, Forever 21, Westside\n\nಆರಾಮದಾಯಕ ಮತ್ತು ಸ್ಟೈಲಿಶ್!"
        }
        return responses.get(lang, responses['en'])
    
    # Men's party outfit queries
    if intent == 'men_party' or (intent == 'party' and any(word in query_lower for word in ['men', 'man', 'male', 'guy'])):
        responses = {
            'en': "**Party Outfit Ideas for Men:** 🎉✨\n\n**Casual Party:**\n• Fitted shirt with chinos\n• Polo shirt with jeans\n• Casual blazer with t-shirt and jeans\n• Henley shirt with trousers\n\n**Formal Party:**\n• Suit without tie (open collar)\n• Blazer with dress shirt and trousers\n• Waistcoat with dress pants\n• Tuxedo (for black-tie events)\n\n**Footwear:** Loafers, brogues, Chelsea boots, dress shoes\n**Accessories:** Watch, leather bracelet, sunglasses, cologne\n**Grooming:** Styled hair, trimmed beard, fresh look\n\n**Colors:** Navy, black, grey, burgundy, white\n**Brands:** Zara, H&M, Jack & Jones, Levi's\n\nBe the life of the party! 🎊",
            'kn': "**ಪುರುಷರಿಗೆ ಪಾರ್ಟಿ ಉಡುಪು ಐಡಿಯಾಗಳು:** 🎉✨\n\n**ಕ್ಯಾಶುಯಲ್ ಪಾರ್ಟಿ:**\n• ಚಿನೋಸ್ನೊಂದಿಗೆ ಫಿಟ್ಟೆಡ್ ಶರ್ಟ್\n• ಜೀನ್ಸ್ನೊಂದಿಗೆ ಪೋಲೋ ಶರ್ಟ್\n• ಟಿ-ಶರ್ಟ್ ಮತ್ತು ಜೀನ್ಸ್ನೊಂದಿಗೆ ಕ್ಯಾಶುಯಲ್ ಬ್ಲೇಜರ್\n• ಪ್ಯಾಂಟ್ಸ್ನೊಂದಿಗೆ ಹೆನ್ಲಿ ಶರ್ಟ್\n\n**ಫಾರ್ಮಲ್ ಪಾರ್ಟಿ:**\n• ಟೈ ಇಲ್ಲದೆ ಸೂಟ್ (ಓಪನ್ ಕಾಲರ್)\n• ಡ್ರೆಸ್ ಶರ್ಟ್ ಮತ್ತು ಪ್ಯಾಂಟ್ಸ್ನೊಂದಿಗೆ ಬ್ಲೇಜರ್\n• ಡ್ರೆಸ್ ಪ್ಯಾಂಟ್ಸ್ನೊಂದಿಗೆ ವೇಸ್ಟ್ಕೋಟ್\n• ಟಕ್ಸೆಡೋ (ಬ್ಲ್ಯಾಕ್-ಟೈ ಈವೆಂಟ್ಸ್ಗೆ)\n\n**ಪಾದರಕ್ಷೆ:** ಲೋಫರ್ಸ್, ಬ್ರೋಗ್ಸ್, ಚೆಲ್ಸಿಯಾ ಬೂಟ್ಸ್\n**ಆಕ್ಸೆಸರೀಸ್:** ವಾಚ್, ಲೆದರ್ ಬ್ರೇಸ್ಲೆಟ್, ಸನ್ಗ್ಲಾಸ್\n**ಗ್ರೂಮಿಂಗ್:** ಸ್ಟೈಲ್ಡ್ ಹೇರ್, ಟ್ರಿಮ್ಡ್ ಬಿಯರ್ಡ್\n\n**ಬಣ್ಣಗಳು:** ನೇವಿ, ಕಪ್ಪು, ಬೂದು, ಬರ್ಗಂಡಿ, ಬಿಳಿ\n**ಬ್ರಾಂಡ್ಗಳು:** Zara, H&M, Jack & Jones, Levi's\n\nಪಾರ್ಟಿಯ ಲೈಫ್ ಆಗಿರಿ! 🎊"
        }
        return responses.get(lang, responses['en'])
    
    # Party outfit queries
    if any(word in query_lower for word in ['party', 'event', 'celebration']):
        responses = {
            'en': "**Party Outfit Ideas:** 💃✨\n\n**For Women:**\n• Statement dress (sequined, silk, velvet)\n• Chic jumpsuit or palazzo set\n• Crop top with high-waisted skirt\n• Indo-western fusion outfit\n• Colors: Jewel tones, metallics, black\n\n**Styling:**\n• Heels: Strappy or platform (4-5 inches)\n• Jewelry: Bold earrings, statement necklace\n• Clutch: Metallic or embellished\n• Makeup: Smoky eyes or bold lips, highlighter\n\n**Brands:** Zara, H&M, FabIndia, Biba\n\nYou'll be the star of the party!",
            'kn': "**ಪಾರ್ಟಿ ಉಡುಪು ಐಡಿಯಾಗಳು:** 💃✨\n\n**ಮಹಿಳೆಯರಿಗೆ:**\n• ಸ್ಟೇಟ್ಮೆಂಟ್ ಡ್ರೆಸ್ (ಸೀಕ್ವಿನ್ಡ್, ಸಿಲ್ಕ್, ವೆಲ್ವೆಟ್)\n• ಶಿಕ್ ಜಂಪ್ಸೂಟ್ ಅಥವಾ ಪಲಾಝೊ ಸೆಟ್\n• ಕ್ರಾಪ್ ಟಾಪ್ ವಿತ್ ಹೈ-ವೇಸ್ಟೆಡ್ ಸ್ಕರ್ಟ್\n• ಇಂಡೋ-ವೆಸ್ಟರ್ನ್ ಫ್ಯೂಷನ್ ಉಡುಪು\n• ಬಣ್ಣಗಳು: ಜ್ಯುವೆಲ್ ಟೋನ್ಸ್, ಮೆಟಾಲಿಕ್ಸ್, ಕಪ್ಪು\n\n**ಸ್ಟೈಲಿಂಗ್:**\n• ಹೀಲ್ಸ್: ಸ್ಟ್ರಾಪಿ ಅಥವಾ ಪ್ಲಾಟ್ಫಾರ್ಮ್\n• ಆಭರಣಗಳು: ಬೋಲ್ಡ್ ಇಯರ್ರಿಂಗ್ಸ್, ಸ್ಟೇಟ್ಮೆಂಟ್ ನೆಕ್ಲೇಸ್\n• ಕ್ಲಚ್: ಮೆಟಾಲಿಕ್ ಅಥವಾ ಎಂಬೆಲಿಶ್ಡ್\n• ಮೇಕಪ್: ಸ್ಮೋಕಿ ಐಸ್ ಅಥವಾ ಬೋಲ್ಡ್ ಲಿಪ್ಸ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** Zara, H&M, FabIndia, Biba\n\nನೀವು ಪಾರ್ಟಿಯ ಸ್ಟಾರ್ ಆಗುತ್ತೀರಿ!"
        }
        return responses.get(lang, responses['en'])
    
    # Festival outfit queries
    if intent == 'festival' or any(word in query_lower for word in ['festival', 'festive', 'ಹಬ್ಬ', 'ಉತ್ಸವ']):
        responses = {
            'en': "**Festival Outfit Ideas:** 🎊✨\n\n**For Women:**\n• Silk saree (traditional festivals)\n• Lehenga or half-saree\n• Anarkali suit or salwar kameez\n• Kurti with palazzo or churidar\n• Colors: Bright colors, gold, red, green, yellow\n\n**For Men:**\n• Kurta pajama (cotton or silk)\n• Dhoti with kurta\n• Nehru jacket with kurta\n• Pathani suit\n• Colors: White, cream, gold, maroon\n\n**Accessories:**\n• Women: Traditional jewelry, bangles, bindi, flowers in hair\n• Men: Mojari, watch, stole\n\n**Makeup (Women):** Traditional, colorful, festive look\n\n**Brands:** FabIndia, Biba, Manyavar, Soch, W\n\nCelebrate in style! 🪔✨",
            'kn': "**ಹಬ್ಬದ ಉಡುಪು ಐಡಿಯಾಗಳು:** 🎊✨\n\n**ಮಹಿಳೆಯರಿಗೆ:**\n• ರೇಷ್ಮೆ ಸೀರೆ (ಸಾಂಪ್ರದಾಯಿಕ ಹಬ್ಬಗಳು)\n• ಲೆಹೆಂಗಾ ಅಥವಾ ಹಾಫ್-ಸೀರೆ\n• ಅನಾರ್ಕಲಿ ಸೂಟ್ ಅಥವಾ ಸಲ್ವಾರ್ ಕಮೀಜ್\n• ಪಲಾಝೊ ಅಥವಾ ಚುರಿದಾರ್ನೊಂದಿಗೆ ಕುರ್ತಿ\n• ಬಣ್ಣಗಳು: ಪ್ರಕಾಶಮಾನ ಬಣ್ಣಗಳು, ಚಿನ್ನ, ಕೆಂಪು, ಹಸಿರು, ಹಳದಿ\n\n**ಪುರುಷರಿಗೆ:**\n• ಕುರ್ತಾ ಪಜಾಮಾ (ಹತ್ತಿ ಅಥವಾ ರೇಷ್ಮೆ)\n• ಕುರ್ತಾದೊಂದಿಗೆ ಧೋತಿ\n• ಕುರ್ತಾದೊಂದಿಗೆ ನೆಹರೂ ಜಾಕೆಟ್\n• ಪಠಾಣಿ ಸೂಟ್\n• ಬಣ್ಣಗಳು: ಬಿಳಿ, ಕ್ರೀಮ್, ಚಿನ್ನ, ಮರೂನ್\n\n**ಆಕ್ಸೆಸರೀಸ್:**\n• ಮಹಿಳೆಯರು: ಸಾಂಪ್ರದಾಯಿಕ ಆಭರಣಗಳು, ಬಳೆಗಳು, ಬಿಂದಿ, ಕೂದಲಿನಲ್ಲಿ ಹೂವುಗಳು\n• ಪುರುಷರು: ಮೊಜರಿ, ವಾಚ್, ಸ್ಟೋಲ್\n\n**ಮೇಕಪ್ (ಮಹಿಳೆಯರು):** ಸಾಂಪ್ರದಾಯಿಕ, ವರ್ಣರಂಜಿತ, ಹಬ್ಬದ ಲುಕ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** FabIndia, Biba, Manyavar, Soch, W\n\nಸ್ಟೈಲ್ನಲ್ಲಿ ಆಚರಿಸಿ! 🪔✨"
        }
        return responses.get(lang, responses['en'])
    
    # Vacation outfit queries
    if intent == 'vacation' or any(word in query_lower for word in ['vacation', 'holiday', 'travel', 'trip', 'beach', 'resort']):
        responses = {
            'en': "**Vacation Outfit Ideas:** ✈️🏖️✨\n\n**For Women:**\n• Maxi dresses or sundresses\n• Shorts with tank tops/t-shirts\n• Swimwear with cover-ups\n• Comfortable rompers or jumpsuits\n• Light cardigan or denim jacket\n• Colors: Bright, tropical, pastels\n\n**For Men:**\n• Casual shorts with polo/t-shirts\n• Linen shirts with chinos\n• Swim trunks with casual shirts\n• Comfortable joggers\n• Light jacket or hoodie\n• Colors: Neutrals, blues, whites\n\n**Footwear:**\n• Women: Sandals, flip-flops, sneakers, espadrilles\n• Men: Sneakers, loafers, flip-flops, boat shoes\n\n**Accessories:**\n• Sunglasses, sun hat, beach bag\n• Sunscreen, light scarf\n• Crossbody bag or backpack\n\n**Pro Tips:**\n• Pack light, breathable fabrics\n• Bring layers for evening\n• Comfortable walking shoes essential\n\n**Brands:** Zara, H&M, Uniqlo, Gap, Old Navy\n\nEnjoy your vacation! 🌴☀️",
            'kn': "**ರಜೆಯ ಉಡುಪು ಐಡಿಯಾಗಳು:** ✈️🏖️✨\n\n**ಮಹಿಳೆಯರಿಗೆ:**\n• ಮ್ಯಾಕ್ಸಿ ಡ್ರೆಸ್ಸೆಸ್ ಅಥವಾ ಸನ್ಡ್ರೆಸ್ಸೆಸ್\n• ಟ್ಯಾಂಕ್ ಟಾಪ್ಸ್/ಟಿ-ಶರ್ಟ್ಸ್ನೊಂದಿಗೆ ಶಾರ್ಟ್ಸ್\n• ಕವರ್-ಅಪ್ಸ್ನೊಂದಿಗೆ ಸ್ವಿಮ್ವೇರ್\n• ಆರಾಮದಾಯಕ ರೋಂಪರ್ಸ್ ಅಥವಾ ಜಂಪ್ಸೂಟ್ಸ್\n• ಲೈಟ್ ಕಾರ್ಡಿಗನ್ ಅಥವಾ ಡೆನಿಮ್ ಜಾಕೆಟ್\n• ಬಣ್ಣಗಳು: ಪ್ರಕಾಶಮಾನ, ಟ್ರಾಪಿಕಲ್, ಪೇಸ್ಟಲ್ಸ್\n\n**ಪುರುಷರಿಗೆ:**\n• ಪೋಲೋ/ಟಿ-ಶರ್ಟ್ಸ್ನೊಂದಿಗೆ ಕ್ಯಾಶುಯಲ್ ಶಾರ್ಟ್ಸ್\n• ಚಿನೋಸ್ನೊಂದಿಗೆ ಲಿನೆನ್ ಶರ್ಟ್ಸ್\n• ಕ್ಯಾಶುಯಲ್ ಶರ್ಟ್ಸ್ನೊಂದಿಗೆ ಸ್ವಿಮ್ ಟ್ರಂಕ್ಸ್\n• ಆರಾಮದಾಯಕ ಜಾಗರ್ಸ್\n• ಲೈಟ್ ಜಾಕೆಟ್ ಅಥವಾ ಹೂಡಿ\n• ಬಣ್ಣಗಳು: ನ್ಯೂಟ್ರಲ್ಸ್, ಬ್ಲೂಸ್, ವೈಟ್ಸ್\n\n**ಪಾದರಕ್ಷೆ:**\n• ಮಹಿಳೆಯರು: ಸ್ಯಾಂಡಲ್ಸ್, ಫ್ಲಿಪ್-ಫ್ಲಾಪ್ಸ್, ಸ್ನೀಕರ್ಸ್\n• ಪುರುಷರು: ಸ್ನೀಕರ್ಸ್, ಲೋಫರ್ಸ್, ಫ್ಲಿಪ್-ಫ್ಲಾಪ್ಸ್\n\n**ಆಕ್ಸೆಸರೀಸ್:**\n• ಸನ್ಗ್ಲಾಸ್, ಸನ್ ಹ್ಯಾಟ್, ಬೀಚ್ ಬ್ಯಾಗ್\n• ಸನ್ಸ್ಕ್ರೀನ್, ಲೈಟ್ ಸ್ಕಾರ್ಫ್\n• ಕ್ರಾಸ್ಬಾಡಿ ಬ್ಯಾಗ್ ಅಥವಾ ಬ್ಯಾಕ್ಪ್ಯಾಕ್\n\n**ಪ್ರೊ ಟಿಪ್ಸ್:**\n• ಲೈಟ್, ಉಸಿರಾಡುವ ಬಟ್ಟೆಗಳನ್ನು ಪ್ಯಾಕ್ ಮಾಡಿ\n• ಸಂಜೆಗೆ ಲೇಯರ್ಸ್ ತನ್ನಿ\n• ಆರಾಮದಾಯಕ ವಾಕಿಂಗ್ ಶೂಸ್ ಅತ್ಯಗತ್ಯ\n\n**ಬ್ರಾಂಡ್ಗಳು:** Zara, H&M, Uniqlo, Gap, Old Navy\n\nನಿಮ್ಮ ರಜೆಯನ್ನು ಆನಂದಿಸಿ! 🌴☀️"
        }
        return responses.get(lang, responses['en'])
    
    # Kanchipuram saree queries
    if intent == 'kanchipuram_saree' or any(word in query_lower for word in ['kanchipuram', 'kanchi', 'kanjivaram']):
        conversation_context[session_id]['last_intent'] = 'kanchipuram_saree'
        if 'red' in query_lower or 'ಕೆಂಪು' in query_lower:
            responses = {
                'en': "**Red Kanchipuram Saree - Stunning Choice!** 🔴✨\n\n**About:**\n• Pure silk from Kanchipuram, Tamil Nadu\n• Rich texture, vibrant red color, gold zari work\n• Traditional temple borders and pallu designs\n• Perfect for weddings, festivals\n\n**Styling:**\n• Jewelry: Gold temple jewelry, antique gold necklace, jhumkas, gold bangles (6-8)\n• Blouse: Gold, green, or maroon contrast\n• Makeup: Bold red/maroon lips, winged eyeliner, bindi, gajra\n\n**Where to Buy:**\n• Nalli, Pothys, RMKV (Chennai)\n• Taneira, FabIndia\n• Price: ₹5,000 - ₹50,000+\n\nYou'll look absolutely regal! 👑",
                'kn': "**ಕೆಂಪು ಕಾಂಚೀಪುರಂ ಸೀರೆ - ಅದ್ಭುತ ಆಯ್ಕೆ!** 🔴✨\n\n**ಬಗ್ಗೆ:**\n• ಕಾಂಚೀಪುರಂ, ತಮಿಳುನಾಡಿನಿಂದ ಶುದ್ಧ ರೇಷ್ಮೆ\n• ಶ್ರೀಮಂತ ವಿನ್ಯಾಸ, ಉತ್ಸಾಹಭರಿತ ಕೆಂಪು ಬಣ್ಣ, ಚಿನ್ನದ ಜರಿ ಕೆಲಸ\n• ಸಾಂಪ್ರದಾಯಿಕ ದೇವಾಲಯ ಗಡಿಗಳು ಮತ್ತು ಪಲ್ಲು ವಿನ್ಯಾಸಗಳು\n• ಮದುವೆಗಳು, ಹಬ್ಬಗಳಿಗೆ ಪರಿಪೂರ್ಣ\n\n**ಸ್ಟೈಲಿಂಗ್:**\n• ಆಭರಣಗಳು: ಚಿನ್ನದ ದೇವಾಲಯ ಆಭರಣಗಳು, ಪುರಾತನ ಚಿನ್ನದ ಹಾರ, ಝುಮ್ಕಾಗಳು, ಚಿನ್ನದ ಬಳೆಗಳು (6-8)\n• ಬ್ಲೌಸ್: ಚಿನ್ನ, ಹಸಿರು, ಅಥವಾ ಮರೂನ್ ಕಾಂಟ್ರಾಸ್ಟ್\n• ಮೇಕಪ್: ಬೋಲ್ಡ್ ಕೆಂಪು/ಮರೂನ್ ತುಟಿಗಳು, ವಿಂಗ್ಡ್ ಐಲೈನರ್, ಬಿಂದಿ, ಗಜ್ರಾ\n\n**ಎಲ್ಲಿ ಖರೀದಿಸಬೇಕು:**\n• ನಲ್ಲಿ, ಪೋತೀಸ್, RMKV (ಚೆನ್ನೈ)\n• ತನೀರಾ, ಫ್ಯಾಬ್ಇಂಡಿಯಾ\n• ಬೆಲೆ: ₹5,000 - ₹50,000+\n\nನೀವು ಸಂಪೂರ್ಣವಾಗಿ ರಾಜಮನೆತನದಂತೆ ಕಾಣುತ್ತೀರಿ! 👑"
            }
            return responses.get(lang, responses['en'])
        else:
            responses = {
                'en': "**Kanchipuram Saree - The Queen of Silk!** 👑✨\n\n**About:**\n• Handwoven pure silk from Kanchipuram\n• 400+ year old tradition\n• Known for durability, rich colors, heavy zari borders\n• Traditional motifs: peacocks, parrots, temples\n\n**Popular Colors:**\n• Red, maroon, green, blue, purple, gold\n• Contrast borders (e.g., red with green border)\n\n**Styling Tips:**\n• Pair with gold temple jewelry\n• Traditional blouse with zari work\n• Gajra in hair, bold makeup\n\n**Top Brands:** Nalli, Pothys, RMKV, Chennai Silks\n**Price:** ₹5,000 - ₹50,000+\n\nA timeless investment!",
                'kn': "**ಕಾಂಚೀಪುರಂ ಸೀರೆ - ರೇಷ್ಮೆಯ ರಾಣಿ!** 👑✨\n\n**ಬಗ್ಗೆ:**\n• ಕಾಂಚೀಪುರಂದಿಂದ ಕೈಯಿಂದ ನೇಯ್ದ ಶುದ್ಧ ರೇಷ್ಮೆ\n• 400+ ವರ್ಷಗಳ ಹಳೆಯ ಸಂಪ್ರದಾಯ\n• ಬಾಳಿಕೆ, ಶ್ರೀಮಂತ ಬಣ್ಣಗಳು, ಭಾರೀ ಜರಿ ಗಡಿಗಳಿಗೆ ಹೆಸರುವಾಸಿ\n• ಸಾಂಪ್ರದಾಯಿಕ ಮೋಟಿಫ್ಗಳು: ನವಿಲುಗಳು, ಗಿಳಿಗಳು, ದೇವಾಲಯಗಳು\n\n**ಜನಪ್ರಿಯ ಬಣ್ಣಗಳು:**\n• ಕೆಂಪು, ಮರೂನ್, ಹಸಿರು, ನೀಲಿ, ನೇರಳೆ, ಚಿನ್ನ\n• ಕಾಂಟ್ರಾಸ್ಟ್ ಗಡಿಗಳು\n\n**ಸ್ಟೈಲಿಂಗ್ ಸಲಹೆಗಳು:**\n• ಚಿನ್ನದ ದೇವಾಲಯ ಆಭರಣಗಳೊಂದಿಗೆ ಜೋಡಿಸಿ\n• ಜರಿ ಕೆಲಸದೊಂದಿಗೆ ಸಾಂಪ್ರದಾಯಿಕ ಬ್ಲೌಸ್\n• ಕೂದಲಿನಲ್ಲಿ ಗಜ್ರಾ, ಬೋಲ್ಡ್ ಮೇಕಪ್\n\n**ಟಾಪ್ ಬ್ರಾಂಡ್ಗಳು:** ನಲ್ಲಿ, ಪೋತೀಸ್, RMKV, ಚೆನ್ನೈ ಸಿಲ್ಕ್ಸ್\n**ಬೆಲೆ:** ₹5,000 - ₹50,000+\n\nಕಾಲಾತೀತ ಹೂಡಿಕೆ!"
            }
            return responses.get(lang, responses['en'])
    
    # Saree queries
    if 'saree' in query_lower or 'ಸೀರೆ' in query_lower:
        conversation_context[session_id]['last_intent'] = 'saree'
        responses = {
            'en': "**Saree Styling Guide:**\n\n**Popular Types:**\n• Silk: Kanchipuram, Banarasi (weddings, festivals)\n• Georgette: Flowy, party wear\n• Chiffon: Lightweight, elegant\n• Cotton: Casual, comfortable\n\n**Styling Tips:**\n• Match jewelry with saree style\n• Contrast or matching blouse\n• Appropriate footwear (heels for parties)\n\n**Occasions:**\n• Wedding: Silk, heavy embroidery\n• Party: Georgette, sequins\n• Festival: Traditional silk\n\n**Brands:** Nalli, Pothys, FabIndia, Taneira\n\nWhat color interests you?",
            'kn': "**ಸೀರೆ ಸ್ಟೈಲಿಂಗ್ ಮಾರ್ಗದರ್ಶಿ:**\n\n**ಜನಪ್ರಿಯ ಪ್ರಕಾರಗಳು:**\n• ರೇಷ್ಮೆ: ಕಾಂಚೀಪುರಂ, ಬನಾರಸಿ (ಮದುವೆಗಳು, ಹಬ್ಬಗಳು)\n• ಜಾರ್ಜೆಟ್: ಹರಿಯುವ, ಪಾರ್ಟಿ ವೇರ್\n• ಶಿಫಾನ್: ಹಗುರ, ಸೊಗಸಾದ\n• ಹತ್ತಿ: ಕ್ಯಾಶುಯಲ್, ಆರಾಮದಾಯಕ\n\n**ಸ್ಟೈಲಿಂಗ್ ಸಲಹೆಗಳು:**\n• ಸೀರೆ ಶೈಲಿಯೊಂದಿಗೆ ಆಭರಣಗಳನ್ನು ಹೊಂದಿಸಿ\n• ಕಾಂಟ್ರಾಸ್ಟ್ ಅಥವಾ ಹೊಂದಾಣಿಕೆಯ ಬ್ಲೌಸ್\n• ಸೂಕ್ತ ಪಾದರಕ್ಷೆ (ಪಾರ್ಟಿಗಳಿಗೆ ಹೀಲ್ಸ್)\n\n**ಸಂದರ್ಭಗಳು:**\n• ಮದುವೆ: ರೇಷ್ಮೆ, ಭಾರೀ ಕಸೂತಿ\n• ಪಾರ್ಟಿ: ಜಾರ್ಜೆಟ್, ಸೀಕ್ವಿನ್ಸ್\n• ಹಬ್ಬ: ಸಾಂಪ್ರದಾಯಿಕ ರೇಷ್ಮೆ\n\n**ಬ್ರಾಂಡ್ಗಳು:** ನಲ್ಲಿ, ಪೋತೀಸ್, ಫ್ಯಾಬ್ಇಂಡಿಯಾ, ತನೀರಾ\n\nಯಾವ ಬಣ್ಣ ನಿಮಗೆ ಆಸಕ್ತಿ?"
        }
        return responses.get(lang, responses['en'])
    
    # Handle based on intent
    if intent == 'wedding_makeup' or (intent.endswith('_continue') and 'makeup' in context_data.get('last_intent', '')):
        if any(word in query_lower for word in ['wedding', 'bridal', 'traditional', 'settled', 'ಮದುವೆ']):
            responses = {
                'en': "**Traditional Wedding Makeup Guide:** 💄✨\n\n**Base:**\n• Primer for long-lasting makeup\n• Full-coverage foundation (match skin tone)\n• Concealer for dark circles\n• Setting powder (translucent)\n• Contour & highlight for definition\n\n**Eyes:**\n• Bold eyeshadow (gold, bronze, maroon)\n• Winged eyeliner (black/brown)\n• False lashes or mascara (2-3 coats)\n• Kajal on waterline\n• Fill & define eyebrows\n\n**Lips:**\n• Red, maroon, or pink lipstick\n• Lip liner to prevent bleeding\n• Gloss for shine (optional)\n\n**Finishing:**\n• Blush (peach/pink)\n• Bindi (traditional)\n• Setting spray for 12+ hour wear\n\n**Brands:** MAC, Huda Beauty, Lakme, Maybelline\n\nYou'll look absolutely stunning! 👰✨",
                'kn': "**ಸಾಂಪ್ರದಾಯಿಕ ಮದುವೆಯ ಮೇಕಪ್ ಮಾರ್ಗದರ್ಶಿ:** 💄✨\n\n**ಬೇಸ್:**\n• ದೀರ್ಘಕಾಲೀನ ಮೇಕಪ್ಗಾಗಿ ಪ್ರೈಮರ್\n• ಫುಲ್-ಕವರೇಜ್ ಫೌಂಡೇಶನ್\n• ಡಾರ್ಕ್ ಸರ್ಕಲ್ಸ್ಗಾಗಿ ಕನ್ಸೀಲರ್\n• ಸೆಟ್ಟಿಂಗ್ ಪೌಡರ್\n• ಕಾಂಟೂರ್ & ಹೈಲೈಟ್\n\n**ಕಣ್ಣುಗಳು:**\n• ಬೋಲ್ಡ್ ಐಶಾಡೋ (ಚಿನ್ನ, ಕಂಚು, ಮರೂನ್)\n• ವಿಂಗ್ಡ್ ಐಲೈನರ್\n• ಫಾಲ್ಸ್ ಲ್ಯಾಶಸ್ ಅಥವಾ ಮಸ್ಕಾರಾ\n• ವಾಟರ್ಲೈನ್ನಲ್ಲಿ ಕಾಜಲ್\n• ಹುಬ್ಬುಗಳನ್ನು ತುಂಬಿಸಿ\n\n**ತುಟಿಗಳು:**\n• ಕೆಂಪು, ಮರೂನ್, ಅಥವಾ ಗುಲಾಬಿ ಲಿಪ್ಸ್ಟಿಕ್\n• ಲಿಪ್ ಲೈನರ್\n• ಹೊಳಪಿಗಾಗಿ ಗ್ಲಾಸ್\n\n**ಫಿನಿಶಿಂಗ್:**\n• ಬ್ಲಶ್ (ಪೀಚ್/ಪಿಂಕ್)\n• ಬಿಂದಿ (ಸಾಂಪ್ರದಾಯಿಕ)\n• ಸೆಟ್ಟಿಂಗ್ ಸ್ಪ್ರೇ\n\n**ಬ್ರಾಂಡ್ಗಳು:** MAC, Huda Beauty, Lakme, Maybelline\n\nನೀವು ಸಂಪೂರ್ಣವಾಗಿ ಅದ್ಭುತವಾಗಿ ಕಾಣುತ್ತೀರಿ! 👰✨"
            }
            return responses.get(lang, responses['en'])
        elif any(word in query_lower for word in ['party', 'evening', 'night']):
            responses = {
                'en': "**Party Makeup Guide:** 💃✨\n\n**Base:**\n• Primer + full-coverage foundation\n• Concealer & setting powder\n• Heavy contour & highlight\n\n**Eyes:**\n• Smoky eyes (black, grey, purple)\n• Glitter eyeshadow\n• Dramatic winged liner\n• False lashes\n\n**Lips:**\n• Bold red or nude lips\n• Matte or glossy finish\n\n**Finishing:**\n• Blush & bronzer\n• Setting spray\n\n**Brands:** Urban Decay, NYX, MAC\n\nGlamorous and party-ready!",
                'kn': "**ಪಾರ್ಟಿ ಮೇಕಪ್ ಮಾರ್ಗದರ್ಶಿ:** 💃✨\n\n**ಬೇಸ್:**\n• ಪ್ರೈಮರ್ + ಫುಲ್-ಕವರೇಜ್ ಫೌಂಡೇಶನ್\n• ಕನ್ಸೀಲರ್ & ಸೆಟ್ಟಿಂಗ್ ಪೌಡರ್\n• ಹೆವಿ ಕಾಂಟೂರ್ & ಹೈಲೈಟ್\n\n**ಕಣ್ಣುಗಳು:**\n• ಸ್ಮೋಕಿ ಐಸ್\n• ಗ್ಲಿಟ್ಟರ್ ಐಶಾಡೋ\n• ಡ್ರಾಮಾಟಿಕ್ ವಿಂಗ್ಡ್ ಲೈನರ್\n• ಫಾಲ್ಸ್ ಲ್ಯಾಶಸ್\n\n**ತುಟಿಗಳು:**\n• ಬೋಲ್ಡ್ ಕೆಂಪು ಅಥವಾ ನ್ಯೂಡ್ ತುಟಿಗಳು\n• ಮ್ಯಾಟ್ ಅಥವಾ ಗ್ಲಾಸಿ ಫಿನಿಶ್\n\n**ಫಿನಿಶಿಂಗ್:**\n• ಬ್ಲಶ್ & ಬ್ರಾಂಜರ್\n• ಸೆಟ್ಟಿಂಗ್ ಸ್ಪ್ರೇ\n\n**ಬ್ರಾಂಡ್ಗಳು:** Urban Decay, NYX, MAC\n\nಗ್ಲಾಮರಸ್ ಮತ್ತು ಪಾರ್ಟಿ-ರೆಡಿ!"
            }
            return responses.get(lang, responses['en'])
        else:
            responses = {
                'en': "**Everyday Makeup Guide:** 💄\n\n**Base:**\n• Moisturizer + primer\n• Light/medium coverage foundation\n• Concealer for blemishes\n• Loose powder\n\n**Eyes:**\n• Neutral eyeshadow (brown, beige)\n• Light eyeliner\n• Mascara (1-2 coats)\n• Fill eyebrows naturally\n\n**Lips:**\n• Nude, pink, or coral lipstick\n• Tinted lip balm\n\n**Finishing:**\n• Light blush\n• Optional: light highlighter\n\n**Brands:** Maybelline, Lakme, L'Oreal\n\nFresh and natural look!",
                'kn': "**ದೈನಂದಿನ ಮೇಕಪ್ ಮಾರ್ಗದರ್ಶಿ:** 💄\n\n**ಬೇಸ್:**\n• ಮಾಯ್ಶ್ಚರೈಜರ್ + ಪ್ರೈಮರ್\n• ಲೈಟ್/ಮೀಡಿಯಂ ಕವರೇಜ್ ಫೌಂಡೇಶನ್\n• ಕನ್ಸೀಲರ್\n• ಲೂಸ್ ಪೌಡರ್\n\n**ಕಣ್ಣುಗಳು:**\n• ನ್ಯೂಟ್ರಲ್ ಐಶಾಡೋ\n• ಲೈಟ್ ಐಲೈನರ್\n• ಮಸ್ಕಾರಾ\n• ಹುಬ್ಬುಗಳನ್ನು ನೈಸರ್ಗಿಕವಾಗಿ ತುಂಬಿಸಿ\n\n**ತುಟಿಗಳು:**\n• ನ್ಯೂಡ್, ಪಿಂಕ್, ಅಥವಾ ಕೋರಲ್ ಲಿಪ್ಸ್ಟಿಕ್\n• ಟಿಂಟೆಡ್ ಲಿಪ್ ಬಾಮ್\n\n**ಫಿನಿಶಿಂಗ್:**\n• ಲೈಟ್ ಬ್ಲಶ್\n• ಐಚ್ಛಿಕ: ಲೈಟ್ ಹೈಲೈಟರ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** Maybelline, Lakme, L'Oreal\n\nತಾಜಾ ಮತ್ತು ನೈಸರ್ಗಿಕ ನೋಟ!"
            }
            return responses.get(lang, responses['en'])
    
    # Handle makeup queries
    if intent == 'makeup' or any(word in query_lower for word in ['makeup', 'cosmetic', 'foundation', 'lipstick', 'eyeshadow', 'mascara', 'ಮೇಕಪ್']):
        if any(word in query_lower for word in ['wedding', 'bridal', 'traditional', 'settled', 'ಮದುವೆ']):
            responses = {
                'en': "**Traditional Wedding Makeup Guide:** 💄✨\n\n**Base:**\n• Primer for long-lasting makeup\n• Full-coverage foundation (match skin tone)\n• Concealer for dark circles\n• Setting powder (translucent)\n• Contour & highlight for definition\n\n**Eyes:**\n• Bold eyeshadow (gold, bronze, maroon)\n• Winged eyeliner (black/brown)\n• False lashes or mascara (2-3 coats)\n• Kajal on waterline\n• Fill & define eyebrows\n\n**Lips:**\n• Red, maroon, or pink lipstick\n• Lip liner to prevent bleeding\n• Gloss for shine (optional)\n\n**Finishing:**\n• Blush (peach/pink)\n• Bindi (traditional)\n• Setting spray for 12+ hour wear\n\n**Brands:** MAC, Huda Beauty, Lakme, Maybelline\n\nYou'll look absolutely stunning! 💐✨",
                'kn': "**ಸಾಂಪ್ರದಾಯಿಕ ಮದುವೆಯ ಮೇಕಪ್ ಮಾರ್ಗದರ್ಶಿ:** 💄✨\n\n**ಬೇಸ್:**\n• ದೀರ್ಘಕಾಲೀನ ಮೇಕಪ್ಗಾಗಿ ಪ್ರೈಮರ್\n• ಫುಲ್-ಕವರೇಜ್ ಫೌಂಡೇಶನ್\n• ಡಾರ್ಕ್ ಸರ್ಕಲ್ಸ್ಗಾಗಿ ಕನ್ಸೀಲರ್\n• ಸೆಟ್ಟಿಂಗ್ ಪೌಡರ್\n• ಕಾಂಟೂರ್ & ಹೈಲೈಟ್\n\n**ಕಣ್ಣುಗಳು:**\n• ಬೋಲ್ಡ್ ಐಶಾಡೋ (ಚಿನ್ನ, ಕಂಚು, ಮರೂನ್)\n• ವಿಂಗ್ಡ್ ಐಲೈನರ್\n• ಫಾಲ್ಸ್ ಲ್ಯಾಶಸ್ ಅಥವಾ ಮಸ್ಕಾರಾ\n• ವಾಟರ್ಲೈನ್ನಲ್ಲಿ ಕಾಜಲ್\n• ಹುಬ್ಬುಗಳನ್ನು ತುಂಬಿಸಿ\n\n**ತುಟಿಗಳು:**\n• ಕೆಂಪು, ಮರೂನ್, ಅಥವಾ ಗುಲಾಬಿ ಲಿಪ್ಸ್ಟಿಕ್\n• ಲಿಪ್ ಲೈನರ್\n• ಹೊಳಪಿಗಾಗಿ ಗ್ಲಾಸ್\n\n**ಫಿನಿಶಿಂಗ್:**\n• ಬ್ಲಶ್ (ಪೀಚ್/ಪಿಂಕ್)\n• ಬಿಂದಿ (ಸಾಂಪ್ರದಾಯಿಕ)\n• ಸೆಟ್ಟಿಂಗ್ ಸ್ಪ್ರೇ\n\n**ಬ್ರಾಂಡ್ಗಳು:** MAC, Huda Beauty, Lakme, Maybelline\n\nನೀವು ಸಂಪೂರ್ಣವಾಗಿ ಅದ್ಭುತವಾಗಿ ಕಾಣುತ್ತೀರಿ! 💐✨"
            }
            return responses.get(lang, responses['en'])
    
    # Men's wedding outfit queries
    if intent == 'men_wedding' or (intent == 'wedding' and any(word in query_lower for word in ['men', 'man', 'male', 'groom', 'guy'])):
        responses = {
            'en': "**Wedding Outfit Guide for Men:** 💍✨\n\n**Traditional:**\n• Sherwani with churidar (gold, cream, maroon)\n• Kurta pajama with Nehru jacket\n• Bandhgala suit (Indo-western)\n• Dhoti with silk kurta\n\n**Western:**\n• Three-piece suit (navy, black, grey)\n• Tuxedo with bow tie\n• Blazer with formal trousers\n\n**Accessories:**\n• Turban/Safa (for groom)\n• Mojari/Jutti or formal shoes\n• Watch, brooch, pocket square\n• Shawl or stole\n\n**Grooming:** Professional haircut, well-groomed beard, subtle cologne\n\n**Brands:** Manyavar, Mohanlal Sons, Raymond, Blackberrys\n\nLook like a king! 👑",
            'kn': "**ಪುರುಷರಿಗೆ ಮದುವೆಯ ಉಡುಪು ಮಾರ್ಗದರ್ಶಿ:** 💍✨\n\n**ಸಾಂಪ್ರದಾಯಿಕ:**\n• ಚುರಿದಾರ್ನೊಂದಿಗೆ ಶೇರ್ವಾನಿ (ಚಿನ್ನ, ಕ್ರೀಮ್, ಮರೂನ್)\n• ನೆಹರೂ ಜಾಕೆಟ್ನೊಂದಿಗೆ ಕುರ್ತಾ ಪಜಾಮಾ\n• ಬಂಧಗಲಾ ಸೂಟ್ (ಇಂಡೋ-ವೆಸ್ಟರ್ನ್)\n• ಸಿಲ್ಕ್ ಕುರ್ತಾದೊಂದಿಗೆ ಧೋತಿ\n\n**ವೆಸ್ಟರ್ನ್:**\n• ಥ್ರೀ-ಪೀಸ್ ಸೂಟ್ (ನೇವಿ, ಕಪ್ಪು, ಬೂದು)\n• ಬೋ ಟೈನೊಂದಿಗೆ ಟಕ್ಸೆಡೋ\n• ಫಾರ್ಮಲ್ ಪ್ಯಾಂಟ್ಸ್ನೊಂದಿಗೆ ಬ್ಲೇಜರ್\n\n**ಆಕ್ಸೆಸರೀಸ್:**\n• ಟರ್ಬನ್/ಸಫಾ (ವರನಿಗೆ)\n• ಮೊಜರಿ/ಜುಟ್ಟಿ ಅಥವಾ ಫಾರ್ಮಲ್ ಶೂಸ್\n• ವಾಚ್, ಬ್ರೂಚ್, ಪಾಕೆಟ್ ಸ್ಕ್ವೇರ್\n• ಶಾಲ್ ಅಥವಾ ಸ್ಟೋಲ್\n\n**ಗ್ರೂಮಿಂಗ್:** ಪ್ರೊಫೆಷನಲ್ ಹೇರ್ಕಟ್, ಗ್ರೂಮ್ಡ್ ಬಿಯರ್ಡ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** Manyavar, Mohanlal Sons, Raymond\n\nರಾಜನಂತೆ ಕಾಣಿರಿ! 👑"
        }
        return responses.get(lang, responses['en'])
    
    # Wedding outfit queries
    if intent == 'wedding' or intent == 'wedding_continue' or any(word in query_lower for word in ['wedding', 'bridal', 'ಮದುವೆ', 'ವೆಡ್ಡಿಂಗ್']):
        responses = {
            'en': "**Wedding Outfit Guide:** 💍✨\n\n**For Women:**\n• Silk saree (Kanchipuram, Banarasi)\n• Lehenga choli (heavy embroidery)\n• Designer saree with embellishments\n• Colors: Red, maroon, pink, green, gold\n\n**Jewelry:** Gold temple jewelry, diamond sets, jhumkas, bangles\n**Makeup:** Bold, glamorous, traditional\n**Brands:** Nalli, Pothys, Taneira, FabIndia\n\nYou'll look stunning!",
            'kn': "**ಮದುವೆಯ ಉಡುಪು ಮಾರ್ಗದರ್ಶಿ:** 💍✨\n\n**ಮಹಿಳೆಯರಿಗೆ:**\n• ರೇಷ್ಮೆ ಸೀರೆ (ಕಾಂಚೀಪುರಂ, ಬನಾರಸಿ)\n• ಲೆಹೆಂಗಾ ಚೋಲಿ (ಭಾರೀ ಕಸೂತಿ)\n• ಡಿಸೈನರ್ ಸೀರೆ\n• ಬಣ್ಣಗಳು: ಕೆಂಪು, ಮರೂನ್, ಗುಲಾಬಿ, ಹಸಿರು, ಚಿನ್ನ\n\n**ಆಭರಣಗಳು:** ಚಿನ್ನದ ದೇವಾಲಯ ಆಭರಣಗಳು, ವಜ್ರ ಸೆಟ್ಗಳು, ಝುಮ್ಕಾಗಳು, ಬಳೆಗಳು\n**ಮೇಕಪ್:** ದಪ್ಪ, ಆಕರ್ಷಕ, ಸಾಂಪ್ರದಾಯಿಕ\n**ಬ್ರಾಂಡ್ಗಳು:** ನಲ್ಲಿ, ಪೋತೀಸ್, ತನೀರಾ, ಫ್ಯಾಬ್ಇಂಡಿಯಾ\n\nನೀವು ಅದ್ಭುತವಾಗಿ ಕಾಣುತ್ತೀರಿ!"
        }
        return responses.get(lang, responses['en'])
    
    # Overall look queries
    if intent == 'complete_office_look' or (any(word in query_lower for word in ['overall', 'complete', 'full', 'entire', 'whole']) and any(word in query_lower for word in ['look', 'style'])):
        if any(word in query_lower for word in ['casual', 'office', 'work']) or context_data.get('last_intent') in ['casual_office', 'formal_office']:
            responses = {
                'en': "**Complete Casual Office Look:** 💼✨\n\n**Outfit:**\n• Tailored trousers with blouse/shirt\n• OR midi skirt with tucked-in top\n• Blazer (optional)\n• Colors: Navy, black, grey, white, pastels\n\n**Footwear:** Loafers, ballet flats, low heels\n\n**Accessories:**\n• Simple watch\n• Small stud earrings\n• Tote bag or structured handbag\n• Minimal necklace (optional)\n\n**Makeup:**\n• Natural foundation\n• Nude/pink lipstick\n• Light eyeshadow\n• Mascara\n• Filled eyebrows\n\n**Hair:** Neat bun, low ponytail, or loose waves\n\n**Brands:** Zara, H&M, Marks & Spencer, Westside\n\nProfessional, polished, and comfortable! 💼",
                'kn': "**ಸಂಪೂರ್ಣ ಕ್ಯಾಶುಯಲ್ ಆಫೀಸ್ ಲುಕ್:** 💼✨\n\n**ಉಡುಪು:**\n• ಬ್ಲೌಸ್/ಶರ್ಟ್ನೊಂದಿಗೆ ಟೈಲರ್ಡ್ ಪ್ಯಾಂಟ್ಸ್\n• ಅಥವಾ ಟಾಪ್ನೊಂದಿಗೆ ಮಿಡಿ ಸ್ಕರ್ಟ್\n• ಬ್ಲೇಜರ್ (ಐಚ್ಛಿಕ)\n• ಬಣ್ಣಗಳು: ನೇವಿ, ಕಪ್ಪು, ಬೂದು, ಬಿಳಿ\n\n**ಪಾದರಕ್ಷೆ:** ಲೋಫರ್ಸ್, ಬ್ಯಾಲೆ ಫ್ಲಾಟ್ಸ್, ಲೋ ಹೀಲ್ಸ್\n\n**ಆಕ್ಸೆಸರೀಸ್:**\n• ಸಿಂಪಲ್ ವಾಚ್\n• ಸ್ಮಾಲ್ ಸ್ಟಡ್ ಇಯರ್ರಿಂಗ್ಸ್\n• ಟೋಟ್ ಬ್ಯಾಗ್\n• ಮಿನಿಮಲ್ ನೆಕ್ಲೇಸ್\n\n**ಮೇಕಪ್:**\n• ನ್ಯಾಚುರಲ್ ಫೌಂಡೇಶನ್\n• ನ್ಯೂಡ್/ಪಿಂಕ್ ಲಿಪ್ಸ್ಟಿಕ್\n• ಲೈಟ್ ಐಶಾಡೋ\n• ಮಸ್ಕಾರಾ\n• ಫಿಲ್ಡ್ ಐಬ್ರೋಸ್\n\n**ಹೇರ್:** ನೀಟ್ ಬನ್, ಲೋ ಪೋನಿಟೇಲ್\n\n**ಬ್ರಾಂಡ್ಗಳು:** Zara, H&M, Marks & Spencer\n\nಪ್ರೊಫೆಷನಲ್ ಮತ್ತು ಆರಾಮದಾಯಕ! 💼"
            }
            return responses.get(lang, responses['en'])
    
    # Outfit queries
    if 'outfit' in query_lower or 'ಉಡುಪು' in query_lower:
        responses = {
            'en': "I'd love to help with outfit ideas! Could you tell me the occasion? (wedding, party, casual, formal)",
            'kn': "ಉಡುಪು ಐಡಿಯಾಗಳೊಂದಿಗೆ ಸಹಾಯ ಮಾಡಲು ನಾನು ಇಷ್ಟಪಡುತ್ತೇನೆ! ಸಂದರ್ಭವನ್ನು ಹೇಳಬಹುದೇ? (ಮದುವೆ, ಪಾರ್ಟಿ, ಕ್ಯಾಶುಯಲ್, ಫಾರ್ಮಲ್)"
        }
        return responses.get(lang, responses['en'])
    
    # Default fashion response
    responses = {
        'en': "I'm here to help with all your fashion, beauty, and styling needs! Feel free to ask about trends, outfit ideas, makeup tips, or any fashion advice.",
        'kn': "ನಿಮ್ಮ ಎಲ್ಲಾ ಫ್ಯಾಷನ್, ಸೌಂದರ್ಯ ಮತ್ತು ಸ್ಟೈಲಿಂಗ್ ಅಗತ್ಯಗಳಿಗೆ ಸಹಾಯ ಮಾಡಲು ನಾನು ಇಲ್ಲಿದ್ದೇನೆ! ಟ್ರೆಂಡ್ಗಳು, ಉಡುಪು ಐಡಿಯಾಗಳು, ಮೇಕಪ್ ಸಲಹೆಗಳು ಅಥವಾ ಯಾವುದೇ ಫ್ಯಾಷನ್ ಸಲಹೆಯ ಬಗ್ಗೆ ಕೇಳಲು ಮುಕ್ತವಾಗಿರಿ."
    }
    return responses.get(lang, responses['en'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default')
    
    if not user_message:
        return jsonify({'response': 'Please ask me something about fashion or beauty!'})
    
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []
    if session_id not in conversation_context:
        conversation_context[session_id] = {}
    
    # Update session timestamp
    session_timestamps[session_id] = time.time()
    
    # Optimize memory if needed
    optimize_memory()
    
    conversation_memory[session_id].append(user_message)
    if len(conversation_memory[session_id]) > MAX_MEMORY_SIZE:
        conversation_memory[session_id] = conversation_memory[session_id][-MAX_MEMORY_SIZE:]
    
    lang = detect_language(user_message)
    
    if is_greeting(user_message) and len(user_message.split()) <= 3:
        response = get_greeting_response(lang)
        return jsonify({'response': response})
    
    if is_gratitude(user_message) and len(user_message.split()) <= 5:
        response = get_gratitude_response(lang)
        return jsonify({'response': response})
    
    if not is_fashion_related(user_message, conversation_memory.get(session_id, [])) and not is_greeting(user_message):
        return jsonify({'response': get_out_of_scope_message(lang)})
    
    response = generate_fashion_response(user_message, lang, session_id)
    
    return jsonify({'response': response, 'images': []})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
