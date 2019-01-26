import urllib2
import httplib
import os
from flask import Flask, request
import re
import json
import requests


flask_app = Flask(__name__)

@flask_app.route('/teamswebhook', methods=['POST'])
def teamsWebHook():
    print("Got a request")

    #ALL CODE GOES HERE
    return 'OK'


def get_ngrok_url():
    os.system("curl  http://localhost:4040/api/tunnels > tunnels.json 2> /dev/null")


    with open('tunnels.json') as data_file:
        datajson = json.load(data_file)
    
    msg = "ngrok URL's: \n"
    for i in datajson['tunnels']:
        msg = msg + i['public_url'] + '\n'

    print(datajson['tunnels'][0]['public_url'])
    return datajson['tunnels'][0]['public_url']

#os.system("ngrok http 5005 $> /dev/null &")

#print("Ngrok started")

url = get_ngrok_url()

data = {"name": "New messages in ICHack room",
        "targetUrl": url,
        "resource": "messages",
        "event": "created", "filter":
        "roomId=Y2lzY29zcGFyazovL3VzL1JPT00vODNlNDAzOTAtMjE2Ni0xMWU5LWJmNTYtYTlhY2I2NTU0Y2Ji"}

hdr = {"Authorization": "Bearer MmViOWRjNDMtZDM4MC00OWQ4LWE3ZGQtNDExZDQ2NjA0YjU4Zjc5MTU3NDYtMGM3_PF84_consumer"}

print(data)

r = requests.post("https://api.ciscospark.com/v1/webhooks",
              data=data, headers=hdr)

if r.status_code != 200:
    print("Failed to create webhook")
    quit()

flask_app.run(host='0.0.0.0', port=5005)
