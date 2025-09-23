import requests

with requests.get(
    "http://localhost:8000/scrape?url=https://nigeriapropertycentre.com/for-rent/flats-apartments/lagos",
    stream=True
) as r:
    for line in r.iter_lines():
        if line:
            print(line.decode())
