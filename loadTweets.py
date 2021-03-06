#!/usr/bin/python3.6

import json
import sys
import os.path
from datetime import datetime
from datetime import timedelta
import readConfig
from pymongo import MongoClient
from pymongo import errors


def main():

    #set up connection
    database = 'furzedowntweets'
    collection = 'tweets'
    settings = readConfig.ConfigSettings('config.json')
    client = MongoClient(settings.ConnectionString)
    tweet_database = client[database]

    #get yesterday's date
    yesterday = datetime.now() + timedelta(days=-1)
    year = yesterday.year
    month = yesterday.month
    day = yesterday.day

    start_date = datetime(year, month, day, 0, 0, 0)
    end_date = datetime(year, month, day, 23, 59, 59)

    print(start_date)
    print(end_date)

    #clear down tweets for the day being loaded - ie re-runnable
    deleted = tweet_database[collection].delete_many({"created_at": {"$gte": start_date, "$lte": end_date}})
    print('deleted: ' + str(deleted.deleted_count))

    #get tweets out of json file
    filename = os.path.join(sys.path[0], 'export', 'tweet_data_%4d%02d%02d.json' % (year, month, day))
    print(filename)
    if not os.path.isfile(filename):
        print('File does not exist: ' + filename)
        exit()

    print('loading ' + filename)
    data = []
    for line in open(filename, 'r'):
        data.append(json.loads(line))

    #load tweets into database
    print('inserting records...')
    counter = 1
    for rec in data:
        try:
            tweet_database[collection].insert_one(rec)
        except errors.OperationFailure:
            print("Operation Failure: ", sys.exc_info()[0], str(counter))
        except:
            print("Unexpectec Error: ", sys.exc_info()[0], str(counter))
        counter = counter + 1
    print('inserted: ' + str(counter))

    #update string dates to datetime
    print('converting strings to dates...')
    for doc in tweet_database[collection].find({"created_at": {"$type": 2}}):
        tweet_database[collection].update_one(
            {'_id': doc['_id']},
            {'$set':{'created_at' : datetime.strptime(doc['created_at'], "%a %b %d %H:%M:%S +0000 %Y")}})

    print('done')
if __name__ == '__main__':
    main()
