from config import bootstrap_ip, bootstrap_port

class Ring():
    def __init__(self, bootstrap_ip, bootstrap_port):
        """
        This class will be used by the bootstrap NODE to keep track
        of the nodes that are in the ring network.
        """
        self.ring = [(bootstrap_ip, bootstrap_port)]
        
    def insert(self, ip, port):
        prev = self.ring[-1]
        self.ring.append((ip, port))
        return prev