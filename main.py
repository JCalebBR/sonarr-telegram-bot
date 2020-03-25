import json
import sys
import time
from datetime import datetime

import requests
from docopt import docopt

doc="""Usage: 
    main.py [-s SERIES | -as SERIES] [-b] [-v | -vv | -vvv]
    main.py [-c SERIES | -dc SERIES] [-b] [-v | -vv | -vvv]
    main.py [-q] [-b] [-v | -vv | -vvv]

Options:
    -h --help                     Show this
    -s SERIES --search=SERIES     Search for a given series online
    -c SERIES --search-library    Search for a given series within your library
    -a --add                      Add a given series to your library
    -d --delete                   Delete a given series from your library
    -q --queue                    Check the download queue
    -v                            Level 1 debug messages [default: False]
    -vv                           Level 2 debug messages [default: False]
    -vvv                          Level 3 debug messages [default: False]
    -b --benchmark                Benchmark process time [default: False]
"""
with open("apikey.txt", "r") as f:
    APIKEY = f.readline()

default_headers = {
    "X-Api-Key" : APIKEY
}
json_headers = {
    "Content-Type":"application/json", 
    "X-Api-Key" : APIKEY
}
URL = "http://localhost:8989/api/"

def search_series(series=str, library=False):
    url = URL + "series/lookup"
    if VERBOSE_2:
        verbose(series, 2, "Search name: ")
    series = series.replace(" ", "%20")
    series = {"term" : series}

    req = requests.get(url, params=series, headers=default_headers)
    req = req.json()

    results = []
    
    for r in req:
        results.append(r["title"])
    
    for idx, i in enumerate(results):
        idx += 1
        print("{0}. {1}".format(idx, i))

    selection = int(input("Select best matched result: "))
    selection -= 1

    if library:
        tvdbId = int(req[selection]["tvdbId"])
        url = URL + "series"
        
        req = requests.get(url, headers=default_headers)
        req = req.json()

        for idx, series in enumerate(req):
            for info in series:
                if tvdbId == series[info]:
                    print("Series is present in your library")
                    seriesId = int(series["id"])
                    if VERBOSE_3:
                        verbose(seriesId, 3, "seriesId: ")
                    return seriesId
        print("Series is not present in your library")
        print("Exiting...")
        exit()
    else:
        return req, selection

def get_profiles():
    url = URL + "profile"

    req = requests.get(url, headers=default_headers)
    req = req.json()

    print("\nSelect from one of the available quality profiles: ")

    for idx, i in enumerate(req):
        idx += 1
        print("{0}. {1}". format(idx, i["name"]))

    profile = int(input("Selection: "))

    return profile

def add_series(series_data, selection=int):
    url = URL + "series"
    
    profile = get_profiles()

    invalid = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
    title = series_data[selection]["title"]

    for char in invalid:
        if char in title:
            title = title.replace(char, "")
            if VERBOSE:
                print("--- Invalid char {0}".format(char))
    
    data = {
        "tvdbId" : series_data[selection]["tvdbId"],
        "title" : series_data[selection]["title"],
        "profileId": profile,
        "titleSlug": series_data[selection]["titleSlug"],
        "images" : series_data[selection]["images"],
        "seasons": series_data[selection]["seasons"],
        "path": "E:\\Torrents\\Completos\\" + title,
        "addOptions" : {
            "ignoreEpisodesWithFiles": True,
            "ignoreEpisodesWithoutFiles": False,
            "searchForMissingEpisodes": False
        }
    }
    
    series_data = dict()
    series_data.update(data)
    series_data = json.dumps(series_data, indent=4)
    req = requests.post(url, data=series_data, headers=json_headers)
    status_code = req.status_code
    req = req.json()

    if VERBOSE_2:
        verbose(status_code, 2, "Status code: ")

    if status_code == 201:
        return print("The series has been added to your library")
    elif status_code == 400:
        return print("Error: {0}".format(req[0]["errorMessage"]))

