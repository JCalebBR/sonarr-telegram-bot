import requests
import json

#curl --request GET "localhost:8989/api/series/lookup?term=The%20Blacklist&apikey=YOURAPIKEY"

apikey = "f28f978931c54f3fbbed7471cb457297"
kind = ["search"]
series = "The Blacklist"
#headers = {"Content-Type":"application/json", "X-Api-Key": apikey}
headers = {"X-Api-Key": apikey}
series = series.replace(" ", "%20")

payload = {
    "term" : series
}
'''
payload = {
    "id" : 109610
}
'''
#payload = json.dumps(payload)

url = "http://localhost:8989/api/series/lookup"
print(payload)
#r = requests.post(url, data=payload, headers=headers)
r = requests.get(url, params=payload, headers=headers)
for i in r.json():
    print("Title: {0}".format(i['title']))
    print("\tSeasons: {0}".format(i['seasonCount']))
    print("\tStatus: {0}".format(i['status']))
    print("\tYear: {0}".format(i['year']))
    print("\tTVDB ID: {0}".format(i['tvdbId']))
