import pandas as pd
from pymongo import MongoClient


def connect_mongo(db):
    mongo_uri = "mongodb+srv://himanshugulechha:123456seven@autoquote.vz1lawt.mongodb.net/?retryWrites=true&w=majority&appName=AutoQuote"
    conn = MongoClient(mongo_uri)
    return conn[db]


def read_mongo(db, collection, query={}):
    db = connect_mongo(db)
    cursor = db[collection].find(query)
    df =  pd.DataFrame(list(cursor))
    return df

def main():
    df = read_mongo(db='sampleInventory', collection='inventory', query={'product':'Room Dustbin'})
    print(df)

if __name__ == "__main__":
    main()