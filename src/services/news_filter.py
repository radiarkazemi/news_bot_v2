"""
Enhanced news filter for financial and geopolitical content.
Optimized for Iranian financial news with lower thresholds.
"""
import logging
import re

logger = logging.getLogger(__name__)

class NewsFilter:
    """Enhanced filter for financial and geopolitical news with market impact."""
    
    # CRITICAL FINANCIAL KEYWORDS (Highest Priority)
    CRITICAL_FINANCIAL_KEYWORDS = [
        # Persian critical financial
        "طلا", "سکه", "دلار", "یورو", "ارز", "نرخ", "قیمت", "بازار",
        "افزایش", "کاهش", "رشد", "سقوط", "جهش", "ثبت",
        "بانک‌مرکزی", "تورم", "اقتصاد", "بورس", "سهام",
        
        # English critical financial  
        "gold", "dollar", "euro", "currency", "rate", "price", "market",
        "economy", "economic", "inflation", "bank", "stock"
    ]
    
    # HIGH PRIORITY KEYWORDS
    HIGH_PRIORITY_KEYWORDS = [
        # Persian high priority
        "ایران", "ایرانی", "تهران", "کشور", "ملی", "دولت",
        "صرافی", "صرافی‌ها", "تجارت", "صادرات", "واردات",
        "نفت", "گاز", "انرژی", "پتروشیمی", "صنعت", "تولید",
        "سرمایه", "سرمایه‌گذاری", "مالی", "بودجه",
        
        # English high priority
        "iran", "iranian", "tehran", "trade", "export", "import",
        "oil", "gas", "energy", "investment", "financial", "budget"
    ]
    
    # GEOPOLITICAL KEYWORDS
    GEOPOLITICAL_KEYWORDS = [
        # Persian geopolitical
        "تحریم", "تحریم‌ها", "عقوبات", "فشار‌اقتصادی", "جنگ‌اقتصادی",
        "آمریکا", "امریکا", "اسرائیل", "اروپا", "چین", "روسیه",
        "برجام", "مذاکره", "توافق", "سیاست", "دیپلماسی",
        
        # English geopolitical
        "sanctions", "embargo", "america", "israel", "china", "russia",
        "nuclear", "diplomacy", "political", "agreement", "jcpoa"
    ]
    
    # TECHNICAL ANALYSIS KEYWORDS
    TECHNICAL_KEYWORDS = [
        # Persian technical
        "تحلیل", "پیش‌بینی", "انتظار", "احتمال", "روند", "گزارش",
        "شاخص", "نمودار", "آمار", "اطلاعات", "داده", "رقم",
        
        # English technical
        "analysis", "forecast", "prediction", "trend", "report",
        "index", "chart", "data", "statistics", "figure"
    ]

    @classmethod
    def is_relevant_news(cls, text):
        """
        Enhanced relevance check for financial news with LOWER thresholds.
        
        Returns:
            tuple: (is_relevant, relevance_score, matching_topics)
        """
        if not text or len(text.strip()) < 30:
            return False, 0, []
        
        text_lower = text.lower()
        matching_topics = []
        relevance_score = 0
        
        # Critical financial keywords (score: 5 each - LOWERED from 10)
        critical_matches = [kw for kw in cls.CRITICAL_FINANCIAL_KEYWORDS if kw in text_lower]
        if critical_matches:
            relevance_score += len(critical_matches) * 5
            matching_topics.extend([f"FINANCIAL:{kw}" for kw in critical_matches[:3]])
        
        # High priority keywords (score: 3 each - LOWERED from 5)
        high_matches = [kw for kw in cls.HIGH_PRIORITY_KEYWORDS if kw in text_lower]
        if high_matches:
            relevance_score += len(high_matches) * 3
            matching_topics.extend([f"HIGH:{kw}" for kw in high_matches[:3]])
        
        # Geopolitical keywords (score: 2 each - SAME)
        geo_matches = [kw for kw in cls.GEOPOLITICAL_KEYWORDS if kw in text_lower]
        if geo_matches:
            relevance_score += len(geo_matches) * 2
            matching_topics.extend([f"GEO:{kw}" for kw in geo_matches[:2]])
        
        # Technical analysis keywords (score: 1 each)
        tech_matches = [kw for kw in cls.TECHNICAL_KEYWORDS if kw in text_lower]
        if tech_matches:
            relevance_score += len(tech_matches) * 1
            matching_topics.extend([f"TECH:{kw}" for kw in tech_matches[:2]])
        
        # Bonus for news structure patterns
        if cls._has_news_structure(text):
            relevance_score += 2  # LOWERED from 5
            matching_topics.append("NEWS_STRUCTURE")
        
        # Bonus for multiple financial entities
        entity_bonus = cls._calculate_financial_entity_bonus(text_lower)
        relevance_score += entity_bonus
        if entity_bonus > 0:
            matching_topics.append(f"MULTI_FINANCIAL:{entity_bonus}")
        
        # Determine relevance with LOWERED thresholds
        is_relevant = cls._determine_financial_relevance(
            relevance_score, critical_matches, high_matches, text_lower
        )
        
        # Clean up matching topics
        matching_topics = list(dict.fromkeys(matching_topics))[:10]
        
        # Log for debugging
        if relevance_score > 0:
            logger.debug(f"Financial relevance: score={relevance_score}, "
                        f"critical={len(critical_matches)}, high={len(high_matches)}, "
                        f"is_relevant={is_relevant}")
        
        return is_relevant, relevance_score, matching_topics

    @classmethod
    def _has_news_structure(cls, text):
        """Check if text has news-like structure."""
        # Look for news patterns
        news_patterns = [
            r'اعلام\s+(شد|کرد)',      # announced
            r'گزارش\s+می‌دهد',       # reports
            r'بیان\s+داشت',          # stated
            r'تأیید\s+کرد',          # confirmed
            r'منابع\s+خبری',         # news sources
            r'خبرگزاری',             # news agency
            r'آژانس',                # agency
            r'قیمت\s+.+\s+رسید',     # price reached
            r'نرخ\s+.+\s+شد',        # rate became
            r'بازار\s+.+\s+(بسته|باز)', # market closed/opened
            r'\d+\s+(تومان|دلار|یورو)', # numbers with currency
        ]
        
        return any(re.search(pattern, text) for pattern in news_patterns)

    @classmethod
    def _calculate_financial_entity_bonus(cls, text_lower):
        """Calculate bonus for multiple financial entities mentioned."""
        financial_entities = {
            'gold': any(kw in text_lower for kw in ['طلا', 'سکه', 'gold', 'ounce']),
            'currency': any(kw in text_lower for kw in ['دلار', 'یورو', 'ارز', 'dollar', 'euro', 'currency']),
            'iran_economy': any(kw in text_lower for kw in ['ایران', 'تهران', 'iran', 'iranian']),
            'market': any(kw in text_lower for kw in ['بازار', 'بورس', 'market', 'stock']),
            'price': any(kw in text_lower for kw in ['قیمت', 'نرخ', 'price', 'rate']),
            'bank': any(kw in text_lower for kw in ['بانک', 'bank', 'central']),
            'oil': any(kw in text_lower for kw in ['نفت', 'گاز', 'oil', 'gas']),
            'crypto': any(kw in text_lower for kw in ['بیت‌کوین', 'bitcoin', 'crypto'])
        }
        
        entity_count = sum(financial_entities.values())
        
        # LOWERED bonus scoring
        if entity_count >= 4:
            return 5  # was 10
        elif entity_count >= 3:
            return 3  # was 7
        elif entity_count >= 2:
            return 2  # was 5
        else:
            return 0

    @classmethod
    def _determine_financial_relevance(cls, score, critical_matches, high_matches, text_lower):
        """Enhanced relevance determination with LOWERED criteria for financial news."""
        
        # Always relevant if strong financial content
        if len(critical_matches) >= 2:
            return True
        
        # Always relevant if single financial keyword + decent score
        if critical_matches and score >= 8:  # LOWERED from 15
            return True
        
        # LOWERED threshold for general financial content
        if score >= 10:  # LOWERED from 25
            return True
        
        # LOWERED threshold for news with structure
        if score >= 6 and cls._has_news_structure(text_lower):  # LOWERED from 15
            return True
        
        # Iran-specific financial content
        iran_content = any(kw in text_lower for kw in ['ایران', 'iran', 'iranian', 'tehran', 'تهران'])
        if iran_content and score >= 5:  # LOWERED from 10
            return True
        
        # Strong financial indicators (gold, currency, etc.)
        strong_financial = any(kw in text_lower for kw in [
            'طلا', 'سکه', 'دلار', 'یورو', 'gold', 'dollar', 'euro', 'ارز', 'نرخ', 'قیمت'
        ])
        if strong_financial and score >= 4:  # LOWERED from 8
            return True
        
        # Economic/market content
        market_content = any(kw in text_lower for kw in ['بازار', 'بورس', 'market', 'stock', 'اقتصاد', 'economy'])
        if market_content and score >= 3:  # LOWERED from 10
            return True
        
        # Standard threshold - SIGNIFICANTLY LOWERED
        return score >= 8  # LOWERED from 20

    @classmethod
    def get_priority_level(cls, relevance_score):
        """Get priority level based on enhanced scoring - LOWERED thresholds."""
        if relevance_score >= 25:      # was 50
            return "CRITICAL"
        elif relevance_score >= 15:    # was 30
            return "URGENT"
        elif relevance_score >= 8:     # was 20
            return "HIGH"
        elif relevance_score >= 4:     # was 10
            return "NORMAL"
        else:
            return "LOW"

    @classmethod
    def get_financial_category(cls, text, matching_topics):
        """Determine primary financial category from enhanced analysis."""
        if not matching_topics:
            return "GENERAL_FINANCIAL"
        
        # Count different category types
        category_counts = {}
        for topic in matching_topics:
            if ':' in topic:
                category = topic.split(':')[0]
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Determine based on topic analysis and text content
        text_lower = text.lower() if text else ""
        
        if any('طلا' in topic or 'سکه' in topic or 'gold' in topic for topic in matching_topics):
            return "GOLD_PRECIOUS"
        elif any('دلار' in topic or 'یورو' in topic or 'ارز' in topic or 'dollar' in topic or 'euro' in topic for topic in matching_topics):
            return "CURRENCY_FOREX"
        elif any('نفت' in topic or 'گاز' in topic or 'oil' in topic or 'gas' in topic for topic in matching_topics):
            return "OIL_ENERGY"
        elif any('بیت‌کوین' in topic or 'bitcoin' in topic or 'crypto' in topic for topic in matching_topics):
            return "CRYPTOCURRENCY"
        elif any('بورس' in topic or 'سهام' in topic or 'stock' in topic for topic in matching_topics):
            return "STOCK_MARKET"
        elif any('تحریم' in topic or 'sanctions' in topic for topic in matching_topics):
            return "ECONOMIC_SANCTIONS"
        elif any('ایران' in topic or 'iran' in topic for topic in matching_topics):
            return "IRANIAN_ECONOMY"
        else:
            return "GENERAL_FINANCIAL"