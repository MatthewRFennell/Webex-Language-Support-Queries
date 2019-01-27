from google.cloud import texttospeech
from google.cloud.texttospeech import enums

client = texttospeech.TextToSpeechClient()

text = ""
name = "en-GB-Wavenet-A"

input_text = texttospeech.types.SynthesisInput(text=text)

# Note: the voice can also be specified by name.
# Names of voices can be retrieved with client.list_voices().
voice = texttospeech.types.VoiceSelectionParams(name=name, language_code="en-GB")

audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3)

response = client.synthesize_speech(input_text, voice, audio_config)

# The response's audio_content is binary.
with open('output.mp3', 'wb') as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')

'''
voices = client.list_voices()

file = open("voices.csv", "w+")

languages = []

def shortcode_exists(shortcode):
    global languages
    for lang in languages:
        if lang.startswith(shortcode):
            return True
    return False


for voice in voices.voices:
    shortcode = voice.name.partition("-")[0]
    if not shortcode_exists(shortcode):
        line=shortcode + "," + voice.name + "," + voice.language_codes[0] + ","
        ssml_gender = enums.SsmlVoiceGender(voice.ssml_gender)
        # Display the SSML Voice Gender
        line += ssml_gender.name + "\n"
        languages.append(line)
        file.write(line)
'''