import urllib2
import httplib
import json
from get_shortcode import get_shortcode_of
from google.cloud import translate

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

# Instantiates a client
translate_client = translate.Client()
target = 'en'
messages=[]
toTranslate=[]
noTranslate=[]
output=[]
result=[]

for msg in cont["items"]:
    if "text" in msg:
        txt = msg["text"]
        if len(txt) < 100:
          messages.append(txt)

for msg in messages:
    ascii = msg.encode('ascii', 'ignore')
    if ascii.startswith("!setLanguage"):
        #Attempt to set the language
        newLang = ascii.split()
        detectedLang = get_shortcode_of(newLang[1])
        if len(newLang) > 1 and :
            target = get_shortcode_of(newLang[1])
    elif ascii.startswith("!noTranslate"):
        #Add word to ignored list
        for word in ascii.split():
            if word != "!noTranslate":
                noTranslate.append(word)
    else:
        toTranslate.append(msg)

for msg in toTranslate:
    result = translate_client.detect_language(msg)
    language = result['language']
    if language != target and language != "und" and result['confidence'] > 0.7:
        print(u"Language of {} detected as {} with confidence {}".format(msg, result['language'], result['confidence']))
        input = ""
        for word in msg.split():
            if word in noTranslate:
                input += "<span translate=\"no\">"+word+"</span>"
            else:
                input += word
        output.append(input)

if len(output) > 0:
    result = translate_client.translate(output, target)

if len(result) > 0:
    for translation in result:
        print(translation['translatedText'])