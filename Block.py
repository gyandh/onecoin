import json
from MerkleTree import MerkleTree
import time
import hashlib
import ecdsa
from binascii import hexlify, unhexlify
from Transaction import Transaction
import os

TARGET = b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'


# The Block class for the Blockchain
class Block:
    # we are defining all the parts that should go into the block header here.
    def __init__(self,index, prev_hash, prev_block,transactions, root=None, timestamp=None, nonce=None):
        self.index = index
        self.prev_hash = prev_hash
        self.prev_block= prev_block
        self.transactions = transactions
        self.root = root
        self.timestamp = timestamp
        self.nonce = nonce

    # Here we create our genesis block. Inspiration taken from LOTR :)

    @classmethod
    def Mountdoom(cls):
        index=0
        prev_hash=hexlify(hashlib.sha256(b"Multiple coins were given to the Human Race.\
                            All the coins were given into the hands of needy people\
                            But then One Coin was made to rule over them all.\
                            This One Coin has the power to unite the Human Race.\
                            Or divide in an endless search for power.").digest()).decode("utf-8")
        return cls(index,prev_hash,None,[])
    # If we want to make a new block, we need the previous hash and transactions in order to add the block to the blockchain.
    @classmethod
    def new(cls, index, prev_hash, prev_block,transactions):
        return cls(index, prev_hash, prev_block, transactions)

    # Builds the Merkle Tree for the blocks, for each level of penalty we have to hash it again
    def pow(self):
        # If there was not a transaction tree yet, we create one for the transactions.
        t_tree = MerkleTree()
        for t in self.transactions:
            t_tree.add(str.encode(t.to_json()))
        t_tree.build()
        self.root= hexlify(t_tree.root.data).decode("utf-8")
        self.timestamp = int(time.time())
        # Here we try to brute force the hash< target. We will find the nonce that is needed for this hash.
        found= False
        for i in range(0,20000):
            n= os.urandom(4)
            self.nonce=hexlify(n).decode("utf-8")
            guess = hashlib.sha256(self.header_to_json().encode("utf-8")).digest()
            if(guess <= TARGET):
                found = True
                return found
        self.nonce= None
        return found

    # Ecodes the block object into a JSON object
    def to_json(self):
        temp = {}
        for x in range(0, len(self.transactions)):
            temp[x] = self.transactions[x].to_json()
        transactions = json.dumps(temp, sort_keys=True)
        return json.dumps({'index': self.index,
                           'prev_hash': self.prev_hash,
                           'root': self.root,
                           'timestamp': self.timestamp,
                           'nonce': self.nonce,
                           'transactions': transactions}, sort_keys=True)

    def header_to_json(self):
        return json.dumps({'index': self.index,
                           'prev_hash': self.prev_hash,
                           'root': self.root,
                           'timestamp': self.timestamp,
                           'nonce': self.nonce}, sort_keys=True)

    # Decodes the JSON object to a transaction object
    @classmethod
    def from_json(cls, json_data):
        try:
            decoded = json.loads(json_data)
        except Exception as e:
            print(e)
        try:
            decoded_trans = json.loads(decoded['transactions'])
            transactions = []
            for k in decoded_trans:
                transactions += [Transaction.from_json(decoded_trans[k])]

            return cls(decoded['index'], decoded['prev_hash'],
                       None, transactions, decoded['root'],
                       decoded['timestamp'], decoded['nonce'])
        except KeyError as ke:
            print(ke)

    # Validates the Block via it's transactions and tree
    def validate(self):
        # validate each transaction's signature, if one is wrong return false
        for t in self.transactions:
            t_dict = json.loads(t.to_json())
            if not Transaction.validate(t_dict):
                return False
        # validate the block's transaction merkle tree
        valid_tree = False
        test_tree = MerkleTree()
        for t in self.transactions:
            test_tree.add(str.encode(t.to_json()))
        test_tree.build()
        return MerkleTree.verify_proof(test_tree.get_root(), test_tree.get_proof())

# def main():
#     ta = Transaction("lol", "123", 12, "", b'\x12', 123)
#     tb = Transaction("lol1", "1232", 13, "", b'\x12', 123)

#     test = Block(21, "abc", None, [ta,tb], "wow", "1337", 12314123)
#     print(test.to_json())

# if __name__ == '__main__':
#     main()
