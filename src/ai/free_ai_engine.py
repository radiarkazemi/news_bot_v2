"""
FREE AI Engine for News Approval - No API Costs!
Uses local models, enhanced rules, and machine learning concepts.
100% Free and offline operation.
"""
import asyncio
import logging
import json
import re
import time
import pickle
import hashlib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

# Free AI imports
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.linear_model import LogisticRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class FreeAIResult:
    """Result from free AI analysis."""
    decision: str  # 'approve', 'reject', 'human_review'
    confidence: float  # 0.0 to 10.0
    reasoning: str
    category: str
    financial_score: float
    quality_score: float
    sentiment_score: float
    entity_score: float
    risk_factors: List[str]
    detected_entities: List[str]
    processing_time: float

class FreeAIModels:
    """Manages free local AI models."""
    
    def __init__(self):
        self.models = {}
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        self.cache_dir = Path("ai_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        logger.info("🤖 Initializing FREE AI models...")

    async def initialize_models(self):
        """Initialize all free AI models."""
        try:
            # Sentiment Analysis Model (Free)
            if TRANSFORMERS_AVAILABLE:
                logger.info("📥 Loading sentiment analysis model...")
                self.models['sentiment'] = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
                    return_all_scores=True
                )
                logger.info("✅ Sentiment model loaded")
            
            # Multilingual NER Model (Free)
            if TRANSFORMERS_AVAILABLE:
                logger.info("📥 Loading NER model...")
                self.models['ner'] = pipeline(
                    "ner",
                    model="Babelscape/wikineural-multilingual-ner",
                    aggregation_strategy="simple"
                )
                logger.info("✅ NER model loaded")
            
            # Sentence Embeddings (Free)
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.info("📥 Loading sentence embeddings...")
                self.models['embeddings'] = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )
                logger.info("✅ Embeddings model loaded")
            
            # spaCy model (Free)
            if SPACY_AVAILABLE:
                try:
                    logger.info("📥 Loading spaCy model...")
                    self.models['spacy'] = spacy.load("en_core_web_sm")
                    logger.info("✅ spaCy model loaded")
                except OSError:
                    logger.warning("spaCy model not found, skipping...")
            
            # Initialize custom models
            await self._initialize_custom_models()
            
            logger.info("🎉 All FREE AI models initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing models: {e}")
            # Continue with rule-based fallback
            
    async def _initialize_custom_models(self):
        """Initialize custom trained models."""
        try:
            # Load pre-trained financial classifier if exists
            classifier_path = self.model_dir / "financial_classifier.pkl"
            if classifier_path.exists():
                with open(classifier_path, 'rb') as f:
                    self.models['financial_classifier'] = pickle.load(f)
                logger.info("✅ Custom financial classifier loaded")
            else:
                # Create and train basic classifier
                await self._create_basic_financial_classifier()
            
        except Exception as e:
            logger.warning(f"Custom models initialization failed: {e}")

    async def _create_basic_financial_classifier(self):
        """Create a basic financial news classifier using free tools."""
        if not SKLEARN_AVAILABLE:
            return
            
        try:
            # Sample training data (you can expand this)
            training_data = [
                # Financial news (positive examples)
                ("قیمت طلا افزایش یافت", 1),
                ("دلار در بازار آزاد گران شد", 1),
                ("بورس تهران رشد کرد", 1),
                ("نرخ ارز تغییر کرد", 1),
                ("بانک مرکزی اعلام کرد", 1),
                ("سکه طلا ارزان شد", 1),
                ("تحریم اقتصادی جدید", 1),
                ("نفت خام گران شد", 1),
                
                # Non-financial news (negative examples)  
                ("تیم فوتبال برد", 0),
                ("فیلم جدید اکران شد", 0),
                ("آب و هوا بارانی است", 0),
                ("جشنواره موسیقی برگزار شد", 0),
                ("رستوران جدید باز شد", 0),
                ("کتاب جدید منتشر شد", 0),
                ("بازی کامپیوتری جدید", 0),
                ("مسابقه ورزشی", 0),
            ]
            
            texts = [item[0] for item in training_data]
            labels = [item[1] for item in training_data]
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
            X = vectorizer.fit_transform(texts)
            
            # Train classifier
            classifier = LogisticRegression()
            classifier.fit(X, labels)
            
            # Save the model
            model_data = {
                'vectorizer': vectorizer,
                'classifier': classifier,
                'created': time.time()
            }
            
            with open(self.model_dir / "financial_classifier.pkl", 'wb') as f:
                pickle.dump(model_data, f)
            
            self.models['financial_classifier'] = model_data
            logger.info("✅ Basic financial classifier created and saved")
            
        except Exception as e:
            logger.error(f"Failed to create basic classifier: {e}")

    def get_model(self, model_name: str):
        """Get a loaded model."""
        return self.models.get(model_name)

