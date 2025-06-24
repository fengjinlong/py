import tweepy
import time
from datetime import datetime

def log_message(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {message}")

def wait_for_rate_limit():
    log_message("Rate limit reached. Waiting for reset...")
    time.sleep(60)  # 等待1分钟后重试

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except tweepy.errors.TooManyRequests as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = 60 * (attempt + 1)  # 逐步增加等待时间
            log_message(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
        except Exception as e:
            raise e

# 配置认证
auth = tweepy.OAuthHandler('GsSh1p5jFV2HuymoYOOZzvGre', 'ssEWy2mw7DiFDkAn3Ca6Ia5G58D8116Cq67asTmm3VUEKTaFZX')
auth.set_access_token('1781273617705418752-9zB7oK4TAliY1bEtu8gpF34d3MTCZE', 'Ze2kpr7C0jBZUQYFYtTtfaKIp2nb66mMMVCCczk3MPZgL')

# 创建API对象
api = tweepy.API(auth, wait_on_rate_limit=True)

# 创建Client对象 - 使用 API v2
client = tweepy.Client(
    consumer_key='GsSh1p5jFV2HuymoYOOZzvGre',
    consumer_secret='ssEWy2mw7DiFDkAn3Ca6Ia5G58D8116Cq67asTmm3VUEKTaFZX',
    access_token='1781273617705418752-9zB7oK4TAliY1bEtu8gpF34d3MTCZE',
    access_token_secret='Ze2kpr7C0jBZUQYFYtTtfaKIp2nb66mMMVCCczk3MPZgL',
    wait_on_rate_limit=True
)

# 目标推文ID
tweet_id = "1932609825357054135"

try:
    # 使用 v2 API 获取推文
    def get_tweet():
        tweet = client.get_tweet(tweet_id, user_auth=True)
        if not tweet.data:
            raise Exception("Tweet not found")
        return tweet

    log_message("Checking tweet...")
    tweet = retry_with_backoff(get_tweet)
    log_message(f"Found tweet: {tweet.data}")

    # 使用 v2 API 点赞
    def like_tweet():
        result = client.like(tweet_id)
        if not result.data:
            raise Exception("Like operation failed")
        return result

    log_message("Attempting to like the tweet...")
    retry_with_backoff(like_tweet)
    log_message("Successfully liked the tweet!")

    # 使用 v2 API 回复
    def reply_tweet():
        response = client.create_tweet(
            text="Great post! 👍",
            in_reply_to_tweet_id=tweet_id
        )
        if not response.data:
            raise Exception("Reply operation failed")
        return response

    log_message("Attempting to reply to the tweet...")
    retry_with_backoff(reply_tweet)
    log_message("Successfully replied to the tweet!")

except tweepy.errors.TooManyRequests:
    log_message("Rate limit exceeded. Please try again later.")
    log_message("Consider upgrading your Twitter API access level for higher limits.")
except Exception as e:
    log_message(f"An error occurred: {e}")
    log_message("\nNote: Free Twitter API access has limited functionality.")
    log_message("To get full access, you need to:")
    log_message("1. Visit https://developer.twitter.com/en/portal/products")
    log_message("2. Apply for Elevated access or subscribe to a paid tier")
    log_message("3. Wait for approval or complete the subscription process")