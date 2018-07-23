import pika
import json
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')
data = {"bot":"cci", "text":"Something interesting"}
#dict_ = {"416552809": ['ccc', 'macd'], "383166779": [], "114871797": []}
message = json.dumps(data)
channel.basic_publish(exchange='',routing_key='hello',body=message)
print(" [x] Sent 'Hello World!'")
connection.close()
