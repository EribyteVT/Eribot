import requests

urlBase = 'http://127.0.0.1:8080'





#data for update
data = {"timestamp":"1717944540","streamName":"TEST","description":"Nuh uh"}

#data to send update to
url = urlBase + '/AddStream'

#send request
request = requests.post(url,json=data).text

print(request)

