import praw
import requests
from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
import prawcore  # Ensure prawcore is imported

# Load configuration file
config = ConfigParser()
config.read('config.ini')

# Reddit API Credentials from config.ini
client_id = config.get('reddit', 'client_id')
client_secret = config.get('reddit', 'client_secret')
user_agent = config.get('reddit', 'user_agent')

# Keywords for Bitcoin and Ethereum
keywords_bitcoin = ["Bitcoin", "BTC"]
keywords_ethereum = ["Ethereum", "ETH"]

# Define the timeframe of the last 12 hours
timeframe_start = datetime.now(timezone.utc) - timedelta(hours=12)

# API URL to send data
api_url = "http://localhost:5001/store-text"

# Initialize PRAW with your credentials
try:
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent=user_agent)

    # Function to process subreddit posts
    def process_subreddit_posts(subreddit, keywords):
        entries_to_store = []

        hot_posts = subreddit.hot(limit=20)
        for post in hot_posts:
            title_contains_keyword = any(keyword.lower() in post.title.lower() for keyword in keywords)
            if title_contains_keyword:
                post.comment_sort = 'best'
                post.comments.replace_more(limit=0)
                top_comments = list(post.comments[:10])

                for comment in top_comments:
                    comment_time = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)
                    if comment_time > timeframe_start:
                        print(f"Post Title: {post.title}")
                        print(f"Comment: {comment.body}\n")

                        entry = {
                            'user': comment.author.name if comment.author else '[deleted]',
                            'title': post.title,
                            'text': comment.body,
                            'date': comment_time.isoformat()
                        }
                        entries_to_store.append(entry)
        return entries_to_store

    # Function to send data to API
    def send_to_api(entries, source, keyword):
        if entries:
            data_to_send = {
                'source': source,
                'keyword': keyword,
                'entries': entries
            }
            response = requests.post(api_url, json=data_to_send)
            print(f"Status Code for {keyword}: {response.status_code}")
            print(f"Response for {keyword}: {response.json()}")
        else:
            print(f"No new relevant comments found for {keyword} in the last 12 hours.")

except prawcore.exceptions.ResponseException as e:
    print(f"An authentication error occurred: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

# Process Bitcoin and Ethereum subreddits
btc_entries = process_subreddit_posts(reddit.subreddit('bitcoin'), keywords_bitcoin)
send_to_api(btc_entries, 'Reddit', 'Bitcoin')

eth_entries = process_subreddit_posts(reddit.subreddit('ethereum'), keywords_ethereum)
send_to_api(eth_entries, 'Reddit', 'Ethereum')