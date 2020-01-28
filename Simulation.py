from Miner import Miner
from Blockchain import Blockchain
from ecdsa import SigningKey
from Transaction import Transaction
import random
import time, copy
from binascii import hexlify

class Simulation:
    # WE DID NOT ADD IN A BALANCE YET, BECAUSE WE HAVE QUESTIONS ABOUT IT !

    def __init__(self, n):
        self.num_of_miners = n
        self.miners = []
        # create new miners
        for x in range(0,n):
            # create each miner
            self.miners += [Miner(Blockchain(), x)]
        # self.balances = {}

    def create_random_transactions(self):
        # addresses = [m.get_pub_key() for m in self.miners]
        transactions = []
        for j in range(0, 10):
            senderRand = random.randint(0, len(self.miners)-1)
            recRand = random.randint(0, len(self.miners)-1)
            sender = hexlify(self.miners[senderRand].keypair.get_verifying_key().to_string()).decode('utf-8')
            receiver = hexlify(self.miners[recRand].keypair.get_verifying_key().to_string()).decode('utf-8')
            transactions += [Transaction.new(sender,
                                             receiver,
                                             random.randint(1, 4),
                                             "",
                                             self.miners[senderRand].keypair)]
        return transactions
        

    @classmethod
    def new(cls, n):
        return cls(n)

    # start the actual simulation
    def simulate(self):
        blocks = int(input("How many blocks do you want?"))
        fork = []
        for i in range(1, blocks + 1):
            print('Block {}'.format(i))
            chains = []
            for j in range(0, self.num_of_miners):
                miner=self.miners[j]
                transactions = self.create_random_transactions()
                print("\tMiner {}:".format(miner.id))
                if len(fork) > 1:
                    index1 = int(input("\t\tto add to the chain enter 1, to add to a fork enter a number bigger than 1")) - 1
                    miner.blockchain=copy.deepcopy(net_chain[index1])
                else:
                    index = 0
                miner.update_balance(None, miner.blockchain)
                if miner.blockchain.depth(index) > 1 and input("\t\tDo you want to creata fork? y/n ") == "y":
                    '{}{}'.format("\t\tAt what block should the fork start? Choose between 1 and ", miner.blockchain.depth(index))
                    num = int(input('{}'.format("\t\tHow many blocks before this should the fork start? ")))
                    miner.mine(transactions, index, num)
                    fork.append(miner.blockchain)
                else:
                    num = None
                    miner.mine(transactions, index, num)
                    chains.append(miner.blockchain)
                print("\t\tChain: {}".format(miner.blockchain.chain[0].hash[-16:]))

            randnum = random.randint(0, len(chains) - 1)
            net_chain=[]
            net_chain.append(chains[randnum])
            for miner in self.miners:
                miner.blockchain=copy.deepcopy(net_chain[0])

            for f in fork:
                net_chain.append(f)
            if len(fork)>0:
                if input("Do you want to resolve all nodes? y/n ") == "y":
                    longest = net_chain[0]
                    for k in range(1, len(net_chain)):
                        if net_chain[k].depth(0) > longest.depth(0):
                            longest = net_chain[k]
                    fork=[]
                    for miner in self.miners:
                        miner.blockchain = copy.deepcopy(longest)

        print(net_chain)