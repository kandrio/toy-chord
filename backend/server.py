#!/usr/bin/env python3

from flask import Flask, request
from threading import Thread
from node import Node
from ring import Ring
from config import bootstrap_ip, bootstrap_port, K_replicas, type_replicas
from utils import (
    insert_node_to_ring, get_data_from_next_node,
    get_node_hash_id, between, hashing, hexToInt,
    call_update_data, forward_replicas_to_next_node,
    delete_replicas_in_next_nodes
)
import requests
import argparse

app = Flask(__name__)

ring = Ring(bootstrap_ip, bootstrap_port)
node = Node()


@app.route('/insert', methods=['POST'])
def insert():
    """
    This is a route for ALL NODES.

    The client sends POST requests to this route so that new key-value pairs
    are inserted.

    In the case of "eventual consistency", the client gets a response to the
    request after the primary replica of the key-value pair is inserted. The
    other replicas are inserted by a thread, without blocking the response
    to the client.
    """

    # Extract the key and value from the data of the 'insert' request.
    key = request.form['key']
    value = request.form['value']

    # Hash the key of the inserted key-value pair in order to find the node
    # that it's owned by.
    hash_key = hashing(key)

    if between(hash_key, node.my_id, node.prev_id):
        # If we are the node that owns this hask key,
        # we insert the key-value pair in our database.

        node.storage[key] = value
        print(
            "A key-value pair with key:", key,
            "and hash:", hash_key, "was inserted/updated."
        )
        print("Our database now looks like this:", node.storage)

        # If we aren't the only Node in the Ring, we forward the key-value pair
        # to the next node while decreasing the replication factor by 1.
        if (node.next_id != node.my_id):
            if type_replicas == "eventual consistency":
                # In this case, we start a thread that handles the
                # forwarding of the key-value pair to the next nodes

                thread = Thread(
                    target=forward_replicas_to_next_node,
                    args=(key, value, node)
                )

                thread.start()

                # We don't care if the forwarding of the key-value pair has
                # completed. We return a response and a status code to the
                # user.
                message = "The key-value pair was successfully inserted."
                status_code = 200
            elif type_replicas == "linearizability":
                # In this case, we wait until the key-value pair is inserted
                # in the next nodes and then we return a response to the user.
                message, status_code = forward_replicas_to_next_node(
                    key=key,
                    value=value,
                    node=node
                )
            return message, status_code

        return "The key-value pair was successfully inserted.", 200
    else:
        # Otherwise, if we don't own the hash key, we forward the data
        # to the NEXT node. The data will be forwarded by the next nodes
        # until they reach the node that is responsible for the hash key.
        url_next = "http://" + node.next_ip + ":" + \
            str(node.next_port) + "/insert"

        data = {
            'key': key,
            'value': value,
        }

        r = requests.post(url_next, data)
        if r.status_code != 200:
            message = "Error while retransmitting the key-value pair."
            print(message)
            return message, 500

        return r.text


@app.route('/insert/replicas', methods=['POST'])
def replicas_on_insert():
    """
    This is a route for ALL NODES.

    A neighbor node sends POST requests to this route, so that a key-value
    pair replica is inserted in the current NODE.
    """

    # The hash ID of the node with the primary replica
    start_id = request.form['id']
    key = request.form['key']
    value = request.form['value']
    k = int(request.form['k'])

    node.storage[key] = value
    print(
        "The replica with key:", key, "and value:", value,
        "was successfully inserted."
    )

    print("Our database now looks like this:\n", node.storage)

    if (node.next_id == start_id or k == 1):
        return "All replicas have been inserted!", 200

    data_to_next = {
        'id': start_id,
        'key': key,
        'value': value,
        'k': k-1
    }

    url_next = "http://" + node.next_ip + ":" + str(node.next_port) +\
        "/insert/replicas"

    print("Informing the next node to update its replicas.")
    r = requests.post(url_next, data_to_next)
    if r.status_code != 200:
        print("Something went wrong with updating replicas of next node.")

    return r.text


