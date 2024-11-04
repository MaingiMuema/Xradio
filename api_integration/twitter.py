import requests
from requests_oauthlib import OAuth1
from django.conf import settings
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TwitterNewsService:
    def __init__(self):
        self.api_base_url = "https://api.twitter.com/2"
        self.auth = OAuth1(
            settings.TWITTER_API_KEY,
            settings.TWITTER_API_SECRET_KEY,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        logger.info("Twitter client initialized")

    def _make_request(self, endpoint, params=None):
        url = f"{self.api_base_url}/{endpoint}"
        response = requests.get(url, auth=self.auth, params=params)
        if response.status_code != 200:
            raise Exception(f"Request returned an error: {response.status_code} {response.text}")
        return response.json()

    def get_kenya_news(self, max_results=10):
        try:
            # User IDs for @citizentvkenya (33027232) and @KTNNewsKE (308348251)
            user_ids = ["33027232", "308348251"]
            all_tweets = []

            for user_id in user_ids:
                logger.info(f"Fetching tweets for user ID: {user_id}")

                params = {
                    "max_results": max_results,
                    "tweet.fields": "created_at,text",
                    "exclude": "retweets,replies"
                }

                response_json = self._make_request(f"users/{user_id}/tweets", params)

                if "data" in response_json and response_json["data"]:
                    tweets = [{
                        'text': tweet['text'],
                        'created_at': datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc),
                        'id': tweet['id']
                    } for tweet in response_json["data"]]
                    all_tweets.extend(tweets)

            if not all_tweets:
                logger.warning("No tweets found")
                return []

            # Sort tweets by created_at in descending order (most recent first)
            all_tweets.sort(key=lambda x: x['created_at'], reverse=True)

            # Limit to max_results
            all_tweets = all_tweets[:max_results]

            logger.info(f"Successfully fetched {len(all_tweets)} tweets")
            return all_tweets

        except Exception as e:
            logger.error(f"Error fetching tweets: {str(e)}")
            return []

    def test_api_connection(self):
        try:
            response_json = self._make_request("users/me")
            username = response_json["data"]["username"]
            logger.info(f"API test successful. Connected as: {username}")
            return True
        except Exception as e:
            logger.error(f"API test failed: {str(e)}")
            return False
