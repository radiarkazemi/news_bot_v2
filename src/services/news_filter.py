"""
Expanded news filter for financial and geopolitical content.
"""
import logging
import re

logger = logging.getLogger(__name__)

class NewsFilter:
    """Expanded filter for financial and geopolitical news with market impact."""
    
    # CRITICAL KEYWORDS (Highest Priority)
    CRITICAL_KEYWORDS = [
        # Persian critical
        "ایران", "اسرائیل", "ترامپ", "بایدن", "جنگ", "حمله", "تهدید", "هسته‌ای",
        "تحریم", "طلا", "دلار", "یورو", "نفت", "بحران", "اقتصاد",
        
        # English critical  
        "iran", "israel", "trump", "biden", "war", "attack", "threat", "nuclear",
        "sanctions", "gold", "dollar", "euro", "oil", "crisis", "economy"
    ]
    
    # HIGH PRIORITY KEYWORDS
    HIGH_PRIORITY_KEYWORDS = [
        # Persian high priority
        "آمریکا", "واشنگتن", "تل‌آویو", "تهران", "سپاه", "حزب‌الله", "حماس", "غزه",
        "موشک", "پهپاد", "بمباران", "عملیات", "نظامی", "ارتش", "بازار", "بورس",
        "نرخ", "قیمت", "ارز", "صرافی", "بانک‌مرکزی", "تورم", "صادرات", "واردات",
        
        # English high priority
        "america", "washington", "telaviv", "tehran", "irgc", "hezbollah", "hamas", "gaza",
        "missile", "drone", "bombing", "operation", "military", "army", "market", "stock",
        "rate", "price", "currency", "exchange", "central", "bank", "inflation", "export"
    ]
    
    # GEOPOLITICAL REGIONS
    REGIONAL_KEYWORDS = [
        # Persian regions
        "خاورمیانه", "خلیج‌فارس", "فلسطین", "لبنان", "سوریه", "عراق", "یمن", "عربستان",
        "امارات", "کویت", "قطر", "بحرین", "عمان", "ترکیه", "پاکستان", "افغانستان",
        
        # English regions
        "middle", "east", "persian", "gulf", "palestine", "lebanon", "syria", "iraq",
        "yemen", "saudi", "arabia", "uae", "kuwait", "qatar", "bahrain", "oman", "turkey"
    ]
    
    # ECONOMIC WARFARE KEYWORDS
    ECONOMIC_WARFARE_KEYWORDS = [
        # Persian economic warfare
        "جنگ‌اقتصادی", "تحریم‌اقتصادی", "محاصره‌اقتصادی", "فشار‌اقتصادی", "عقوبات",
        "مسدود‌کردن", "دارایی", "منابع", "سوئیفت", "بانکی", "مالی", "سرمایه",
        
        # English economic warfare
        "economic", "warfare", "embargo", "blockade", "freeze", "assets", "swift",
        "financial", "monetary", "capital", "trade", "commerce"
    ]

    @classmethod
    def is_relevant_news(cls, text):
        """
        Enhanced relevance check for financial and geopolitical news.
        
        Returns:
            tuple: (is_relevant, relevance_score, matching_topics)
        """
        if not text or len(text.strip()) < 30:
            return False, 0, []
        
        text_lower = text.lower()
        matching_topics = []
        relevance_score = 0
        
        # Critical keywords (score: 10 each)
        critical_matches = [kw for kw in cls.CRITICAL_KEYWORDS if kw in text_lower]
        if critical_matches:
            relevance_score += len(critical_matches) * 10
            matching_topics.extend([f"CRITICAL:{kw}" for kw in critical_matches[:3]])
        
        # High priority keywords (score: 5 each)
        high_matches = [kw for kw in cls.HIGH_PRIORITY_KEYWORDS if kw in text_lower]
        if high_matches:
            relevance_score += len(high_matches) * 5
            matching_topics.extend([f"HIGH:{kw}" for kw in high_matches[:3]])
        
        # Regional keywords (score: 3 each)
        regional_matches = [kw for kw in cls.REGIONAL_KEYWORDS if kw in text_lower]
        if regional_matches:
            relevance_score += len(regional_matches) * 3
            matching_topics.extend([f"REGION:{kw}" for kw in regional_matches[:2]])
        
        # Economic warfare keywords (score: 7 each)
        econ_war_matches = [kw for kw in cls.ECONOMIC_WARFARE_KEYWORDS if kw in text_lower]
        if econ_war_matches:
            relevance_score += len(econ_war_matches) * 7
            matching_topics.extend([f"ECON_WAR:{kw}" for kw in econ_war_matches[:2]])
        
        # Bonus for news structure patterns
        if cls._has_news_structure(text):
            relevance_score += 5
            matching_topics.append("NEWS_STRUCTURE")
        
        # Bonus for multiple entities (Iran + USA, Israel + Gaza, etc.)
        entity_bonus = cls._calculate_entity_bonus(text_lower)
        relevance_score += entity_bonus
        if entity_bonus > 0:
            matching_topics.append(f"MULTI_ENTITY:{entity_bonus}")
        
        # Determine relevance with multiple thresholds
        is_relevant = cls._determine_enhanced_relevance(
            relevance_score, critical_matches, high_matches, text_lower
        )
        
        # Clean up matching topics
        matching_topics = list(dict.fromkeys(matching_topics))[:10]
        
        # Log for debugging
        if relevance_score > 0:
            logger.debug(f"Enhanced relevance: score={relevance_score}, "
                        f"critical={len(critical_matches)}, high={len(high_matches)}, "
                        f"is_relevant={is_relevant}")
        
        return is_relevant, relevance_score, matching_topics

    @classmethod
    def _has_news_structure(cls, text):
        """Check if text has news-like structure."""
        # Look for news patterns
        news_patterns = [
            r'گزارش\s+می‌دهد',  # reports
            r'اعلام\s+کرد',      # announced
            r'بیان\s+داشت',     # stated
            r'گفت',             # said
            r'مدعی\s+شد',       # claimed
            r'تأیید\s+کرد',     # confirmed
            r'منابع\s+خبری',    # news sources
            r'خبرگزاری',        # news agency
            r'آژانس',           # agency
            r':[^:]+$',         # ends with colon (common in news)
        ]
        
        return any(re.search(pattern, text) for pattern in news_patterns)

    @classmethod
    def _calculate_entity_bonus(cls, text_lower):
        """Calculate bonus for multiple important entities mentioned."""
        entities = {
            'iran': any(kw in text_lower for kw in ['ایران', 'iran', 'iranian']),
            'israel': any(kw in text_lower for kw in ['اسرائیل', 'israel', 'israeli']),
            'usa': any(kw in text_lower for kw in ['آمریکا', 'امریکا', 'america', 'usa', 'washington']),
            'trump': any(kw in text_lower for kw in ['ترامپ', 'trump']),
            'gaza': any(kw in text_lower for kw in ['غزه', 'gaza', 'palestine']),
            'war': any(kw in text_lower for kw in ['جنگ', 'حمله', 'war', 'attack', 'conflict']),
            'nuclear': any(kw in text_lower for kw in ['هسته‌ای', 'اتمی', 'nuclear', 'atomic']),
            'sanctions': any(kw in text_lower for kw in ['تحریم', 'sanctions', 'embargo'])
        }
        
        entity_count = sum(entities.values())
        
        # Bonus scoring
        if entity_count >= 4:
            return 10  # Multiple major entities
        elif entity_count >= 3:
            return 7   # Several entities
        elif entity_count >= 2:
            return 5   # Two entities
        else:
            return 0

    @classmethod
    def _determine_enhanced_relevance(cls, score, critical_matches, high_matches, text_lower):
        """Enhanced relevance determination with multiple criteria."""
        
        # Always relevant if multiple critical keywords
        if len(critical_matches) >= 2:
            return True
        
        # Always relevant if single critical + high score
        if critical_matches and score >= 15:
            return True
        
        # High threshold for general content
        if score >= 25:
            return True
        
        # Medium threshold for news with structure
        if score >= 15 and cls._has_news_structure(text_lower):
            return True
        
        # Lower threshold for Iran-specific content
        iran_content = any(kw in text_lower for kw in ['ایران', 'iran', 'iranian', 'tehran', 'تهران'])
        if iran_content and score >= 10:
            return True
        
        # War/conflict threshold
        war_content = any(kw in text_lower for kw in ['جنگ', 'حمله', 'war', 'attack', 'conflict', 'threat'])
        if war_content and score >= 12:
            return True
        
        # Economic crisis threshold
        crisis_content = any(kw in text_lower for kw in ['بحران', 'تحریم', 'crisis', 'sanctions', 'embargo'])
        if crisis_content and score >= 10:
            return True
        
        # Standard threshold
        return score >= 20

    @classmethod
    def get_priority_level(cls, relevance_score):
        """Get priority level based on enhanced scoring."""
        if relevance_score >= 50:
            return "CRITICAL"
        elif relevance_score >= 30:
            return "URGENT"
        elif relevance_score >= 20:
            return "HIGH"
        elif relevance_score >= 10:
            return "NORMAL"
        else:
            return "LOW"

    @classmethod
    def get_news_category(cls, text, matching_topics):
        """Determine primary news category from enhanced analysis."""
        text_lower = text.lower()
        
        # Analyze critical patterns
        if any('CRITICAL:هسته‌ای' in topic or 'CRITICAL:nuclear' in topic for topic in matching_topics):
            return "NUCLEAR_CRISIS"
        elif any('CRITICAL:جنگ' in topic or 'CRITICAL:war' in topic for topic in matching_topics):
            return "WAR_CONFLICT"
        elif any('CRITICAL:ایران' in topic for topic in matching_topics):
            return "IRAN_GEOPOLITICAL"
        elif any('CRITICAL:اسرائیل' in topic or 'CRITICAL:israel' in topic for topic in matching_topics):
            return "ISRAEL_OPERATIONS"
        elif any('CRITICAL:طلا' in topic or 'CRITICAL:gold' in topic for topic in matching_topics):
            return "GOLD_MARKETS"
        elif any('CRITICAL:دلار' in topic or 'CRITICAL:dollar' in topic for topic in matching_topics):
            return "CURRENCY_MARKETS"
        elif any('ECON_WAR:' in topic for topic in matching_topics):
            return "ECONOMIC_WARFARE"
        else:
            return "GEOPOLITICAL_ECONOMIC"