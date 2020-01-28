from ecdsa import SigningKey
from binascii import hexlify
from Transaction import Transaction
from Blockchain import Blockchain
import hashlib
import random
import copy

class Miner:

    def __init__(self, blockchain, id, penalty=1, selfish=False):
        self.blockchain = blockchain
        self.keypair = SigningKey.generate()
        self.id = id+1
        self.balances=[]
        self.balance={}
        self.penalty = penalty
        self.selfish = selfish
        if selfish:
            self.selfishchain= Blockchain()
            self.privchainlen=0

    @classmethod
    def new(cls, blockchain, id, penalty,selfish):
        return cls(blockchain, id, penalty,selfish)

    def mine(self, transactions, chain):
        pk = self.get_pk()
        reward = Transaction.new(pk, pk, 1, "One step closer to rule over them all.", self.keypair)
        transactions=[reward]+transactions
        if not self.selfish:
            self.update_balance(None, self.blockchain, chain)
        else:
            self.update_balance(None, self.selfishchain, chain=0)
        oldbalance=copy.deepcopy(self.balance)
        transactions=list(filter(lambda x: self.check_balance(x), transactions))
        newlist=[]
        for i in transactions:
            if i not in newlist:
                newlist.append(i)
        transactions=newlist
        transactionscheck=[]
        for i in transactions:
            if self.check_balance(i):
                self.update_balance(i)
                transactionscheck.append(i)
        if not self.selfish:
            added = self.blockchain.add(transactionscheck, chain)
        else:
            added = self.selfishchain.add(transactionscheck, chain=0)
        if added == False:
            self.balance=copy.deepcopy(oldbalance)
            return added        
        return added

    def get_pk(self):
        return hexlify(self.keypair.get_verifying_key().to_string()).decode('utf-8')

    def update_balance(self, transaction, blockchain=None, chain=None):
        if blockchain != None:
            self.balance = {}
            ini=False
            for sub_list in self.balances:
                if blockchain.chain[chain] in sub_list:
                    ini= True
                    self.balance= copy.deepcopy(self.balances[self.balances.index(sub_list)][sub_list.index(blockchain.chain[chain])+1])
                    return True
            depth=blockchain.depth(chain)
            if depth != 1:
                block = blockchain.chain[chain]
                for k in range(1, depth-1):
                    block = block.prev_block
                    for i in block.transactions:
                        self.update_balance(i)
                block = blockchain.chain[chain]
                for i in block.transactions:
                    self.update_balance(i)
            if not ini:
                self.balances.append([blockchain.chain[chain],copy.deepcopy(self.balance)])
            return True
        sender = transaction.sender
        receiver = transaction.receiver
        amount = transaction.amount
        if (sender in self.balance and sender!= receiver):
            self.balance[sender]-=amount
        #if (sender!=receiver and sender not in self.balance):
        #    self.balance[sender]= -amount
        print(receiver)
        if receiver not in self.balance:
            self.balance[receiver] = 0
        if receiver in self.balance:
            self.balance[receiver]+= amount
        
    def check_balance(self, transaction):
        sender = transaction.sender
        receiver = transaction.receiver
        amount = transaction.amount
        if (sender!= receiver and sender not in self.balance):
            return False
        if  (sender!=receiver and amount > self.balance[sender]):
            return False
        return True

    def make_transactions(self,publist):
        recRand = random.randint(0, len(publist) - 1)
        sender = self.get_pk()
        receiver = publist[recRand]
        amount=random.randint(1, 10)
        transaction = Transaction.new(sender, receiver,amount,"",self.keypair)
        return transaction

    def addblock(self, newblock):
        found=False
        newcalhash = hashlib.sha256(newblock.header_to_json().encode("utf-8")).digest()
        newcalchash = hexlify(newcalhash).decode("utf-8")
        if self.selfish:
            self.blockchain.chain.append(self.selfishchain.chain[0])
        for j in range(0, len(self.blockchain.chain)) :
            if (not found):
                depth = self.blockchain.depth(j)
                block = self.blockchain.chain[j]
                calhash = hashlib.sha256(block.header_to_json().encode("utf-8")).digest()
                calchash = hexlify(calhash).decode("utf-8")
                #print("Miner: {}\t{}\t{}\t{}," .format(self.get_pk()[-4:],newcalchash[-4:], newblock.prev_hash[-4:], calchash[-4:]))
                if newblock.prev_hash == calchash:
                    self.blockchain.chain.append(block)
                    self.update_balance(None, self.blockchain, -1)
                    del self.blockchain.chain[-1]
                    valid_trans = True
                    for t in newblock.transactions:
                    	valid_trans = valid_trans and self.check_balance(t)
                    	if not self.check_balance(t):
                    	    print(t)
                    if not (valid_trans):
                        print(
                            " This block cannot be added to the chain because the transactions are not valid")
                        return False
                    newblock.prev_block = block
                    if self.selfish:
                        if j != (len(self.blockchain.chain)-1):
                                del self.blockchain.chain[-1]
                    self.blockchain.chain[j] = newblock
                    self.update_balance(None,self.blockchain,j)
                    found= True
                    return found
                for k in range(1, depth):
                    if (not found):
                        block = block.prev_block
                        calhash = hashlib.sha256(block.header_to_json().encode("utf-8")).digest()
                        calchash = hexlify(calhash).decode("utf-8")
                        #print("Miner: {}\t{}\t{}\t{}," .format(self.get_pk()[-4:],newcalchash[-4:], newblock.prev_hash[-4:], calchash[-4:]))
                        if newblock.prev_hash == calchash:
                            self.blockchain.chain.append(block)
                            self.update_balance(None, self.blockchain, -1)
                            del self.blockchain.chain[-1]
                            valid_trans = True
                            for t in newblock.transactions:
                                valid_trans = valid_trans and self.check_balance(t)
                                if not self.check_balance(t):
                                    print(t)
                            if not (valid_trans):
                                print(
                                    " This block cannot be added to the chain because the transactions are not valid")
                                return False
                            newblock.prev_block = block
                            if self.selfish:
                                del self.blockchain.chain[-1]
                            self.blockchain.chain.append(newblock)
                            self.update_balance(None,self.blockchain,j)
                            found= True
                            return found
                        
        if (not found):
            if self.selfish:
                del self.blockchain.chain[-1]
            print("For miner{}, This block: {} cannot be added to the chain at this moment, because it previous hash{} does not link to any known chains.".format(self.get_pk()[-4:],newcalchash[-4:], newblock.prev_hash[-4:]))
            return False
            
    def t_already_there(self,transaction):
        t= transaction.to_json()
        found=False
        if self.selfish:
            self.blockchain.chain.append(self.selfishchain.chain[0])
        for j in range(0, len(self.blockchain.chain)) : 
            if (not found):
                depth = self.blockchain.depth(j)
                block = self.blockchain.chain[j]
                if transaction in block.transactions:
                    found=True
                for k in range(1, depth):
                    if (not found):
                        block = block.prev_block
                        if transaction in block.transactions:
                            found=True
        if self.selfish:
            del self.blockchain.chain[-1]
        return found