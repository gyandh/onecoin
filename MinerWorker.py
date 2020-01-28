import json, requests, time, sys, os
from threading import Thread
from Miner import Miner
from Transaction import Transaction
from Blockchain import Blockchain
from Block import Block
from ecdsa import VerifyingKey
from MerkleTree import MerkleTree
import hashlib
from binascii import hexlify

class MinerWorker:
    def __init__(self, work_queue, difficulty, identity, selfish=False,trydospending=False):
        self.wq = work_queue
        self.miner = Miner.new(Blockchain(), 0, difficulty,selfish)
        self.upcoming_transactions = []
        self.received_blocks = []
        self.identity = identity
        self.spv_clients = [5007, 5008, 5009]
        self.other_miners = [5000, 5001, 5002, 5003, 5004, 5005]
        self.publist=[]
        self.other_miners.remove(self.identity)
        self.addr = '127.0.0.1'
        self.pubkeys = []
        self.selfish=selfish
        self.trydospending=trydospending
        self.dospending=False
        f = open(str(self.identity)+'.txt', 'w')
        f.write(self.miner.get_pk())
        f.close()


    def work(self):
        time.sleep(2)
        print("my port {}, my pubkey{}".format(self.identity,self.miner.get_pk()[-4:]))
        penalty =self.miner.penalty
        self.learn_pks()
        if self.selfish:
            published=0
        for m in self.other_miners:
            f = open(str(m)+'.txt', 'r')
            self.pubkeys.append(f.readline())
            f.close()
        while True:
            # TODO: how many requests to parse each round??
            # 1. answering queries
            for x in range(0,50):
                if not self.wq.empty():
                    # todo has following structure
                    # (response_queue, command, data)
                    # response_queue: if a response to server process is needed, put here
                    # command: the command issues
                    # data: json format key:value of needed extra data, for example which block to get
                    todo = self.wq.get()
                    rq = todo[0]
                    cmd = todo[1]
                    data = todo[2]
                    success, response = self.evaluate_command(cmd, data)
                    #if success:
                    #    b = Block.from_json(data['block'])
                    #    calhash = hashlib.sha256(b.to_json().encode("utf-8")).digest()
                    #    calchash = hexlify(calhash).decode("utf-8")
                    #    #print("Miner{} received to queue {}".format(self.miner.get_pk()[-4:],calchash[-4:]))
                    if success and cmd[0] != 'put':
                        rq.put((True, response))
                        rq.task_done()
                    elif not success and cmd[0] != 'put':
                        rq.put((False, None))
                        rq.task_done()
            # stop answering queries
            # 2. add blocks received
            #print("adding new blocks")
            if self.received_blocks != []:
                failed = []
                #print(self.received_blocks)
                for x in range(0, len(self.received_blocks)):
                    # add_existing() should return (succeeded:boolean, block)
                    if(not self.miner.addblock(self.received_blocks[x])):
                        failed.append(self.received_blocks[x])
                        #print("failed", failed)
                        #print(self.miner.blockchain.chain)
                if self.selfish:
                    dif=self.miner.selfishchain.depth(0)-self.miner.blockchain.depth(self.miner.blockchain.get_longest())
                    if dif == -1:
                        self.miner.selfishchain.chain[0]== self.miner.blockchain.chain[self.miner.blockchain.get_longest()]
                        self.miner.privchainlen=0
                        published=0
                    elif dif ==0:
                        prevsblock=self.miner.selfishchain.chain[0]
                        tr = Thread(target=self.broadcast_block, args=(self.other_miners, prevsblock.to_json(),))
                        tr.setDaemon(True)
                        tr.run()
                        htr = Thread(target=self.broadcast_header, args=(self.spv_clients, prevsblock.header_to_json(),))
                        htr.setDaemon(True)
                        htr.run()
                        published=0
                    elif dif ==1:
                        prevsprevsblock=self.miner.selfishchain.chain[0]
                        tr = Thread(target=self.broadcast_block, args=(self.other_miners, prevsprevsblock.to_json(),))
                        tr.setDaemon(True)
                        tr.run()
                        htr = Thread(target=self.broadcast_header, args=(self.spv_clients, prevsprevsblock.header_to_json(),))
                        htr.setDaemon(True)
                        htr.run()
                        for i in range( 0, published-1):
                            prevsprevsblock=prevsprevsblock.prev_block
                            tr = Thread(target=self.broadcast_block, args=(self.other_miners, prevsprevsblock.to_json(),))
                            tr.setDaemon(True)
                            tr.run()
                            htr = Thread(target=self.broadcast_header, args=(self.spv_clients, prevsprevsblock.header_to_json(),))
                            htr.setDaemon(True)
                            htr.run()
                        self.miner.privchainlen=0
                        published=0
                    else:
                        prevsprevsblock=self.miner.selfishchain.chain[0]
                        for i in range( 0, published-1):
                            prevsprevsblock=prevsprevsblock.prev_block
                        tr = Thread(target=self.broadcast_block, args=(self.other_miners, prevsprevsblock.to_json(),))
                        tr.setDaemon(True)
                        tr.run()
                        htr = Thread(target=self.broadcast_header, args=(self.spv_clients, prevsprevsblock.header_to_json(),))
                        htr.setDaemon(True)
                        htr.run()
                        published-=1
                penalty= self.miner.penalty
                self.received_blocks = failed
                #self.miner.blockchain.resolve()
            # 3. do some mining
            #print("started mining")
            #print(self.miner.blockchain.chain)
            chain=self.miner.blockchain.get_longest()
            if self.dospending:
                self.miner.blockchain.chain.append(self.miner.blockchain.chain[self.miner.blockchain.get_longest()].prev_block)
                chain=-1
            for t in self.upcoming_transactions:
                if self.miner.t_already_there(t):
                    self.upcoming_transactions.remove(t)
            mined_block = self.miner.mine(self.upcoming_transactions, chain)
            #print("done mining")
            # broadcast newly mined block
            if mined_block != False:
                penalty -=1
                if penalty ==0:
                    if not self.selfish:
                        self.miner.blockchain.chain[chain]= self.miner.blockchain.chain[0]
                        self.miner.blockchain.chain[0]=mined_block
                        tr = Thread(target=self.broadcast_block, args=(self.other_miners, mined_block.to_json(),))
                        tr.setDaemon(True)
                        tr.run()
                        htr = Thread(target=self.broadcast_header, args=(self.spv_clients, mined_block.header_to_json(),))
                        htr.setDaemon(True)
                        htr.run()
                        if self.dospending:
                            self.dospending=False
                    else:
                        dif=self.miner.selfishchain.depth(0)-self.miner.blockchain.depth(self.miner.blockchain.get_longest())
                        print(self.miner.selfishchain.depth(0))
                        print(self.miner.blockchain.depth(self.miner.blockchain.get_longest()))
                        #print(self.miner.selfishchain.chain, self.miner.blockchain.chain)
                        prevsblock=self.miner.selfishchain.chain[0]
                        self.miner.selfishchain.chain[0]=mined_block
                        self.miner.privchainlen+=1
                        published+=1
                        print(dif, self.miner.privchainlen)
                        if dif==0 and self.miner.privchainlen==2:
                            print("send")
                            tr = Thread(target=self.broadcast_block, args=(self.other_miners, prevsblock.to_json(),))
                            tr.setDaemon(True)
                            tr.run()
                            tr = Thread(target=self.broadcast_block, args=(self.other_miners, mined_block.to_json(),))
                            tr.setDaemon(True)
                            tr.run()
                            htr = Thread(target=self.broadcast_header, args=(self.spv_clients, prevsblock.header_to_json(),))
                            htr.setDaemon(True)
                            htr.run()
                            htr = Thread(target=self.broadcast_header, args=(self.spv_clients, mined_block.header_to_json(),))
                            htr.setDaemon(True)
                            htr.run()
                            self.miner.privchainlen=0
                            published=0
                    #self.miner.blockchain.chain.append(mined_block)
                    penalty= self.miner.penalty
            #print("gogo")
            chain_len = str(self.miner.blockchain.depth(self.miner.blockchain.get_longest()))
            miner_name = self.miner.get_pk()[-4:]
            info_str = '{}: {}'.format(miner_name, chain_len)
            print(info_str)
            if int(chain_len)%10==0:
                self.miner.update_balance(None, self.miner.blockchain, self.miner.blockchain.get_longest())
                balance=self.miner.balance
                print('Miner{} keeps a balance which is{}'.format(miner_name, balance))
                if self.trydospending:
                    self.dospending=True
            htr = Thread(target=self.make_transactions, args=(self.miner,self.other_miners,self.publist,self.identity,))
            htr.setDaemon(True)
            htr.run()
            time.sleep(0.25)

            
    @staticmethod
    def broadcast_block(other_miners, block_json):
        b = Block.from_json(block_json)
        calhash = hashlib.sha256(b.to_json().encode("utf-8")).digest()
        calchash = hexlify(calhash).decode("utf-8")
        try:
            for other_miner in other_miners:
                url = 'http://127.0.0.1:'+str(other_miner)+'/put_block'
                try:
                    r = requests.post(url, data={'block':block_json}, timeout=1)
                    #print("the url is {}, the block is{}" .format(url, calchash[-4:]))
                except requests.exceptions.ReadTimeout as d:
                    print(d)                    
                    continue
        except Exception as e:
            print(e)

    @staticmethod
    def broadcast_header(spvs, header):
        for client in spvs:
            MinerWorker.tell_miner(client, '/put_header', {'header':header})
        

    def ask_miner(self, miner, cmd):
        url = 'http://127.0.0.1:'+str(miner)+cmd
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return r.json()
            else:
                return None
        except requests.exceptions.ReadTimeout:
            return None

    @staticmethod
    def tell_miner(miner, cmd, data_to_send):
        url = 'http://127.0.0.1:'+str(miner)+cmd
        try:
            r = requests.post(url, data=data_to_send, timeout=1)
        except requests.exceptions.ReadTimeout:
            pass
            
    @staticmethod
    def make_transactions(miner,minerlist,publist,identity):
        transaction = miner.make_transactions(publist)
        transaction= Transaction.to_json(transaction)
        minerlist.append(identity)
        try:
            for miners in minerlist:
                url = 'http://127.0.0.1:'+str(miners)+'/put_transaction'
                try:
                    r = requests.post(url, data={'transaction':transaction}, timeout=1)
                    #print("the url is {}, the block is{}" .format(url, calchash[-4:]))
                except requests.exceptions.ReadTimeout as d:
                    print(d)                    
                    continue
        except Exception as e:
            print(e) 
    
    # execute command
    # return (successful:boolean, response:string/None)
    def evaluate_command(self, cmd, data):
        #print("evaluating")
        category, item = cmd
        if data != None:
            recv_data = data
        else:
            recv_data = {}
        if category == 'put':
            if item == 'transaction':
                return self.put_transaction(recv_data['transaction'])
            elif item == 'block':
                return self.put_block(recv_data['block'])
            else:
                return (False, None)
        elif category == 'get':
            if item == 'proof':
                return self.get_proof(recv_data['signature'])
            elif item == 'block':
                try:
                    b_index = recv_data['index']
                    return self.get_block(b_index)
                except KeyError:
                    return self.get_block()
            elif item == 'header':
                try:
                    h_index = int(recv_data['index'])
                    print("getting header: {}".format(h_index))
                    return self.get_header(h_index)
                except KeyError as ke:
                    print(ke)
                    return self.get_header()
            elif item == 'pubkey':
                return self.get_pubkey()
            else:
                return (False, None)
        else:
            return (False, None)
    # Following methods should return the following format:
    # (successful:boolean, response:string/None)
    def get_proof(self, signature):
        # find block in chain containing transaction with given signtaure
        lc = self.miner.blockchain.get_longest()
        curr_block = self.miner.blockchain.chain[lc]
        found = False
        found_tran = None
        while curr_block != None:
            for t in curr_block.transactions:
                if t.signature == signature:
                    found = True
                    found_tran = t
                    break
            if found:
                break
            else:
                curr_block = curr_block.prev_block
        if curr_block == None:
            return (False, None)
        # build tree
        tree = MerkleTree()
        for t in curr_block.transactions:
            tree.add(t)
        # calculate proof
        proof = tree.get_proof(found_tran)
        # send back root and proof as json
        if proof == False:
            return (False, None)
        root_proof = {'root':curr_block.root, 'proof':proof}
        return_data = json.dumps(root_proof)
        return (True, return_data)



    # used by miners and includes entire transaction set
    def get_block(self, n=-1):
        block = self.miner.blockchain.get_nth(n)
        if block != None:
            return (True, block.to_json())
        else:
            return (False, None)
    # used by SPV, only includes header/meta info
    def get_header(self, n=-1):
        block = self.miner.blockchain.get_nth(n)
        if block != None:
            return (True, block.header_to_json())
        else:
            return (False, None)
    
    # return this client's public key, to be able to receive money
    def get_pubkey(self):
        return (True, json.dumps({'pubkey':self.miner.get_pk()}, sort_keys=True))
        
    def learn_pks(self):
        for x in self.other_miners+self.spv_clients:
            f = open(str(x)+'.txt', 'r')
            pk = f.readline()
            f.close()
            self.publist.append(pk)
    
    def put_transaction(self, transaction):
        # create a Transaction object from the json data, it also validates it
        t = Transaction.from_json(transaction)
        if not self.miner.t_already_there(t):
            self.upcoming_transactions.append(t)
        return (True, 'Transaction added')

    def put_block(self, block):
        b = Block.from_json(block)
        calhash = hashlib.sha256(b.to_json().encode("utf-8")).digest()
        calchash = hexlify(calhash).decode("utf-8")
        #print("Miner : {} Received block with hash {}".format(self.miner.get_pk()[-4:],calchash[-4:]))
        #if b not in self.received_blocks:
        self.received_blocks += [b]
        return (True, 'Block added')