from hashlib import hash1

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


        # !! template code added below !!
        # assumed to be known: port/ ip of this node
        # id computed from bootstrap -   hashing(ip+ port) - and given as argument

        self.id=id
        # keeping (key, value) pairs
        self.storage={}
        sel.in_proc=[]


    # managing processes asked from other nodes - when searching the right position in Z*m
    # ptypes: "query", "insert", "delete"
    # in_proc: queue order 
    def incoming_processes(self, ptype, data):
        if len(self.in_proc) == 0:
            return
        # ISSUES TO BE RESOLVED: 
        # !!! key must be in Z*m arithmetic !!! -> function "hashing"
        # successor variable to be defined 
        # return type to be determined (it's just a template)
        key=data[0]
        if len(data)==2:
            value=data[1]

        if(between(key, self.id, self.successor.id)):
            if(ptype=="delete"):
                self.storage.pop(key, None)
                return
            if (ptype=="insert" ):
                self.storage[key]=value
                return
            if(ptype=="query"):
                if (ID not in self.storage) :
                    # ... synchronization with flask
                    print("oopsie")
                else:
                    print("found value", self.storage[key] ," with key ", key)
                return
        else:
            self.successor.incoming_processes(ptype, data)

    # checks if a key that corresponds to an ID in Zn, is between the below values
    # that means, that this key corresponds to
    def between(ID, curID, succesorID):
        return (ID==curID or (ID > curID and ID < successorID))

    def hasing(value):
        # for size proportional with the output of sha1
        return int.from_bytes(sha1(value.encode()).digest(), byteorder='big') 
        # for size 2**n -> check below/ working in Zn
        # int(int.from_bytes(sha1(key.encode()).digest(), byteorder='big') % 2**n)

