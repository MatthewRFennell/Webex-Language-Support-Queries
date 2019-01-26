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
			fuzzy[row[0]] = fuzz.ratio(row[0], language)
			if language == row[0]:
				return true, row[1]
		# At this point we haven't found an exact match
		return false, max(fuzzy.items(), key=operator.itemgetter(1))[0]