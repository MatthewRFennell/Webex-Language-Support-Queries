import csv

def get_voice_of(shortcode):
	with open('voices.csv', mode='r') as csvFile:
		reader = csv.reader(csvFile)
		for row in reader:
			if shortcode == row[0]:
				return row[2], row[1], row[3]