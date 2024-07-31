from df_to_excel import main
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS, cross_origin
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://himanshugulechha:123456seven@autoquote.vz1lawt.mongodb.net/?retryWrites=true&w=majority&appName=AutoQuote"

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__, template_folder='templates')
CORS(app, support_credentials=True)

db = client['sampleInventory']

@app.route('/add_inventory', methods=['POST'])
@cross_origin(support_credentials=True)
def save_product():
    data = request.form.to_dict()
    collection = db['inventory']
    collection.insert_one(data)
    return "data saved"

@app.route('/add_inventory', methods=['GET'])
@cross_origin(support_credentials=True)
def add_product():
    return render_template('inventory.html')

@app.route('/view_inventory', methods=['GET'])
@cross_origin(support_credentials=True)
def view_data():
    collection = db['inventory']
    books = collection.find()
    return render_template('inventoryview.html', books=books)

@app.route('/edit_inventory/<model>', methods=['POST', 'GET'])
@cross_origin(support_credentials=True)
def edit_inventory(model):
    collection = db['inventory']
    item = collection.find_one({'model': model})
    if request.method == 'GET':
        return render_template('edit_inventory.html', mybooks=item)
    collection.update_one({"model": model},
                          {"$set": {
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

@app.route('/generate', methods=['POST'])
def generate():
    file = request.files['file'].filename
    gst = request.form.get('gst')
    hsn = request.form.get('hsn')
    main(file, gst, hsn)
    print("File generated successfully!")
    return jsonify({"message": "Quotation generated successfully!"})

@app.route("/", methods=['GET', 'POST'])
@cross_origin(support_credentials=True)
def home_page():
    if request.method == 'POST':
        data = request.form.to_dict()
        collection = db['inventory']
        collection.insert_one(data)
        return jsonify({"message": "Data received successfully"}), 200
    return render_template('homepage.html')

if __name__ == '__main__':
    app.run(debug=True)