@app.route('/delete', methods=['POST'])
def delete():
    """
    This is a route for ALL NODES. The client sends sequests to this route
    so that a key-value pair is deleted.
    """

    # Extract the key of the 'delete' request.
    key = request.form['key']
    hash_key = hashing(key)

    if between(hash_key, node.my_id, node.prev_id):
        # We are the node that owns that hash key.
        if (key in node.storage):
            # Delete the key-value pair from our database.
            del node.storage[key]

            print("The key:", key, "was deleted from our database.")
            print("The database now looks like this:", node.storage)

            response = "The key-value pair was successfully deleted."
            status = 200

            if (node.next_id != node.my_id):

                if (type_replicas == "eventual consistency"):

                    thread = Thread(
                        delete_replicas_in_next_nodes,
                        (key, node)
                    )

                    thread.start()

                elif type_replicas == "linearizability":

                    response, status = delete_replicas_in_next_nodes(
                        key, node
                    )
        else:
            response = "There isn't such a key-value pair."
            status = 404
    else:
        # We are NOT the node that owns that hash key.
        # So we retransmit the request until we find the
        # node-owner of the key.

        url_next = "http://" + node.next_ip + ":" + \
            str(node.next_port) + "/delete"

        data = {
            'key': key,
        }

        r = requests.post(url_next, data)
        if r.status_code != 200:
            print("Something went wrong with the request to the next node.")

        response = r.text
        status = r.status_code

    return response, status


@app.route('/delete/replicas', methods=['POST'])
def replicas_on_delete():

    start_id = request.form['id']
    key = request.form['key']
    k = int(request.form['k'])

    if (key in node.storage):
        # delete item
        del node.storage[key]
    if (k == 0 or node.next_id == start_id):
        return "Replicas have been deleted!"
    data_to_next = {
        'id' : start_id, 
        'key': key,
        'k' : k-1
    }

    url_next = "http://" + node.next_ip + ":" + \
        str(node.next_port) + "/delete/replicas"

    print("Informing the next neighbor to update it's replicas.")
    r = requests.post(url_next, data_to_next)
    if r.status_code != 200:
        print("Something went wrong with deleting replicas of the next node.")
    return r.text


@app.route('/query', methods=['POST'])
def query():
    """
    This is a route for ALL NODES. The client sends a get request to this route,
    so that the value of a key-value pair is retrieved.
    """
    key = request.form['key']
    hash_key = hashing(key)
    
    if (key=='*'):
        # The user wants to GET all key-value pairs from the database, so we send a
        # request to the BOOTSTRAP server. The BOOTSTRAP server "knows" each node in
        # the ring network.
        url_next = "http://" + bootstrap_ip + ":" + str(bootstrap_port) + "/bootstrap/queryall"
        r = requests.get(url_next)
        return r.text[:-1], 200
    
    if between(hash_key, node.my_id, node.prev_id):
        # If we are the node that owns the hash key.
        if key not in node.storage:
            # The key-value pair doesn't exist in the toy-chord database.
            response = "Sorry, we don't have that song."
            status = 404
            return response, status

    if type_replicas == "linearizability":
        if key not in node.storage:
            url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/query"
            data = {
                'key' : key
            }

            r = requests.post(url_next, data)
            response = r.text
            status = r.status_code
        else:
            data_to_next = {
            'id' : node.my_id, 
            'key': key
            }                
            
            url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/query/replicas"
            print("Submitting the query to the next node.")
            r = requests.post(url_next, data_to_next)
            if r.status_code == 418:
                response = node.storage[key]
                status = 200
            else:
                response = r.text
                status = r.status_code

    elif type_replicas=="eventual consistency": 
        if key not in node.storage:
            url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/query"
            data = {
                'key' : key
            }

            r = requests.post(url_next, data)
            response = r.text
            status = r.status_code
        else:
            response = node.storage[key]
            status = 200
    
    return response, status
    

@app.route('/bootstrap/queryall', methods=['GET'])
def query_all():
    """
    This is a route for the BOOTSTRAP NODE only. 
    Whenever a client requests for ALL the key-value pairs in the database,
    through the "/query/*" route, then the REGULAR node sends a request to this
    route of the bootstrap server.
    """
    
    response = ""
    status = 200

    # Gather all datasets of the nodes in the ring.
    for node in ring.ring:
        ip = node[ 'ip']
        port = node['port']
        url_node = "http://" + ip + ":" + str(port) + "/node/sendalldata"
        r = requests.get(url_node)     
        if r.status_code != 200:
            response = "A problem occurred when trying to all fetch all data."
            status = 404
            break
        response += r.text

    return response, status

