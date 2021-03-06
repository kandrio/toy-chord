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

@app.route('/node/insert', methods=['POST'])
def insert_node():
    """
    This is a route for the BOOTSTRAP NODE only. New nodes will
    make POST requests to this route of the BOOTSTRAP NODE server
    so that they can be inserted in the RING network.
    """
    ip = request.form['ip']
    port = request.form['port']
    prev_ip, prev_port = ring.insert(ip, port)
    next_ip = bootstrap_ip
    next_port = bootstrap_port

    response = {'prev_ip': prev_ip, 
                'prev_port': prev_port,
                'next_ip': bootstrap_ip,
                'next_port': bootstrap_port}

    status = 200

    data_prev = {
        'prev_or_next': 'prev',
        'ip': ip,
        'port': port
    }

    data_next = {
        'prev_or_next': 'next',
        'ip': ip,
        'port': port
    }

    print("Node:", ip + ":" + str(port), "wants to be inserted in the RING network.")

    url_prev = "http://" + prev_ip + ":" + str(prev_port) + "/node/update"
    print("About to update the previous neighbor.")
    r = requests.post(url_prev, data_prev)

    if r.status_code != 200:
        print("Something went wrong with updating the previous node.")
    
    url_next = "http://" + next_ip + ":" + str(next_port) + "/node/update"
    
    r = requests.post(url_next, data_next)

    if r.status_code != 200:
        print("Something went wrong with updating the next node.")

    print("Node:", ip + ":" + str(port), "was inserted in the RING network.")

    return response, status

@app.route('/node/update', methods=['POST'])
def update_node():
    """
    This is a route for ALL NODES. When a new node is inserted in
    the RING (via the '/node/insert' route), then the neighbors of that
    node must update their links, so that they point at that new node.
    """
    print("About to update the links to the neighbors.")

    prev_or_next = request.form['prev_or_next']
    if prev_or_next == 'prev':
        node.next_ip = request.form['ip']
        node.next_port = request.form['port']
    elif prev_or_next == 'next':
        node.prev_ip = request.form['ip']
        node.prev_port = request.form['port']
    else:
        print("Something's wrong with prev_or_next")
        return "Error", 500

    print("The previous node now has IP:", node.prev_ip, "and port:", node.prev_port)
    print("The next node now has IP:", node.next_ip, "and port:", node.next_port)

    return "Link update OK", 200

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

        node = Node(
            prev_ip=bootstrap_ip, 
            prev_port=bootstrap_port, 
            next_ip=bootstrap_ip, 
            next_port=bootstrap_port
        )

        print("--------------")
        print("BOOTSTRAP NODE")
        print("--------------")
    else:
        host = args.host
        port = args.port

        response = insert_node_to_ring(node_ip=host, node_port=port)
        
        node = Node(
            prev_ip=response['prev_ip'], 
            prev_port=response['prev_port'], 
            next_ip=response['next_ip'], 
            next_port=response['next_port']
        )

        print("The node was successfully inserted to the ring network.")
        print("The previous node has IP:", node.prev_ip, "and port:", node.prev_port)
        print("The next node has IP:", node.next_ip, "and port:", node.next_port)

    app.run(host=host, port=port)