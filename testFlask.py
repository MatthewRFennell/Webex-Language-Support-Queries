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
import readwolfram
from summa import summarizer
from pprint import pprint

# Instantiates google API clients
translate_client = translate.Client()
voice_client = texttospeech.TextToSpeechClient()

#Initialise empty directories of people to custom languages
roomFollows = {}

# Initialise empty dictionary of room id to language
roomLanguages = {}
# Room id to words to not be translated
roomFilters = {}
roomVoices = {}

roomWolfram = {}
wolframConvos = {}

# Create the webook API data
teams_api = WebexTeamsAPI(access_token="MjA0NTMyNTMtYzM2NS00NmVhLTkzNjQtNGE0ZjNmY2MxZWVkZWMwMjJlMDMtODZm_PF84_consumer")
flask_app = Flask(__name__)

@flask_app.route('/teamswebhook', methods=['POST'])
def teamsWebHook():
    global roomFollows
    global roomLanguages
    global roomFilters
    global roomVoices
    format="text"
    json_data = request.json

    # Pass the JSON data so that it can get parsed by the Webhook class
    webhook_obj = Webhook(json_data)

    # Obtain information about the request data such as room, message, the person it came from 
    # and person's email address. 
    room = teams_api.rooms.get(webhook_obj.data.roomId)
    message = teams_api.messages.get(webhook_obj.data.id)
    person = teams_api.people.get(message.personId)
    email = person.emails[0]
    group = room.type == "group"

    if room.id not in roomLanguages:
        roomLanguages[room.id] = ["en", "English"]
        roomFilters[room.id] = []
        roomFollows[room.id] = {}
        roomVoices[room.id] = True
        roomWolfram[room.id] = True

    has_translation = False
    has_voice = False
    new_follow = False
    text = message.text
    if text:
        # Message was sent by the bot, do not respond.
        # At the moment there is no way to filter this out, there will be in the future
        me = teams_api.people.me()
        print(u"Message sent by {} of type {} from room {}.\n Content is {}".format(person.displayName, room.type, room.id, text))
        if message.personId == me.id:
            return 'OK'
        else:
            #Start the translation process
            ascii = text.encode('ascii', 'ignore')
            lower = ascii.lower()
            output = ""
            if lower.startswith("!setlanguage"):
                #Attempt to set the language
                newLang = ascii.split()
                if len(newLang) > 1:
                    confidence, detectedLang, shortcode = get_shortcode_of(newLang[1])
                    if confidence == 100:
                        roomLanguages[room.id] = [shortcode, detectedLang]
                        output = "Language set to {}".format(newLang[1])
                    elif confidence > 70:
                        roomLanguages[room.id] = [shortcode, detectedLang]
                        output = "Language set to {} (Auto-recognised with confidence level {})".format(detectedLang, confidence)
                    else:
                        output = "We did not understand {}, did you mean {}?".format(newLang[1], detectedLang)
                else:
                    output = "No language was provided for !setlanguage"
            elif lower.startswith("!notranslate"):
                #Add word to ignored list
                words = ""
                for word in lower.split():
                    if word != "!notranslate" and word not in noTranslate:
                        roomFilters[room.id].append(word)
                output = "The following words are now not translated: {}".format(roomFilters[room.id])
            elif lower.startswith("!dotranslate"):
                words = ""
                for word in lower.split():
                    if word != "!notranslate" and word in roomFilters[room.id]:
                        roomFilters[room.id].remove(word)
                output = "The following words are now not translated: {}".format(roomFilters[room.id])
            elif lower.startswith("!help"):
                output = "The following commands are valid:\n"
                output += "!help - List this help command\n"
                output += "!notranslate word1 word2 .. - Do not translate these words\n"
                output += "!dotranslate word1 word2 .. - Remove these words from the no translate list\n"
                output += "!setlanguage language - Set the translation target to the language. Minor spelling errors are corrected automatically\n"
                output += "!follow language - Follow a group chat in a specific language (excludes your messages).\n"
                output += "!voice - Allow attaching of voice pronounciation for supported languages.\n"
                output += "!novoice - Disable attaching of voice pronounciation for supported languages.\n"
                output += "!nowolfram - Disable attempted parsing of messages by wolfram API"
                output += "!wolfram - Enable attempted parsing of messages by wolfram API"
            elif lower.startswith("!follow"):
                if not group:
                    output = "You cannot follow a direct chat!"
                else:
                    newLang = ascii.split()
                    if len(newLang) > 1:
                        confidence, detectedLang, shortcode = get_shortcode_of(newLang[1])
                        if confidence == 100:
                            roomFollows[room.id][message.personId] = [shortcode, detectedLang]
                            output = "{} is now following {} in {}".format(person.displayName, room.title,newLang[1])
                            new_follow = True
                        elif confidence > 70:
                            roomFollows[room.id][message.personId] = [shortcode, detectedLang]
                            output = "{} is now following {} in {} (Auto-recognised with confidence level {})".format(person.displayName, room.title,newLang[1], confidence)
                            new_follow = True
                        else:
                            output = "We did not understand {}, did you mean {}?".format(newLang[1], detectedLang)
                        print(output + " in room " + room.title)
                        print(roomFollows[room.id])
                    else:
                        output = "No language was provided for !follow"
            elif lower.startswith("!voice"):
                if roomVoices[room.id]:
                    output = "Voice attachments are already enabled!"
                else:
                    roomVoices[room.id] = True
                    output = "Voice attachments are enabled for supported languages."
            elif lower.startswith("!novoice"):
                if not roomVoices[room.id]:
                    output = "Voice attachments are already disabled!"
                else:
                    roomVoices[room.id] = False
                    output = "Voice attachments are disabled for this room"
            elif lower.startswith("!wolfram"):
                if roomWolfram[room.id]:
                    output = "Wolfram parsing is already enabled!"
                else:
                    roomWolfram[room.id] = True
                    output = "Wolfram parsing is enabled for supported languages."
            elif lower.startswith("!nowolfram"):
                if not roomWolfram[room.id]:
                    output = "Wolfram parsing is already disabled!"
                else:
                    roomWolfram[room.id] = False
                    output = "Wolfram parsing is disabled for this room"
            elif lower.startswith("!summarize"):
                msgs = list(teams_api.messages.list(room.id))
                string = []
                for msg in msgs:
                    if type(msg.text) is unicode:
                        string.append(msg.text)
                stringstring = '\n'.join(string)
                text = summarizer.summarize(stringstring, ratio=0.02)
                text = summarizer.summarize(stringstring, ratio=0.02)
                text = summarizer.summarize(stringstring, ratio=0.02)
                text = summarizer.summarize(stringstring, ratio=0.02)
                teams_api.messages.create(room.id, text=text)
                print(text)
            else:
                #Translate normally
                result = translate_client.detect_language(text)
                language = result['language']
                target = roomLanguages[room.id][0]
                fullTarget = roomLanguages[room.id][1]
                print("Detected is " + language)
                print("Target is " + target)
                print("Confidence {}".format(result['confidence']))
                has_result = False
                if roomWolfram[room.id]:
                    wolfram_result = ""
                    english = ""
                    attempt_again =  language != "en" and language != "und" and result['confidence'] > 0.7
                    if attempt_again:
                        english = translate_client.translate(text, "en", format_="text")['translatedText']
                    if message.personId not in wolframConvos:
                        wolfram_result = readwolfram.ask(text)
                        if "result" in wolfram_result:
                            has_result = True
                            wolframConvos[message.personId] = wolfram_result
                        elif attempt_again:
                            wolfram_result = readwolfram.ask(english)
                            if "result" in wolfram_result:
                                has_result = True
                                wolframConvos[message.personId] = wolfram_result
                    else:
                        wolfram_result = readwolfram.askContinuingConvo(text, wolframConvos[message.personId])
                        if "result" not in wolfram_result:
                            del wolframConvos[message.personId]
                            # Try again
                            wolfram_result = readwolfram.ask(text)
                            if "result" in wolfram_result:
                                has_result = True
                                wolframConvos[message.personId] = wolfram_result
                            elif attempt_again:
                                wolfram_result = readwolfram.ask(english)
                                if "result" in wolfram_result:
                                    has_result = True
                                    wolframConvos[message.personId] = wolfram_result
                        else:
                            # Refresh the answer
                            wolframConvos[message.personId] = wolfram_result
                            has_result = True
                    print(wolfram_result)
                    if has_result:
                        if attempt_again:
                            back_translated = translate_client.translate(wolframConvos[message.personId]["result"], language, format_="text")['translatedText']
                            teams_api.messages.create(room.id, text=u"Wolfram Alpha suggests the following:\n{}\nOriginal:({})".format( back_translated, wolframConvos[message.personId]["result"]))
                        else:
                            teams_api.messages.create(room.id, text=u"Wolfram Alpha suggests the following:\n{}".format(wolframConvos[message.personId]["result"]))
                if language != "und" and result['confidence'] > 0.7:
                    has_translation = True
                elif not has_result:
                    output = u"Sorry, could not recognise the language of {} with enough certainty. Maybe it is too short?".format(text)
                if language != target and has_translation:
                    print(u"Language of {} detected as {} with confidence {}".format(text, result['language'], result['confidence']))
                    input = ""
                    for word in text.split():
                        if word.lower() in roomFilters[room.id]:
                            input += "<span translate=\"no\">"+word+"</span> "
                            format="html"
                        else:
                            input += word + " "
                    output = translate_client.translate(input, target, format_=format)['translatedText']
                    if format == "html":
                        regex = re.compile("<span translate ?= ?\"no\"> ?(\w+) ?<\/ ?span>")
                        output = regex.sub("\\1", output)
                    if roomVoices[room.id] and get_voice_of(target):
                        #Get the voice file
                        voice_lang, voice_type, voice_gender = get_voice_of(target)
                        voice_input = texttospeech.types.SynthesisInput(text=output)
                        voice = texttospeech.types.VoiceSelectionParams(language_code=voice_lang,name=voice_type)
                        audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3)
                        response = voice_client.synthesize_speech(voice_input, voice, audio_config)
                        # The response's audio_content is binary.
                        with open('output.mp3', 'wb') as out:
                            out.write(response.audio_content)
                        has_voice=True
                    output = u"{}'s message in {} is {}".format(person.displayName, fullTarget, output) 
            print(output)
            if output != "":
                teams_api.messages.create(room.id, text=output)
            if has_voice:
                #Attach the voice file
                teams_api.messages.create(room.id, text="Language is compatible, play file for speech output", files=["output.mp3"])
            if has_translation:
            # Now notify the followers
                print(roomFollows[room.id])
                for key, value in roomFollows[room.id].iteritems():
                    format = "text"
                    if language != value[0] and message.personId != key:
                        target = value[0]
                        input = ""
                        for word in text.split():
                            if word.lower() in roomFilters[room.id]:
                                input += "<span translate=\"no\">"+word+"</span> "
                                format="html"
                            else:
                                input += word + " "
                        output = translate_client.translate(input, target, format_=format)['translatedText']
                        if format == "html":
                            regex = re.compile("<span translate ?= ?\"no\"> ?(\w+) ?<\/ ?span>")
                            output = regex.sub("\\1", output)
                        # Write to user here
                        output = u"{}'s message from {} in {} is {}".format(person.displayName, room.title, fullTarget, output)
                        teams_api.messages.create(toPersonId=key, text=output)
                        print("Message should be sent here")
                        if roomVoices[room.id] and get_voice_of(target):
                            #Get the voice file
                            voice_lang, voice_type, voice_gender = get_voice_of(target)
                            voice_input = texttospeech.types.SynthesisInput(text=output)
                            voice = texttospeech.types.VoiceSelectionParams(language_code=voice_lang,name=voice_type)
                            audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3)
                            response = voice_client.synthesize_speech(voice_input, voice, audio_config)
                            # The response's audio_content is binary.
                            with open('output.mp3', 'wb') as out:
                                out.write(response.audio_content)
                            #Attach the voice file
                            teams_api.messages.create(toPersonId=key, text="Language is compatible, play file for speech output", files=["output.mp3"])                            
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
        "event": "created"}
#        "filter": "roomId=Y2lzY29zcGFyazovL3VzL1JPT00vODNlNDAzOTAtMjE2Ni0xMWU5LWJmNTYtYTlhY2I2NTU0Y2Ji"}

hdr = {"Authorization": "Bearer MjA0NTMyNTMtYzM2NS00NmVhLTkzNjQtNGE0ZjNmY2MxZWVkZWMwMjJlMDMtODZm_PF84_consumer"}

print(data)

r = requests.post("https://api.ciscospark.com/v1/webhooks",
              data=data, headers=hdr)

if r.status_code != 200:
    print("Failed to create webhook")
    quit()

#teams_api.messages.create("Y2lzY29zcGFyazovL3VzL1JPT00vODNlNDAzOTAtMjE2Ni0xMWU5LWJmNTYtYTlhY2I2NTU0Y2Ji", text="Started up translating bot. Default language: English")
flask_app.run(host='0.0.0.0', port=5005)
