import google.generativeai as genai
from django.conf import settings
from django.core.cache import cache
import logging
import json
import hashlib
import re

logger = logging.getLogger(__name__)

class GoogleAIService:
    def __init__(self):
        self.api_key = settings.GOOGLE_AI_API_KEY
        if not self.api_key:
            logger.error("GOOGLE_AI_API_KEY is not set in settings")
            raise ValueError("GOOGLE_AI_API_KEY is not set")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logger.info(f"Google AI service initialized successfully with API key: {self.api_key[:5]}...")
        
        # Define hosts and their traits
        self.hosts = {
            'main_host': 'Alex',
            'news_anchor': 'Sarah',
            'tech_expert': 'Michael',
            'culture_host': 'Diana'
        }
        
        # Add detailed host traits
        self.host_traits = {
            'main_host': {
                'personality': 'warm and engaging',
                'style': 'conversational and inclusive',
                'interests': ['current events', 'technology', 'society']
            },
            'news_anchor': {
                'personality': 'professional and clear',
                'style': 'precise and authoritative',
                'interests': ['news', 'current affairs', 'global events']
            },
            'tech_expert': {
                'personality': 'enthusiastic and knowledgeable',
                'style': 'explanatory and passionate',
                'interests': ['technology', 'innovation', 'science']
            },
            'culture_host': {
                'personality': 'insightful and relatable',
                'style': 'thoughtful and engaging',
                'interests': ['culture', 'society', 'trends']
            }
        }
        
        self.current_host = 'main_host'
    
    async def generate_news_script(self, news_articles):
        cache_key = self._generate_cache_key(news_articles)
        cached_script = cache.get(cache_key)
        
        if cached_script:
            logger.info("Returning cached news script")
            return cached_script
        
        try:
            news_context = "\n".join([f"- {article['text'][:100]}" for article in news_articles[:5]])
            
            prompt = f"""As a professional news broadcaster, present a brief summary of these news items:

            {news_context}

            Guidelines:
            - Keep the tone neutral and factual
            - Avoid any controversial interpretations
            - Focus on main facts only
            - Use simple, clear language
            - Limit each item to 2-3 sentences
            """
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if not response or not response.text:
                logger.warning("Empty response from AI model, using fallback")
                return "Here are today's top stories. " + " ".join([
                    article['text'][:100] + "..." for article in news_articles[:3]
                ])
            
            processed_text = self._remove_punctuation(response.text)
            cache.set(cache_key, processed_text, timeout=3600)  # Cache for 1 hour
            return processed_text
            
        except Exception as e:
            logger.error(f"Error generating script: {str(e)}")
            return "We are experiencing technical difficulties with our news service. Here are the headlines: " + \
                   " ".join([article['text'][:50] + "..." for article in news_articles[:2]])

    def _generate_cache_key(self, news_articles):
        content = json.dumps([article['text'][:50] for article in news_articles[:5]], sort_keys=True)
        return f"news_script_{hashlib.md5(content.encode()).hexdigest()}"

    async def generate_educational_content(self):
        try:
            prompt = """Share a brief interesting fact or insight about science technology or culture
            Requirements:
            - Keep it simple and engaging
            - Focus on positive and neutral topics
            - Avoid controversial subjects
            - Keep it under 50 words"""
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 512,
            }
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if not response or not response.text:
                return "Did you know that the human brain processes images in just 13 milliseconds Thats faster than the blink of an eye"
            
            return self._remove_punctuation(response.text)
        
        except Exception as e:
            logger.error(f"Error generating educational content: {str(e)}")
            return "Here is an interesting fact about technology and innovation"

    def _remove_punctuation(self, text):
        # Remove punctuation but keep apostrophes for contractions
        return re.sub(r'[^\w\s\']', '', text)

    async def generate_contextual_transition(self, current_host, next_host):
        try:
            current_trait = self.host_traits[current_host]
            next_trait = self.host_traits[next_host]
            
            prompt = f"""As {self.hosts[current_host]}, create a natural transition to {self.hosts[next_host]}.
            
            Your style: {current_trait['style']}
            Next host: {self.hosts[next_host]} ({next_trait['personality']})
            
            Requirements:
            - Keep it natural and conversational
            - Reference your discussion if relevant
            - Maximum 15 seconds of speech
            """
            
            response = await self.model.generate_content_async(prompt)
            return self._remove_punctuation(response.text)
        except Exception as e:
            logger.error(f"Error generating transition: {str(e)}")
            return None

    async def generate_host_handover(self, from_host, to_host, topic=None):
        try:
            prompt = f"""As a radio host named {self.hosts[from_host]}, create a friendly handover to {self.hosts[to_host]}.
            Requirements:
            - Keep it simple and friendly
            - Avoid any controversial topics
            - Focus on positive transitions
            - Keep it under 20 words
            Example: "Thanks everyone Now lets welcome {self.hosts[to_host]} to share more insights"
            """
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 256,
            }
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if not response or not response.text:
                logger.warning("Empty response from AI model, using fallback")
                return f"Thanks everyone Now lets welcome {self.hosts[to_host]} to share more insights"
                
            return self._remove_punctuation(response.text)
            
        except Exception as e:
            logger.error(f"Error generating handover: {str(e)}")
            return f"And now over to {self.hosts[to_host]}"

    async def generate_host_reaction(self, topic):
        try:
            prompt = f"""As {self.hosts[self.current_host]}, give a brief natural reaction to: {topic}
            Requirements:
            - Keep it under 15 words
            - Sound spontaneous
            - No explicit punctuation
            - Include a personal touch"""
            
            response = await self.model.generate_content_async(prompt)
            return self._remove_punctuation(response.text)
        except Exception as e:
            logger.error(f"Error generating reaction: {str(e)}")
            return "That's really fascinating"

    async def generate_segment_content(self, content_type, subtopic, previous_content=None):
        try:
            prompt = f"""Generate engaging radio content about {subtopic} for a {content_type} segment.
            Previous segments: {', '.join(previous_content) if previous_content else 'None'}
            
            Requirements:
            - Keep it fresh and engaging
            - Avoid repeating topics from previous segments
            - Include relevant examples or stories
            - Use conversational language
            - Keep it under 100 words
            - Match the tone to the topic
            """
            
            generation_config = {
                "temperature": 0.8,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return self._remove_punctuation(response.text)
        except Exception as e:
            logger.error(f"Error generating segment content: {str(e)}")
            return None

    async def generate_host_discussion(self, host1, host2, topic, subtopic):
        try:
            prompt = f"""Generate a natural discussion between {self.hosts[host1]} and {self.hosts[host2]} about {subtopic} in {topic}.
            
            Requirements:
            - Create 2-3 exchanges
            - Keep it conversational
            - Include different perspectives
            - Each response should be 1-2 sentences
            - Match each host's personality
            
            Format the response as:
            HOST1: [text]
            HOST2: [text]
            HOST1: [text]
            """
            
            response = await self.model.generate_content_async(prompt)
            
            if not response or not response.text:
                return None
                
            discussion = []
            lines = response.text.split('\n')
            
            for line in lines:
                if ':' in line:
                    speaker, text = line.split(':', 1)
                    speaker = speaker.strip().lower()
                    text = self._remove_punctuation(text.strip())
                    
                    if speaker == self.hosts[host1].lower():
                        discussion.append({'speaker': host1, 'text': text})
                    elif speaker == self.hosts[host2].lower():
                        discussion.append({'speaker': host2, 'text': text})
            
            return discussion
        except Exception as e:
            logger.error(f"Error generating discussion: {str(e)}")
            return None

    async def generate_news_analysis(self, host_type, news_items):
        try:
            host_trait = self.host_traits[host_type]
            prompt = f"""As {self.hosts[host_type]}, provide thoughtful analysis of these news items:
            {[item['text'] for item in news_items]}
            
            Your personality: {host_trait['personality']}
            Your expertise: {', '.join(host_trait['interests'])}
            
            Requirements:
            - Provide deeper context and implications
            - Draw connections to broader trends
            - Keep it engaging but professional
            - Aim for about 2-3 minutes of speech
            """
            
            response = await self.model.generate_content_async(prompt)
            return self._remove_punctuation(response.text)
        except Exception as e:
            logger.error(f"Error generating news analysis: {str(e)}")
            return None

    async def generate_deep_dive_content(self):
        try:
            prompt = """Create an in-depth exploration of a current technology or scientific topic.
            Requirements:
            - Focus on one specific aspect for thorough coverage
            - Include real-world applications and implications
            - Make complex concepts accessible
            - Aim for about 3-4 minutes of speech
            """
            
            response = await self.model.generate_content_async(prompt)
            return self._remove_punctuation(response.text)
        except Exception as e:
            logger.error(f"Error generating deep dive content: {str(e)}")
            return None

    async def generate_analysis_intro(self):
        try:
            host_trait = self.host_traits['main_host']
            prompt = f"""As {self.hosts['main_host']}, introduce an analysis segment.
            
            Your personality: {host_trait['personality']}
            Your style: {host_trait['style']}
            
            Requirements:
            - Set up the context for the upcoming analysis
            - Keep it engaging and welcoming
            - Maximum 30 seconds of speech
            """
            
            response = await self.model.generate_content_async(prompt)
            return self._remove_punctuation(response.text)
        except Exception as e:
            logger.error(f"Error generating analysis intro: {str(e)}")
            return None

    async def generate_expert_perspective(self):
        try:
            host_trait = self.host_traits['tech_expert']
            prompt = f"""As {self.hosts['tech_expert']}, provide expert analysis on current technological trends.
            
            Your personality: {host_trait['personality']}
            Your expertise: {', '.join(host_trait['interests'])}
            
            Requirements:
            - Focus on technical insights and implications
            - Make complex concepts accessible
            - Aim for about 2 minutes of speech
            """
            
            response = await self.model.generate_content_async(prompt)
            return self._remove_punctuation(response.text)
        except Exception as e:
            logger.error(f"Error generating expert perspective: {str(e)}")
            return None

    async def generate_cultural_perspective(self, host_type, content):
        """Generate cultural perspective on a given topic"""
        try:
            host_trait = self.host_traits[host_type]
            prompt = f"""As {self.hosts[host_type]}, provide cultural perspective on:
            {content}
            
            Your personality: {host_trait['personality']}
            Your expertise: {', '.join(host_trait['interests'])}
            
            Requirements:
            - Connect technical concepts to cultural impact
            - Share relevant cultural insights
            - Keep it engaging and relatable
            - Aim for about 2 minutes of speech
            """
            
            response = await self.model.generate_content_async(prompt)
            return self._remove_punctuation(response.text)
        except Exception as e:
            logger.error(f"Error generating cultural perspective: {str(e)}")
            return None
