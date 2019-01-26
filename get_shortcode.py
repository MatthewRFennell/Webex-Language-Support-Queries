import csv
def get_shortcode_of(language):
	with open('languages.csv', mode='r') as csvFile:
		reader = csv.reader(csvFile)
		for row in reader:
			if language == row[0]:
				return row[1]
