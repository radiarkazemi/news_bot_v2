"""
Enhanced financial and geopolitical news detector.
Optimized for detecting financial news from Iranian gold/currency channels.
"""
import logging
import re

logger = logging.getLogger(__name__)

class NewsDetector:
    """Enhanced news detector optimized for financial and economic content."""
    
    # COMPREHENSIVE FINANCIAL KEYWORDS
    GOLD_KEYWORDS = [
        # Persian gold terms
        "طلا", "طلای", "سکه", "سکه‌طلا", "نیم‌سکه", "ربع‌سکه", "گرم‌طلا", 
        "طلای‌۱۸عیار", "طلای‌۲۴عیار", "طلای‌۲۲عیار", "طلای‌۲۱عیار",
        "اونس", "اونس‌طلا", "طلافروشی", "بازار‌طلا", "قیمت‌طلا", "نرخ‌طلا", 
        "آبشده", "طلای‌آب‌شده", "طلای‌کهنه", "گرمی",
        
        # English gold terms  
        "gold", "ounce", "troy", "bullion", "precious", "metal", "xau", "xauusd", "golden"
    ]
    
    CURRENCY_KEYWORDS = [
        # Persian currency terms
        "دلار", "یورو", "پوند", "ین", "یوان", "روپیه", "درهم", "دینار", "لیر", "ریال",
        "ارز", "ارزی", "نرخ‌ارز", "قیمت‌دلار", "قیمت‌یورو", "بازار‌ارز",
        "صرافی", "صرافی‌ها", "تتر", "usdt", "دلار‌تتر", "نرخ", "قیمت",
        "آزاد", "سامانه‌نیما", "نیما", "رسمی", "مبادله", "تبدیل",
        "افزایش", "کاهش", "رشد", "سقوط", "جهش", "ثبت",
        
        # English currency terms
        "dollar", "euro", "pound", "yen", "yuan", "currency", "exchange", 
        "forex", "usd", "eur", "gbp", "jpy", "cny", "rate", "price"
    ]
    
    IRANIAN_ECONOMY_KEYWORDS = [
        # Persian economic terms
        "اقتصاد", "اقتصادی", "بازار", "بورس", "سهام", "شاخص", "تورم", "رکود",
        "بانک‌مرکزی", "سرمایه", "سرمایه‌گذاری", "تجارت", "صادرات", "واردات",
        "بودجه", "مالی", "مالیات", "درآمد", "هزینه", "سود", "زیان",
        "صنعت", "تولید", "تولیدات", "کارخانه", "کارگاه", "اشتغال", "بیکاری",
        "تهران", "ایران", "ایرانی", "کشور", "ملی", "دولت", "دولتی",
        
        # English economic terms
        "economy", "economic", "market", "stock", "index", "inflation", "gdp",
        "central", "bank", "investment", "trade", "export", "import", "budget",
        "iran", "iranian", "tehran"
    ]
    
    GEOPOLITICAL_KEYWORDS = [
        # Persian geopolitical terms  
        "تحریم", "تحریم‌ها", "عقوبات", "جنگ‌اقتصادی", "فشار‌اقتصادی",
        "ایران", "آمریکا", "امریکا", "اسرائیل", "اروپا", "چین", "روسیه",
        "برجام", "مذاکره", "توافق", "دیپلماسی", "سیاست", "سیاسی",
        "واشنگتن", "تل‌آویو", "پکن", "مسکو", "بروکسل",
        
        # English geopolitical terms
        "sanctions", "embargo", "iran", "america", "israel", "china", "russia",
        "nuclear", "diplomacy", "political", "policy", "agreement", "jcpoa",
        "washington", "telaviv", "beijing", "moscow"
    ]
    
    CRYPTO_KEYWORDS = [
        # Persian crypto terms
        "ارز‌دیجیتال", "رمزارز", "بیت‌کوین", "اتریوم", "کریپتو", "دیجیتال",
        "بلاک‌چین", "استخراج", "ماینر", "ماینینگ", "رمزنگاری",
        
        # English crypto terms  
        "bitcoin", "ethereum", "crypto", "cryptocurrency", "blockchain", 
        "btc", "eth", "mining", "digital", "coin", "token"
    ]
    
    OIL_ENERGY_KEYWORDS = [
        # Persian oil/energy terms
        "نفت", "گاز", "انرژی", "پتروشیمی", "پالایش", "پالایشگاه",
        "اوپک", "opec", "بشکه", "تن", "لیتر", "بنزین", "گازوئیل",
        "کرود", "برنت", "صنایع‌نفتی", "گاز‌طبیعی",
        
        # English oil/energy terms
        "oil", "gas", "energy", "petroleum", "crude", "barrel", "brent", "wti",
        "opec", "gasoline", "diesel", "refinery"
    ]
    
    # NEWS STRUCTURE INDICATORS (Lower weight but helps detection)
    NEWS_INDICATORS = [
        # Persian news indicators
        "اعلام", "گزارش", "خبر", "فوری", "بیان", "اظهار", "تأیید", "رد",
        "افزایش", "کاهش", "رشد", "ثبت", "رسید", "شد", "می‌شود",
        "به‌روزرسانی", "تحلیل", "پیش‌بینی", "انتظار", "احتمال",
        "امروز", "دیروز", "فردا", "هفته", "ماه", "سال",
        
        # English news indicators  
        "announced", "reported", "breaking", "update", "reached", "rose", "fell",
        "analysis", "forecast", "expected", "today", "yesterday", "week", "month"
    ]
    
    # NON-NEWS FILTERS (Higher penalty)
    NON_NEWS_KEYWORDS = [
        # Persian non-news
        "ورزش", "فوتبال", "والیبال", "بسکتبال", "موسیقی", "سینما", "فیلم", 
        "بازی", "سرگرمی", "تفریح", "غذا", "آشپزی", "رستوران", 
        "مد", "لباس", "زیبایی", "آرایش", "سلامت", "پزشکی",
        "عاشقانه", "ازدواج", "عروسی", "تولد", "جشن", "تعطیلات",
        "مسافرت", "گردش", "طبیعت", "حیوانات",
        
        # English non-news
        "sports", "football", "soccer", "basketball", "music", "movie", "film",
        "game", "entertainment", "food", "cooking", "restaurant", "fashion",
        "beauty", "health", "medical", "travel", "tourism", "animals"
    ]

    def is_news(self, text):
        """Enhanced news detection for financial content."""
        if not text or len(text.strip()) < 30:
            return False
        
        text_lower = text.lower()
        
        # Calculate scores for different categories
        gold_score = self._calculate_keyword_score(text_lower, self.GOLD_KEYWORDS, 3)
        currency_score = self._calculate_keyword_score(text_lower, self.CURRENCY_KEYWORDS, 3) 
        iranian_economy_score = self._calculate_keyword_score(text_lower, self.IRANIAN_ECONOMY_KEYWORDS, 2)
        geopolitical_score = self._calculate_keyword_score(text_lower, self.GEOPOLITICAL_KEYWORDS, 2)
        crypto_score = self._calculate_keyword_score(text_lower, self.CRYPTO_KEYWORDS, 2)
        oil_score = self._calculate_keyword_score(text_lower, self.OIL_ENERGY_KEYWORDS, 2)
        
        # News structure bonus (lower weight)
        structure_score = self._calculate_keyword_score(text_lower, self.NEWS_INDICATORS, 1)
        
        # Penalty for non-news content
        non_news_penalty = self._calculate_keyword_score(text_lower, self.NON_NEWS_KEYWORDS, 2)
        
        # Calculate total score
        total_score = (gold_score + currency_score + iranian_economy_score + 
                      geopolitical_score + crypto_score + oil_score + 
                      min(structure_score, 3) - non_news_penalty)  # Cap structure bonus
        
        # LOWERED THRESHOLD: Accept if score >= 2 (was higher before)
        is_relevant = total_score >= 2 and non_news_penalty <= 1
        
        # Special case: If has strong financial indicators but low score
        if not is_relevant and (gold_score >= 3 or currency_score >= 3):
            is_relevant = True
        
        # Log detailed analysis in debug mode
        if total_score > 0 or non_news_penalty > 0:
            logger.debug(f"Financial news analysis: gold={gold_score}, currency={currency_score}, "
                        f"economy={iranian_economy_score}, geo={geopolitical_score}, "
                        f"crypto={crypto_score}, oil={oil_score}, structure={structure_score}, "
                        f"penalty={non_news_penalty}, total={total_score}, is_news={is_relevant}")
        
        return is_relevant

    def _calculate_keyword_score(self, text_lower, keywords, multiplier):
        """Calculate score for a keyword category."""
        return sum(multiplier for kw in keywords if kw in text_lower)

    def get_financial_category(self, text):
        """Determine the primary financial category."""
        if not text:
            return "unknown"
        
        text_lower = text.lower()
        
        # Count matches in each category
        categories = {
            "GOLD": self._calculate_keyword_score(text_lower, self.GOLD_KEYWORDS, 1),
            "CURRENCY": self._calculate_keyword_score(text_lower, self.CURRENCY_KEYWORDS, 1),
            "IRANIAN_ECONOMY": self._calculate_keyword_score(text_lower, self.IRANIAN_ECONOMY_KEYWORDS, 1),
            "GEOPOLITICAL": self._calculate_keyword_score(text_lower, self.GEOPOLITICAL_KEYWORDS, 1),
            "CRYPTO": self._calculate_keyword_score(text_lower, self.CRYPTO_KEYWORDS, 1),
            "OIL_ENERGY": self._calculate_keyword_score(text_lower, self.OIL_ENERGY_KEYWORDS, 1)
        }
        
        # Return category with highest score
        max_category = max(categories.items(), key=lambda x: x[1])
        return max_category[0] if max_category[1] > 0 else "GENERAL_FINANCIAL"

    def get_relevance_score(self, text):
        """Get comprehensive relevance score."""
        if not text:
            return 0
        
        text_lower = text.lower()
        
        gold_score = self._calculate_keyword_score(text_lower, self.GOLD_KEYWORDS, 3)
        currency_score = self._calculate_keyword_score(text_lower, self.CURRENCY_KEYWORDS, 3)
        iranian_economy_score = self._calculate_keyword_score(text_lower, self.IRANIAN_ECONOMY_KEYWORDS, 2)
        geopolitical_score = self._calculate_keyword_score(text_lower, self.GEOPOLITICAL_KEYWORDS, 2)
        crypto_score = self._calculate_keyword_score(text_lower, self.CRYPTO_KEYWORDS, 2)
        oil_score = self._calculate_keyword_score(text_lower, self.OIL_ENERGY_KEYWORDS, 2)
        structure_score = self._calculate_keyword_score(text_lower, self.NEWS_INDICATORS, 1)
        
        return gold_score + currency_score + iranian_economy_score + geopolitical_score + crypto_score + oil_score + min(structure_score, 3)

    def get_news_category(self, text):
        """Determine the primary news category."""
        return self.get_financial_category(text)

    def clean_news_text(self, text):
        """Clean and format news text with appropriate emoji."""
        if not text:
            return ""
        
        # Basic cleaning
        cleaned = text.strip()
        cleaned = re.sub(r'@\w+', '', cleaned)  # Remove handles
        cleaned = re.sub(r'https?://\S+', '', cleaned)  # Remove URLs
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
        
        # Add appropriate emoji based on content
        if not self._has_financial_emoji(cleaned):
            emoji = self._get_financial_emoji(cleaned)
            cleaned = f"{emoji} {cleaned}"
        
        return cleaned.strip()

    def _has_financial_emoji(self, text):
        """Check if text already has financial emoji."""
        financial_emojis = ['💰', '💱', '🏆', '₿', '🛢️', '📈', '📊', '💎', '🪙']
        return any(emoji in text for emoji in financial_emojis)

    def _get_financial_emoji(self, text):
        """Get appropriate financial emoji."""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in self.GOLD_KEYWORDS):
            return "🏆"
        elif any(kw in text_lower for kw in self.CURRENCY_KEYWORDS):
            return "💱"
        elif any(kw in text_lower for kw in self.CRYPTO_KEYWORDS):
            return "₿"
        elif any(kw in text_lower for kw in self.OIL_ENERGY_KEYWORDS):
            return "🛢️"
        else:
            return "📈"

    def split_combined_news(self, text):
        """Split combined news messages into segments."""
        if not text:
            return [text]
        
        # Look for news separators
        separators = ['---', '===', '***', '░░░', '▫️▫️', '◦◦◦', '━━━', '▬▬▬']
        
        for sep in separators:
            if sep in text:
                segments = [seg.strip() for seg in text.split(sep)]
                return [seg for seg in segments if len(seg.strip()) >= 30]
        
        # Check for numbered items (1. 2. 3. etc.)
        if re.search(r'\d+[\.\)]\s', text):
            segments = re.split(r'\d+[\.\)]\s', text)
            segments = [seg.strip() for seg in segments if len(seg.strip()) >= 30]
            if len(segments) > 1:
                return segments
        
        # No separators found
        return [text]