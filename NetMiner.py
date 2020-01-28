from flask import Flask, request
from queue import Queue
from threading import Thread
from MinerWorker import MinerWorker
from Block import Block
import hashlib
from binascii import hexlify
import logging
import json
app = Flask(__name__)

log=logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
work_queue=[Queue(maxsize=0),Queue(maxsize=0),Queue(maxsize=0),Queue(maxsize=0),Queue(maxsize=0),Queue(maxsize=0)]
# route to handle all requests
@app.route('/<string:category>_<string:item>', methods=['GET', 'POST'])
def get_stuff(category, item):
    if item=='block':
        desminer=request.base_url[:-10]
        desminer=int(desminer[-4:])
    if item=='transaction':
        desminer=request.base_url[:-16]
        desminer=int(desminer[-4:])
    q=desminer-5000
    data = request.form
    if category not in ['put', 'get']:
        return 'Not a valid request', 400
    response_q = Queue(maxsize=0)
    if category == 'put' and item == 'pubkey':
        print("putting into queue")
    work_queue[q].put((response_q, (category, item), data))
    work_queue[q].task_done()
    if category == 'put':
        return 'Success!', 200
    else:
        while True:
            if not response_q.empty():
                success, resp_data = response_q.get()
                #response_q.task_done()
                if success:
                    return resp_data, 200
                else:
                    return 'Not a valid request', 400        

def start_all_stuff(portnum, difficulty, selfish, trydospending):
    work_que = work_queue[portnum-5000]
    minerworker = MinerWorker(work_que, difficulty, portnum,selfish,trydospending)
    werk = Thread(target=minerworker.work)
    werk.setDaemon(True)
    werk.start()
    app.run(port=portnum,threaded=True)

#def main():
#    minerworker = MinerWorker(work_queue, 1)
#    werk = Thread(target=minerworker.work)
#    werk.setDaemon(True)
#    werk.start()
#    app.run()

#if __name__ == '__main__':
#    main()