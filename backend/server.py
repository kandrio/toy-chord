from flask import Flask, request
from node import Node
from ring import Ring
from config import bootstrap_ip, bootstrap_port
from utils import insert_node_to_ring
import requests
import argparse

app = Flask(__name__)

database = {}

ring = Ring(bootstrap_ip, bootstrap_port)
node = Node()

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
    prev_ip, prev_port = ring.insert(ip, port)

    response = {'prev_ip': prev_ip, 
                'prev_port': prev_port,
                'next_ip': bootstrap_ip,
                'next_port': bootstrap_port}

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

    # This is set by the user with: "--bootstrap True" when running the "server.py". 
    # Otherwise, it defaults to False.
    is_bootstrap = args.is_bootstrap

    if (is_bootstrap):
        host = bootstrap_ip
        port = bootstrap_port
    else:
        host = args.host
        port = args.port

        resp = insert_node_to_ring(node_ip=host, node_port=port)
        print(resp)

    app.run(host=host, port=port)