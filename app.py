import base64
from flask import Flask,request,render_template
from flask_cors import CORS,cross_origin
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://himanshugulechha:123456seven@autoquote.vz1lawt.mongodb.net/?retryWrites=true&w=majority&appName=AutoQuote"

# Creating a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Sending a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__,template_folder='templates')
CORS(app,support_credentials=True)  
# Set up MongoDB connection
db = client['sampleInventory']

@app.route('/add_inventory',methods=['POST'])
@cross_origin(supports_credentials=True)
def save_product():
    data=request.form.to_dict()
    collection=db['inventory']
    collection.insert_one(data)
    return "data saved"

@app.route("/add_inventory",methods=['GET'])
@cross_origin(supports_credentials=True)
def add_product():
    return render_template('inventory.html')

@app.route('/view_inventory',methods=['GET'])
@cross_origin(supports_credentials=True)
def view_data():
    collection=db['inventory']
    books=collection.find()
    # for book in books:
    #     if 'image' in book:
    #         book['image'] = base64.b64decode(book['image'])
    # print(book['image'])
    return render_template('inventoryview.html',books=books)

@app.route('/edit_inventory/<model>', methods=['POST', 'GET'])
@cross_origin(supports_credentials=True)
def edit_inventory(model):
    collection=db['inventory']
    item = collection.find_one({'model': model})
    if request.method == 'GET':
        return render_template('edit_inventory.html',mybooks=item)
    collection.update_one({"model": model},
                  { "$set": {
                             "category": request.form.get('category'),
                              "brand": request.form.get('brand'),
                              "name": request.form.get('name'),
                              "specifications": request.form.get('specifications'),
                              "remarks": request.form.get('remarks'),
                              "price": request.form.get('price'),
                              "hotel": request.form.get('hotel'),
                              "image": request.form.get('image')
                             }
                 })

    return 'Updated, success'

@app.route("/",methods=['GET'])
@cross_origin(supports_credentials=True)
def home_page():
    return render_template('homepage.html')

if __name__ == '__main__':
    app.run(debug=True)