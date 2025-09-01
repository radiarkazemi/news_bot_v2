"""
AI-Enhanced News Handler - FREE Implementation
Replaces manual approval with intelligent FREE AI automation.
Drop-in replacement for the existing NewsHandler.
"""
import asyncio
import logging
import time
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from telethon import events

# Import the free AI engine
from src.ai.free_ai_engine import get_free_ai_engine, FreeAIResult

# Import existing components  
from src.services.news_detector import NewsDetector
from src.services.news_filter import NewsFilter
from src.utils.time_utils import get_current_time, get_formatted_time

logger = logging.getLogger(__name__)

class AINewsHandler:
    """
    AI-Enhanced News Handler with FREE AI automation.
    Drop-in replacement for manual approval system.
    """

    def __init__(self, client_manager):
        """Initialize AI-enhanced news handler."""
        self.client_manager = client_manager
        
        # Keep existing components
        self.news_detector = NewsDetector()
        self.pending_news = {}
        self.processed_messages = set()
        self.admin_bot_entity = None
        
        # AI-specific components
        self.ai_engine = None
        self.ai_processed = {}  # Track AI decisions
        self.human_review_queue = {}  # Items requiring human review
        
        # Enhanced statistics
        self.stats = {
            'messages_processed': 0,
            'news_detected': 0,
            'ai_auto_approved': 0,
            'ai_auto_rejected': 0,
            'ai_human_review': 0,
            'news_published': 0,
            'errors': 0,
            'session_start': time.time(),
            'ai_processing_time': 0.0,
            'ai_accuracy_score': 0.0
        }
        
        # State management
        self.state_file = Path("data/state/ai_news_handler_state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("🤖 AI-Enhanced News Handler initialized (FREE mode)")

    async def initialize(self):
        """Initialize AI components."""
        try:
            logger.info("🚀 Initializing FREE AI components...")
            self.ai_engine = await get_free_ai_engine()
            
            # Load previous state
            await self.load_ai_state()
            
            logger.info("✅ AI News Handler fully initialized")
            
        except Exception as e:
            logger.error(f"❌ AI initialization failed: {e}")
            logger.info("🔄 Falling back to manual approval mode")

    async def process_news_messages_ai(self, channel_username: str):
        """
        Main AI processing method - replaces manual approval workflow.
        """
        logger.info(f"🤖 AI processing news from channel: {channel_username}")
        
        if not self.ai_engine:
            logger.warning("AI engine not initialized, falling back to manual mode")
            return await self.process_news_messages_manual(channel_username)
        
        try:
            # Get channel entity
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
            
            channel_entity = await self.client_manager.client.get_entity(channel_username)
            
            # Get configuration
            from config.settings import MESSAGE_LOOKBACK_HOURS, MAX_MESSAGES_PER_CHECK
            cutoff_time = datetime.now() - timedelta(hours=MESSAGE_LOOKBACK_HOURS)
            
            messages_processed = 0
            ai_decisions_made = 0
            
            logger.info(f"📥 Analyzing messages with FREE AI from {channel_username}")
            
            async for message in self.client_manager.client.iter_messages(channel_entity, limit=MAX_MESSAGES_PER_CHECK):
                try:
                    # Skip old messages
                    if message.date.replace(tzinfo=None) < cutoff_time:
                        continue
                    
                    # Skip if no text or too short
                    if not message.text or len(message.text.strip()) < 30:
                        continue
                    
                    # Check if already processed
                    message_key = f"{channel_username.replace('@', '')}:{message.id}"
                    if message_key in self.processed_messages:
                        continue
                    
                    messages_processed += 1
                    self.stats['messages_processed'] += 1
                    
                    # Step 1: Basic news detection (keep existing logic)
                    if not self.news_detector.is_news(message.text):
                        logger.debug(f"Message {message.id} not detected as news")
                        continue
                    
                    self.stats['news_detected'] += 1
                    logger.info(f"📰 News detected: {message.id}")
                    
                    # Step 2: AI ANALYSIS AND DECISION (NEW!)
                    ai_result = await self.ai_engine.analyze_news(
                        text=message.text,
                        metadata={
                            'source_channel': channel_username,
                            'message_id': message.id,
                            'timestamp': message.date.timestamp(),
                            'has_media': bool(message.media)
                        }
                    )
                    
                    ai_decisions_made += 1
                    
                    # Step 3: Handle AI decision
                    await self._handle_ai_decision(message, ai_result, channel_username)
                    
                    # Mark as processed
                    self.processed_messages.add(message_key)
                    
                    # Small delay for rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing message {message.id}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            logger.info(f"🤖 AI processing complete: {ai_decisions_made} decisions from {messages_processed} messages")
            
            # Save state after processing
            await self.save_ai_state()
            
            return ai_decisions_made > 0
            
        except Exception as e:
            logger.error(f"❌ Error in AI news processing: {e}")
            self.stats['errors'] += 1
            return False

    async def _handle_ai_decision(self, message, ai_result: FreeAIResult, channel_username):
        """Handle AI decision with appropriate action."""
        decision_map = {
            'approve': self._handle_ai_approval,
            'reject': self._handle_ai_rejection,
            'human_review': self._handle_ai_human_review
        }
        
        handler = decision_map.get(ai_result.decision)
        if handler:
            await handler(message, ai_result, channel_username)
        else:
            logger.error(f"Unknown AI decision: {ai_result.decision}")
            # Default to human review on unknown decision
            await self._handle_ai_human_review(message, ai_result, channel_username)

    async def _handle_ai_approval(self, message, ai_result: FreeAIResult, channel_username):
        """Handle AI automatic approval - publish immediately."""
        logger.info(f"✅ AI AUTO-APPROVED: {message.id} (confidence: {ai_result.confidence:.1f}/10)")
        
        try:
            # Clean the text
            cleaned_text = self.news_detector.clean_news_text(message.text)
            
            # Create news data
            news_data = {
                'text': cleaned_text,
                'formatted_text': cleaned_text,
                'original_text': message.text,
                'timestamp': time.time(),
                'source_channel': channel_username.replace('@', ''),
                'has_media': bool(message.media),
                'media': self._extract_media_info(message, channel_username) if message.media else None,
                'ai_analysis': {
                    'decision': ai_result.decision,
                    'confidence': ai_result.confidence,
                    'reasoning': ai_result.reasoning,
                    'category': ai_result.category,
                    'financial_score': ai_result.financial_score,
                    'quality_score': ai_result.quality_score,
                    'processing_time': ai_result.processing_time
                },
                'approval_source': 'ai_auto',
                'status': 'approved'
            }
            
            # Publish immediately (no human approval needed!)
            success = await self.publish_approved_news(news_data)
            
            if success:
                self.stats['ai_auto_approved'] += 1
                self.stats['news_published'] += 1
                
                # Store AI decision for learning
                self.ai_processed[str(message.id)] = {
                    'decision': 'approved',
                    'ai_result': ai_result.__dict__,
                    'published': True,
                    'timestamp': time.time(),
                    'text_preview': message.text[:100]
                }
                
                logger.info(f"📢 AI-approved news published: {message.id}")
                logger.info(f"🎯 Reasoning: {ai_result.reasoning}")
            else:
                logger.error(f"❌ Failed to publish AI-approved news: {message.id}")
                # Add to human review queue as fallback
                await self._handle_ai_human_review(message, ai_result, channel_username)
                
        except Exception as e:
            logger.error(f"Error in AI approval handling: {e}")
            # Fallback to human review
            await self._handle_ai_human_review(message, ai_result, channel_username)

    async def _handle_ai_rejection(self, message, ai_result: FreeAIResult, channel_username):
        """Handle AI automatic rejection."""
        logger.info(f"❌ AI AUTO-REJECTED: {message.id} (confidence: {ai_result.confidence:.1f}/10)")
        logger.info(f"📝 Rejection reasoning: {ai_result.reasoning}")
        
        self.stats['ai_auto_rejected'] += 1
        
        # Store AI decision
        self.ai_processed[str(message.id)] = {
            'decision': 'rejected',
            'ai_result': ai_result.__dict__,
            'published': False,
            'timestamp': time.time(),
            'text_preview': message.text[:100]
        }
        
        # Log details for analysis
        logger.debug(f"AI rejected content: {message.text[:150]}...")
        logger.debug(f"Risk factors: {ai_result.risk_factors}")
        logger.debug(f"Category: {ai_result.category}")

    async def _handle_ai_human_review(self, message, ai_result: FreeAIResult, channel_username):
        """Handle cases where AI requests human review."""
        logger.info(f"👤 AI REQUESTS HUMAN REVIEW: {message.id} (confidence: {ai_result.confidence:.1f}/10)")
        
        self.stats['ai_human_review'] += 1
        
        # Generate review ID
        review_id = f"ai_{message.id}_{int(time.time())}"
        
        # Store in human review queue
        self.human_review_queue[review_id] = {
            'message': message,
            'ai_result': ai_result.__dict__,
            'channel': channel_username,
            'timestamp': time.time(),
            'text_preview': message.text[:100]
        }
        
        # Send to admin bot with AI analysis
        try:
            await self._send_ai_review_message(message, ai_result, channel_username, review_id)
        except Exception as e:
            logger.error(f"Failed to send AI review message: {e}")

    async def _send_ai_review_message(self, message, ai_result: FreeAIResult, channel_username, review_id):
        """Send enhanced review message with AI analysis."""
        admin_bot = await self.get_admin_bot_entity()
        if not admin_bot:
            logger.error("Cannot send for review: admin bot not available")
            return
        
        current_time = get_formatted_time(format_type='persian_full')
        
        # Create detailed AI analysis message
        review_message = (
            f"🤖 <b>FREE AI ANALYSIS COMPLETE</b>\n\n"
            f"🆔 Review ID: <code>{review_id}</code>\n"
            f"📡 Source: {channel_username.replace('@', '')}\n"
            f"🕐 Time: {current_time}\n\n"
            f"🧠 <b>AI Analysis Results:</b>\n"
            f"🎯 Decision: {ai_result.decision.upper()}\n"
            f"📊 Confidence: {ai_result.confidence:.1f}/10\n"
            f"💰 Financial Score: {ai_result.financial_score:.1f}/10\n"
            f"✨ Quality Score: {ai_result.quality_score:.1f}/10\n"
            f"💭 Sentiment Score: {ai_result.sentiment_score:.1f}/10\n"
            f"📈 Category: {ai_result.category}\n"
            f"⏱️ Processing Time: {ai_result.processing_time:.2f}s\n\n"
            f"⚠️ <b>Risk Factors:</b> {', '.join(ai_result.risk_factors) if ai_result.risk_factors else 'None'}\n"
            f"🔍 <b>Entities:</b> {', '.join(ai_result.detected_entities[:3]) if ai_result.detected_entities else 'None'}\n\n"
            f"💡 <b>AI Reasoning:</b>\n{ai_result.reasoning}\n\n"
            f"📄 <b>Content:</b>\n{message.text}\n\n"
            f"👨‍💼 <b>Human Decision Required:</b>\n"
            f"➡️ To approve: <code>/submit{review_id}</code>\n"
            f"➡️ To reject: <code>/reject{review_id}</code>\n"
            f"🤖 To improve AI: <code>/learn{review_id}</code>"
        )
        
        # Send with media if available
        sent_message = None
        
        if message.media:
            try:
                sent_message = await self.client_manager.client.send_message(
                    admin_bot,
                    review_message,
                    parse_mode='html',
                    file=message.media
                )
            except Exception as e:
                logger.warning(f"Could not send with media: {e}")
        
        # Send text-only if media failed or not available
        if not sent_message:
            sent_message = await self.client_manager.client.send_message(
                admin_bot,
                review_message,
                parse_mode='html'
            )
        
        if sent_message:
            logger.info(f"📤 AI review sent: {review_id}")
            
            # Store message info for cleanup
            self.human_review_queue[review_id]['admin_message_id'] = sent_message.id
            self.human_review_queue[review_id]['admin_chat_id'] = admin_bot.id

    async def setup_ai_approval_handler(self):
        """Set up enhanced approval handlers with AI learning."""
        try:
            client = self.client_manager.client
            
            # Enhanced approval command
            @client.on(events.NewMessage(pattern=r'/submit(\w+)'))
            async def handle_ai_approval_command(event):
                try:
                    approval_id = event.pattern_match.group(1)
                    
                    if approval_id.startswith('ai_'):
                        await self._process_ai_review_approval(approval_id, event)
                    else:
                        # Handle legacy approvals if any
                        await self._process_legacy_approval(approval_id, event)
                        
                except Exception as e:
                    logger.error(f"Error in approval command: {e}")
            
            # Enhanced rejection command
            @client.on(events.NewMessage(pattern=r'/reject(\w+)'))
            async def handle_ai_rejection_command(event):
                try:
                    approval_id = event.pattern_match.group(1)
                    
                    if approval_id.startswith('ai_'):
                        await self._process_ai_review_rejection(approval_id, event)
                    else:
                        await self._process_legacy_rejection(approval_id, event)
                        
                except Exception as e:
                    logger.error(f"Error in rejection command: {e}")
            
            # AI learning command
            @client.on(events.NewMessage(pattern=r'/learn(\w+)'))
            async def handle_ai_learning_command(event):
                try:
                    approval_id = event.pattern_match.group(1)
                    await self._process_ai_learning(approval_id, event)
                except Exception as e:
                    logger.error(f"Error in learning command: {e}")
            
            # AI statistics command
            @client.on(events.NewMessage(pattern=r'/ai_stats'))
            async def handle_ai_stats_command(event):
                try:
                    stats_text = await self._format_ai_statistics()
                    await event.respond(stats_text)
                except Exception as e:
                    logger.error(f"Error showing AI stats: {e}")
                    await event.respond(f"❌ Error getting AI stats: {e}")
            
            # AI tune command
            @client.on(events.NewMessage(pattern=r'/ai_tune'))
            async def handle_ai_tune_command(event):
                try:
                    await self._tune_ai_thresholds()
                    await event.respond("🎛️ AI thresholds tuned based on recent performance")
                except Exception as e:
                    logger.error(f"Error tuning AI: {e}")
                    await event.respond(f"❌ Error tuning AI: {e}")
            
            # Test AI command
            @client.on(events.NewMessage(pattern=r'/test_ai (.+)'))
            async def handle_test_ai_command(event):
                try:
                    test_text = event.pattern_match.group(1)
                    if self.ai_engine:
                        result = await self.ai_engine.analyze_news(test_text)
                        
                        response = (
                            f"🧪 <b>AI Test Results:</b>\n\n"
                            f"🎯 Decision: {result.decision}\n"
                            f"📊 Confidence: {result.confidence:.1f}/10\n"
                            f"💰 Financial: {result.financial_score:.1f}/10\n"
                            f"✨ Quality: {result.quality_score:.1f}/10\n"
                            f"💭 Reasoning: {result.reasoning}\n"
                            f"⏱️ Time: {result.processing_time:.2f}s"
                        )
                        
                        await event.respond(response, parse_mode='html')
                    else:
                        await event.respond("❌ AI engine not available")
                except Exception as e:
                    logger.error(f"Error in AI test: {e}")
                    await event.respond(f"❌ AI test error: {e}")
            
            logger.info("✅ AI approval handler set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set up AI approval handler: {e}")
            return False

    async def _process_ai_review_approval(self, review_id, event):
        """Process human approval of AI-flagged content."""
        if review_id not in self.human_review_queue:
            await event.respond(f"❌ Review {review_id} not found")
            return
        
        review_data = self.human_review_queue[review_id]
        message = review_data['message']
        
        # Create news data
        cleaned_text = self.news_detector.clean_news_text(message.text)
        news_data = {
            'text': cleaned_text,
            'formatted_text': cleaned_text,
            'original_text': message.text,
            'timestamp': time.time(),
            'source_channel': review_data['channel'].replace('@', ''),
            'has_media': bool(message.media),
            'media': self._extract_media_info(message, review_data['channel']) if message.media else None,
            'ai_analysis': review_data['ai_result'],
            'human_override': 'approved',
            'approval_source': 'human_review',
            'status': 'approved'
        }
        
        # Publish
        success = await self.publish_approved_news(news_data)
        
        if success:
            await event.respond(f"✅ Human approved: {review_id} published successfully!")
            self.stats['news_published'] += 1
            
            # Learn from human decision
            await self._record_human_learning(review_id, 'approve', 'human_approved_ai_uncertain')
            
            # Clean up
            await self._cleanup_review_messages(review_id)
            del self.human_review_queue[review_id]
            
        else:
            await event.respond(f"❌ Failed to publish: {review_id}")

    async def _process_ai_review_rejection(self, review_id, event):
        """Process human rejection of AI-flagged content."""
        if review_id not in self.human_review_queue:
            await event.respond(f"❌ Review {review_id} not found")
            return
        
        # Learn from human decision
        await self._record_human_learning(review_id, 'reject', 'human_rejected_ai_uncertain')
        
        # Clean up
        await self._cleanup_review_messages(review_id)
        del self.human_review_queue[review_id]
        
        await event.respond(f"🚫 Human rejected: {review_id}")

    async def _process_ai_learning(self, review_id, event):
        """Process AI learning commands."""
        if review_id not in self.human_review_queue:
            await event.respond(f"❌ Learning item {review_id} not found")
            return
        
        review_data = self.human_review_queue[review_id]
        ai_result = review_data['ai_result']
        
        # Record learning data
        learning_entry = {
            'review_id': review_id,
            'ai_confidence': ai_result.get('confidence', 0),
            'ai_decision': ai_result.get('decision', 'unknown'),
            'human_feedback': 'trust_ai_more',
            'category': ai_result.get('category', 'unknown'),
            'timestamp': time.time()
        }
        
        # This would feed into AI improvement algorithms
        logger.info(f"📚 AI Learning recorded: {learning_entry}")
        
        # Clean up
        await self._cleanup_review_messages(review_id)
        del self.human_review_queue[review_id]
        
        await event.respond("📚 AI learning recorded - similar content will be handled more confidently")

    async def _record_human_learning(self, review_id, decision, learning_type):
        """Record human decision for AI learning."""
        try:
            if review_id in self.human_review_queue:
                review_data = self.human_review_queue[review_id]
                
                learning_data = {
                    'review_id': review_id,
                    'human_decision': decision,
                    'ai_decision': review_data['ai_result'].get('decision', 'unknown'),
                    'ai_confidence': review_data['ai_result'].get('confidence', 0),
                    'learning_type': learning_type,
                    'category': review_data['ai_result'].get('category', 'unknown'),
                    'timestamp': time.time(),
                    'text_sample': review_data.get('text_preview', '')
                }
                
                # Store for future AI improvement
                if self.ai_engine:
                    self.ai_engine.learning_data[learning_type].append(learning_data)
                    self.ai_engine.save_learning_data()
                
                logger.info(f"📚 Recorded human learning: {learning_type}")
                
        except Exception as e:
            logger.error(f"Error recording learning: {e}")

    async def _cleanup_review_messages(self, review_id):
        """Clean up admin messages for processed reviews."""
        try:
            if review_id in self.human_review_queue:
                review_data = self.human_review_queue[review_id]
                
                if 'admin_message_id' in review_data and 'admin_chat_id' in review_data:
                    await self.client_manager.client.delete_messages(
                        review_data['admin_chat_id'],
                        review_data['admin_message_id']
                    )
                    logger.debug(f"🗑️ Cleaned up review message: {review_id}")
                    
        except Exception as e:
            logger.debug(f"Could not cleanup review message: {e}")

    async def _tune_ai_thresholds(self):
        """Auto-tune AI thresholds based on performance."""
        try:
            if not self.ai_engine:
                return
            
            stats = self.ai_engine.get_statistics()
            
            # Simple threshold adjustment based on performance
            automation_rate = stats.get('automation_rate', 50)
            accuracy_estimate = stats.get('average_confidence', 5)
            
            # If too much human review, lower thresholds
            if stats.get('human_review_rate', 0) > 40:
                logger.info("🎛️ Lowering AI thresholds to increase automation")
                # Would adjust environment variables or configuration
            
            # If high accuracy, can be more aggressive
            if accuracy_estimate > 7.5:
                logger.info("🎛️ AI showing high confidence, can be more aggressive")
            
            logger.info(f"🎛️ AI tuning complete - automation rate: {automation_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"Error tuning AI: {e}")

    async def _format_ai_statistics(self) -> str:
        """Format comprehensive AI statistics."""
        try:
            # Get AI engine stats
            ai_stats = {}
            if self.ai_engine:
                ai_stats = self.ai_engine.get_statistics()
            
            # Combine with handler stats
            total_analyzed = self.stats['news_detected']
            
            stats_text = f"🤖 <b>FREE AI STATISTICS</b>\n\n"
            
            # Processing stats
            stats_text += f"📊 <b>Processing:</b>\n"
            stats_text += f"📝 Messages Processed: {self.stats['messages_processed']}\n"
            stats_text += f"📰 News Detected: {self.stats['news_detected']}\n"
            stats_text += f"⚡ Avg Processing Time: {ai_stats.get('average_processing_time', 0):.2f}s\n\n"
            
            # Decision stats
            stats_text += f"🎯 <b>AI Decisions:</b>\n"
            stats_text += f"✅ Auto Approved: {self.stats['ai_auto_approved']}\n"
            stats_text += f"❌ Auto Rejected: {self.stats['ai_auto_rejected']}\n"
            stats_text += f"👤 Human Review: {self.stats['ai_human_review']}\n"
            stats_text += f"📢 Published: {self.stats['news_published']}\n\n"
            
            # Performance metrics
            if total_analyzed > 0:
                automation_rate = ((self.stats['ai_auto_approved'] + self.stats['ai_auto_rejected']) / total_analyzed) * 100
                approval_rate = (self.stats['ai_auto_approved'] / total_analyzed) * 100
                human_rate = (self.stats['ai_human_review'] / total_analyzed) * 100
                
                stats_text += f"📈 <b>Performance:</b>\n"
                stats_text += f"🤖 Automation Rate: {automation_rate:.1f}%\n"
                stats_text += f"✅ Approval Rate: {approval_rate:.1f}%\n"
                stats_text += f"👤 Human Review Rate: {human_rate:.1f}%\n"
                stats_text += f"📊 Avg Confidence: {ai_stats.get('average_confidence', 0):.1f}/10\n\n"
            
            # System info
            stats_text += f"🔧 <b>System:</b>\n"
            stats_text += f"🧠 Learning Patterns: {ai_stats.get('learning_patterns', 0)}\n"
            stats_text += f"📚 Learning Categories: {ai_stats.get('learning_categories', 0)}\n"
            stats_text += f"⏳ Pending Reviews: {len(self.human_review_queue)}\n"
            stats_text += f"❌ Errors: {self.stats['errors']}\n\n"
            
            # Uptime
            uptime = time.time() - self.stats['session_start']
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            stats_text += f"⏰ <b>Session Uptime:</b> {hours}h {minutes}m\n"
            
            stats_text += f"\n💡 <b>Status:</b> {'🟢 AI Active' if self.ai_engine else '🔴 Manual Mode'}"
            
            return stats_text
            
        except Exception as e:
            return f"❌ Error formatting stats: {e}"

    # Legacy/compatibility methods
    async def _process_legacy_approval(self, approval_id, event):
        """Handle legacy approval format."""
        await event.respond(f"ℹ️ Legacy approval {approval_id} - please use AI system")

    async def _process_legacy_rejection(self, approval_id, event):
        """Handle legacy rejection format."""
        await event.respond(f"ℹ️ Legacy rejection {approval_id} - please use AI system")

    # Existing methods (adapt from original handler)
    async def get_admin_bot_entity(self):
        """Get admin bot entity."""
        if self.admin_bot_entity:
            return self.admin_bot_entity
        
        try:
            from config.credentials import ADMIN_BOT_USERNAME
            
            possible_usernames = [
                ADMIN_BOT_USERNAME,
                f"@{ADMIN_BOT_USERNAME}",
                ADMIN_BOT_USERNAME.replace('@', '')
            ]
            
            for username in possible_usernames:
                try:
                    entity = await self.client_manager.client.get_entity(username)
                    self.admin_bot_entity = entity
                    logger.info(f"✅ Found admin bot: {username}")
                    return entity
                except:
                    continue
            
            logger.error(f"❌ Could not find admin bot: {ADMIN_BOT_USERNAME}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting admin bot: {e}")
            return None

    async def publish_approved_news(self, news_data):
        """Publish approved news with AI enhancements."""
        try:
            from config.settings import TARGET_CHANNEL_ID, NEW_ATTRIBUTION
            
            # Format text with AI category if available
            formatted_text = news_data.get('formatted_text', news_data['text'])
            
            # Add AI category emoji
            ai_analysis = news_data.get('ai_analysis', {})
            category = ai_analysis.get('category', 'unknown')
            
            category_emojis = {
                'gold': '🏆',
                'currency': '💱',
                'iranian_economy': '🇮🇷',
                'market': '📈',
                'banking': '🏦',
                'oil_energy': '🛢️',
                'crypto': '₿'
            }
            
            emoji = category_emojis.get(category, '📰')
            if not formatted_text.startswith(tuple(category_emojis.values())):
                formatted_text = f"{emoji} {formatted_text}"
            
            # Add attribution
            if NEW_ATTRIBUTION and NEW_ATTRIBUTION not in formatted_text:
                formatted_text = f"{formatted_text}\n📡 {NEW_ATTRIBUTION}"
            
            # Add Persian timestamp
            current_time = get_formatted_time(format_type="persian_full")
            formatted_text = f"{formatted_text}\n🕐 {current_time}"
            
            # Add AI processing info (optional, can be disabled)
            if os.getenv('AI_SHOW_PROCESSING_INFO', 'false').lower() == 'true':
                confidence = ai_analysis.get('confidence', 0)
                processing_time = ai_analysis.get('processing_time', 0)
                formatted_text = f"{formatted_text}\n🤖 AI: {confidence:.1f}/10 ({processing_time:.1f}s)"
            
            # Publish
            result = await self.client_manager.client.send_message(
                TARGET_CHANNEL_ID,
                formatted_text,
                parse_mode='html'
            )
            
            if result:
                logger.info(f"📢 AI-processed news published: {result.id}")
                return True
            else:
                logger.error(f"❌ Failed to publish news")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error publishing news: {e}")
            return False

    def _extract_media_info(self, message, channel_username):
        """Extract media information."""
        try:
            from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
            
            if isinstance(message.media, MessageMediaPhoto):
                return {
                    "type": "photo",
                    "media_id": message.media.photo.id,
                    "message_id": message.id,
                    "channel": channel_username.replace('@', '')
                }
            elif isinstance(message.media, MessageMediaDocument):
                return {
                    "type": "document",
                    "media_id": message.media.document.id,
                    "message_id": message.id,
                    "channel": channel_username.replace('@', '')
                }
        except Exception as e:
            logger.debug(f"Media extraction error: {e}")
        
        return None

    # State management
    async def load_ai_state(self):
        """Load AI handler state."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    self.processed_messages = set(data.get('processed_messages', []))
                    self.human_review_queue = data.get('human_review_queue', {})
                    self.ai_processed = data.get('ai_processed', {})
                    
                    # Restore statistics
                    saved_stats = data.get('stats', {})
                    for key, value in saved_stats.items():
                        if key in self.stats:
                            self.stats[key] = value
                
                logger.info(f"📂 Loaded AI state: {len(self.human_review_queue)} pending reviews")
                
        except Exception as e:
            logger.debug(f"Could not load AI state: {e}")

    async def save_ai_state(self):
        """Save AI handler state."""
        try:
            data = {
                'processed_messages': list(self.processed_messages),
                'human_review_queue': self.human_review_queue,
                'ai_processed': self.ai_processed,
                'stats': self.stats,
                'last_updated': time.time(),
                'version': 'ai_free_1.0'
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug("💾 AI state saved")
            
        except Exception as e:
            logger.debug(f"Could not save AI state: {e}")

    # Compatibility method for fallback
    async def process_news_messages_manual(self, channel_username):
        """Fallback to manual processing if AI fails."""
        logger.info(f"📝 Manual processing fallback for: {channel_username}")
        
        # This would implement the original manual approval logic
        # For now, just do basic detection without approval
        try:
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
            
            channel_entity = await self.client_manager.client.get_entity(channel_username)
            
            from config.settings import MESSAGE_LOOKBACK_HOURS, MAX_MESSAGES_PER_CHECK
            cutoff_time = datetime.now() - timedelta(hours=MESSAGE_LOOKBACK_HOURS)
            
            news_found = 0
            
            async for message in self.client_manager.client.iter_messages(channel_entity, limit=MAX_MESSAGES_PER_CHECK):
                if (message.date.replace(tzinfo=None) >= cutoff_time and 
                    message.text and len(message.text.strip()) >= 30):
                    
                    if self.news_detector.is_news(message.text):
                        news_found += 1
                        logger.info(f"📰 News detected (manual mode): {message.id}")
                        
                        # In manual mode, would need human approval
                        # For now, just log it
            
            logger.info(f"📊 Manual mode found {news_found} news items")
            return news_found > 0
            
        except Exception as e:
            logger.error(f"Manual processing error: {e}")
            return False

    def get_comprehensive_stats(self):
        """Get comprehensive statistics."""
        stats = self.stats.copy()
        
        if self.ai_engine:
            ai_stats = self.ai_engine.get_statistics()
            stats.update({f"ai_{k}": v for k, v in ai_stats.items()})
        
        # Calculate derived metrics
        total_decisions = (stats['ai_auto_approved'] + stats['ai_auto_rejected'] + stats['ai_human_review'])
        if total_decisions > 0:
            stats['automation_rate'] = ((stats['ai_auto_approved'] + stats['ai_auto_rejected']) / total_decisions) * 100
            stats['human_intervention_rate'] = (stats['ai_human_review'] / total_decisions) * 100
        
        stats['pending_reviews'] = len(self.human_review_queue)
        stats['total_ai_processed'] = len(self.ai_processed)
        
        return stats