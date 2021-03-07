from config import bootstrap_ip, bootstrap_port
from utils import get_node_hash_id

class Ring():
    def __init__(self, bootstrap_ip: str, bootstrap_port: int):
        """
        This class will be used by the BOOTSTRAP NODE to keep track
        of the nodes that are in the ring network.
        """

        # A Ring() object is always initialized by the BOOTSTRAP NODE.
        # So, the BOOTSTRAP NODE will be the only node in the ring network
        # at that time. 
        hash_id = get_node_hash_id(bootstrap_ip, bootstrap_port)
        self.ring = [{'hash_id': hash_id, 'ip': bootstrap_ip, 'port': bootstrap_port}]
    
    def insert(self, hash_id, ip, port):

        dict_to_insert = {'hash_id': hash_id, 'ip': ip, 'port':port}

        if self.ring[0]['hash_id'] > hash_id:
            self.ring.insert(0, dict_to_insert)
            prev_ip = self.ring[-1]['ip']
            prev_port = self.ring[-1]['port']
            next_ip = self.ring[1]['ip']
            next_port = self.ring[1]['port']
        elif self.ring[-1]['hash_id'] < hash_id:
            self.ring.append(dict_to_insert)
            prev_ip = self.ring[-2]['ip']
            prev_port = self.ring[-2]['port']
            next_ip = self.ring[0]['ip']
            next_port = self.ring[0]['port']
        else:
            for i in range(0, len(self.ring)-1):
                if self.ring[i]['hash_id'] < hash_id and self.ring[i+1]['hash_id'] > hash_id:
                    self.ring.insert(i+1, dict_to_insert)
                    prev_ip = self.ring[i]['ip']
                    prev_port = self.ring[i]['port']
                    next_ip = self.ring[i+2]['ip']
                    next_port = self.ring[i+2]['port']
                    break

        return prev_ip, prev_port, next_ip, next_port