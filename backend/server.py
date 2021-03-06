from flask import Flask, request
import requests
import argparse

bootstrap_ip = '127.0.0.1'
bootstrap_port = 8000

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

@app.route('/node', methods=['POST'])
def insert_node():

    ip = request.form['ip']
    port = request.form['port']

    response = "The node was successfully inserted"
    status = 200

    print(ip, port, "wants to be inserted.")

    return response, status


if __name__ == '__main__':
    
    # This parser object will be used for reading the command line arguments 
    # when running the server. 
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type = str, default="127.0.0.1")
    parser.add_argument('--port', type = int, default=5000)
    parser.add_argument('--is_bootstrap', type = bool, default=False)
    args = parser.parse_args()

    is_bootstrap = args.is_bootstrap

    if (is_bootstrap):
        host = bootstrap_ip
        port = bootstrap_port
    else:
        host = args.host
        port = args.port
        bootstrap_url = "http://" + bootstrap_ip + ":" + str(bootstrap_port) + "/node"
        data = {'ip': host, 'port': port}
        r = requests.post(bootstrap_url, data)
        print(r.text)

    app.run(host=host, port=port)