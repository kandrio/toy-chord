import requests
from config import bootstrap_ip, bootstrap_port, K_replicas
from hashlib import sha1

def insert_node_to_ring(hash_id: str, node_ip: str, node_port: int):
    """ 
    This function adds a given node to the ring network by sending a request
    to the BOOTSTRAP NODE.
    """
    bootstrap_url = "http://" + bootstrap_ip + ":" + str(bootstrap_port) + "/bootstrap/node/join"
    data = {'hash_id': hash_id, 'ip': node_ip, 'port': node_port}

    print("Sending request to the BOOTSTRAP server, in URL:", bootstrap_url)
    
    r  = requests.post(bootstrap_url, data)
    
    return r.json()

def get_data_from_next_node(node_ip: str , node_port: int):
    
    next_node_url = "http://" + node_ip + ":" + str(node_port) + "/node/sendyourdata"
    
    print("Sending request to the NEXT node, in URL:", next_node_url)    

    r = requests.get(next_node_url)

    return r.json()

def call_update_data(data, my_id, next_ip, next_port):
	data['start_id'] = my_id
	data['k'] = K_replicas-1
	url_next = "http://" + next_ip + ":" + str(next_port) + "/node/update/data/join"
	r = requests.post(url_next, data)
	if r.status_code == 418:
		return r.text, r.status_code
	if r.status_code != 200:
		print("Something went wrong with moving our data to the next node.")
		return "Something went wrong", r.status_code
	else:
		return r.text, 200

def get_node_hash_id(node_ip: str, node_port: int):
    name = node_ip + str(node_port)
    bytes_name = name.encode('utf-8')
    return sha1(bytes_name).hexdigest()

def hashing(value):
    return sha1(value.encode('utf-8')).hexdigest()

def hexToInt(hexVal):
    return int(hexVal,16)
    
def between(song_hash, curr_node_hash, prev_node_hash):
    if (curr_node_hash > prev_node_hash):
        return (song_hash <= curr_node_hash and song_hash > prev_node_hash)  
    elif (curr_node_hash < prev_node_hash):
        return (song_hash <= curr_node_hash or song_hash > prev_node_hash)
    return True

def forward_replicas_to_next_node(key, value, node):

    data = {
        'id': node.my_id,
        'key': key,
        'value': value,
        'k': K_replicas-1
    }

    url_next = "http://" + node.next_ip + ":" \
        + str(node.next_port) + "/insert/replicas"

    r = requests.post(url_next, data)

    if r.status_code != 200:
        message = "Error while retransmitting the key-value pair:\
            with key:" + key + "and value:" + value
    else:
        message = "The key-value pair was successfully inserted."

    return message, r.status_code

def delete_replicas_in_next_nodes(key, node):

    data = {
        'id': node.my_id,
        'key': key,
        'k': K_replicas-1
    }

    url_next = "http://" + node.next_ip + ":" + \
        str(node.next_port) + "/delete/replicas"

    r = requests.post(url_next, data)

    if r.status_code != 200:
        response = "Something went wrong with retransmitting the 'delete replicas'\
            request to the next nodes."
    else:
        response = "The key-value pair was successfully deleted."

    print(response)

    return response, r.status_code
