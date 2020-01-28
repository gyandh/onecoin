from Block import Block, TARGET
import hashlib
import random
from binascii import hexlify, unhexlify

# Class for the actual Blockchain
class Blockchain:

    # Initializes the chain with the genesis block
    def __init__(self):
        self.chain = [Block.Mountdoom()]

    # Finds the depth of the chain by iterating through it
    def depth(self, chain):
        go=True
        depth=0
        block=self.chain[chain]
        while go:
            if(block.prev_block==None):
                depth+=1
                go=False
            else:
                depth+=1
                block = block.prev_block
        return depth

    def add(self, transactions, chain):
        depth=self.depth(chain)
        index= depth+1
        prevblock=self.chain[chain]
        prevblockhash= hexlify(hashlib.sha256(prevblock.header_to_json().encode('utf-8')).digest()).decode('utf-8')
        prevhash = prevblockhash
        newblock= Block.new(index, prevhash,prevblock,transactions)
        if (newblock.pow()):
            if(self.validateblock(newblock,chain)):
                #self.chain[chain]= self.chain[0]
                #self.chain[0]=newblock
                return newblock
        else:
            return False
       


    # Here we check if the block uses the previous hashblock and if the hashvalue is calculated correct and below target
    def validateblock(self, newblock,chain):
        calhash=hashlib.sha256(newblock.header_to_json().encode("utf-8")).digest()
        calchash= hexlify(calhash).decode("utf-8")
        prevblock = self.chain[chain]
        prevblockhash = hexlify(hashlib.sha256(prevblock.header_to_json().encode('utf-8')).digest()).decode('utf-8')
        newblockhash = hexlify(hashlib.sha256(newblock.header_to_json().encode('utf-8')).digest()).decode('utf-8')
        if(newblockhash ==calchash and calhash< TARGET and newblock.prev_hash== prevblockhash):
            return True
        else:
            return False

    # Validates a fork by iterating over it
    @staticmethod
    def validate_fork(head):
        if(head.prev_block == None):
            return head.validate()
        else:
            return head.validate() and validate_fork(head.prev_block)

    # Validates the whole chain by iterating over it
    @staticmethod
    def validate_chain(bc):
        is_valid = True
        for head, depth in bc.chain:
            is_valid = is_valid and validate_fork(head)
        return is_valid

    # TODO: update to new version
    # Reolves the forks by chosing the longest chain as the new chain
    def resolve(self):
        longestchain=self.chain
        for chain in self.otherchains:
            if len(chain)>len(longestchain):
                longestchain=chain
            elif(len(chain)==len(longestchain)):
                if random.random() > 0.5:
                    longestchain=chain
        self.chain=longestchain
    
    def get_longest(self):
        longest = (0, self.depth(0))
        for x in range(1, len(self.chain)):
            candidate = (x, self.depth(x))
            if candidate[1] > longest[1]:
                longest = candidate
        return longest[0]

    @staticmethod
    def get_nth_help(block, n):
        current = block
        while current != None:
            if current.index == n:
                return current
            else:
                current = current.prev_block
        return None

    # Returns the nth block for specified number n
    # calls get_nth_help()
    def get_nth(self, n):
        longest = (0,0) # (index, depth)
        for x in range(0, len(self.chain)):
            depth = self.depth(x)
            if depth > longest[1]:
                longest = (x, depth)
        if n == -1:
            return self.chain[longest[0]]
        else:
            return self.get_nth_help(self.chain[longest[0]], n)
    
    
