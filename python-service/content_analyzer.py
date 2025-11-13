"""
Content Analyzer Module
Analyzes web page content to determine if it's work-related or distracting
"""

import re
import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    def __init__(self):
        # Work-related keywords
        self.work_keywords = {
            'programming': ['tutorial', 'documentation', 'guide', 'how to', 'learn', 'programming', 
                          'coding', 'development', 'api', 'framework', 'library', 'course', 
                          'education', 'training', 'technical', 'software', 'code', 'debug',
                          'stackoverflow', 'github', 'python', 'javascript', 'react', 'node',
                          'css', 'html', 'database', 'sql', 'algorithm', 'data structure'],
            'productivity': ['project', 'task', 'planning', 'meeting', 'work', 'business',
                           'professional', 'career', 'skill', 'improvement', 'efficiency'],
            'research': ['research', 'study', 'analysis', 'report', 'article', 'academic',
                        'scientific', 'paper', 'journal', 'reference', 'documentation']
        }
        
        # Distraction keywords
        self.distraction_keywords = {
            'entertainment': ['funny', 'humor', 'comedy', 'entertainment', 'viral', 'memes',
                            'fails', 'compilation', 'reaction', 'prank', 'challenge',
                            'celebrity', 'gossip', 'drama', 'scandal', 'trending'],
            'news': ['breaking', 'urgent', 'scandal', 'controversy', 'politics', 'election',
                    'sports scores', 'celebrity news', 'fashion', 'lifestyle'],
            'social': ['social media', 'instagram', 'tiktok', 'snapchat', 'dating',
                      'relationship', 'personal', 'friends', 'party'],
            'gaming': ['gaming', 'gameplay', 'streamer', 'twitch', 'esports', 'game review',
                      'let\'s play', 'walkthrough', 'easter egg']
        }
        
        # Trusted work domains
        self.work_domains = {
            'stackoverflow.com', 'github.com', 'developer.mozilla.org', 'docs.python.org',
            'reactjs.org', 'w3schools.com', 'codecademy.com', 'freecodecamp.org',
            'coursera.org', 'udemy.com', 'edx.org', 'khan academy.org', 'pluralsight.com',
            'linkedin.com/learning', 'microsoft.com/docs', 'aws.amazon.com/documentation'
        }
        
        # Known distraction domains
        self.distraction_domains = {
            '9gag.com', 'buzzfeed.com', 'tmz.com', 'reddit.com/r/funny',
            'reddit.com/r/memes', 'tiktok.com', 'instagram.com', 'facebook.com/watch'
        }
        
        # User learning patterns
        self.user_patterns = {
            'allowed_sites': set(),
            'blocked_sites': set(),
            'keyword_preferences': {},
            'domain_overrides': {}
        }
        
        self.load_user_patterns()
    
    def analyze_content(self, content_data: Dict) -> Dict:
        """
        Main analysis function
        Returns: {'decision': 'WORK'|'DISTRACTION'|'NEUTRAL', 'confidence': float, 'reason': str}
        """
        try:
            logger.info(f"🔍 Analyzing content: {content_data.get('title', 'No title')[:50]}...")
            
            # Extract domain
            domain = self._extract_domain(content_data.get('url', ''))
            
            # Check domain whitelist/blacklist first
            domain_result = self._check_domain_patterns(domain)
            if domain_result:
                return domain_result
            
            # Combine all text content
            all_text = self._combine_text_content(content_data)
            
            # Analyze different aspects
            keyword_score = self._analyze_keywords(all_text)
            youtube_score = self._analyze_youtube_specific(content_data)
            context_score = self._analyze_context(content_data)
            
            # Calculate final decision
            final_decision = self._make_final_decision(
                keyword_score, youtube_score, context_score, domain
            )
            
            # Log the decision
            logger.info(f"📊 Decision: {final_decision['decision']} "
                       f"(confidence: {final_decision['confidence']:.2f}) - "
                       f"{final_decision['reason']}")
            
            return final_decision
            
        except Exception as e:
            logger.error(f"❌ Error analyzing content: {e}")
            return {
                'decision': 'NEUTRAL',
                'confidence': 0.0,
                'reason': f'Analysis error: {str(e)}'
            }
    
    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL"""
        try:
            # Remove protocol and www
            domain = re.sub(r'https?://', '', url)
            domain = re.sub(r'^www\.', '', domain)
            # Get just the domain part
            domain = domain.split('/')[0]
            return domain.lower()
        except:
            return url.lower()
    
    def _check_domain_patterns(self, domain: str) -> Dict:
        """Check if domain is in whitelist/blacklist"""
        if domain in self.work_domains or domain in self.user_patterns['allowed_sites']:
            return {
                'decision': 'WORK',
                'confidence': 0.95,
                'reason': f'Trusted work domain: {domain}'
            }
        
        if domain in self.distraction_domains or domain in self.user_patterns['blocked_sites']:
            return {
                'decision': 'DISTRACTION',
                'confidence': 0.95,
                'reason': f'Known distraction domain: {domain}'
            }
        
        return None
    
    def _combine_text_content(self, content_data: Dict) -> str:
        """Combine all available text content"""
        text_parts = []
        
        # Add title (weighted more heavily)
        title = content_data.get('title', '')
        text_parts.append(title * 2)  # Give title more weight
        
        # Add description
        description = content_data.get('description', '')
        text_parts.append(description)
        
        # Add headings
        headings = content_data.get('headings', [])
        text_parts.extend(headings)
        
        # Add main content (first part only)
        page_text = content_data.get('pageText', '')
        text_parts.append(page_text)
        
        # Add keywords
        keywords = content_data.get('keywords', '')
        text_parts.append(keywords)
        
        return ' '.join(text_parts).lower()
    
    def _analyze_keywords(self, text: str) -> Dict:
        """Analyze text for work vs distraction keywords"""
        work_score = 0
        distraction_score = 0
        matched_keywords = {'work': [], 'distraction': []}
        
        # Count work keywords
        for category, keywords in self.work_keywords.items():
            for keyword in keywords:
                count = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text))
                if count > 0:
                    work_score += count
                    matched_keywords['work'].append(f"{keyword}({count})")
        
        # Count distraction keywords
        for category, keywords in self.distraction_keywords.items():
            for keyword in keywords:
                count = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text))
                if count > 0:
                    distraction_score += count
                    matched_keywords['distraction'].append(f"{keyword}({count})")
        
        return {
            'work_score': work_score,
            'distraction_score': distraction_score,
            'matched_keywords': matched_keywords
        }
    
    def _analyze_youtube_specific(self, content_data: Dict) -> Dict:
        """YouTube-specific analysis"""
        youtube_data = content_data.get('youtubeData', {})
        if not youtube_data:
            return {'youtube_score': 0, 'youtube_reason': 'Not YouTube'}
        
        channel = youtube_data.get('channelName', '').lower()
        title = youtube_data.get('videoTitle', '').lower()
        
        # Educational channels
        educational_channels = [
            'freecodecamp', 'traversy media', 'net ninja', 'academind',
            'programming with mosh', 'tech with tim', 'corey schafer',
            'sentdex', 'derek banas', 'new boston', 'edureka'
        ]
        
        # Check channel reputation
        if any(edu_channel in channel for edu_channel in educational_channels):
            return {
                'youtube_score': 3,
                'youtube_reason': f'Educational channel: {channel}'
            }
        
        # Check for educational content in title
        educational_terms = ['tutorial', 'course', 'learn', 'how to', 'explained', 'guide']
        if any(term in title for term in educational_terms):
            return {
                'youtube_score': 2,
                'youtube_reason': 'Educational content detected'
            }
        
        # Check for entertainment content
        entertainment_terms = ['funny', 'fail', 'reaction', 'meme', 'prank', 'viral']
        if any(term in title for term in entertainment_terms):
            return {
                'youtube_score': -3,
                'youtube_reason': 'Entertainment content detected'
            }
        
        return {'youtube_score': 0, 'youtube_reason': 'Neutral YouTube content'}
    
    def _analyze_context(self, content_data: Dict) -> Dict:
        """Analyze contextual clues"""
        context_score = 0
        reasons = []
        
        # Time-based analysis
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Work hours
            context_score += 1
            reasons.append("During work hours")
        
        # URL pattern analysis
        url = content_data.get('url', '').lower()
        if '/docs/' in url or '/documentation/' in url or '/api/' in url:
            context_score += 2
            reasons.append("Documentation URL pattern")
        
        if '/watch?' in url and 'youtube' in url:
            # YouTube video - neutral by default
            pass
        
        return {
            'context_score': context_score,
            'context_reasons': reasons
        }
    
    def _make_final_decision(self, keyword_score: Dict, youtube_score: Dict, 
                           context_score: Dict, domain: str) -> Dict:
        """Make the final classification decision"""
        
        # Calculate total scores
        total_work = (keyword_score['work_score'] + 
                     max(0, youtube_score['youtube_score']) + 
                     context_score['context_score'])
        
        total_distraction = (keyword_score['distraction_score'] + 
                           max(0, -youtube_score['youtube_score']))
        
        # Decision logic
        if total_work >= 2 and total_work > total_distraction:
            confidence = min(0.9, 0.6 + (total_work - total_distraction) * 0.1)
            decision = 'WORK'
            reason = f"Work indicators: {keyword_score['matched_keywords']['work'][:3]}"
            
        elif total_distraction >= 2 and total_distraction > total_work:
            confidence = min(0.9, 0.6 + (total_distraction - total_work) * 0.1)
            decision = 'DISTRACTION'
            reason = f"Distraction indicators: {keyword_score['matched_keywords']['distraction'][:3]}"
            
        else:
            # Unclear - default to neutral/ask user
            confidence = 0.3
            decision = 'NEUTRAL'
            reason = "Ambiguous content - needs user decision"
        
        return {
            'decision': decision,
            'confidence': confidence,
            'reason': reason,
            'scores': {
                'work': total_work,
                'distraction': total_distraction,
                'keyword_details': keyword_score,
                'youtube_details': youtube_score,
                'context_details': context_score
            }
        }
    
    def add_user_preference(self, domain: str, decision: str):
        """Learn from user decisions"""
        if decision == 'WORK':
            self.user_patterns['allowed_sites'].add(domain)
            self.user_patterns['blocked_sites'].discard(domain)
        elif decision == 'DISTRACTION':
            self.user_patterns['blocked_sites'].add(domain)
            self.user_patterns['allowed_sites'].discard(domain)
        
        self.save_user_patterns()
        logger.info(f"📚 Learned user preference: {domain} → {decision}")
    
    def save_user_patterns(self):
        """Save user patterns to file"""
        try:
            # Convert sets to lists for JSON serialization
            patterns_to_save = {
                'allowed_sites': list(self.user_patterns['allowed_sites']),
                'blocked_sites': list(self.user_patterns['blocked_sites']),
                'keyword_preferences': self.user_patterns['keyword_preferences'],
                'domain_overrides': self.user_patterns['domain_overrides']
            }
            
            with open('user_patterns.json', 'w') as f:
                json.dump(patterns_to_save, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error saving user patterns: {e}")
    
    def load_user_patterns(self):
        """Load user patterns from file"""
        try:
            with open('user_patterns.json', 'r') as f:
                patterns = json.load(f)
                
            self.user_patterns['allowed_sites'] = set(patterns.get('allowed_sites', []))
            self.user_patterns['blocked_sites'] = set(patterns.get('blocked_sites', []))
            self.user_patterns['keyword_preferences'] = patterns.get('keyword_preferences', {})
            self.user_patterns['domain_overrides'] = patterns.get('domain_overrides', {})
            
            logger.info(f"📚 Loaded user patterns: {len(self.user_patterns['allowed_sites'])} allowed, "
                       f"{len(self.user_patterns['blocked_sites'])} blocked")
            
        except FileNotFoundError:
            logger.info("📚 No user patterns file found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Error loading user patterns: {e}")
