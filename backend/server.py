from flask import Flask, request

app = Flask(__name__)

database = {}

@app.route('/insert', methods=['POST'])
def insert():
    # Extract the key and value from the data of the 'insert' request.
    key = request.form['key']
    value = request.form['value']

    # Insert it in the "database".
    database[key] = value
    
    # Confirm that the database is indeed updated.
    print(database)
    
    return 'The key-value pair was successfully inserted.'

@app.route('/delete', methods=['POST'])
def delete():

    # Extract the key of the 'delete' request.
    key = request.form['key']

    if (key in database):
        del database[key]
        response = "The key : '" + key + "' was successfully deleted." 
        status = 200
    else:
        response = "The key: '" + key + "' doesn't exist." 
        status = 404

    print(database)

    return response, status

@app.route('/query/<key>', methods=['GET'])
def query(key):

    if key == "*":
        response = database
        status = 200
    else:
        if key not in database:
            response = "Sorry, we don't have that song."
            status = 404
        else:
            response = database[key]
            status = 200
    
    return response, status
    