class FreeAIEngine:
    """
    Complete FREE AI engine for news approval.
    Uses local models, enhanced rules, and learning algorithms.
    """
    
    def __init__(self):
        self.models = FreeAIModels()
        self.learning_data = defaultdict(list)
        self.pattern_cache = {}
        
        # Enhanced rule-based scoring weights
        self.weights = {
            'financial_keywords': 3.0,
            'iranian_economy': 2.5, 
            'news_structure': 1.5,
            'entity_recognition': 2.0,
            'sentiment_relevance': 1.0,
            'quality_indicators': 2.0,
            'risk_factors': -2.0,  # Negative weight
            'length_appropriateness': 1.0
        }
        
        # Statistics
        self.stats = {
            'total_analyzed': 0,
            'auto_approved': 0,
            'auto_rejected': 0,
            'human_review': 0,
            'average_confidence': 0.0,
            'average_processing_time': 0.0
        }
        
        # Load learning data
        self._load_learning_data()

    async def initialize(self):
        """Initialize the AI engine."""
        logger.info("🚀 Initializing FREE AI Engine...")
        await self.models.initialize_models()
        logger.info("✅ FREE AI Engine ready!")

    async def analyze_news(self, text: str, metadata: Dict = None) -> FreeAIResult:
        """
        Main analysis function - FREE AI news approval.
        
        Args:
            text: News text to analyze
            metadata: Additional context
            
        Returns:
            FreeAIResult: Complete analysis with decision
        """
        start_time = time.time()
        
        try:
            logger.info(f"🤖 FREE AI analyzing: {text[:100]}...")
            
            # Multi-layer analysis
            financial_analysis = await self._analyze_financial_content(text)
            quality_analysis = await self._analyze_content_quality(text)
            sentiment_analysis = await self._analyze_sentiment(text)
            entity_analysis = await self._analyze_entities(text)
            risk_analysis = await self._analyze_risk_factors(text)
            
            # Enhanced rule-based scoring
            enhanced_score = await self._calculate_enhanced_score(
                text, financial_analysis, quality_analysis, 
                sentiment_analysis, entity_analysis
            )
            
            # Make decision
            decision, confidence, reasoning = await self._make_decision(
                enhanced_score, financial_analysis, quality_analysis,
                risk_analysis, text
            )
            
            processing_time = time.time() - start_time
            
            # Create result
            result = FreeAIResult(
                decision=decision,
                confidence=confidence,
                reasoning=reasoning,
                category=financial_analysis.get('category', 'unknown'),
                financial_score=enhanced_score.get('financial_score', 0),
                quality_score=enhanced_score.get('quality_score', 0),
                sentiment_score=sentiment_analysis.get('relevance_score', 0),
                entity_score=entity_analysis.get('score', 0),
                risk_factors=risk_analysis.get('factors', []),
                detected_entities=entity_analysis.get('entities', []),
                processing_time=processing_time
            )
            
            # Update statistics
            self._update_stats(result)
            
            # Learn from patterns
            await self._learn_from_analysis(text, result)
            
            logger.info(f"🎯 FREE AI Decision: {decision} (confidence: {confidence:.1f}/10)")
            return result
            
        except Exception as e:
            logger.error(f"❌ FREE AI analysis failed: {e}")
            # Return safe fallback
            return FreeAIResult(
                decision='human_review',
                confidence=5.0,
                reasoning=f"AI error, requires human review: {str(e)}",
                category='error',
                financial_score=5.0,
                quality_score=5.0,
                sentiment_score=0.0,
                entity_score=0.0,
                risk_factors=['ai_error'],
                detected_entities=[],
                processing_time=time.time() - start_time
            )

    async def _analyze_financial_content(self, text: str) -> Dict:
        """Analyze financial content using multiple free methods."""
        analysis = {}
        
        # Enhanced keyword analysis
        financial_keywords = {
            'gold': ['طلا', 'سکه', 'اونس', 'گرم', 'gold', 'ounce', 'bullion'],
            'currency': ['دلار', 'یورو', 'پوند', 'ارز', 'نرخ', 'dollar', 'euro', 'currency', 'exchange'],
            'iranian_economy': ['ایران', 'تهران', 'ریال', 'تومان', 'iran', 'iranian', 'tehran'],
            'market': ['بازار', 'بورس', 'سهام', 'شاخص', 'market', 'stock', 'index'],
            'banking': ['بانک', 'بانکی', 'سپرده', 'وام', 'bank', 'banking', 'loan'],
            'oil_energy': ['نفت', 'گاز', 'انرژی', 'بنزین', 'oil', 'gas', 'energy'],
            'crypto': ['بیت‌کوین', 'ارز دیجیتال', 'bitcoin', 'cryptocurrency', 'crypto']
        }
        
        category_scores = {}
        text_lower = text.lower()
        
        for category, keywords in financial_keywords.items():
            score = sum(3 if kw in text_lower else 0 for kw in keywords)
            # Bonus for multiple keywords in same category
            keyword_count = sum(1 for kw in keywords if kw in text_lower)
            if keyword_count > 1:
                score += keyword_count * 2
            category_scores[category] = score
        
        # Determine primary category
        primary_category = max(category_scores, key=category_scores.get)
        total_score = sum(category_scores.values())
        
        # Use custom classifier if available
        if 'financial_classifier' in self.models.models:
            try:
                classifier_data = self.models.get_model('financial_classifier')
                vectorizer = classifier_data['vectorizer']
                classifier = classifier_data['classifier']
                
                text_vector = vectorizer.transform([text])
                probability = classifier.predict_proba(text_vector)[0]
                financial_probability = probability[1] if len(probability) > 1 else 0.5
                
                # Boost score based on classifier confidence
                total_score += financial_probability * 10
                
            except Exception as e:
                logger.debug(f"Classifier analysis failed: {e}")
        
        analysis.update({
            'category': primary_category,
            'total_score': total_score,
            'category_scores': category_scores,
            'financial_relevance': min(total_score / 5, 10),  # Normalize to 0-10
        })
        
        return analysis

    async def _analyze_content_quality(self, text: str) -> Dict:
        """Analyze content quality using free methods."""
        quality_factors = {}
        
        # Length analysis
        word_count = len(text.split())
        char_count = len(text)
        
        quality_factors['appropriate_length'] = 1.0 if 30 <= word_count <= 300 else 0.5
        quality_factors['reasonable_char_count'] = 1.0 if 100 <= char_count <= 2000 else 0.7
        
        # Structure analysis
        news_indicators = [
            'اعلام', 'گزارش', 'خبر', 'فوری', 'بر اساس', 'منابع', 
            'announced', 'reported', 'breaking', 'according'
        ]
        has_news_structure = any(indicator in text.lower() for indicator in news_indicators)
        quality_factors['news_structure'] = 1.0 if has_news_structure else 0.3
        
        # Numerical data (good for financial news)
        has_numbers = bool(re.search(r'\d+', text))
        has_financial_numbers = bool(re.search(r'\d+.*(?:تومان|دلار|یورو|درصد|٪)', text))
        quality_factors['has_numbers'] = 1.0 if has_numbers else 0.5
        quality_factors['financial_numbers'] = 1.0 if has_financial_numbers else 0.7
        
        # Language quality
        excessive_caps = len(re.findall(r'[A-Z]{3,}', text)) > 3
        excessive_emojis = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text)) > 5
        quality_factors['language_quality'] = 0.3 if (excessive_caps or excessive_emojis) else 1.0
        
        # Calculate overall quality score
        overall_quality = sum(quality_factors.values()) / len(quality_factors)
        
        return {
            'overall_quality': overall_quality,
            'quality_factors': quality_factors,
            'word_count': word_count,
            'char_count': char_count
        }

    async def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment using free models."""
        sentiment_data = {}
        
        try:
            # Use transformer model if available
            sentiment_model = self.models.get_model('sentiment')
            if sentiment_model:
                results = sentiment_model(text)
                
                # Convert to relevance score
                sentiment_scores = {}
                for result in results:
                    sentiment_scores[result['label']] = result['score']
                
                # For financial news, we care more about neutral/informative tone
                relevance_score = 0.0
                if 'NEUTRAL' in sentiment_scores:
                    relevance_score = sentiment_scores['NEUTRAL'] * 8
                elif 'POSITIVE' in sentiment_scores or 'NEGATIVE' in sentiment_scores:
                    # Strong sentiment can be relevant for market-moving news
                    max_sentiment = max(sentiment_scores.values())
                    if max_sentiment > 0.8:  # Strong conviction
                        relevance_score = 7.0
                    else:
                        relevance_score = 5.0
                
                sentiment_data.update({
                    'sentiment_scores': sentiment_scores,
                    'relevance_score': relevance_score,
                    'confidence': max(sentiment_scores.values())
                })
                
        except Exception as e:
            logger.debug(f"Sentiment analysis failed: {e}")
            
        # Fallback rule-based sentiment
        if not sentiment_data:
            # Simple rule-based sentiment for financial context
            positive_indicators = ['افزایش', 'رشد', 'بهبود', 'موفقیت', 'increase', 'growth', 'success']
            negative_indicators = ['کاهش', 'سقوط', 'بحران', 'کمبود', 'decrease', 'fall', 'crisis']
            
            positive_count = sum(1 for indicator in positive_indicators if indicator in text.lower())
            negative_count = sum(1 for indicator in negative_indicators if indicator in text.lower())
            
            if positive_count > negative_count:
                sentiment_data['relevance_score'] = 6.0 + min(positive_count, 2)
            elif negative_count > positive_count:
                sentiment_data['relevance_score'] = 6.0 + min(negative_count, 2)
            else:
                sentiment_data['relevance_score'] = 5.0  # Neutral
                
        return sentiment_data

    async def _analyze_entities(self, text: str) -> Dict:
        """Analyze named entities using free models."""
        entity_data = {'entities': [], 'score': 0}
        
        try:
            # Use NER model if available
            ner_model = self.models.get_model('ner')
            if ner_model:
                entities = ner_model(text)
                
                financial_entities = []
                for entity in entities:
                    # Filter for financially relevant entities
                    if entity['entity_group'] in ['PER', 'ORG', 'LOC', 'MISC']:
                        financial_entities.append({
                            'text': entity['word'],
                            'label': entity['entity_group'],
                            'confidence': entity['score']
                        })
                
                entity_data['entities'] = financial_entities
                entity_data['score'] = len(financial_entities) * 1.5
                
        except Exception as e:
            logger.debug(f"NER analysis failed: {e}")
            
        # Fallback rule-based entity extraction
        if not entity_data['entities']:
            # Extract Iranian financial entities
            iranian_entities = [
                'بانک مرکزی', 'بورس تهران', 'وزارت اقتصاد', 'اتاق بازرگانی',
                'central bank', 'tehran stock exchange', 'ministry of economy'
            ]
            
            found_entities = []
            for entity in iranian_entities:
                if entity in text.lower():
                    found_entities.append({
                        'text': entity,
                        'label': 'ORG',
                        'confidence': 0.9
                    })
            
            # Extract currency amounts
            currency_pattern = r'(\d+(?:\.\d+)?)\s*(تومان|دلار|یورو|ریال|dollar|euro)'
            currency_matches = re.findall(currency_pattern, text, re.IGNORECASE)
            for amount, currency in currency_matches:
                found_entities.append({
                    'text': f"{amount} {currency}",
                    'label': 'MONEY',
                    'confidence': 0.95
                })
            
            entity_data['entities'] = found_entities
            entity_data['score'] = len(found_entities) * 2
        
        return entity_data

    async def _analyze_risk_factors(self, text: str) -> Dict:
        """Analyze potential risk factors."""
        risk_factors = []
        
        # Check for speculation
        speculation_words = [
            'شایعه', 'احتمال', 'ممکن است', 'گفته می‌شود', 
            'rumor', 'maybe', 'might', 'speculation', 'allegedly'
        ]
        if any(word in text.lower() for word in speculation_words):
            risk_factors.append('speculation')
        
        # Check for unverified sources
        unverified_indicators = [
            'منابع ناشناس', 'منابع آگاه', 'گمنام', 'anonymous sources', 'unnamed sources'
        ]
        if any(indicator in text.lower() for indicator in unverified_indicators):
            risk_factors.append('unverified_source')
        
        # Check for emotional language
        emotional_words = [
            'فاجعه', 'بحران شدید', 'نابودی', 'disaster', 'catastrophe', 'destruction'
        ]
        if any(word in text.lower() for word in emotional_words):
            risk_factors.append('emotional_language')
        
        # Check length issues
        if len(text.split()) < 20:
            risk_factors.append('too_short')
        elif len(text.split()) > 500:
            risk_factors.append('too_long')
        
        return {
            'factors': risk_factors,
            'risk_score': len(risk_factors)
        }

    async def _calculate_enhanced_score(
        self, text: str, financial: Dict, quality: Dict, 
        sentiment: Dict, entity: Dict
    ) -> Dict:
        """Calculate enhanced AI-like score using multiple factors."""
        
        scores = {}
        
        # Financial relevance score
        financial_score = financial.get('financial_relevance', 0)
        scores['financial_score'] = financial_score
        
        # Quality score
        quality_score = quality.get('overall_quality', 0) * 10
        scores['quality_score'] = quality_score
        
        # Sentiment relevance
        sentiment_score = sentiment.get('relevance_score', 5)
        scores['sentiment_score'] = sentiment_score
        
        # Entity score
        entity_score = min(entity.get('score', 0), 10)
        scores['entity_score'] = entity_score
        
        # Weighted total score
        total_score = (
            financial_score * self.weights['financial_keywords'] +
            quality_score * self.weights['quality_indicators'] * 0.1 +  # Scale down
            sentiment_score * self.weights['sentiment_relevance'] +
            entity_score * self.weights['entity_recognition'] * 0.5  # Scale down
        )
        
        # Check for learning patterns
        pattern_boost = await self._check_learning_patterns(text)
        total_score += pattern_boost
        
        scores['total_score'] = total_score
        scores['pattern_boost'] = pattern_boost
        
        return scores

    async def _check_learning_patterns(self, text: str) -> float:
        """Check for learned patterns from previous decisions."""
        try:
            # Simple pattern matching based on learned data
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            
            if text_hash in self.pattern_cache:
                cached_result = self.pattern_cache[text_hash]
                logger.debug(f"Found cached pattern for similar content")
                return cached_result.get('boost', 0)
            
            # Check for similar patterns in learning data
            for category, decisions in self.learning_data.items():
                # Simple keyword overlap check
                for decision_data in decisions[-10:]:  # Check last 10 decisions
                    previous_text = decision_data.get('text', '')
                    if len(previous_text) > 50:
                        # Simple similarity check
                        common_words = set(text.lower().split()) & set(previous_text.lower().split())
                        if len(common_words) > 3:  # If significant word overlap
                            decision = decision_data.get('decision', 'human_review')
                            if decision == 'approve':
                                return 1.0  # Small boost for similar approved content
                            elif decision == 'reject':
                                return -1.0  # Small penalty for similar rejected content
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"Pattern check failed: {e}")
            return 0.0

    async def _make_decision(
        self, scores: Dict, financial: Dict, quality: Dict, 
        risk: Dict, text: str
    ) -> Tuple[str, float, str]:
        """Make final decision based on all analyses."""
        
        total_score = scores.get('total_score', 0)
        financial_score = scores.get('financial_score', 0)
        quality_score = scores.get('quality_score', 0)
        risk_factors = risk.get('factors', [])
        
        # Normalize total score to 0-10 range
        normalized_score = min(max(total_score / 5, 0), 10)
        
        # Decision thresholds from config
        from config.settings import DEBUG_MODE
        auto_approve_threshold = float(os.getenv('AI_AUTO_APPROVE_THRESHOLD', '8.5'))
        auto_reject_threshold = float(os.getenv('AI_AUTO_REJECT_THRESHOLD', '3.0'))
        human_review_min = float(os.getenv('AI_HUMAN_REVIEW_MIN', '3.0'))
        human_review_max = float(os.getenv('AI_HUMAN_REVIEW_MAX', '8.5'))
        
        # Risk factor penalties
        risk_penalty = len(risk_factors) * 1.0
        final_score = max(normalized_score - risk_penalty, 0)
        
        # Decision logic
        reasoning_parts = []
        
        if final_score >= auto_approve_threshold and len(risk_factors) <= 1:
            decision = 'approve'
            reasoning_parts.append(f"High confidence score ({final_score:.1f}/10)")
            if financial_score >= 7:
                reasoning_parts.append("Strong financial relevance")
            if quality_score >= 7:
                reasoning_parts.append("Good content quality")
                
        elif final_score <= auto_reject_threshold or len(risk_factors) >= 3:
            decision = 'reject'
            reasoning_parts.append(f"Low confidence score ({final_score:.1f}/10)")
            if financial_score < 3:
                reasoning_parts.append("Poor financial relevance")
            if risk_factors:
                reasoning_parts.append(f"Risk factors: {', '.join(risk_factors)}")
                
        else:
            decision = 'human_review'
            reasoning_parts.append(f"Uncertain confidence ({final_score:.1f}/10)")
            reasoning_parts.append("Requires human judgment")
            if risk_factors:
                reasoning_parts.append(f"Some risks: {', '.join(risk_factors)}")
        
        reasoning = "; ".join(reasoning_parts)
        
        return decision, final_score, reasoning

    async def _learn_from_analysis(self, text: str, result: FreeAIResult):
        """Learn from analysis patterns for future improvement."""
        try:
            # Store pattern data
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            
            self.pattern_cache[text_hash] = {
                'decision': result.decision,
                'confidence': result.confidence,
                'category': result.category,
                'boost': 0.5 if result.decision == 'approve' else -0.5,
                'timestamp': time.time()
            }
            
            # Store in learning data
            self.learning_data[result.category].append({
                'text': text[:200],  # Store partial text for privacy
                'decision': result.decision,
                'confidence': result.confidence,
                'timestamp': time.time()
            })
            
            # Limit storage size
            if len(self.learning_data[result.category]) > 100:
                self.learning_data[result.category] = self.learning_data[result.category][-50:]
                
        except Exception as e:
            logger.debug(f"Learning storage failed: {e}")

    def _update_stats(self, result: FreeAIResult):
        """Update statistics."""
        self.stats['total_analyzed'] += 1
        
        if result.decision == 'approve':
            self.stats['auto_approved'] += 1
        elif result.decision == 'reject':
            self.stats['auto_rejected'] += 1
        else:
            self.stats['human_review'] += 1
        
        # Update averages
        total = self.stats['total_analyzed']
        self.stats['average_confidence'] = (
            (self.stats['average_confidence'] * (total - 1) + result.confidence) / total
        )
        self.stats['average_processing_time'] = (
            (self.stats['average_processing_time'] * (total - 1) + result.processing_time) / total
        )

    def _load_learning_data(self):
        """Load previous learning data."""
        try:
            learning_file = self.models.cache_dir / "learning_data.json"
            if learning_file.exists():
                with open(learning_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learning_data = defaultdict(list, data)
                logger.info("📚 Loaded previous learning data")
        except Exception as e:
            logger.debug(f"Could not load learning data: {e}")

    def save_learning_data(self):
        """Save learning data for persistence."""
        try:
            learning_file = self.models.cache_dir / "learning_data.json"
            with open(learning_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.learning_data), f, ensure_ascii=False, indent=2)
            logger.debug("💾 Saved learning data")
        except Exception as e:
            logger.debug(f"Could not save learning data: {e}")

    def get_statistics(self) -> Dict:
        """Get comprehensive statistics."""
        stats = self.stats.copy()
        
        total = stats['total_analyzed']
        if total > 0:
            stats['approval_rate'] = (stats['auto_approved'] / total) * 100
            stats['rejection_rate'] = (stats['auto_rejected'] / total) * 100
            stats['human_review_rate'] = (stats['human_review'] / total) * 100
            stats['automation_rate'] = ((stats['auto_approved'] + stats['auto_rejected']) / total) * 100
        
        stats['learning_patterns'] = len(self.pattern_cache)
        stats['learning_categories'] = len(self.learning_data)
        
        return stats

# Global instance
free_ai_engine = None

async def get_free_ai_engine() -> FreeAIEngine:
    """Get or create the global free AI engine."""
    global free_ai_engine
    
    if free_ai_engine is None:
        free_ai_engine = FreeAIEngine()
        await free_ai_engine.initialize()
    
    return free_ai_engine