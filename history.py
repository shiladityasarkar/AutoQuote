# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi
# import excel_to_df as ed
# from sentence_transformers import SentenceTransformer, util
# import numpy as np
# import warnings
# warnings.filterwarnings('ignore')
#
# uri = "mongodb+srv://himanshugulechha:123456seven@autoquote.vz1lawt.mongodb.net/?retryWrites=true&w=majority&appName=AutoQuote"
#
# # Create a new client and connect to the server
# client = MongoClient(uri, server_api=ServerApi('1'))
#
# # Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Ping! You're successfully connected to MongoDB..")
# except Exception as e:
#     print(e)


# import pandas as pd
# def get_unique_model_values(file_path):
#     excel_data = pd.read_excel(file_path, sheet_name=None)
#     for sheet_name, df in excel_data.items():
#         print(df)
#         model_column = [col for col in df.columns if 'model' in col.lower()]
#         if model_column:
#             model_column = model_column[0]
#             unique_values = df[model_column].unique()
#             print(unique_values)
#             exit()
#         else:
#             print(f"No column containing 'model' was found in sheet: {sheet_name}")

# Example usage
file_path = r"C:\StrangerCodes\AutoQuote\data\ROOM LIST  1 - WITH QUOTE.xls"
# get_unique_model_values(file_path)

import excel_to_df as ed
sheets, names = ed.dfmaker('C:\StrangerCodes\AutoQuote\data\Quoted BOQ.xls')

# c = -1
#
# while True:
#     c += 1
#     try:
#         sheets[c].columns = [x.lower() for x in sheets[c].columns]
#     except IndexError:
#         print('All sheets completed.')
#         break
