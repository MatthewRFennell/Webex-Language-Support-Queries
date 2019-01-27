import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import operator

# Returns true if the find was an exact match, false if it tried to find the neares
def get_shortcode_of(language):
	with open('languages.csv', mode='r') as csvFile:
		reader = csv.reader(csvFile)
		fuzzy = {}
		for row in reader:
			fuzzy[row[0]] = fuzz.ratio(row[0].lower(), language.lower())
			if language.lower() == row[0].lower():
				return 100, row[0], row[1]
		# At this point we haven't found an exact match
		lan = max(fuzzy.items(), key=operator.itemgetter(1))
		return max(fuzzy.values()), lan[0], shortcode(lan[0])

def shortcode(full):
	with open('languages.csv', mode='r') as csvFile:
		reader = csv.reader(csvFile)
		for row in reader:
			if full == row[0]:
				return row[1]