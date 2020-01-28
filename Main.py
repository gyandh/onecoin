import ecdsa
from ecdsa import SigningKey
from Transaction import Transaction
import random, time
from threading import Thread
from Miner import Miner
from Simulation import Simulation
import NetMiner
import SPV_net
from time import sleep

def main():
    # SPVs running on 5007-5009
    start_spv()
    sleep(0.5)
    start_51miners()
    #start_selfishminers()
    while True:
        try:
            pass
        except:
            pass

def start_normalminers(num=5):
    for x in range(5000, 5001+num):
        td = Thread(target=NetMiner.start_all_stuff, args=(x,1,False,False,))
        td.setDaemon(True)
        td.start()

def start_51miners(num=5):
    diffs = [1,5,5,5,5,5]
    for x,d in zip(range(0,num+1), diffs):
        if x==0:
                trydospending=True
        else:
            trydospending= False
        td = Thread(target=NetMiner.start_all_stuff, args=(5000+x,d,False,trydospending,))
        td.setDaemon(True)
        td.start()

def start_spv(num=3):
    ports = [5007, 5008, 5009]
    for p in ports:
        td = Thread(target=SPV_net.start_SPV, args=(p,))
        td.setDaemon(True)
        td.start()


def start_selfishminers(num=5):
    diffs = [1,5,5,5,5,5]
    for x,d in zip(range(0,num+1), diffs):
        if x==0:
            selfish=True
        else:
            selfish= False
        td = Thread(target=NetMiner.start_all_stuff, args=(5000+x,d,selfish,False,))
        td.setDaemon(True)
        td.start()

if __name__ == '__main__':
    main()
