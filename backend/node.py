class Node():
    def __init__(
        self,
        my_ip=None,
        my_port=None,
        prev_ip=None,
        prev_port=None,
        next_ip=None,
        next_port=None
    ):
        """
        This class will be used by all nodes to preserve information
        about themselves, as well as their neighbors in the ring eg:
        links to the previous node, the next node etc.
        """
        self.my_id = None
        self.my_ip = my_ip
        self.my_port = my_port

        self.prev_id = None
        self.prev_ip = prev_ip
        self.prev_port = prev_port

        self.next_id = None
        self.next_ip = next_ip
        self.next_port = next_port

        self.storage = {}
