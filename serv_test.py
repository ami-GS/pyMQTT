from server import Broker
import sys

port = 8888
if len(sys.argv) == 2:
    port = int(sys.argv[1])

broker = Broker("127.0.0.1", port)
broker.runServer()
