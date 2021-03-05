from flask import Flask, request

app = Flask(__name__)

database = {}

@app.route('/insert', methods=['POST'])
def insert():
    key = request.form['key']
    value = request.form['value']
    database[key] = value
    print(database)
    
    return 'The key-value pair was successfully inserted'