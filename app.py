import os

import pandas as pd
from df_to_excel import main
from flask import Flask, redirect, request, render_template, jsonify, url_for
from flask_cors import CORS, cross_origin
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import send_file
from mongo import push_to_db

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
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

@app.route('/bulk_inventory', methods=['GET'])
@cross_origin(support_credentials=True)
def bulk_product():
    return render_template('bulkinventory.html')

@app.route('/bulk_add', methods=['GET', 'POST'])
@cross_origin(support_credentials=True)
def bulk_add():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        response = push_to_db("C:\\Users\\purus\\Documents\\GitHub\\AutoQuote\\data\\" + file.filename)
        if response == 200:
            return jsonify({'message': 'File processed and data added to MongoDB'}), 200
        else:
            return jsonify({'message': 'Data was not added to the database'}), 400
    return jsonify({'error': 'Unknown error occurred'}), 500

@app.route('/add_discount', methods=['GET'])
@cross_origin(support_credentials=True)
def add_discount():
    return render_template('discount.html')

@app.route('/get_column', methods=['POST'])
@cross_origin(support_credentials=True)
def get_column():
    file = request.files['file']
    df = pd.read_excel(file)
    if 'brand' in df.columns:
        column_data = list(set(df['brand'].dropna().values))
    else:
        return jsonify({'error': 'Brand column not found'}), 400
    return jsonify({'column_data': column_data})

@app.route('/submit_discounts', methods=['POST'])
@cross_origin(support_credentials=True)
def submit_discounts():
    data = request.form
    return jsonify({'status': 'success', 'message': 'Discounts submitted successfully!'})

@app.route('/BOQ_history', methods=['GET'])
@cross_origin(support_credentials=True)
def add_history():
    return render_template('history.html')

@app.route('/view_inventory', methods=['GET', 'POST'])
@cross_origin(support_credentials=True)
def view_data():
    collection = db['inventory']
    books = list(collection.find().limit(10))
    for book in books:
        book['image'] = str(book['image'])[2:-1]
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
                              "product": request.form.get('product'),
                              "specifications": request.form.get('specifications'),
                              "remarks": request.form.get('remarks'),
                              "price": request.form.get('price'),
                              "GST": request.form.get('GST'),
                              "HSN": request.form.get('HSN'),
                              "image": request.form.get('image')
                          }
                          })
    return redirect(url_for('view_data'))

@app.route('/generate', methods=['POST'])
def generate():
    file = request.files['file'].filename
    gst = request.form.get('gst')
    hsn = request.form.get('hsn')
    reasonable = request.form.get('reasonable')
    moderate = request.form.get('moderate')
    luxury = request.form.get('luxury')
    options = request.form.get('options')
    output_file = main(file, gst, hsn, options, [reasonable, moderate, luxury])
    print("File generated successfully!")
    return send_file(output_file, as_attachment=True)

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
    app.run(debug=False)