@app.route('/query/replicas', methods=['POST'])
def replicas_on_query():
    
    start_id = request.form['id']
    key = request.form['key']

    if key not in node.storage:
        return "No data", 418
    elif start_id==node.my_id:
        return "It's rewind time", 418


    data_to_next = {
        'id' : start_id, 
        'key': key
    }

    url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/query/replicas"
    print("Submitting the query to the next node.")
    r = requests.post(url_next, data_to_next)
    if r.status_code == 418:
        return node.storage[key], 200
    elif r.status_code != 200:
        print("Something went wrong while forwarding the query to the next node.")
    return r.text


@app.route('/node/sendalldata', methods=['GET'])
def send_all_data():
    """
    This is a route for the ALL NODES. Whenever a client requests for ALL the key-value 
    pairs in the database, through the "/query/*" route, then the BOOTSTRAP node sends 
    a request to this route of of every REGULAR node, in order to collect their databases.
    """
    data = "NodeID: "+str(hexToInt(node.my_id))+"\n"
    for key in node.storage:
        data += '<'+key+', '+node.storage[key]+'>'
        data += "\n"
    
    return data, 200


@app.route('/bootstrap/node/join', methods=['POST'])
def join_node():
    """
    This is a route for the BOOTSTRAP NODE only. New nodes will
    make POST requests to this route of the BOOTSTRAP NODE server
    so that they can be inserted in the RING network.
    """
    response = {}

    hash_id = request.form['hash_id']
    ip = request.form['ip']
    port = request.form['port']

    print("Node:", ip + ":" + str(port), "with ID:", hash_id, "wants to be inserted in the RING network.")

    # These will be the links to the PREVIOUS and the NEXT node.
    prev_ip, prev_port, next_ip, next_port = ring.insert(hash_id, ip, port)

    # These data will be sent to the PREVIOUS node, so that it can update
    # its link to the NEXT node now that a new node is inserted.
    data_prev = {
        'prev_or_next': 'prev',
        'ip': ip,
        'port': port
    }

    url_prev = "http://" + prev_ip + ":" + str(prev_port) + "/node/update/link"

    print("About to send an update to the PREVIOUS neighbor of node", hash_id)
    
    r = requests.post(url_prev, data_prev)
    if r.status_code != 200:
        print("Something went wrong with updating the previous node.")
        return response, r.status_code
    else:
        print("The update was successful.")
    

    # This data will be sent to the NEXT node, so that it can update 
    # its link to its PREVIOUS node now that a new node is inserted.
    data_next = {
        'prev_or_next': 'next',
        'ip': ip,
        'port': port
    }
    
    url_next = "http://" + next_ip + ":" + str(next_port) + "/node/update/link"

    print("About to send an update to the NEXT neighbor of node", hash_id)
    r = requests.post(url_next, data_next)
    if r.status_code != 200:
        print("Something went wrong with updating the next node.")
        return response, r.status_code
    else:
        print("The update was successful.")
    
    
    print("Node:", ip + ":" + str(port), "was inserted in the RING network.")
    print("The RING now looks like this:")
    print(ring.ring)    

    response = {'prev_ip': prev_ip, 
                'prev_port': prev_port,
                'next_ip': next_ip,
                'next_port': next_port}

    return response, r.status_code


@app.route('/node/update/link', methods=['POST'])
def update_link():
    """
    This is a route for ALL NODES. When a new node is inserted in
    the RING (via the '/bootstrap/node/join' route), then the neighbors of that
    node must update their links, so that they point at that new node.
    """

    prev_or_next = request.form['prev_or_next']
    if prev_or_next == 'prev':
        print("About to update the link to the NEXT node.")
        node.next_ip = request.form['ip']
        node.next_port = request.form['port']
        node.next_id = get_node_hash_id(node.next_ip, node.next_port)
    elif prev_or_next == 'next':
        print("About to update the link to the PREVIOUS node.")
        node.prev_ip = request.form['ip']
        node.prev_port = request.form['port']
        node.prev_id = get_node_hash_id(node.prev_ip, node.prev_port)
    else:
        print("Something's wrong with prev_or_next value.")
        return "Error", 500

    print("The link was updated.")
    print("The previous node has IP:", node.prev_ip, ", port:", node.prev_port, "and hash ID:", node.prev_id)
    print("The next node has IP:", node.next_ip, ", port:", node.next_port, "and hash ID:", node.next_id)

    return "The link was updated successfully", 200


