from flask import Flask, request
from node import Node
from ring import Ring
from config import bootstrap_ip, bootstrap_port
from utils import insert_node_to_ring, get_node_hash_id, between, hashing
import requests
import argparse

app = Flask(__name__)


ring = Ring(bootstrap_ip, bootstrap_port)
node = Node()

@app.route('/insert', methods=['POST'])
def insert():
    # Extract the key and value from the data of the 'insert' request.
    key = request.form['key']
    value = request.form['value']

    # hashing the key in order to find it's position into the ring
    hashKey = hashing(key)
    data= {
        'key': key,
        'value': value,
    }
    # if you are the responsible node for this id, insert it in your "database"
    if (between(hashKey,node.my_id,node.next_id)):
        node.storage[key]=value
        return 'The key-value pair was successfully inserted.'
    else:
        # otherwise send the data to your successor
        url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/insert"
        r = requests.post(url_next, data)
        if r.status_code != 200:
            print("Something went wrong.")
            return "Error, 404"
        return r.text
    

@app.route('/delete', methods=['POST'])
def delete():

    # Extract the key of the 'delete' request.
    key = request.form['key']
    hashKey = hashing(key)
    data= {
        'key': key,
    }
    
    # if you are the responsible node for this id
    if (between(hashKey,node.my_id,node.next_id)):
        print("before", node.my_port, node.storage)
        if ( key in node.storage):
            # delete item
            del node.storage[key]
            print("after: ", node.storage)
            return(" The key-value pair was successfully deleted.")
        else:
            # item doesn't exist
            return ("There isn't value with such a key.")
    else:
        # otherwise, inform your successor for deleting item    
        url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/delete"
        r = requests.post(url_next, data)
        if r.status_code != 200:
            print("Something went wrong.")
            return "Error, 404"
        return r.text

@app.route('/query', methods=['POST'])
def query():


    key = request.form['key']
    hashKey = hashing(key)
    data= {
        'key': key,
    }

    if key == "*":
        response = database
        status = 200
        return response, status

    # if you are the responsible node for this id
    if (between(hashKey,node.my_id,node.next_id)):
        # item not found
        if key not in node.storage:
            response = "Sorry, we don't have that song."
            status = 404
        # here is your item
        else:
            response=node.storage[key]
            status = 200
        return response, status
    else:
        # otherwise, inform your successor for querying item
        url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/query"
        r = requests.post(url_next, data)
        if r.status_code != 200:
            print("Something went wrong.")
            response="A problem occurred. "
            status= "404"
            return response + status
        return ""
    

@app.route('/node/join', methods=['POST'])
def join_node():
    """
    This is a route for the BOOTSTRAP NODE only. New nodes will
    make POST requests to this route of the BOOTSTRAP NODE server
    so that they can be inserted in the RING network.
    """

    hash_id = request.form['hash_id']
    ip = request.form['ip']
    port = request.form['port']

    # These will be the links to the PREVIOUS and the NEXT node.
    prev_ip, prev_port, next_ip, next_port = ring.insert(hash_id, ip, port)

    status = 200

    # These data will be sent to the PREVIOUS node, so that it can update
    # its link to the NEXT node now that a new node is inserted.
    data_prev = {
        'prev_or_next': 'prev',
        'ip': ip,
        'port': port
    }

    # This data will be sent to the NEXT node, so that it can update 
    # its link to its PREVIOUS node now that a new node is inserted.
    data_next = {
        'prev_or_next': 'next',
        'ip': ip,
        'port': port
    }

    print("Node:", ip + ":" + str(port), "wants to be inserted in the RING network.")
    
    url_prev = "http://" + prev_ip + ":" + str(prev_port) + "/node/update"
    print("About to send an update to the previous neighbor of the newly inserted node.")
    r = requests.post(url_prev, data_prev)
    if r.status_code != 200:
        print("Something went wrong with updating the previous node.")
    
    url_next = "http://" + next_ip + ":" + str(next_port) + "/node/update"
    print("About to send an update to the next neighbor of the newly inserted node.")
    r = requests.post(url_next, data_next)
    if r.status_code != 200:
        print("Something went wrong with updating the next node.")

    print("Node:", ip + ":" + str(port), "was inserted in the RING network.")

    print("The RING looks like this:")
    print(ring.ring)

    response = {'prev_ip': prev_ip, 
                'prev_port': prev_port,
                'next_ip': next_ip,
                'next_port': next_port}

    return response, status

