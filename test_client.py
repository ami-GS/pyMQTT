from client import Client
import time
import sys

port = 8888
if len(sys.argv) == 2:
    port = int(sys.argv[1])

client = Client(("lite.mqtt.shiguredo.jp", 1883), "ID")
client.connect("Account@github", "PASSWORD", {"QoS":1, "topic":"Account@github/will", "message":"dead"}, 0)
client.publish("Account@github/test2", "message!!", qos = 0, retain = 1)
client.subscribe([["Account@github/test1", 2], ["Account@github/will", 0]], messageID = 10)
client.subscribe([["Account@github/test2", 0]], messageID = 11)
client.unsubscribe(["Account@github/test1"])
time.sleep(10)
client.disconnect()
