import pandas as pd
from pandas import DataFrame
import secrets
import sys, os
import twitter
import time
from util import *

# Must be a valid set of credentials
api = twitter.Api(consumer_key=secrets.consumer_key,
                  consumer_secret=secrets.consumer_secret,
                  access_token_key=secrets.access_token_key,
                  access_token_secret=secrets.access_token_secret)

# Load a set of tweet ids from a file, pull the tweet data from the Twitter API and output to a csv
# params:
#   tweet_id_file: the filename of the tweet ids.
#   output_file: the file to output tweet data to
# returns:
#   None. All output goes to the file.
def load_historical(tweet_id_file,output_file):
    loaded_tweets = []

    # just so we don't have to keep retrieveing tweets we already got
    # check to see if this file already exists. If so, lets pull the tweet ids from it and skip them
    if os.path.isfile(output_file):
        loaded_tweets = pd.read_csv(output_file).id.values

    tweet_data = []

    # get the tweet ids from the file
    with open(tweet_id_file, 'r') as file:
        tweet_ids = [line.rstrip('\n') for line in file.readlines()]

    # we can only request 100 tweets at a time, so we fill up this array,
    # pass it to the worker function at 99 ids, then dump it and start again
    ids_to_request = []
    for tweet_id in tweet_ids:

        # skip ids that are already saved in file
        if int(tweet_id) in loaded_tweets: # skip it if this id has already been loaded
            print("Tweet ID {} already loaded...".format(tweet_id))
            continue
        else:
            ids_to_request.append(tweet_id)

        if len(ids_to_request) > 99:
            for data in request_tweet_data(ids_to_request):
                tweet_data.append(data)
            # just so we know it's working and how fast it's going
            super_print("loading tweets {} thru {}...".format(ids_to_request[0], ids_to_request[-1]))
            # we're rate limited to 1 request a second.
            time.sleep(1)
            ids_to_request = []

    # get any last ids that didn't make it
    for data in request_tweet_data(ids_to_request):
        tweet_data.append(data)

    # save the data we collected to a csv
    if os.path.isfile(output_file):
        # the file already exists, so append the data to the end
        DataFrame(tweet_data).to_csv(output_file, mode='a', header=False)
    else:
        DataFrame(tweet_data).to_csv(output_file)

# request a set of tweets by id from the Twitter API
# params:
#   ids: an array of integers that correspond to tweet ids
# returns:
#   a list of dict objects
def request_tweet_data(ids):
    tweet_data = []
    data = api.GetStatuses(ids, trim_user=True)
    for tweet in data:
        tweet_data.append({
                "id":tweet.id,
                "user":tweet.user.id,
                "time":tweet.created_at_in_seconds,
                "text":tweet.text,
                "urls":",".join([url.expanded_url for url in tweet.urls])
            })
    return tweet_data

if __name__=="__main__":
    if len(sys.argv) > 1:
        if "--load" in sys.argv and len(sys.argv) >= 4:
            if sys.argv[2] == "senators":
                print("Loading all historical Senator tweets...")
                load_historical("data/senators.txt", sys.argv[3])
            elif sys.argv[2] == "reps":
                print("Loading all historical Representative tweets...")
                load_historical("data/representatives.txt", sys.argv[3])
