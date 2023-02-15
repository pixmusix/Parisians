from bs4 import BeautifulSoup
import requests
import json

URL = r"https://en.wiktionary.org/wiki/Appendix:French_given_names"
page = requests.get(URL)
soup = BeautifulSoup(page.text, 'html.parser')

french_names = [x.text for x in soup.find_all('dd')]

data = []
for idx, name in enumerate(french_names):
	agent = {"id" : idx, "name" : name}
	data.append(agent)

with open("FrenchName_Database.json", "w") as db:
	json.dump(data, db)