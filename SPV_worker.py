from SPV_client import SPVclient
from time import sleep
import json, requests, time, sys, os, random
from threading import Thread
from Transaction import Transaction
from MerkleTree import MerkleTree
class SPVworker:
    def __init__(self, work_queue, port):
        self.client = SPVclient(port)
        self.wq = work_queue
        self.received_headers = []
        self.client.learn_pks()
        self.received_headers=[]
        self.spv_clients = [5007, 5008, 5009]
        self.other_miners = [5000, 5001, 5002, 5003, 5004, 5005]

    def work(self):
        print("SPV:{} ".format(self.client.identity[-4:]))
        sleep(1)
        self.client.learn_pks()
        # unconfirmed transactions
        unconfirmed = []
        while True:
            sleep(1)
            # check max 50 reveived headers
            for x in range(0,50):
                if not self.wq.empty():
                    ((category, item), data) = self.wq.get()
                    if category == 'put' and item == 'header':
                        self.received_headers.append(self.client.Blockheader.new(data['header']))
                else:
                    break
            # add the headers to datastructure
            if self.received_headers != []:
                failed = []
                for x in range(0, len(self.received_headers)):
                    success = self.client.add_header(self.received_headers[x])
                    if not success:
                        failed.append(self.received_headers[x])
                #self.client.print_chain()
                self.received_headers = failed
            # send transactions
                htr = Thread(target=self.make_transactions, args=(self.client,self.other_miners,self.client.pk_list, unconfirmed,))
                htr.setDaemon(True)
                htr.run()
            # check proofs
            if unconfirmed != []:
                temp = []
                for t in unconfirmed:
                    r_miner = random.randint(0, len(self.other_miners)-1)
                    url = 'http://127.0.0.1:'+str(self.other_miners[r_miner])+'/get_proof'
                    r = requests.get(url, data={'signature':str(t.signature)}, timeout=1)
                    data = json.loads(r.json)
                    proof = data['proof']
                    root = data['root']
                    # do proof
                    success = MerkleTree.verify_proof(root, proof)
                    if success:
                        print("Successfully validated transaction: {}".format(t.signature[-8:]))
                    else:
                        temp.append(t)
                unconfirmed = temp
                
    @staticmethod
    def make_transactions(client,minerlist,publist, temp_list):
        transaction = client.make_transactions(publist)
        transaction= Transaction.to_json(transaction)
        try:
            for miners in minerlist:
                url = 'http://127.0.0.1:'+str(miners)+'/put_transaction'
                try:
                    r = requests.post(url, data={'transaction':transaction}, timeout=1)
                    #print("the url is {}, the block is{}" .format(url, calchash[-4:]))
                    temp_list.append(transaction)
                except requests.exceptions.ReadTimeout as d:
                    print(d)                    
                    continue
        except Exception as e:
            print(e)           
        

