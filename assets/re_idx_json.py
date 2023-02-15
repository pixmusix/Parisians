import json
import os

filename = 'FrenchName_Database.json'
with open(filename, 'r') as f:
    data = json.load(f)
    for e, wd in enumerate(data):
        wd['id'] = e

with open(f"re-dex_{filename}", 'w') as f:
    json.dump(data, f, indent=4)