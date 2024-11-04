from newsapi import NewsApiClient
from django.conf import settings
import logging
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import asyncio

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        self.api = NewsApiClient(api_key=settings.NEWSAPI_KEY)
        self.citizen_url = "https://www.citizen.digital/"
        self.last_citizen_update = 0
        self.CITIZEN_UPDATE_INTERVAL = 480  # 8 minutes
        self.news_cache = []
        self.last_news_fetch = 0
        self.NEWS_CACHE_DURATION = 300  # 5 minutes
        logger.info("NewsAPI client initialized with Citizen Digital scraping")

    async def get_citizen_news(self):
        """Scrape news from Citizen Digital"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            response = await asyncio.to_thread(requests.get, self.citizen_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []
            
            # Get top stories
            top_stories = soup.find_all('div', class_='topstory')
            for story in top_stories:
                # Get headline
                headline = story.find('h1')
                if headline and headline.find('a'):
                    title = headline.find('a').text.strip()
                    # Get category and time if available
                    category_time = story.find('div', class_='next-topstory-tags')
                    category = category_time.find('span').text.strip() if category_time else ''
                    time_published = category_time.find('span', class_='timepublished').text.strip() if category_time else ''
                    # Get description
                    description = story.find('p')
                    description_text = description.text.strip() if description else ''
                    
                    if title:
                        full_text = f"{category}: {title}"
                        if description_text:
                            full_text += f". {description_text}"
                        
                        news_items.append({
                            'text': full_text,
                            'created_at': datetime.now(timezone.utc),
                            'id': 'citizen-' + str(len(news_items)),
                            'source': 'Citizen Digital',
                            'category': category
                        })

            # Get featured stories
            featured_stories = soup.find_all('div', class_='featuredstory')
            for story in featured_stories:
                if story not in top_stories:  # Avoid duplicates
                    headline = story.find(['h1', 'h2', 'h3'])
                    if headline and headline.find('a'):
                        title = headline.find('a').text.strip()
                        description = story.find('p')
                        description_text = description.text.strip() if description else ''
                        
                        if title:
                            full_text = title
                            if description_text:
                                full_text += f". {description_text}"
                            
                            news_items.append({
                                'text': full_text,
                                'created_at': datetime.now(timezone.utc),
                                'id': 'citizen-' + str(len(news_items)),
                                'source': 'Citizen Digital'
                            })

            # Remove duplicates while preserving order
            seen = set()
            unique_news = []
            for item in news_items:
                if item['text'] not in seen:
                    seen.add(item['text'])
                    unique_news.append(item)

            logger.info(f"Successfully scraped {len(unique_news)} news items from Citizen Digital")
            return unique_news[:10]  # Return top 10 news items

        except Exception as e:
            logger.error(f"Error scraping Citizen Digital: {str(e)}")
            if 'response' in locals():
                logger.error(f"Response status code: {response.status_code}")
                logger.debug(f"Sample HTML: {response.text[:500]}")
            return []

    async def get_trending_news(self, max_results=10):
        """Get news from both NewsAPI and Citizen Digital"""
        try:
            current_time = asyncio.get_event_loop().time()
            
            # Return cached news if within cache duration
            if self.news_cache and current_time - self.last_news_fetch < self.NEWS_CACHE_DURATION:
                logger.info("Returning cached news")
                return self.news_cache

            news_data = []
            
            # Get international news from NewsAPI
            newsapi_response = await asyncio.to_thread(
                self.api.get_top_headlines,
                language='en',
                page_size=max_results
            )
            
            if newsapi_response['status'] == 'ok':
                articles = newsapi_response['articles']
                news_data.extend([{
                    'text': article['title'] + '. ' + (article['description'] or ''),
                    'created_at': datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
                    'id': article['url'],
                    'source': 'NewsAPI'
                } for article in articles if article['title'] and article['description']])

            # Get Citizen Digital news
            citizen_news = await self.get_citizen_news()
            news_data.extend(citizen_news)

            # Update cache
            self.news_cache = sorted(news_data, key=lambda x: x['created_at'], reverse=True)[:max_results]
            self.last_news_fetch = current_time

            logger.info(f"Successfully fetched {len(self.news_cache)} total news articles")
            return self.news_cache

        except Exception as e:
            logger.error(f"Error fetching trending news: {str(e)}")
            return self.news_cache if self.news_cache else []

    def test_api_connection(self):
        try:
            response = self.api.get_top_headlines(language='en', page_size=1)
            citizen_response = requests.get(self.citizen_url)
            
            api_ok = response['status'] == 'ok'
            citizen_ok = citizen_response.status_code == 200
            
            if api_ok and citizen_ok:
                logger.info("NewsAPI and Citizen Digital connection tests successful")
                return True
            else:
                logger.error("Connection test failed for one or more news sources")
                return False
        except Exception as e:
            logger.error(f"News service connection test failed: {str(e)}")
            return False
