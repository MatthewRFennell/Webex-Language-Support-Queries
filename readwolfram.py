import urllib, json
appId = "Q54GYL-GWV59LL2VT"
inputValueString = "&i="

def ask(query):
	baseUrl = "http://api.wolframalpha.com/v1/conversation.jsp?appid="
	url = baseUrl + appId + inputValueString + query
	print(url)
	return readResult(url)

def askContinuingConvo(convoId, query):
	baseUrl = "http://www4b.wolframalpha.com/api/v1/conversation.jsp?appid="
	convoIdString = "&conversationid="
	url = baseUrl + appId + convoIdString + convoId + inputValueString + query
	return readResult(url)

def readResult(url):
	response = urllib.urlopen(url)
	data = json.loads(response.read())
	print(data)
	convoId = data[data.keys()[0]]
	result = data[data.keys()[2]]
	return convoId, result
