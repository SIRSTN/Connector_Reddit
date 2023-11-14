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

# Initialize PRAW with your credentials
try:
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent=user_agent)

    # Access the subreddit
    subreddit = reddit.subreddit('bitcoin')

    # Fetch the top 20 hot posts
    hot_posts = subreddit.hot(limit=20)

    # Define the timeframe of the last 12 hours using timezone-aware datetime
    timeframe_start = datetime.now(timezone.utc) - timedelta(hours=12)

    keywords = ["Bitcoin", "BTC"]

    # API URL to send data
    api_url = "http://localhost:5000/store-text"

    # List to store entries to be sent to the API
    entries_to_store = []

    for post in hot_posts:
        # Convert the post timestamp to a timezone-aware datetime object
        title_contains_keyword = any(keyword.lower() in post.title.lower() for keyword in keywords)

        if title_contains_keyword:
            # Fetch the top 5 comments
            post.comment_sort = 'best'  # Sorts the comments to get the best comments on top
            post.comments.replace_more(limit=0)  # Expands the comment forest fully
            top_comments = list(post.comments[:5])  # Get the top 5 comments

            for comment in top_comments:
                # Convert the comment timestamp to a timezone-aware datetime object
                comment_time = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)

                # Check if the comment is within the last 12 hours
                if comment_time > timeframe_start:
                    print(f"Post Title: {post.title}")
                    print(f"Comment: {comment.body}\n")
                    
                    # Create the entry for each relevant comment
                    entry = {
                        'user': comment.author.name if comment.author else '[deleted]',
                        'title': post.title,
                        'text': comment.body,
                        'date': comment_time.isoformat()  # using the comment time
                    }
                    entries_to_store.append(entry)

    # Send the collected Reddit data to the local API
    if entries_to_store:
        # Prepare the data for the API request
        data_to_send = {
            'source': 'Reddit',
            'keyword': 'Bitcoin',
            'entries': entries_to_store
        }

        # Send a POST request to the API with the Reddit data
        response = requests.post(api_url, json=data_to_send)
        print("Status Code:", response.status_code)
        print("Response:", response.json())
    else:
        print("No new relevant comments found in the last 12 hours.")
except prawcore.exceptions.ResponseException as e:
    print(f"An authentication error occurred: {e}")
except Exception as e:
    print(f"An error occurred: {e}")