@app.route('/node/update', methods=['POST'])
def update_node():
    """
    This is a route for ALL NODES. When a new node is inserted in
    the RING (via the '/node/join' route), then the neighbors of that
    node must update their links, so that they point at that new node.
    """
    print("About to update the links to the neighbors.")

    prev_or_next = request.form['prev_or_next']
    if prev_or_next == 'prev':
        node.next_ip = request.form['ip']
        node.next_port = request.form['port']
        node.next_id = get_node_hash_id(node.next_ip, node.next_port)
    elif prev_or_next == 'next':
        node.prev_ip = request.form['ip']
        node.prev_port = request.form['port']
        node.prev_id = get_node_hash_id(node.prev_ip, node.prev_port)
    else:
        print("Something's wrong with prev_or_next")
        return "Error", 500

    print("The previous node now has IP:", node.prev_ip, ", port:", node.prev_port, "and hash ID:", node.prev_id)
    print("The next node now has IP:", node.next_ip, ", port:", node.next_port, "and hash ID:", node.next_id)

    return "Link update OK", 200
  

if __name__ == '__main__':
    
    # This parser object will be used to read the command line arguments 
    # when running the server. 
    parser = argparse.ArgumentParser()

    # Whenever a server-node is running, we need to know 3 things:
    # its host IP, its port and whether it is a bootstrap node or not. 
    parser.add_argument('--host', type = str, default="127.0.0.1")
    parser.add_argument('--port', type = int, default=5000)
    parser.add_argument('--is_bootstrap', type = bool, default=False)

    args = parser.parse_args()

    # This can be set by the user by adding the argument: '--bootstrap True' 
    # when running the "server.py". Otherwise, it defaults to False.
    is_bootstrap = args.is_bootstrap

    if (is_bootstrap):

        # In this case, the BOOTSTRAP node is running.
        print("--------------")
        print("BOOTSTRAP NODE")
        print("--------------")

        host = bootstrap_ip
        port = bootstrap_port

        # The bootstrap node is the first to be inserted in the ring, so
        # it is the ONLY NODE in the ring.
        node = Node(
            my_ip=bootstrap_ip,
            my_port=bootstrap_port,
            prev_ip=bootstrap_ip, 
            prev_port=bootstrap_port, 
            next_ip=bootstrap_ip, 
            next_port=bootstrap_port
        )

        node.my_id = get_node_hash_id(bootstrap_ip, bootstrap_port)
        node.prev_id = node.my_id
        node.next_id = node.my_id

    else:
        # In this case, a regular node is running.
        print("------------")
        print("REGULAR NODE")
        print("------------")
        host = args.host
        port = args.port

        node = Node(
            my_ip=host,
            my_port=port,
        )

        node.my_id = get_node_hash_id(host, port)
        
        # Before this regular node-server can run, it must be inserted in the ring network.
        response = insert_node_to_ring( 
            hash_id = node.my_id,
            node_ip = host, 
            node_port = port
        )
        
        node.prev_ip = response['prev_ip']
        node.prev_port = response['prev_port'] 
        node.prev_id = get_node_hash_id(node.prev_ip, node.prev_port)

        node.next_ip = response['next_ip']
        node.next_port = response['next_port']
        node.next_id = get_node_hash_id(node.next_ip, node.next_port)

        print("The node was successfully inserted to the ring network.")
        print("The previous node has IP:", node.prev_ip, ", port:", node.prev_port, "and hash:", node.prev_id)
        print("The next node has IP:", node.next_ip, ", port:", node.next_port, "and hash:", node.next_id)

    app.run(host=host, port=port)