@app.route('/node/sendyourdata', methods=['GET'])
def send_your_data():
    """
    This is a route for ALL NODES. When a new node is inserted in
    the RING (via the '/bootstrap/node/join' route), then the NEXT neighbor of that
    newly inserted node must send part of its database to that new node.

    The data that will be sent are owned by the new node, because they belong to 
    its keyspace.
    """

    print("The newly inserted PREVIOUS node requested its data...")

    data={}

    for key in node.storage:
        hash_key = hashing(key)
        if(hash_key <= node.prev_id):
            data[key] = node.storage[key]
    
    print("The data that are now owned by the previous node are: ", data)



    print("Our updated database now is:", node.storage)

    return data, 200


@app.route('/node/depart', methods=['POST'])
def depart_node():
    """
    This is a route for ALL NODES. 
    Whenever a client asks for a node to depart, it sends a post request
    to this route.
    """

    # The node is about to depart gracefully.
    print("We are about to depart gracefully...")
    
    # We inform our neighbors to update their links.
    data_prev = {
        'prev_or_next': 'prev',
        'ip': node.next_ip,
        'port': node.next_port
    }

    url_prev = "http://" + node.prev_ip + ":" + str(node.prev_port) + "/node/update/link"

    print("About to send a link update to the PREVIOUS node.")
    
    r = requests.post(url_prev, data_prev)

    if r.status_code != 200:
        print("Something went wrong with updating the previous node.")
        return "Something went wrong", r.status_code
    else:
        print("The update of the previous node was successful.")
    

    # This data will be sent to the NEXT node, so that it can update 
    # its link to its PREVIOUS node now that a new node is inserted.
    data_next = {
        'prev_or_next': 'next',
        'ip': node.prev_ip,
        'port': node.prev_port
    }
    
    url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/node/update/link"

    print("About to send a link update to the NEXT node.")

    r = requests.post(url_next, data_next)

    if r.status_code != 200:
        print("Something went wrong with updating the next node.")
        return "Something went wrong", r.status_code
    else:
        print("The update of the next node was successful.")

    # We send all of our database to the next node, before we depart gracefully.   

    print("About to move our entire database to the next node.")
    if type_replicas=="linearizability":
        url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/node/update/data/depart"
        data=node.storage
        data['start_id'] = node.next_id
        r = requests.post(url_next, data)

        if r.status_code != 200:
            print("Something went wrong with moving our data to the next node.")
            return "Something went wrong", r.status_code
        else:
            print("The update of the database of the next node was successful.")

    print("About to be removed from the ring")

    url_bootstrap = "http://" + bootstrap_ip + ":" + str(bootstrap_port) + "/bootstrap/update/ring"

    data = {
        'ip': node.my_ip,
        'port': node.my_port
    }

    r = requests.post(url_bootstrap, data)   

    if r.status_code != 200:
        print("Something went wrong with getting removed from the ring.")
        return "Something went wrong", r.status_code
    else:
        print("We were successfully removed from the ring.") 

    return r.text, 200


@app.route('/node/update/data/depart', methods=['POST'])
def update_node_data_depart():
    """
    This is a route for ALL NODES. 
    Whenever the PREVIOUS NODE departs from the ring, 
    all of its data are transfered to us through this route.
    """
    start_id = request.form['start_id']
    prev_storage = {}
    for key in request.form:
        prev_storage[key] = request.form[key]
    del prev_storage['start_id']
    print("Some new data have arrived:", type(prev_storage))
    to_be_deleted = []
    for key in prev_storage:
        if key not in node.storage:
            node.storage[key] = prev_storage[key]
            to_be_deleted.append(key)
    for key in to_be_deleted:
        del prev_storage[key]

    print("Our database now looks like this:", node.storage)

    if not prev_storage or  node.next_id == start_id:
        return "The database was successfully updated.", 200
    
    url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/node/update/data/depart"
    data_to_next= prev_storage
    data_to_next['start_id']=start_id
    r = requests.post(url_next, data_to_next)

    if r.status_code != 200:
        print("Something went wrong with moving our data to the next node.")
        return "Something went wrong", r.status_code
    else:
        return r.text




