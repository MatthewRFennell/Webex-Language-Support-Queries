import urllib, json
appId = "Q54GYL-GWV59LL2VT"
inputValueString = "&i="

def ask(query):
	baseUrl = "http://api.wolframalpha.com/v1/conversation.jsp?appid="
	url = baseUrl + appId + inputValueString + query.encode('utf-8')
	return readResult(url)

def askContinuingConvo(query, data):
	if "result" in data:
		baseUrl = "http://" + data["host"]
		baseUrl += "/api/v1/conversation.jsp?appid="
		convoIdString = "&conversationid="
		url = baseUrl + appId + convoIdString + data["conversationID"] + inputValueString + query.encode('utf-8')
		return readResult(url)

def readResult(url):
	response = urllib.urlopen(url)
	data = json.loads(response.read())
	print(data)
	return data
