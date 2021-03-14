import requests
from config import bootstrap_port, bootstrap_ip
from hashlib import sha1
import json

K_replicas = 5
type1="linearizability"
type2="eventual consistency"
type_replicas=type1

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
