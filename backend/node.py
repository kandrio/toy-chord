class Node():
    def __init__(self, prev_ip=None, prev_port=None, next_ip=None, next_port=None):
        """ 
        This class will be used by the bootstrap NODE and all the other NODES
        to preserve information about their NEIGHBORS in the ring network, eg:
        the previous node and the next node in the ring.
        """

        self.prev_ip = prev_ip
        self.prev_port = prev_port
        self.next_ip = next_ip
        self.next_port = next_port
