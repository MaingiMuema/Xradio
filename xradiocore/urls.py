from django.urls import path
from . import views

app_name = 'xradiocore'

urlpatterns = [
    path('', views.news_player, name='news_player'),
    path('api/stream-broadcast/', views.stream_broadcast, name='stream_broadcast'),
    path('api/news/trending/', views.trending_news, name='trending_news'),
]
