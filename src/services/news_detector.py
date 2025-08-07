"""
Advanced news detection service for identifying news content in Telegram messages.
Optimized for Persian/English war and geopolitical news.
"""
import logging
import re

logger = logging.getLogger(__name__)

try:
    from config.settings import NEW_ATTRIBUTION
except ImportError:
    NEW_ATTRIBUTION = "@anilgoldgallerynews"


class NewsDetector:
    """Advanced news detector for Telegram messages with focus on war/geopolitical content."""

    # Comprehensive financial and geopolitical news keywords (Persian & English)
    FINANCIAL_NEWS_KEYWORDS = [
        # War and conflict terminology
        "جنگ", "حمله", "بمباران", "موشک", "تنش", "درگیری", "عملیات نظامی", "تهدید",
        "war", "attack", "bombing", "missile", "conflict", "military", "strike", "threat",
        
        # Israel-Iran specific terms
        "اسرائیل", "ایران", "حزب‌الله", "حماس", "نتانیاهو", "رهبر انقلاب", "سپاه",
        "israel", "iran", "hezbollah", "hamas", "netanyahu", "irgc", "gaza", "lebanon",
        
        # Nuclear and sanctions
        "تحریم", "هسته‌ای", "اورانیوم", "غنی‌سازی", "برجام", "آژانس اتمی", "نطنز",
        "sanctions", "nuclear", "uranium", "enrichment", "jcpoa", "iaea", "natanz",
        
        # Economic warfare terms
        "دلار", "طلا", "نفت", "بورس", "اقتصاد", "تورم", "بحران اقتصادی", "قیمت نفت",
        "economic crisis", "oil price", "gold", "dollar", "economic warfare", "inflation",
        
        # Geopolitical actors
        "آمریکا", "اروپا", "روسیه", "چین", "ناتو", "عربستان", "ترکیه", "مصر",
        "usa", "america", "europe", "russia", "china", "nato", "saudi", "turkey",
        
        # Military and defense
        "پهپاد", "جنگنده", "ناوشکن", "پدافند", "سامانه دفاعی", "رادار", "فریگات",
        "drone", "fighter", "destroyer", "defense system", "radar", "frigate",
        
        # News format indicators
        "فوری", "خبر", "گزارش", "به گزارش", "منابع خبری", "تأیید شد", "اعلام شد",
        "breaking", "news", "report", "confirmed", "announced", "sources say",
        
        # Regional terms
        "خاورمیانه", "خلیج فارس", "منطقه", "تنگه هرمز", "دریای سرخ", "مدیترانه",
        "middle east", "persian gulf", "region", "strait of hormuz", "red sea",
        
        # International organizations
        "سازمان ملل", "شورای امنیت", "اتحادیه اروپا", "اوپک", "گروه هفت",
        "united nations", "security council", "european union", "opec", "g7"
    ]

    # Non-news content indicators
    NON_NEWS_KEYWORDS = [
        # Commercial content
        "تبلیغ", "فروش", "خرید", "تخفیف", "ویژه", "رستوران", "کافه", "هتل",
        "advertisement", "sale", "buy", "discount", "special", "restaurant", "cafe",
        
        # Entertainment
        "سرگرمی", "فیلم", "سینما", "موسیقی", "کنسرت", "بازیگر", "خواننده",
        "entertainment", "movie", "cinema", "music", "concert", "actor", "singer",
        
        # Sports
        "ورزش", "فوتبال", "والیبال", "بسکتبال", "تنیس", "شنا", "دوچرخه‌سواری",
        "sports", "football", "soccer", "volleyball", "basketball", "tennis",
        
        # Personal/social
        "تولد", "عروسی", "سفر", "تعطیلات", "خانواده", "دوستان", "شخصی",
        "birthday", "wedding", "travel", "vacation", "family", "friends", "personal",
        
        # Weather and routine
        "آب و هوا", "هواشناسی", "بارش", "برف", "گرما", "سرما", "ترافیک",
        "weather", "forecast", "rain", "snow", "traffic", "temperature"
    ]

    @classmethod
    def is_news(cls, text):
        """Enhanced news detection with pattern matching."""
        if not text or len(text.strip()) < 30:
            logger.debug("Text too short for news detection")
            return False

        text_lower = text.lower()
        
        # Count relevant keywords with weighted scoring
        relevant_term_count = 0
        high_priority_matches = 0
        
        for keyword in cls.FINANCIAL_NEWS_KEYWORDS:
            if keyword.lower() in text_lower:
                relevant_term_count += 1
                # Extra weight for war/conflict terms
                if keyword in ["جنگ", "حمله", "موشک", "تحریم", "war", "attack", "missile", "sanctions"]:
                    high_priority_matches += 1
        
        # Count non-news indicators
        non_news_count = sum(1 for keyword in cls.NON_NEWS_KEYWORDS 
                           if keyword.lower() in text_lower)
        
        # News format indicators with regex patterns
        format_indicators = [
            r'فوری[::\s]',          # "فوری:"
            r'خبر فوری[::\s]',      # "خبر فوری:"
            r'به گزارش',             # "به گزارش"
            r'منابع خبری',           # "منابع خبری"
            r'تأیید شد',            # "تأیید شد"
            r'اعلام شد',            # "اعلام شد"
            r'گزارش می‌دهد',         # "گزارش می‌دهد"
            r'breaking[::\s]', 
            r'urgent[::\s]',
            r'news[::\s]',
            r'report[::\s]',
            r'confirmed[::\s]',
            r'announced[::\s]'
        ]
        
        format_indicator_count = sum(1 for pattern in format_indicators 
                                   if re.search(pattern, text_lower))
        
        # High-priority news pattern detection
        priority_patterns = [
            r'فوری.*?حمله',         # "فوری: حمله"
            r'موشک.*?شلیک',        # "موشک شلیک شد"
            r'تحریم.*?جدید',        # "تحریم جدید"
            r'اسرائیل.*?حمله',      # "اسرائیل حمله کرد"
            r'ایران.*?اعلام',       # "ایران اعلام کرد"
            r'breaking.*?news',
            r'urgent.*?update',
            r'missile.*?attack',
            r'israel.*?strikes',
            r'iran.*?announces'
        ]
        
        priority_pattern_count = sum(1 for pattern in priority_patterns 
                                   if re.search(pattern, text_lower))
        
        # Decision logic with multiple criteria
        logger.debug(f"News analysis: relevant_terms={relevant_term_count}, "
                    f"high_priority={high_priority_matches}, "
                    f"format_indicators={format_indicator_count}, "
                    f"priority_patterns={priority_pattern_count}, "
                    f"non_news={non_news_count}")
        
        # Strong news indicators
        if priority_pattern_count >= 1:
            logger.debug("Detected as news: priority pattern match")
            return True
            
        if high_priority_matches >= 2 and format_indicator_count >= 1:
            logger.debug("Detected as news: multiple high-priority terms with format")
            return True
            
        if relevant_term_count >= 4 and non_news_count == 0:
            logger.debug("Detected as news: high relevant term count, no non-news terms")
            return True
            
        if relevant_term_count >= 2 and format_indicator_count >= 2:
            logger.debug("Detected as news: relevant terms with strong format indicators")
            return True
            
        # For longer texts with decent relevance
        if len(text) > 150 and relevant_term_count >= 2 and format_indicator_count >= 1:
            logger.debug("Detected as news: long text with relevant content")
            return True
            
        # Reject if too many non-news indicators
        if non_news_count >= 2:
            logger.debug("Rejected as news: too many non-news indicators")
            return False
            
        logger.debug("Not detected as news")
        return False

    @classmethod
    def clean_news_text(cls, text):
        """Clean and format news text for professional redistribution."""
        if not text:
            return ""
            
        logger.debug(f"Cleaning news text (length: {len(text)})")
        
        # Step 1: Normalize whitespace and line breaks
        cleaned = re.sub(r'\n{3,}', '\n\n', text.strip())
        cleaned = re.sub(r'\r\n', '\n', cleaned)
        cleaned = re.sub(r'\r', '\n', cleaned)
        
        # Step 2: Remove Telegram-specific elements
        cleaned = re.sub(r'@\w+\b', '', cleaned)  # Remove handles
        cleaned = re.sub(r'https?://\S+', '', cleaned)  # Remove URLs
        cleaned = re.sub(r't\.me/\S+', '', cleaned)  # Remove t.me links
        cleaned = re.sub(r'#\w+', '', cleaned)  # Remove hashtags
        
        # Step 3: Remove excessive emojis and symbols
        cleaned = re.sub(r'[\U00010000-\U0010ffff]{3,}', '🔸', cleaned)  # Replace emoji spam
        cleaned = re.sub(r'[🔸🔹➖⬛⬜]{3,}', '', cleaned)  # Remove symbol spam
        
        # Step 4: Remove common prefixes that we'll replace
        prefixes_to_remove = [
            "فوری:", "فوری", "خبر فوری:", "خبر:", "گزارش:", "اطلاعیه:",
            "Breaking:", "Urgent:", "News:", "Report:"
        ]
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Step 5: Clean up whitespace
        cleaned = re.sub(r'\s+$', '', cleaned)  # Remove trailing whitespace
        cleaned = re.sub(r'^\s+', '', cleaned)  # Remove leading whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Max 2 consecutive newlines
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # Normalize spaces
        
        # Step 6: Professional formatting
        if cleaned:
            # Determine urgency indicator
            urgency_indicator = "📰"  # Default
            if any(urgent in text.lower() for urgent in ["فوری", "urgent", "breaking", "عاجل"]):
                urgency_indicator = "🔴"
            elif any(important in text.lower() for important in ["مهم", "important", "هشدار", "warning"]):
                urgency_indicator = "🔶"
            elif any(conflict in text.lower() for conflict in ["جنگ", "حمله", "موشک", "war", "attack", "missile"]):
                urgency_indicator = "⚡"
            
            # Add professional formatting with attribution
            try:
                from src.utils.time_utils import get_formatted_time
                timestamp = get_formatted_time()
                formatted_text = f"{urgency_indicator} {cleaned}\n\n📡 {NEW_ATTRIBUTION}\n🕐 {timestamp}"
            except ImportError:
                # Fallback if time_utils not available
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_text = f"{urgency_indicator} {cleaned}\n\n📡 {NEW_ATTRIBUTION}\n🕐 {timestamp}"
            
            return formatted_text
            
        return cleaned

    @classmethod
    def split_combined_news(cls, text):
        """Split combined news messages into individual news items."""
        # Enhanced separators for Persian news channels
        separators = [
            r'[-]{3,}',               # Multiple dashes: ---
            r'[=]{3,}',               # Multiple equals: ===
            r'[_]{3,}',               # Multiple underscores: ___
            r'[*]{3,}',               # Multiple asterisks: ***
            r'[.]{3,}',               # Multiple periods: ...
            r'🔸{2,}',                # Diamond symbols
            r'🔹{2,}',                # Diamond symbols  
            r'➖{2,}',                # Minus symbols
            r'⬛{2,}',                # Black squares
            r'⬜{2,}',                # White squares
            r'〰️{1,}',               # Wavy dashes
            r'〰{1,}',                # Wavy dashes alt
            r'\n\s*\n\s*\n',         # Multiple empty lines
            r'━{3,}',                 # Heavy horizontal lines
            r'▪{3,}',                 # Black squares
            r'▫{3,}',                 # White squares
            r'■{3,}',                 # Black large squares
            r'□{3,}',                 # White large squares
            r'●{3,}',                 # Black circles
            r'○{3,}',                 # White circles
            # Persian-specific patterns
            r'خبر\s+(?:بعدی|دوم|سوم)',  # "خبر بعدی", "خبر دوم"
            r'(?:۱|۲|۳|۴|۵)\s*[-.)]\s*',  # Persian numbers with separators
            r'\n\s*[۱-۹]+\s*[-.)]\s*'     # Numbered lists in Persian
        ]
        
        # Combine all separators
        pattern = '|'.join(separators)
        
        # Split the text
        segments = re.split(pattern, text, flags=re.IGNORECASE)
        
        # Clean and filter segments
        cleaned_segments = []
        for segment in segments:
            segment = segment.strip()
            if len(segment) >= 50:  # Only keep substantial segments
                cleaned_segments.append(segment)
        
        # If no segments found, return original as single item
        if not cleaned_segments:
            return [text]
            
        logger.debug(f"Split news into {len(cleaned_segments)} segments")
        return cleaned_segments

    @classmethod
    def extract_news_metadata(cls, text):
        """Extract metadata from news text."""
        metadata = {
            'urgency': 'normal',
            'category': 'general',
            'source': None,
            'language': 'mixed',
            'word_count': len(text.split()),
            'char_count': len(text)
        }
        
        text_lower = text.lower()
        
        # Detect urgency
        if any(urgent in text_lower for urgent in ["فوری", "breaking", "urgent", "عاجل"]):
            metadata['urgency'] = 'urgent'
        elif any(important in text_lower for important in ["مهم", "important", "هشدار"]):
            metadata['urgency'] = 'important'
        
        # Detect category
        if any(war in text_lower for war in ["جنگ", "حمله", "موشک", "war", "attack"]):
            metadata['category'] = 'war'
        elif any(econ in text_lower for econ in ["تحریم", "اقتصاد", "دلار", "sanctions"]):
            metadata['category'] = 'economic'
        elif any(nuke in text_lower for nuke in ["هسته‌ای", "اورانیوم", "nuclear"]):
            metadata['category'] = 'nuclear'
        
        # Detect source patterns
        source_patterns = [
            r'به گزارش\s+([^،]+)',      # "به گزارش SOURCE"
            r'بر اساس\s+([^،]+)',       # "بر اساس SOURCE"
            r'منابع\s+([^،]+)',         # "منابع SOURCE"
            r'according to\s+([^,]+)',  # "according to SOURCE"
            r'reported by\s+([^,]+)'    # "reported by SOURCE"
        ]
        
        for pattern in source_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['source'] = match.group(1).strip()
                break
        
        # Detect language predominance
        persian_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if persian_chars > english_chars * 2:
            metadata['language'] = 'persian'
        elif english_chars > persian_chars * 2:
            metadata['language'] = 'english'
        
        return metadata