import requests
from config import bootstrap_port, bootstrap_ip

def insert_node_to_ring(node_ip, node_port):
    """ 
    This function adds the given node in the ring network by sending a request
    to the bootstrap node.
    """

    bootstrap_url = "http://" + bootstrap_ip + ":" + str(bootstrap_port) + "/node/insert"
    data = {'ip': node_ip, 'port': node_port}
    r = requests.post(bootstrap_url, data)

    return r.json()