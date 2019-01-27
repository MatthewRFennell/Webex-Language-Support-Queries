import urllib2
import httplib
import re
import json
import requests
import time
import os
from get_shortcode import get_shortcode_of
from get_voices import get_voice_of
from google.cloud import translate, texttospeech
from flask import Flask, request
from webexteamssdk import WebexTeamsAPI, Webhook
from helpers.spark_helper import (find_webhook_by_name,
                     delete_webhook, create_webhook)
import re

# Instantiates a client
translate_client = translate.Client()
voice_client = texttospeech.TextToSpeechClient()
noTranslate=[]
target='en'
fullTarget='English'
teams_api = WebexTeamsAPI(access_token="MmViOWRjNDMtZDM4MC00OWQ4LWE3ZGQtNDExZDQ2NjA0YjU4Zjc5MTU3NDYtMGM3_PF84_consumer")
flask_app = Flask(__name__)

@flask_app.route('/teamswebhook', methods=['POST'])
def teamsWebHook():
    global target
    global fullTarget
    global noTranslate
    format="text"
    print("Got a request")
    json_data = request.json

    # Pass the JSON data so that it can get parsed by the Webhook class
    webhook_obj = Webhook(json_data)

    # Obtain information about the request data such as room, message, the person it came from 
    # and person's email address. 
    room = teams_api.rooms.get(webhook_obj.data.roomId)
    message = teams_api.messages.get(webhook_obj.data.id)
    person = teams_api.people.get(message.personId)
    email = person.emails[0]

    has_voice = False
    text = message.text
    if text:
        # Message was sent by the bot, do not respond.
        # At the moment there is no way to filter this out, there will be in the future
        me = teams_api.people.me()
        print(me.id)
        print(message.personId)
        if message.personId == me.id:
            return 'OK'
        else:
            #Start the translation process
            ascii = text.encode('ascii', 'ignore')
            lower = ascii.lower()

            if lower.startswith("!setlanguage"):
                #Attempt to set the language
                newLang = ascii.split()
                if len(newLang) > 1:
                    confidence, detectedLang, shortcode = get_shortcode_of(newLang[1])
                    if confidence == 100:
                        target = shortcode
                        fullTarget = detectedLang
                        output = "Language set to {}".format(newLang[1])
                        print(output)
                    elif confidence > 70:
                        target = shortcode
                        fullTarget = detectedLang
                        output = "Language set to {} (Auto-recognised with confidence level {})".format(detectedLang, confidence)
                        print(output)
                    else:
                        output = "We did not understand {}, did you mean {}?".format(newLang[1], detectedLang)
                        print(output)
            elif lower.startswith("!notranslate"):
                #Add word to ignored list
                words = ""
                for word in lower.split():
                    if word != "!notranslate" and word not in noTranslate:
                        noTranslate.append(word)
                output = "The following words are now not translated: {}".format(noTranslate)
            elif lower.startswith("!dotranslate"):
                words = ""
                for word in lower.split():
                    if word != "!notranslate" and word in noTranslate:
                        noTranslate.remove(word)
                output = "The following words are now not translated: {}".format(noTranslate)
            else:
                #Translate normally
                result = translate_client.detect_language(text)
                language = result['language']
                if language != target and language != "und" and result['confidence'] > 0.7:
                    print(u"Language of {} detected as {} with confidence {}".format(text, result['language'], result['confidence']))
                    input = ""
                    for word in text.split():
                        if word.lower() in noTranslate:
                            input += "<span translate=\"no\">"+word+"</span> "
                            format="html"
                        else:
                            input += word + " "
                    output = translate_client.translate(input, target, format_=format)['translatedText']
                    if format == "html":
                        regex = re.compile("<span translate ?= ?\"no\"> ?(\w+) ?<\/ ?span>")
                        output = regex.sub("\\1", output)
                    if get_voice_of(target):
                        #Get the voice file
                        voice_lang, voice_type, voice_gender = get_voice_of(target)
                        voice_input = texttospeech.types.SynthesisInput(text=output)
                        voice = texttospeech.types.VoiceSelectionParams(language_code=voice_lang,name=voice_type)
                        audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3)
                        response = voice_client.synthesize_speech(voice_input, voice, audio_config)
                        # The response's audio_content is binary.
                        with open('output.mp3', 'wb') as out:
                            out.write(response.audio_content)
                            print('Audio content written to file "output.mp3"')
                        has_voice=True
                    output = u"{}'s message in {} is {}".format(person.displayName, fullTarget, output)

                else:
                    output = "Sorry, the sentence was not recognised as a language"
            print(output)
            teams_api.messages.create(room.id, text=output)
            if has_voice:
                #Attach the voice file
                teams_api.messages.create(room.id, text="Language is compatible, play file for speech output", files=["output.mp3"])
    return 'OK'


def get_ngrok_url():
    os.system("curl http://localhost:4040/api/tunnels > tunnels.json 2> /dev/null")


    with open('tunnels.json') as data_file:
        datajson = json.load(data_file)

    return datajson['tunnels'][0]['public_url']

os.system("ngrok http 5005 > /dev/null &")

time.sleep(2)

url = get_ngrok_url()

# Define the name of webhook
webhook_name = "New messages in ICHack room"

# Find any existing webhooks with this name and if this already exists then delete it
dev_webhook = find_webhook_by_name(teams_api, webhook_name)
if dev_webhook:
    delete_webhook(teams_api, dev_webhook)

data = {"name": webhook_name,
        "targetUrl": url + "/teamswebhook",
        "resource": "messages",
        "event": "created", "filter":
        "roomId=Y2lzY29zcGFyazovL3VzL1JPT00vODNlNDAzOTAtMjE2Ni0xMWU5LWJmNTYtYTlhY2I2NTU0Y2Ji"}

hdr = {"Authorization": "Bearer YmQ1OTY0MDgtNmE1My00NzA2LWI2MDEtNWNjNjYxNDU3M2M4OWRiM2ExM2MtZjg2_PF84_consumer"}

print(data)

r = requests.post("https://api.ciscospark.com/v1/webhooks",
              data=data, headers=hdr)

if r.status_code != 200:
    print("Failed to create webhook")
    quit()

teams_api.messages.create("Y2lzY29zcGFyazovL3VzL1JPT00vODNlNDAzOTAtMjE2Ni0xMWU5LWJmNTYtYTlhY2I2NTU0Y2Ji", text="Started up translating bot. Default language: English")
flask_app.run(host='0.0.0.0', port=5005)
