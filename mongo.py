# link to go to mongodb atlas
# https://cloud.mongodb.com/v2/66928628c254460ee1b97422#/metrics/replicaSet/669287078569ea69a361c334/explorer/sampleInventory/inventory/find

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import excel_to_df as ed
from sentence_transformers import SentenceTransformer, util
import numpy as np
import warnings
warnings.filterwarnings('ignore')

uri = "mongodb+srv://himanshugulechha:123456seven@autoquote.vz1lawt.mongodb.net/?retryWrites=true&w=majority&appName=AutoQuote"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Ping! You're successfully connected to MongoDB..")
except Exception as e:
    print(e)


model = SentenceTransformer('all-MiniLM-L6-v2')

targets = ['category', 'brand', 'product type', 'model number', 'specifications', 'gst', 'hsn code', 'remarks', 'price', 'hotel name', 'image']

# (only uncomment the code below if any changes are made in targets)
# tar_embeds = model.encode(targets, convert_to_tensor=True)
# np.save('tar_embeds.npy', np.array(tar_embeds))

tar_embeds = np.load('C:/StrangerCodes/AutoQuote/tar_embeds.npy')

sheets_with = ed.dfmaker('C:\StrangerCodes\AutoQuote\data\ROOM LIST  1 - WITH QUOTE.xls')
sheets_without = ed.dfmaker('C:\StrangerCodes\AutoQuote\data\ROOM LIST  1 - WITHOUT QUOTE.xlsy')
c = -1

while True:
    c += 1
    try:
        wilist = list(sheets_with[c].columns.difference(sheets_without[c].columns)) # wishlist
    except IndexError:
        print('All sheets completed.')
        break
    sheets_with[c] = sheets_with[c][wilist]
    sheets_with[c].columns = [x.lower() for x in sheets_with[c].columns]

    try:
        sheets_with[c].drop(['amount'], axis=1, inplace=True)
    except KeyError:
        pass
    try:
        sheets_with[c].drop(['gst value'], axis=1, inplace=True)
    except KeyError:
        pass

    sheets_with[c].dropna(how='all', inplace=True)

    rec = sheets_with[c].columns # recieved
    cols = []
    print('---------------------------------------------')
    for i in range(len(rec)):
        rec_embed = model.encode(rec[i], convert_to_tensor=True)
        sims = util.cos_sim(tar_embeds, rec_embed)
        top_sim_idx = sims.argmax().item()
        top_sim_word = targets[top_sim_idx]
        cols.append(top_sim_word)
        print(f'{rec[i]} = {top_sim_word}')
    print('---------------------------------------------')

    sheets_with[c].columns = cols

    db = client['Inventory']
    collection = db['MainInventory']
    dick = sheets_with[c].to_dict('records')
    ch = input('Do you want to insert this data? (y/n) ')
    if ch == 'y' or ch == 'Y':
        collection.insert_many(dick)
        print('Data inserted successfully!')
    else:
        print('Data not inserted.n')