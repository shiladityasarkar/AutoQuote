from math import floor
import pathlib
import re
import tempfile
import warnings
import base64
import io
from tqdm.auto import tqdm
from PIL import Image
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import pandas as pd
from mongo_to_df import read_mongo
from excel_to_df import df_maker
from langchain import hub
from pinecone.grpc import PineconeGRPC as Pinecone
from langchain_groq import ChatGroq
from langchain_community.document_loaders import CSVLoader
from langchain_pinecone import PineconeVectorStore
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

warnings.filterwarnings('ignore')
load_dotenv()

def create_vectordb(file, update=False):
    print("Reading data from mongoDB...")
    quote = read_mongo(db='sampleInventory', collection='inventory')
    # User sheets
    sheets, sheet_names = df_maker(file)
    print(sheets)
    
    # To be executed only when the inventory is updated
    if update:
        print("Creating embeddings...")
        quote[['_id', 'product', 'specifications']].to_csv('mongo_data.csv')

        # Indexing
        loader = CSVLoader(r"C:\Users\purus\Documents\GitHub\AutoQuote\mongo_data.csv", encoding='latin1')
        documents = loader.load()
        
        # Emptying the index
        pc = Pinecone()
        pc.Index("autoquote").delete(delete_all=True,
                                     namespace="")

        # Storing all the vectors
        vectorstore = PineconeVectorStore.from_documents(documents=documents,
                                                    embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
                                                    index_name="autoquote")
    else:
        vectorstore = PineconeVectorStore(index_name="autoquote",
                                        embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"))

    return vectorstore, sheets, sheet_names, quote

# Function to get the column index
def get_column_index(columns, names):
    for name in names:
        if name in columns:
            return columns.index(name)
    return None

# Function to decode the images
def decode_base64(base64_string):
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    return image

def main(file, gst, hsn, options, price_range):
    file = "C:/Users/purus/Documents/GitHub/AutoQuote/data/" + file
    print(file)
    vectorstore, sheets, sheet_names, quote = create_vectordb(file, update=False)

    # Retrieve and Generate
    llm = ChatGroq(temperature=0,
                   api_key='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')
    retriever = vectorstore.as_retriever()

    prompt = hub.pull("rlm/rag-prompt")
    
    rag_chain = (
        {'context': retriever, 'question': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    col_list = ["_id", "product", "image", "brand", "model", "specifications", "price", "total price", "remarks"]
    if gst == 'yes':
        col_list.append("GST")
    if hsn == 'yes':
        col_list.append("HSN")
    writer = pd.ExcelWriter('quoted_boq.xlsx', engine='xlsxwriter')
    # Iterating over the sheets
    for sheet, name in zip(sheets, sheet_names):
        # Creating a dataframe
        final_df = pd.DataFrame(columns=col_list)
        cols = list(map(lambda x: x.strip().lower(), sheet.columns))

        # Getting the index of the quantity and item columns
        quantity_idx = get_column_index(cols, ['qty', 'total qty'])
        item_idx = get_column_index(cols, ['item', 'product'])
        
        # Iterating over the rows
        previous_format = pd.DataFrame([sheet.iloc[0]])
        progress_bar = tqdm(sheet.iterrows(), desc=f"Sheet: {name}")
        for idx, row in enumerate(progress_bar):
            product_name = row[1][item_idx]
            quantity = row[1][quantity_idx]
            
            # Retrieve the data from 'quote'
            output = rag_chain.invoke(f"Retrieve the <_id> of the products closest to the following description: {product_name}. Do not look only for an exact match, a closely related match will work just as well. If there are no close matches, simply return <None>.")
            _ids = re.findall(r'\b[0-9][a-z0-9]{22}[a-z0-9]\b', output)
            row = pd.DataFrame([[None] * 11], columns=["_id", "product", "image", "brand", "model", "specifications", "price", "GST", "total price", "HSN", "remarks"])
            print(_ids)
            if len(_ids) == 0:
                previous_format = pd.concat([previous_format, pd.DataFrame([sheet.iloc[idx]])], join='inner')
                previous_format.reset_index(inplace=True, drop=True)
            else:
                # Looping over all the matching items
                for id_idx in range(len(_ids)):
                    # Appending to previous format
                    previous_format = pd.concat([previous_format, pd.DataFrame([sheet.iloc[idx]])], join='inner')
                    previous_format.reset_index(inplace=True, drop=True)
                    # Adding the new item
                    row = pd.concat([quote[quote['_id'].astype(str) == _ids[id_idx]], row], join='inner')
                # Sorting on the basis of price
                row = row[row['_id'].notna()]
                row.sort_values('price', inplace=True)
                # Check for price ranges and see if options are enabled
                range_size = floor(row.shape[0] / 3)
                if range_size >= 1:
                    if price_range[0] == 'yes':
                        row = row.iloc[:range_size]
                    elif price_range[1] == 'yes':
                        row = row.iloc[range_size:range_size * 2]
                    elif price_range[2] == 'yes':
                        row = row.iloc[range_size * 2: range_size * 3]
                print(" Row updated!")
                try:
                    row["total price"] = quantity * (row['price'].astype(float)) * ((row['GST'].astype(float)) + 1)
                except:
                    print('error in total price')
            final_df = pd.concat([final_df, row], join='inner')
            print(final_df)
        # Removing the duplicate indices
        previous_format.drop([0], inplace=True)
        previous_format.reset_index(inplace=True, drop=True)
        final_df.reset_index(inplace=True, drop=True)
        final_df = pd.concat([previous_format, final_df], axis=1)
        final_df.to_excel(writer,
                          sheet_name=name,
                          index=False)
        print(f"Sheet: {name} created!")

        # Formatting the sheet
        workbook  = writer.book
        worksheet = writer.sheets[name]
        empty_row = workbook.add_format({
                'fg_color': 'red',
                'border': 1
            })
        header_row = workbook.add_format({
                'fg_color': 'black',
                'font_color': 'white',
                'bold': True
            })
        for col_num, value in enumerate(final_df.columns.values):
            worksheet.write(0, col_num, value, header_row)
            
        # Inserting images into the Excel file
        for idx, row in enumerate(final_df.iterrows()):
            worksheet.set_row(idx + 1, 50)
            worksheet.set_column(idx + 1, 50)
            try:
                image = decode_base64(row[1]['image'])
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    image.save(tmp_file.name)
                    tmp_file_path = tmp_file.name
                # Inserting the image using xlsxwriter
                img_col = chr(final_df.shape[1] - 8 + 65)
                worksheet.embed_image(f'{img_col}{idx + 2}', tmp_file_path)
            except Exception as e:
                if row[1]['_id'] == None:
                    worksheet.set_row(idx + 1, None, empty_row)
                print(f"{idx}: {e}")
            worksheet.autofit()

    # Saving the file
    writer.close()
    return pathlib.Path(__file__).parent.resolve().__str__() + "\quoted_boq.xlsx"

# if __name__ == "__main__":
#     main('abc', 'yes', 'no')