@app.route('/node/update/data/join', methods=['POST'])
def update_node_data_join():
    """
    This is a route for ALL NODES. 
    Whenever the PREVIOUS NODE departs from the ring, 
    all of its data are transfered to us through this route.
    """
    start_id = request.form['start_id']
    k = int(request.form['k'])
    prev_storage = {}
    to_be_deleted={}
    for key in request.form:
        if key == 'k' or key == 'start_id':
            continue
        if key not in node.storage:
            to_be_deleted[key]=0
        else:
            prev_storage[key] = request.form[key]

    if node.next_id == start_id:
        if k > 0:
            return "Get the rest keys.", 418
        else:
            for key in prev_storage:
                del node.storage[key]
            prev_storage = {}
    
    if (to_be_deleted):
        url_prev = "http://" + node.prev_ip + ":" + str(node.prev_port) + "/node/deleteyourdata"
        r = requests.post(url_prev, to_be_deleted)

    if not prev_storage:
        return "The database was successfully updated.", 200

    prev_storage['start_id'] = start_id
    prev_storage['k'] = k - 1    
    url_next = "http://" + node.next_ip + ":" + str(node.next_port) + "/node/update/data/join"
    r = requests.post(url_next, prev_storage)

    if r.status_code != 200:
        print("Something went wrong with moving our data to the next node.")
        return "Something went wrong", r.status_code
    else:
        return r.text

@app.route('/node/join/sendalldata', methods=['GET'])
def send_all_replicas():
    return node.storage, 200

@app.route('/node/deleteyourdata', methods=['POST'])
def delete_your_data():
 
    for key in request.form:
        if key in node.storage:
            del  node.storage[key]
        else:
            print("this key", key, " wasn't here")
            return "Error!", 404
    return "Keys were successfully deleted!", 200




@app.route('/bootstrap/update/ring', methods=['POST'])
def update_ring():
    """
    This is a route for the BOOTSTRAP node only. 
    Whenever a NODE wants to depart from the ring, the bootstrap node removes it from
    the Ring() structure.
    """

    ip = request.form['ip']
    port = request.form['port']

    print("About to remove node:", ip + ":" + str(port), "from the ring.")
    
    hash_id = get_node_hash_id(ip, port)

    for node in ring.ring:
        if (node['hash_id'] == hash_id and node['ip'] == ip and node['port'] == port):
            ring.ring.remove(node)
            break
    
    print("The node was successfully removed.")
    print("The ring now looks like this:", ring.ring)

    return "The node has departed successfully", 200


@app.route('/overlay', methods=['GET'])
def overlay():
    ans=""
    for dic in ring.ring:
        ans+="Node with ip: " + dic['ip'] + ", port: " + str(dic['port']) + " and id: " +  str(hexToInt(dic['hash_id'])) + '\n'
    return ans




if __name__ == '__main__':
    
    # This parser object will be used to read the command line arguments 
    # when running the server. 
    parser = argparse.ArgumentParser()

    # Whenever a server-node is running, we need to know 3 things:
    # its host IP, its port and whether it is a bootstrap node or not. 
    parser.add_argument('--host', type = str, default="127.0.0.1")
    parser.add_argument('--port', type = int, default=5000)
    parser.add_argument('--is_bootstrap', action='store_true')

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
        print("Our hash ID is:", node.my_id)
        node.prev_id = node.my_id
        node.next_id = node.my_id
        print("Number of replicas:", K_replicas)
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
        print("Our hash ID is:", node.my_id)
        
        # Before this regular node-server can run, it must be inserted in the ring network.
        print("About to get inserted to the ring...")
        
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

        print("We were successfully inserted to the ring network.")
        print("The previous node has IP:", node.prev_ip, ", port:", node.prev_port, "and hash:", node.prev_id)
        print("The next node has IP:", node.next_ip, ", port:", node.next_port, "and hash:", node.next_id)

        print("About to ask the next node for our data...")
        
        response = get_data_from_next_node(
            node_ip=node.next_ip, 
            node_port=node.next_port
        )

        for key in response:
            node.storage[key]=response[key]
        
        res = call_update_data (
            data= response,
            my_id= node.my_id,
            next_ip=node.next_ip, 
            next_port=node.next_port   
        )

        if res[1] == 418:
            print("Got status code 418, should ask my neighbour for all his keys")
            next_node_url = "http://" + node.next_ip + ":" + str(node.next_port) + "/node/join/sendalldata"  
            r = requests.get(next_node_url)
            response = r.json()
            for key in response:
                node.storage[key]=response[key]    
        
        print("The data was successfully transfered, here is our database:")
        print(node.storage)

    app.run(host=host, port=port)
