import json, random, hashlib, requests
from ecdsa import SigningKey
from binascii import hexlify
from Transaction import Transaction
from Block import Block

class SPVclient:
    def __init__(self, port):
        self.port = port
        self.keypair = SigningKey.generate()
        self.blockheaders=[] # maybe remove
        self.blockheaderchain = self.Blockheaderchain(port)
        self.miners = [5000, 5001, 5002, 5003, 5004, 5005]
        self.other_spvs = [5007, 5008, 5009]
        self.other_spvs.remove(port)
        self.identity = hexlify(self.keypair.get_verifying_key().to_string()).decode('utf-8')
        self.pk_list = []
        f = open(str(self.port)+'.txt', 'w')
        f.write(self.identity)
        f.close()
    
    def add_header(self, header):
        return self.blockheaderchain.add(header)

    def print_chain(self):
        if len(self.blockheaderchain.headers) > 0:
            printlist=[]
            for x in range(0, len(self.blockheaderchain.headers)):
                current = self.blockheaderchain.headers[x]
                add="|{},i:{}, -{}".format(x,current.index, current.prev_hash[-4:])
                printlist.append([add])
            print("SPV:{} ".format(self.identity[-4:]),printlist)
                #while current != None:
                #    print("SPV:{} |{} i:{} - {}".format(self.identity[-4:], x, current.index, current.prev_hash[-4:]))
                #    current = current.prev_header

    def make_transactions(self,publist):
        recRand = random.randint(0, len(publist) - 1)
        sender = self.get_pk()
        receiver = publist[recRand]
        amount=random.randint(1, 10)
        transaction = Transaction.new(sender, receiver,amount,"",self.keypair)
        return transaction

    def get_pk(self):
        return hexlify(self.keypair.get_verifying_key().to_string()).decode('utf-8')

    def learn_pks(self):
        for x in self.miners+self.other_spvs:
            f = open(str(x)+'.txt', 'r')
            pk = f.readline()
            f.close()
            self.pk_list.append( pk)
        
    #def get_blockh(self,blockh):
    #    blockh=Blockheader.new(blockh)
    #    calhash = hashlib.sha256(self.to_json(self.blockheaders[-1]).encode("utf-8")).digest()
    #    calchash = hexlify(calhash).decode("utf-8")
    #    if blockh.prev_hash==calchash:
    #        self.blockheaders.append(blockh)
    #    else:
    #        print("Blockheader does not point to previous blockheader.")

    def get_transactionproof(self,root, proof):
        # last entry in proof list is bottom hash
        prev_hash = proof[-1][1]
        # loop through proof list computing each successive hash
        for i in range(len(proof) - 2, -1, -1):
            if (proof[i][0] == 0):
                # current index is a right-node
                prev_hash = hashlib.sha256(b'1' + prev_hash + proof[i][1]).digest()
            else:
                # current index is a left-node
                prev_hash = hashlib.sha256(b'1' + proof[i][1] + prev_hash).digest()
        return prev_hash == root

    @staticmethod
    def to_json(data):
        return json.dumps({'index': data.index,
                           'prev_hash': data.prev_hash,
                           'root': data.root,
                           'timestamp': data.timestamp,
                           'nonce': data.nonce}, sort_keys=True)
    class Blockheader:
        def __init__(self,index, prev_hash, root, timestamp, nonce, prev_header=None):
            self.index = index
            self.prev_hash = prev_hash
            self.root = root
            self.timestamp = timestamp
            self.nonce = nonce
            self.prev_header = prev_header

        @classmethod
        def new(cls, json_data):
            try:
                decoded = json.loads(json_data)
            except Exception as e:
                print(e)
            try:
                return cls(decoded['index'], decoded['prev_hash'],
                           decoded['root'], decoded['timestamp'],
                           decoded['nonce'], None)
            except KeyError as ke:
                print(ke)

    class Blockheaderchain:
        def __init__(self, identifier):
            self.identifier = identifier
            gen=Block.Mountdoom()
            genhead=gen.header_to_json()
            genhead=SPVclient.Blockheader.new(genhead)
            self.headers = [genhead]

        def add(self, header):
            #if len(self.headers) == 0 and header.index == 2:
            #    self.headers = [header]
            #    return True

            for i in range(0, len(self.headers)):
                current_h = self.headers[i]
                curr_hash = hashlib.sha256(SPVclient.to_json(current_h).encode("utf-8")).digest()
                enc_hash = hexlify(curr_hash).decode("utf-8")
                # 1st case: new header is added to head of fork -> push previous one down and add header
                if enc_hash == header.prev_hash:
                        header.prev_header = current_h
                        self.headers[i] = header
                        return True
                # 2nd case: new header is a new fork, find block where fork happened
                else:
                    current_h = current_h.prev_header
                    while current_h != None:
                        curr_hash = hashlib.sha256(SPVclient.to_json(current_h).encode("utf-8")).digest()
                        enc_hash = hexlify(curr_hash).decode("utf-8")
                        #print("{} == {}".format(enc_hash, header.prev_hash))
                        if enc_hash == header.prev_hash:
                            header.prev_header = current_h
                            self.headers.append(header)
                            return True
                        current_h = current_h.prev_header
            print("blockheader not pointing to known header")
            return False
