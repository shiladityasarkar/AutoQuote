import re
import warnings
import base64
import io
from PIL import Image
import os
import tempfile
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
    quote = read_mongo(db='sampleInventory', collection='inventory')
    # User sheets
    sheets, sheet_names = df_maker(r"S:\AutoQuote\data\ROOM LIST  1 - WITHOUT QUOTE.xls")
    print(sheets)
    
    # To be executed only when the inventory is updated
    if update:
        quote[['_id', 'product', 'specifications']].to_csv('mongo_data.csv')

        # Indexing
        loader = CSVLoader("S:\AutoQuote\mongo_data.csv", encoding='latin1')
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

def decode_base64(base64_string):
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    return image

def main(file, gst, hsn):
    file = "S:/AutoQuote/data/" + file
    print(file)
    vectorstore, sheets, sheet_names, quote = create_vectordb(file)

    # Retrieve and Generate
    llm = ChatGroq(temperature=0)
    retriever = vectorstore.as_retriever()

    prompt = hub.pull("rlm/rag-prompt")
    
    rag_chain = (
        {'context': retriever, 'question': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    col_list = ["_id", "product", "image", "brand", "model", "specifications", "price", "remarks"]
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
        for row in sheet.iterrows():
            product_name = row[1][item_idx]
            quantity = row[1][quantity_idx]
            
            # Retrieve the data from 'quote'
            output = rag_chain.invoke(f"Retrieve the <_id> of the products closest to the following description: {product_name}. Do not look only for an exact match, a closely related match will work just as well. If there are no close matches, simply return <None>.")
            _ids = re.findall(r'\b[0-9][a-z0-9]{22}[a-z0-9]\b', output)
            
            if _ids == []:
                row = pd.DataFrame([[None] * 10], columns=["_id", "product", "image", "brand", "model", "specifications", "price", "HSN", "GST", "remarks"])
            else:
                row = quote[quote['_id'].astype(str) == _ids[0]]
            final_df = pd.concat([final_df, row], join='inner')
    
        final_df.to_excel(writer,
                          sheet_name=name,
                          index=False)
        
        # Inserting images into the Excel file
        worksheet = writer.sheets[name]
        for idx, row in final_df.iterrows():
            if pd.notna(row['image']):
                image = decode_base64(row['image'])
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    image.save(tmp_file.name)
                    tmp_file_path = tmp_file.name

                    # Inserting the image using xlsxwriter
                worksheet.insert_image(f'C{idx + 2}', tmp_file_path)
                
                # Removing the temporary image files
                # os.remove(tmp_file_path)

    # Saving the file
    writer.close()

if __name__ == "__main__":
    main('abc', 'yes', 'no')