def del_series(seriesId=int, deleteFiles=bool):
    url = URL + "series/"
    if deleteFiles:
        url += str(seriesId) + "?deleteFiles:" + "true"
    else:
        url += str(seriesId) + "?deleteFiles:" + "false"
    
    req = requests.delete(url, headers=default_headers)
    status_code = req.status_code
    req = req.json()

    if VERBOSE_2:
        verbose(status_code, 2, "Status code: ")

    if status_code == 200:
        return print("The series has been deleted from your library")
    else:
        return print("Error, status code: {0}".format(status_code))


    return json.dumps(req, indent=4)

def download_status():
    def check_size(size, precision=2):
        if size / pow(1024,2) < 1:
            return round(size / pow(1024, 1), precision), "KB"
        elif size / pow(1024,3) < 1:
            return round(size / pow(1024, 2), precision), "MB"
        elif size / pow(1024, 4) < 1:
            return round(size / pow(1024, 3), precision), "GB"
        elif size / pow(1024, 4) < 1:
            return round(size / pow(1024, 3), precision), "TB"
        else:
            return size, "B"
    
    url = URL + "queue"

    req = requests.get(url, headers=default_headers)
    req = req.json()

    for idx, s in enumerate(req):
        idx += 1
        series_title = s["series"]["title"]
        season = s["episode"]["seasonNumber"]
        episode = s["episode"]["episodeNumber"]
        title = s["episode"]["title"]
        quality = s["quality"]["quality"]["name"]
        
        size = s["size"]
        size_left = s["sizeleft"]
        current_size = size - size_left
        percentage = round(current_size / size * 100, 1)
        
        protocol = s["protocol"]
        
        size, u1 = check_size(size)
        current_size, u2 = check_size(current_size)
        
        decorator = "   |__"
        
        print("{0}. {1} S{2}E{3} {4} {5}".format(idx, series_title, season, episode, title, quality))
        print("{0}\t{1}% - {2}{3} of {4}{5} - {6}".format(decorator, percentage, current_size, u2, size, u1, protocol))
        
        if "Downloading" in s["status"]:
            time_left = s["timeleft"]
            import re
            x = re.findall("[0-9][^.]*", time_left)
            if ":" in x[0]:
                hours = x[0][0:2]
                minutes = x[0][3:5]
                seconds = x[0][6:8]
                print("{0}\tTime left: {1}h {2}m {3}s".format(decorator, hours, minutes, seconds))
            else:
                days = x[0]
                hours = x[1][0:2]
                minutes = x[1][3:5]
                seconds = x[1][6:8]
                print("{0}\tTime left: {1}d {2}h {3}m {4}s".format(decorator, days, hours, minutes, seconds))
        else:
            status = s["status"]
            print("--\t{0}".format(status))

def verbose(text, level=int, message=None):
    if message is None:
        if level == 1: return print("-> {0}".format(text))
        if level == 2: return print("--> {0}".format(text))
        if level == 3: return print("---> {0}".format(text))
    if message is not None:
        if level == 1: return print("-> {0} {1}".format(message, text))
        if level == 2: return print("--> {0} {1}".format(message, text))
        if level == 3: return print("---> {0} {1}".format(message, text))

if __name__ == "__main__":
    arguments = docopt(doc, argv=None, help=True, version=None, options_first=False)
    if arguments["--benchmark"]:
        t = time.process_time()
        BENCHMARK = True
    else: BENCHMARK = False

    if arguments["-v"] == 1:
        VERBOSE = True
    else: VERBOSE = False

    if arguments["-v"] == 2: 
        VERBOSE = True
        VERBOSE_2 = True
    else: VERBOSE_2 = False
    
    if arguments["-v"] == 3:
        VERBOSE = True
        VERBOSE_2 = True
        VERBOSE_3 = True
        verbose(arguments, 3)
    else: VERBOSE_3 = False
    
    if arguments["--queue"]: download_status()

    if arguments["--search"] is not None:
        series = arguments["--search"]
        search_json, selection = search_series(series)
        if arguments["--add"] is True:
            response = add_series(search_json, selection)
    
    if arguments["--search-library"] is not None:
        series = arguments["--search-library"]
        search = search_series(series, library=True)
        if arguments["--delete"] is True:
            response = del_series(search, True)

    if BENCHMARK:
        et = time.process_time_ns() - t
        print("\nProcessing time: {0:f}s".format(et/1000000000))
