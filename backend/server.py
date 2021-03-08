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
        if ( key in node.storage):
            # delete item
            del node.storage[key]
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

@app.route('/query/<key>', methods=['GET'])
def query(key):

    hashKey = hashing(key)
    if (key=='*'):
        url_next = "http://" + bootstrap_ip + ":" + str(bootstrap_port) + "/sendall"
        r = requests.get(url_next)
        return r.text
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
        url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/query/" + key
        r = requests.get(url_next)
        if r.status_code != 200:
            response="A problem occurred. "
            status= 404
            return response, status
        return r.text
    
@app.route('/sendall', methods=['GET'])
def sendall():
    ans=""
    for cnt_node in ring.ring:
        ip=cnt_node[ 'ip']
        port=cnt_node['port']
        url_next = "http://" + ip + ":" + str(port) + "/senddata"
        r = requests.get(url_next)
        ans+= r.text 

    if r.status_code != 200:
            response="A problem occurred. "
            status= 404
            return response, status
    return ans

@app.route('/senddata', methods=['GET'])
def senddata():
    data=""
    for dat in node.storage:
        data+=node.storage[dat]
        data+= "\n"
    return data

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




@app.route('/node/depart', methods=['POST'])
def depart_node():
    """
    This is a route for the BOOTSTRAP NODE only. New nodes will
    make POST requests to this route of the BOOTSTRAP NODE server
    so that they can be inserted in the RING network.
    """
    ip = request.form['ip']
    port = request.form['port']

    print("Node:", ip + ":" + str(port), "wants to depart from the RING network.")
    url_prev = "http://" + ip + ":" + str(port) + "/node/depart/update"
    # These will be the links to the PREVIOUS and the NEXT node.
    print("The node has to inform it's neighbors.")
    # !!!               
    r = requests.get(url_next)
    if r.status_code != 200:
        print("Something went wrong with updating the next node.")
        return "Error!"

    return r.text
    



@app.route('/node/depart/update', methods=['GET'])
def update_node_after_depart():
    # These data will be sent to the PREVIOUS node, so that it can update
    # its link to the NEXT node now that a new node is inserted.
    data_to_prev = {
        'prev_or_next': 'prev',
        'ip': node.next_ip,
        'port': node.next_port,
        'id': node.next_id,
        'data': node.storage
    }

    # This data will be sent to the NEXT node, so that it can update 
    # its link to its PREVIOUS node now that a new node is inserted.
    data_to_next = {
        'prev_or_next': 'next',
        'ip': node.prev_ip,
        'port': node.prev_port,
        'id' : node.prev_id, 
        'data': node.storage
    }

    url_prev = "http://" + node.prev_ip + ":" + str(node.prev_port) + "/node/update/neighbor"
    print("About to send an update to the previous neighbor of the departed node.")
    r = requests.post(url_prev, data_to_prev)
    if r.status_code != 200:
        print("Something went wrong with updating the previous node.")
    
    url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/node/update/neighbor"
    print("About to send an update to the next neighbor of the departed node.")
    r = requests.post(url_next, data_to_next)
    if r.status_code != 200:
        print("Something went wrong with updating the next node.")
    
    data= {
        'ip': node.my_ip,
        'port': node.my_port
    }
    url_next = "http://" + bootstrap_ip + ":" + str(bootstrap_port) + "/node/depart/final"
    r = requests.post(url_next,data)
    if r.status_code != 200:
        print("Something went wrong while asking bootstrap to delete you.")
        return ("Error!")
    return r.text    




@app.route('/node/update/neighbor', methods=['POST'])
def update_neighbor():
    """
    This is a route for ALL NODES. When a new node is inserted in
    the RING (via the '/node/join' route), then the neighbors of that
    node must update their links, so that they point at that new node.
    """
    print("About to update neighbor's links and storage.")
    
    data_to_next = {
        'prev_or_next': 'next',
        'ip': node.prev_ip,
        'port': node.prev_port,
        'id' : node.prev_id, 
        'data': node.storage
    }


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
    
    data = request.form['data']
    for dat in data:
        node.storage[dat]=data[dat]
    
    return "Neighbor is updated", 200


@app.route('/node/depart/final', methods=['POST'])
def finally_depart_node():
    """
    This is a route for ALL NODES. When a new node is inserted in
    the RING (via the '/node/join' route), then the neighbors of that
    node must update their links, so that they point at that new node.
    """
    print("About to depart the node.")
    ip = request.form['ip']
    port = request.form['port']
    id=get_node_hash_id(ip, port)
    # to be written search based on id and delete
    dict_to_insert = {'hash_id': hash_id, 'ip': ip, 'port':port}
    for dic in ring.ring:
        if (dic['hash_id']==id and dic['ip']==ip and dic['port']==port):
            ring.ring.remove(dic)

    return "Node has departed successfully", 200








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