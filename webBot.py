import urllib2
import httplib
import json



roomId = "Y2lzY29zcGFyazovL3VzL1JPT00vODNlNDAzOTAtMjE2Ni0xMWU5LWJmNTYtYTlhY2I2NTU0Y2Ji"
url = "https://api.ciscospark.com/v1/messages"
hdr = {
    "Authorization": "Bearer MmViOWRjNDMtZDM4MC00OWQ4LWE3ZGQtNDExZDQ2NjA0YjU4Zjc5MTU3NDYtMGM3_PF84_consumer"
}
url += ("?roomId=" + roomId)
req = urllib2.Request(url, headers=hdr)
response = urllib2.urlopen(req)
webContent = response.read()
cont = json.loads(webContent)

for msg in cont["items"]:
    if "text" in msg:
        txt = msg["text"]
        if len(txt) < 100:
            print(txt)