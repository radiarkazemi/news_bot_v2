"""
Advanced news filtering service for war/geopolitical news relevance.
Focuses on Israel-Iran conflict and economic warfare impact.
"""
import logging
import re

logger = logging.getLogger(__name__)

try:
    from config.settings import (
        WAR_NEWS_ONLY, ISRAEL_IRAN_FOCUS, GEOPOLITICAL_ONLY, 
        MIN_RELEVANCE_SCORE, HIGH_PRIORITY_SCORE
    )
except ImportError:
    # Fallback values
    WAR_NEWS_ONLY = True
    ISRAEL_IRAN_FOCUS = True  
    GEOPOLITICAL_ONLY = True
    MIN_RELEVANCE_SCORE = 2
    HIGH_PRIORITY_SCORE = 5


class NewsFilter:
    """Advanced filter for detecting relevant war and geopolitical news."""

    # High-priority topics (3x weight)
    PRIMARY_TOPICS = [
        # Core Israel-Iran conflict
        "اسرائیل", "ایران", "israel", "iran",
        "نتانیاهو", "netanyahu", "رهبر انقلاب", "khamenei",
        
        # Direct military action
        "حمله", "بمباران", "موشک", "attack", "bombing", "missile", "strike",
        "عملیات نظامی", "military operation", "air strike", "drone attack",
        
        # Nuclear program  
        "هسته‌ای", "اورانیوم", "غنی‌سازی", "nuclear", "uranium", "enrichment",
        "برجام", "jcpoa", "آژانس اتمی", "iaea", "نطنز", "natanz",
        
        # Economic warfare
        "تحریم", "تحریم‌های جدید", "رفع تحریم", "sanctions", "economic pressure",
        "تحریم نفتی", "oil sanctions", "تحریم بانکی", "banking sanctions",
        
        # Key currencies and commodities during conflicts
        "دلار", "طلا", "نفت", "اونس", "dollar", "gold", "oil", "crude",
        
        # Regional proxy conflicts
        "حماس", "حزب‌الله", "hamas", "hezbollah", "gaza", "غزه", "لبنان", "lebanon",
        "سوریه", "syria", "عراق", "iraq", "یمن", "yemen", "حوثی", "houthi",
        
        # Strategic assets and locations
        "تنگه هرمز", "strait of hormuz", "خلیج فارس", "persian gulf",
        "دریای سرخ", "red sea", "کانال سوئز", "suez canal",
        
        # War terminology
        "جنگ", "درگیری", "تنش", "بحران", "war", "conflict", "crisis", "tension"
    ]

    # Medium priority topics (1x weight)
    SECONDARY_TOPICS = [
        # Regional powers
        "آمریکا", "روسیه", "چین", "usa", "russia", "china", "america",
        "عربستان", "امارات", "مصر", "ترکیه", "saudi", "uae", "egypt", "turkey",
        
        # International organizations
        "ناتو", "سازمان ملل", "nato", "united nations", "اتحادیه اروپا", "eu",
        "شورای امنیت", "security council", "آژانس اتمی", "iaea", "اوپک", "opec",
        
        # Economic indicators during conflicts
        "بازار ارز", "بازار طلا", "قیمت نفت", "بورس", "اقتصاد جهانی",
        "currency market", "gold market", "oil prices", "global economy",
        
        # Military terms
        "نیروهای مسلح", "سپاه", "ارتش", "دفاع هوایی", "پدافند",
        "military forces", "defense", "air defense", "army",
        
        # Diplomatic terms
        "مذاکرات", "دیپلماسی", "توافق", "بیانیه", "محکومیت", "هشدار",
        "negotiations", "diplomacy", "agreement", "statement", "condemnation", "warning"
    ]

    # Topics to deprioritize or filter out (-2x weight)
    IRRELEVANT_TOPICS = [
        # Entertainment
        "سینما", "فیلم", "موسیقی", "هنرمند", "بازیگر", "خواننده",
        "cinema", "movie", "music", "artist", "actor", "singer",
        "کنسرت", "جشنواره", "تلویزیون", "شبکه", "سریال",
        "concert", "festival", "television", "network", "series",
        
        # Sports
        "فوتبال", "والیبال", "بسکتبال", "ورزش", "لیگ", "بازیکن", "تیم ملی",
        "football", "soccer", "volleyball", "sports", "league", "player",
        "جام جهانی", "المپیک", "قهرمانی", "مسابقه",
        "world cup", "olympics", "championship", "match",
        
        # Local non-political news
        "آب و هوا", "ترافیک", "تصادف", "آتش‌سوزی", "سیل", "زلزله",
        "weather", "traffic", "accident", "fire", "flood", "earthquake",
        "هواشناسی", "بارش", "برف", "گرما", "سرما",
        "forecast", "rain", "snow", "temperature",
        
        # Commercial
        "تبلیغات", "فروش", "خرید", "تخفیف", "رستوران", "کافه", "هتل",
        "advertisement", "sale", "discount", "restaurant", "cafe", "hotel",
        "خرید و فروش", "املاک", "اجاره", "استخدام",
        "buying", "selling", "real estate", "rental", "hiring",
        
        # Technology/lifestyle (unless conflict-related)
        "گوشی", "اپل", "سامسونگ", "اینستاگرام", "تلگرام",
        "phone", "apple", "samsung", "instagram", "telegram",
        
        # Health/medical (unless conflict-related)
        "پزشک", "بیمارستان", "دارو", "واکسن", "کرونا",
        "doctor", "hospital", "medicine", "vaccine", "corona"
    ]

    @classmethod
    def is_relevant_news(cls, text):
        """
        Determine if news is relevant based on war/geopolitical focus with enhanced scoring.
        
        Args:
            text: News text to analyze
            
        Returns:
            tuple: (is_relevant, relevance_score, matching_topics)
        """
        if not text:
            return False, 0, []

        text_lower = text.lower()
        
        # Find matching topics
        primary_matches = [topic for topic in cls.PRIMARY_TOPICS 
                          if topic.lower() in text_lower]
        secondary_matches = [topic for topic in cls.SECONDARY_TOPICS 
                           if topic.lower() in text_lower]
        irrelevant_matches = [topic for topic in cls.IRRELEVANT_TOPICS 
                            if topic.lower() in text_lower]
        
        # Calculate base relevance score
        relevance_score = (len(primary_matches) * 3) + len(secondary_matches) - (len(irrelevant_matches) * 2)
        
        # Enhanced pattern matching for high-priority content
        high_priority_patterns = [
            # Israel-Iran direct conflict
            r'اسرائیل.*?حمله.*?ایران', r'ایران.*?حمله.*?اسرائیل',
            r'israel.*?attack.*?iran', r'iran.*?attack.*?israel',
            
            # Missile/military actions
            r'موشک.*?شلیک.*?شد', r'حمله.*?هوایی', r'بمباران.*?شد',
            r'missile.*?fired', r'air.*?strike', r'bombing.*?attack',
            
            # Nuclear developments
            r'اورانیوم.*?غنی‌سازی', r'برنامه.*?هسته‌ای', r'تأسیسات.*?هسته‌ای',
            r'uranium.*?enrichment', r'nuclear.*?program', r'nuclear.*?facility',
            
            # Sanctions and economic warfare
            r'تحریم.*?جدید', r'رفع.*?تحریم', r'فشار.*?اقتصادی',
            r'new.*?sanctions', r'sanctions.*?relief', r'economic.*?pressure',
            
            # High-level announcements
            r'نتانیاهو.*?اعلام', r'ایران.*?اعلام', r'آمریکا.*?اعلام',
            r'netanyahu.*?announced', r'iran.*?announced', r'us.*?announced'
        ]
        
        high_priority_count = sum(1 for pattern in high_priority_patterns 
                                if re.search(pattern, text_lower))
        
        # Boost score for high-priority patterns
        if high_priority_count > 0:
            relevance_score += high_priority_count * 4
            logger.debug(f"High priority patterns detected: {high_priority_count}")

        # Apply configuration-based filtering
        if WAR_NEWS_ONLY:
            # Must contain war/conflict terminology
            war_indicators = ["جنگ", "حمله", "موشک", "درگیری", "عملیات", 
                            "war", "attack", "missile", "conflict", "operation"]
            has_war_content = any(indicator in text_lower for indicator in war_indicators)
            if not has_war_content:
                logger.debug("Filtered out: no war content detected")
                return False, relevance_score, primary_matches + secondary_matches
        
        if ISRAEL_IRAN_FOCUS:
            # Boost Israel-Iran content
            israel_iran_indicators = ["اسرائیل", "ایران", "israel", "iran"]
            has_israel_iran = any(indicator in text_lower for indicator in israel_iran_indicators)
            if has_israel_iran:
                relevance_score += 3
                logger.debug("Boosted score for Israel-Iran content")
        
        if GEOPOLITICAL_ONLY:
            # Must have geopolitical relevance
            geopolitical_indicators = [
                "تحریم", "دیپلماسی", "مذاکرات", "توافق", "شورای امنیت",
                "sanctions", "diplomacy", "negotiations", "agreement", "security council"
            ]
            has_geopolitical = any(indicator in text_lower for indicator in geopolitical_indicators)
            if has_geopolitical:
                relevance_score += 2
        
        # Decision logic with multiple thresholds
        is_relevant = False
        
        # Automatic approval conditions
        if relevance_score >= HIGH_PRIORITY_SCORE * 2:  # Very high score
            is_relevant = True
            logger.debug(f"Auto-approved: very high score ({relevance_score})")
        elif high_priority_count >= 2:  # Multiple high-priority patterns
            is_relevant = True
            logger.debug(f"Auto-approved: multiple high-priority patterns ({high_priority_count})")
        elif len(primary_matches) >= 3:  # Many primary topic matches
            is_relevant = True
            logger.debug(f"Auto-approved: many primary matches ({len(primary_matches)})")
        
        # Standard approval conditions
        elif relevance_score >= HIGH_PRIORITY_SCORE:
            is_relevant = True
            logger.debug(f"Approved: high priority score ({relevance_score})")
        elif len(primary_matches) >= 2 and relevance_score >= MIN_RELEVANCE_SCORE:
            is_relevant = True
            logger.debug(f"Approved: multiple primary matches with good score")
        elif high_priority_count >= 1 and len(primary_matches) >= 1:
            is_relevant = True
            logger.debug(f"Approved: high-priority pattern with primary match")
        
        # Override for critical geopolitical events
        critical_keywords = ["جنگ جهانی", "world war", "هسته‌ای", "nuclear war", "تحریم کامل"]
        has_critical = any(keyword in text_lower for keyword in critical_keywords)
        if has_critical and len(primary_matches) >= 1:
            is_relevant = True
            relevance_score += 5
            logger.debug("Override: critical geopolitical event detected")
        
        # Final filtering - reject if too many irrelevant indicators
        if len(irrelevant_matches) >= 3 and relevance_score < HIGH_PRIORITY_SCORE:
            is_relevant = False
            logger.debug("Rejected: too many irrelevant topics")
        
        all_matches = primary_matches + secondary_matches
        
        if is_relevant:
            logger.info(f"✅ Relevant news detected (score: {relevance_score}): {all_matches[:3]}")
        else:
            logger.debug(f"❌ News filtered out (score: {relevance_score}): {text[:100]}...")
        
        return is_relevant, relevance_score, all_matches