from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from api_integration.news import NewsService
from api_integration.chatgpt import GoogleAIService
from api_integration.elevenlabs import ElevenLabsService
import asyncio
import logging
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

async def generate_continuous_broadcast():
    news_service = NewsService()
    google_ai_service = GoogleAIService()
    elevenlabs_service = ElevenLabsService()
    
    last_news_update = 0
    last_content_types = set()  # Track recently used content types
    NEWS_UPDATE_INTERVAL = 600  # 10 minutes
    
    content_types = ['news', 'deep_dive', 'analysis']
    current_content_index = 0
    
    while True:
        try:
            current_time = asyncio.get_event_loop().time()
            
            # Force news update if interval has passed, regardless of content rotation
            if current_time - last_news_update >= NEWS_UPDATE_INTERVAL:
                content_type = 'news'
                last_news_update = current_time
            else:
                # Select content type with preference for unused types
                available_types = [t for t in content_types if t not in last_content_types]
                if not available_types:
                    last_content_types.clear()
                    available_types = content_types
                
                content_type = available_types[current_content_index % len(available_types)]
                current_content_index = (current_content_index + 1) % len(available_types)
                last_content_types.add(content_type)
            
            if content_type == 'news':
                # News segment with comprehensive coverage
                news = await news_service.get_trending_news()
                if news:
                    try:
                        google_ai_service.current_host = 'news_anchor'
                        news_script = await google_ai_service.generate_news_script(news)
                        if news_script:
                            audio_content = await elevenlabs_service.generate_speech(
                                news_script,
                                'news_anchor'
                            )
                            if audio_content:
                                yield audio_content
                                
                        # Add thoughtful analysis from main host
                        if len(news) >= 2:
                            analysis = await google_ai_service.generate_news_analysis('main_host', news[:2])
                            if analysis:
                                audio_content = await elevenlabs_service.generate_speech(
                                    analysis,
                                    'main_host'
                                )
                                if audio_content:
                                    yield audio_content
                    except Exception as e:
                        logger.error(f"Error in news segment: {str(e)}")
                        await asyncio.sleep(5)  # Add delay on error
                        continue  # Skip to next iteration
            
            elif content_type == 'deep_dive':
                # In-depth educational segment with expert perspective
                try:
                    google_ai_service.current_host = 'tech_expert'
                    content = await google_ai_service.generate_deep_dive_content()
                    if content:
                        audio_content = await elevenlabs_service.generate_speech(content, 'tech_expert')
                        if audio_content:
                            yield audio_content
                            
                        # Add cultural perspective
                        cultural_insight = await google_ai_service.generate_cultural_perspective('culture_host', content)
                        if cultural_insight:
                            audio_content = await elevenlabs_service.generate_speech(cultural_insight, 'culture_host')
                            if audio_content:
                                yield audio_content
                except Exception as e:
                    logger.error(f"Error in deep dive segment: {str(e)}")
                    await asyncio.sleep(5)  # Add delay on error
                    continue  # Skip to next iteration
            
            elif content_type == 'analysis':
                # Thoughtful analysis segment with multiple perspectives
                try:
                    # Start with main host introduction
                    google_ai_service.current_host = 'main_host'
                    intro = await google_ai_service.generate_analysis_intro()
                    if intro:
                        audio_content = await elevenlabs_service.generate_speech(intro, 'main_host')
                        if audio_content:
                            yield audio_content
                    
                    # Expert perspective
                    google_ai_service.current_host = 'tech_expert'
                    expert_view = await google_ai_service.generate_expert_perspective()
                    if expert_view:
                        audio_content = await elevenlabs_service.generate_speech(expert_view, 'tech_expert')
                        if audio_content:
                            yield audio_content
                    
                    # Cultural context
                    google_ai_service.current_host = 'culture_host'
                    cultural_view = await google_ai_service.generate_cultural_perspective('culture_host', expert_view)
                    if cultural_view:
                        audio_content = await elevenlabs_service.generate_speech(cultural_view, 'culture_host')
                        if audio_content:
                            yield audio_content
                            
                except Exception as e:
                    logger.error(f"Error in analysis segment: {str(e)}")
                    await asyncio.sleep(5)  # Add delay on error
                    continue  # Skip to next iteration
            
            # Add shorter pause between segments
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in broadcast loop: {str(e)}")
            await asyncio.sleep(5)
            continue

def stream_broadcast_generator():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async_gen = generate_continuous_broadcast()
    while True:
        try:
            yield loop.run_until_complete(async_gen.__anext__())
        except StopAsyncIteration:
            break

@require_http_methods(["GET"])
def stream_broadcast(request):
    return StreamingHttpResponse(stream_broadcast_generator(), content_type='audio/mpeg')

@ensure_csrf_cookie
def news_player(request):
    return render(request, 'xradiocore/player.html')

async def trending_news(request):
    try:
        news_service = NewsService()
        news = await news_service.get_trending_news(max_results=20)
        
        if not news:
            return JsonResponse({
                'error': 'No news available at the moment'
            }, status=404)
        
        # Extract trending topics from news
        topics = {}
        for item in news:
            category = item.get('category', 'General')
            if category not in topics:
                topics[category] = {
                    'count': 1,
                    'latest': item,
                    'trend': 'up'
                }
            else:
                topics[category]['count'] += 1
        
        response_data = {
            'news': news,
            'topics': [
                {
                    'name': category,
                    'count': data['count'],
                    'trend': data['trend'],
                    'latest_news': data['latest']['text'][:100] + '...' if len(data['latest']['text']) > 100 else data['latest']['text']
                }
                for category, data in topics.items()
            ]
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"Error in trending_news view: {str(e)}")
        return JsonResponse({
            'error': 'An error occurred while fetching news',
            'detail': str(e)
        }, status=500)
