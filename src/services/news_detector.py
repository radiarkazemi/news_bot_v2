"""
Expanded financial and geopolitical news detector.
Detects both direct financial news AND geopolitical events that impact markets.
"""
import logging
import re

logger = logging.getLogger(__name__)

class NewsDetector:
    """Expanded news detector for financial + geopolitical content that affects markets."""
    
    # DIRECT FINANCIAL KEYWORDS (Original)
    GOLD_KEYWORDS = [
        "طلا", "گرم‌طلا", "طلای‌۱۸عیار", "طلای‌۲۴عیار", "طلای‌۲۲عیار", "طلای‌۲۱عیار",
        "سکه", "سکه‌طلا", "نیم‌سکه", "ربع‌سکه", "گرمی", "اونس", "طلای‌آب‌شده",
        "آبشده", "طلافروشی", "بازار‌طلا", "قیمت‌طلا", "نرخ‌طلا", "طلای‌کهنه",
        "gold", "ounce", "troy", "bullion", "precious", "metal", "xau", "golden"
    ]
    
    CURRENCY_KEYWORDS = [
        "دلار", "یورو", "پوند", "ین", "یوان", "روپیه", "درهم", "دینار", "لیر", "ریال",
        "نرخ‌ارز", "قیمت‌دلار", "قیمت‌یورو", "بازار‌ارز", "صرافی", "ارز", "ارزی",
        "تتر", "usdt", "دلار‌تتر", "آزاد", "سامانه‌نیما", "نیما", "رسمی",
        "dollar", "euro", "pound", "yen", "yuan", "currency", "exchange", "forex"
    ]
    
    # GEOPOLITICAL KEYWORDS (New - Major Impact)
    IRAN_KEYWORDS = [
        # Persian Iran-related
        "ایران", "جمهوری‌اسلامی", "تهران", "اسلامی", "خامنه‌ای", "رئیسی", "ظریف", "عراقچی",
        "سپاه", "حزب‌الله", "محور‌مقاومت", "ایرانی", "فارس", "خلیج‌فارس",
        
        # English Iran-related
        "iran", "iranian", "tehran", "islamic", "republic", "irgc", "hezbollah", "persian"
    ]
    
    ISRAEL_USA_KEYWORDS = [
        # Persian Israel/USA
        "اسرائیل", "آمریکا", "امریکا", "واشنگتن", "تل‌آویو", "نتانیاهو", "بایدن", "ترامپ",
        "کاخ‌سفید", "پنتاگون", "سیا", "موساد", "یهودی", "صهیونیست",
        
        # English Israel/USA
        "israel", "israeli", "america", "usa", "washington", "netanyahu", "biden", "trump",
        "white", "house", "pentagon", "cia", "mossad", "jewish", "zionist"
    ]
    
    WAR_CONFLICT_KEYWORDS = [
        # Persian war/conflict
        "جنگ", "حمله", "تهدید", "موشک", "پهپاد", "هواپیما", "بمباران", "انفجار",
        "نظامی", "ارتش", "نیروی‌هوایی", "نیروی‌دریایی", "عملیات", "تحریم", "تهدید",
        "حماس", "غزه", "فلسطین", "لبنان", "سوریه", "عراق", "یمن", "حوثی",
        
        # English war/conflict
        "war", "attack", "threat", "missile", "drone", "aircraft", "bombing", "explosion",
        "military", "army", "air", "force", "navy", "operation", "sanction", "gaza", "hamas"
    ]
    
    ECONOMIC_IMPACT_KEYWORDS = [
        # Persian economic impact
        "اقتصاد", "اقتصادی", "تورم", "رکود", "بحران", "بازار", "سهام", "بورس", "قیمت",
        "صادرات", "واردات", "تجارت", "تحریم", "تحریم‌های", "بانک‌مرکزی", "نفت", "گاز",
        "انرژی", "پتروشیمی", "صنعت", "تولید", "بودجه", "مالی", "سرمایه", "ارز",
        
        # English economic impact
        "economic", "economy", "inflation", "recession", "crisis", "market", "stock", "trade",
        "sanctions", "central", "bank", "oil", "gas", "energy", "industry", "budget", "finance"
    ]
    
    # URGENT GEOPOLITICAL KEYWORDS (Highest Priority)
    URGENT_KEYWORDS = [
        # High-impact events
        "هسته‌ای", "اتمی", "برجام", "یورانیوم", "غنی‌سازی", "آژانس", "آمانو",
        "nuclear", "atomic", "uranium", "enrichment", "iaea", "jcpoa",
        
        # Crisis terms
        "بحران", "جنگ‌جهانی", "جنگ‌منطقه‌ای", "crisis", "world", "war", "regional",
        
        # Economic warfare
        "جنگ‌اقتصادی", "تحریم‌اقتصادی", "economic", "warfare", "embargo"
    ]
    
    # NON-NEWS KEYWORDS (to filter out)
    NON_NEWS_KEYWORDS = [
        "ورزش", "فوتبال", "والیبال", "موسیقی", "سینما", "فیلم", "بازی", "سرگرمی",
        "آشپزی", "غذا", "رستوران", "مد", "لباس", "زیبایی", "سلامت", "پزشکی",
        "عاشقانه", "ازدواج", "عروسی", "تولد", "جشن", "تعطیلات",
        "sports", "football", "music", "movie", "game", "food", "fashion", "health"
    ]

    def is_news(self, text):
        """Enhanced news detection for financial + geopolitical content."""
        if not text or len(text.strip()) < 30:
            return False
        
        text_lower = text.lower()
        
        # Count all keyword categories
        financial_score = self._calculate_financial_score(text_lower)
        geopolitical_score = self._calculate_geopolitical_score(text_lower)
        economic_impact_score = self._calculate_economic_impact_score(text_lower)
        urgent_score = self._calculate_urgent_score(text_lower)
        
        # Count non-news penalties
        non_news_count = sum(1 for kw in self.NON_NEWS_KEYWORDS if kw in text_lower)
        
        # Total relevance score
        total_score = financial_score + geopolitical_score + economic_impact_score + (urgent_score * 2)
        
        # Apply penalty for non-news content
        final_score = total_score - (non_news_count * 2)
        
        # Decision logic
        is_relevant = self._determine_relevance(final_score, urgent_score, geopolitical_score, financial_score, non_news_count)
        
        # Log detailed analysis for debugging
        if final_score > 0 or non_news_count > 0:
            logger.debug(f"News analysis: financial={financial_score}, geo={geopolitical_score}, "
                        f"economic={economic_impact_score}, urgent={urgent_score}, "
                        f"penalty={non_news_count}, final_score={final_score}, is_news={is_relevant}")
        
        return is_relevant

    def _calculate_financial_score(self, text_lower):
        """Calculate direct financial keywords score."""
        score = 0
        score += sum(3 for kw in self.GOLD_KEYWORDS if kw in text_lower)
        score += sum(3 for kw in self.CURRENCY_KEYWORDS if kw in text_lower)
        return score

    def _calculate_geopolitical_score(self, text_lower):
        """Calculate geopolitical keywords score."""
        score = 0
        score += sum(2 for kw in self.IRAN_KEYWORDS if kw in text_lower)
        score += sum(2 for kw in self.ISRAEL_USA_KEYWORDS if kw in text_lower)
        score += sum(2 for kw in self.WAR_CONFLICT_KEYWORDS if kw in text_lower)
        return score

    def _calculate_economic_impact_score(self, text_lower):
        """Calculate economic impact keywords score."""
        return sum(1 for kw in self.ECONOMIC_IMPACT_KEYWORDS if kw in text_lower)

    def _calculate_urgent_score(self, text_lower):
        """Calculate urgent keywords score."""
        return sum(3 for kw in self.URGENT_KEYWORDS if kw in text_lower)

    def _determine_relevance(self, final_score, urgent_score, geopolitical_score, financial_score, non_news_count):
        """Determine if content is relevant news."""
        
        # Always relevant if urgent keywords present
        if urgent_score >= 3:
            return True
        
        # High relevance for strong geopolitical content
        if geopolitical_score >= 4 and non_news_count <= 1:
            return True
        
        # Medium relevance for moderate geopolitical + financial
        if (geopolitical_score >= 2 and financial_score >= 1) and non_news_count == 0:
            return True
        
        # Standard financial news
        if financial_score >= 3 and non_news_count <= 1:
            return True
        
        # General threshold
        if final_score >= 5 and non_news_count <= 1:
            return True
        
        # Lower threshold for Iran-specific content
        iran_mentions = sum(1 for kw in self.IRAN_KEYWORDS if kw in final_score)
        if iran_mentions >= 1 and final_score >= 3:
            return True
        
        return False

    def clean_news_text(self, text):
        """Clean and format news text with appropriate emoji."""
        if not text:
            return ""
        
        # Basic cleaning
        cleaned = text.strip()
        cleaned = re.sub(r'@\w+', '', cleaned)
        cleaned = re.sub(r'https?://\S+', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Add appropriate emoji based on content
        if not self._has_news_emoji(cleaned):
            emoji = self._get_appropriate_emoji(cleaned)
            cleaned = f"{emoji} {cleaned}"
        
        # Add attribution
        from config.settings import NEW_ATTRIBUTION
        if NEW_ATTRIBUTION and NEW_ATTRIBUTION not in cleaned:
            cleaned = f"{cleaned}\n\n📡 {NEW_ATTRIBUTION}"
        
        # Add timestamp
        from src.utils.time_utils import get_formatted_time
        try:
            current_time = get_formatted_time()
            cleaned = f"{cleaned}\n🕐 {current_time}"
        except:
            pass
        
        return cleaned.strip()

    def _has_news_emoji(self, text):
        """Check if text already has news emoji."""
        news_emojis = ['💰', '💱', '🏆', '₿', '🛢️', '📈', '📊', '⚡', '🚨', '🔥', '⚠️']
        return any(emoji in text for emoji in news_emojis)

    def _get_appropriate_emoji(self, text):
        """Get appropriate emoji based on content priority."""
        text_lower = text.lower()
        
        # Priority 1: Urgent/Crisis
        if any(kw in text_lower for kw in self.URGENT_KEYWORDS):
            return "🚨"
        
        # Priority 2: War/Conflict
        if any(kw in text_lower for kw in self.WAR_CONFLICT_KEYWORDS):
            return "⚡"
        
        # Priority 3: Iran/Geopolitical
        if any(kw in text_lower for kw in self.IRAN_KEYWORDS + self.ISRAEL_USA_KEYWORDS):
            return "🔥"
        
        # Priority 4: Direct Financial
        if any(kw in text_lower for kw in self.GOLD_KEYWORDS):
            return "🏆"
        elif any(kw in text_lower for kw in self.CURRENCY_KEYWORDS):
            return "💱"
        
        # Default: Economic impact
        return "📈"

    def get_news_category(self, text):
        """Determine the primary news category."""
        if not text:
            return "unknown"
        
        text_lower = text.lower()
        
        # Check categories in priority order
        if any(kw in text_lower for kw in self.URGENT_KEYWORDS):
            return "URGENT_NUCLEAR"
        elif any(kw in text_lower for kw in self.WAR_CONFLICT_KEYWORDS):
            return "WAR_CONFLICT"
        elif any(kw in text_lower for kw in self.IRAN_KEYWORDS):
            return "IRAN_GEOPOLITICAL"
        elif any(kw in text_lower for kw in self.ISRAEL_USA_KEYWORDS):
            return "ISRAEL_USA"
        elif any(kw in text_lower for kw in self.GOLD_KEYWORDS):
            return "GOLD_PRECIOUS"
        elif any(kw in text_lower for kw in self.CURRENCY_KEYWORDS):
            return "CURRENCY_FOREX"
        elif any(kw in text_lower for kw in self.ECONOMIC_IMPACT_KEYWORDS):
            return "ECONOMIC_IMPACT"
        else:
            return "GENERAL_NEWS"

    def get_relevance_score(self, text):
        """Get comprehensive relevance score."""
        if not text:
            return 0
        
        text_lower = text.lower()
        
        financial_score = self._calculate_financial_score(text_lower)
        geopolitical_score = self._calculate_geopolitical_score(text_lower)
        economic_impact_score = self._calculate_economic_impact_score(text_lower)
        urgent_score = self._calculate_urgent_score(text_lower)
        
        return financial_score + geopolitical_score + economic_impact_score + (urgent_score * 2)