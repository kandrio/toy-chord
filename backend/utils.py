import requests
from config import bootstrap_port, bootstrap_ip
from hashlib import sha1

def insert_node_to_ring(hash_id: str, node_ip:str , node_port:int):
    """ 
    This function adds a given node to the ring network by sending a request
    to the bootstrap node.
    """
    print("We are in insert_node_to_ring()")

    bootstrap_url = "http://" + bootstrap_ip + ":" + str(bootstrap_port) + "/node/join"
    data = {'hash_id': hash_id, 'ip': node_ip, 'port': node_port}
    r = requests.post(bootstrap_url, data)

    return r.json()

def get_node_hash_id(node_ip: str, node_port: int):
    name = node_ip + str(node_port)
    bytes_name = name.encode('utf-8')
    return sha1(bytes_name).hexdigest()
