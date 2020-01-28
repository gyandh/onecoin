from flask import Flask, request
from queue import Queue
from threading import Thread
from SPV_worker import SPVworker
import logging
app = Flask(__name__)
log=logging.getLogger('werkzeug')
work_queue = [Queue(maxsize=0), Queue(maxsize=0), Queue(maxsize=0)]
#log.setLevel(logging.ERROR)
# route to handle all requests
@app.route('/<string:category>_<string:item>', methods=['GET', 'POST'])
def get_stuff(category, item):
    desspv=request.base_url[:-11]
    desspv=int(desspv[-4:])
    q=desspv-5007
    data = request.form
    if category not in ['put']:
        return 'Not a valid request', 400
    work_queue[q].put(((category, item), data))
    return 'Success!', 200       

def start_SPV(portnum):
    work_q = work_queue[portnum-5007]
    spvworker = SPVworker(work_q, portnum)
    werk = Thread(target=spvworker.work)
    werk.setDaemon(True)
    werk.start()
    app.run(port=portnum)
