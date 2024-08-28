# link to go to mongodb atlas
# https://cloud.mongodb.com/v2/66928628c254460ee1b97422#/metrics/replicaSet/669287078569ea69a361c334/explorer/sampleInventory/inventory/find

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import excel_to_df as ed
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import numpy as np
import warnings
from sklearn.metrics.pairwise import cosine_similarity
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

model = GoogleGenerativeAIEmbeddings(model='models/embedding-001')

targets = ['category', 'brand', 'product', 'model', 'specifications', 'GST', 'HSN', 'remarks', 'price', 'hotel', 'image']

# (only uncomment the code below if any changes are made in targets)
tar_embeds = model.embed_documents(targets)
np.save('tar_embeds.npy', np.array(tar_embeds))

tar_embeds = np.load(r'C:\Users\purus\Documents\GitHub\AutoQuote\tar_embeds.npy')

def push_to_db(file):
    sheets, names = ed.df_maker(file)

    c = -1

    while True:
        c += 1
        try:
            sheets[c].columns = [x.lower() for x in sheets[c].columns]
        except IndexError:
            print('All sheets completed.')
            break


        # try:
        #     sheets_with[c].drop(['amount'], axis=1, inplace=True)
        # except KeyError:
        #     pass
        # try:
        #     sheets_with[c].drop(['gst value'], axis=1, inplace=True)
        # except KeyError:
        #     pass

        sheets[c].dropna(how='all', inplace=True)
        # sheets_with[c].drop('sl no', axis=1, inplace=True)

        rec = sheets[c].columns # recieved
        cols = []

        print('---------------------------------------------')
        for i in range(len(rec)):
            rec_embed = model.embed_query(rec[i])
            sims = []
            for tar_embed in tar_embeds:
                sims.append(cosine_similarity(tar_embed.reshape(1, -1), np.array(rec_embed).reshape(1, -1)))
            top_sim = np.array(sims).argmax()
            top_sim_word = targets[top_sim.item()]
            if sims[top_sim][0][0] > 0.95:
                cols.append(top_sim_word)
                print(f'{rec[i]} = {top_sim_word}')
            else:
                add = input(f"Do you want to add {rec[i]} in place of {top_sim_word}? (y/n)  ")
                if add == 'y':
                    cols.append(top_sim_word)
                    print(f'{rec[i]} = {top_sim_word}')
                else:
                    cols.append('NA')
        print('---------------------------------------------')

        sheets[c].columns = cols
        
        # Dropping the irrelevant columns
        sheets[c].drop('NA', axis=1, inplace=True)

        for i in list(set(targets).difference(cols)):
            sheets[c][i] = 'NA'

        inp = input(f'Which category is the sheet {names[c]} under? ')
        sheets[c]['category'] = inp # change according to sheet.

        print(sheets[c].head())

        db = client['sampleInventory']
        collection = db['inventory']
        records = sheets[c].to_dict('records')
        ch = input('Do you want to insert this data? (y/n) ')
        # ch = 'y'
        if ch == 'y' or ch == 'Y':
            collection.insert_many(records)
            print('Data inserted successfully!')
            return 200
        else:
            print('Data not inserted.')
            return 404