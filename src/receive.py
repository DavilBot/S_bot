import pika
import json
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')
def callback(ch, method, properties, body):
    data = json.loads(body)
    print(data["name"])
    print(data["age"])
    print(data["city"])
channel.basic_consume(callback, queue = 'hello', no_ack =True)
print('[*] Waiting for messages. To exit press CRTL + C')
channel.start_consuming()
