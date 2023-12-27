import requests 
from math import floor
import time
import random 
import datetime
import re 
import pytz 

class CrudWrapper:
    def __init__(self,env):
        self.env = env
        if(env == "PROD"):
            self.urlBase = 'http://10.0.0.6:8080'

        elif(env == "LOCAL"):
            self.urlBase = 'http://127.0.0.1:8080'
            
        elif(env == "DEV"):
            self.urlBase = 'https://crud.eribyte.net'

        else:
            raise Exception("ERROR, ENV NOT SET")
    def getLevelFromXp(self,xp):
        """
        THE 2 FUNCTIONS FOR XP:
        0-50: 0.04x^3 + 0.8x^2 + 2x
        50+: 400(x-32.25)
        """
        #we have 2 different functions for xp, rollover xp is second function
        rollover_xp=0

        #split into 2 diff xp graphs
        if(xp>7100):
            rollover_xp = xp-7100
            xp=7100
        
        highestLevel = 0

        for i in range(51):
            xp_for_i = .04 * (i**3) + .8 * (i**2) + 2*i
            if xp >= xp_for_i:
                highestLevel = i

        level = highestLevel

        #always rollover, it's either 0 or something
        level += floor((rollover_xp)//400)

        return level

    def getConnectedAccounts(self,id):
        url = self.urlBase + '/getConnections/'+str(id)
        data = requests.get(url)

        #return new discord account
        if(data.text is None or data.text ==""):
            return None
        else:
            json = data.json()
            return json
        
    def getConnectedAccountsTwitch(self,id):
        url = self.urlBase + '/getTwitchConnections/{twitchId}/'+str(id)
        data = requests.get(url)

        #return new discord account
        if(data.text is None or data.text ==""):
            return None
        else:
            json = data.json()
            return json
    
    def getUserTotalXP(self,accounts):
        xp = 0

        did_discord = False
        
        for account in accounts:
            if(not did_discord):
               xp += self.getDataFromDiscordId(account['serviceId'])['xp']
               did_discord = True 

            match(account['serviceName']):
                case "twitch":
                    xp += self.getDataFromTwitchdId(account['serviceId'])['xp']
                case "youtube":
                    xp += self.getDataFromYoutubeId(account['serviceId'])['xp']
                case _:
                    raise Exception("SHIT'S FUCKED, NOT IMPLEMENTED YET")
            
        return xp

        
    def getXpFromAccounts(self,accounts):
        data_list = []
        
        for account in accounts:
            match(account['serviceName']):
                case "twitch":
                    account_xp = self.getDataFromTwitchdId(account['serviceId'])
                case "youtube":
                    account_xp = self.getDataFromYoutubeId(account['serviceId'])
                case _:
                    raise Exception("SHIT'S FUCKED, NOT IMPLEMENTED YET")
            
            data_list.append(account_xp)
        
        return data_list

    ############## ADD SERVICE TO DISCORD ACCOUNT #########################################

    def addTwitchToDiscord(self,discord_id, twitch_id):
        #data for update
        data = {"discordId":discord_id,"serviceId":twitch_id}

        #data to send update to
        url = self.urlBase + '/addConnectionDiscord/twitch'

        #send request
        request = requests.post(url,json=data)

        return request

    def addYoutubeToDiscord(self,discord_id, youtube_id):
        data = {"discordId":discord_id,"serviceId":youtube_id}

        #data to send update to
        url = self.urlBase + '/addConnectionDiscord/youtube'

        #send request
        request = requests.post(url,json=data)

        return request

    #################### CHECK SERVICE CONNECTED ##########################################

    #True if connected, false if not
    def twitchConnected(self,id):
        url = self.urlBase + '/getConnections/twitch/'+str(id)

        #get data
        data = requests.get(url)

        if(data.text is None or data.text ==""):
            return False
        else:
            return True
        
    def youtubeConnected(self,id):
        url = self.urlBase + '/getConnections/youtube/'+str(id)

        #get data
        data = requests.get(url)

        if(data.text is None or data.text ==""):
            return False
        else:
            return True


    ################# GET DATA FROM SERVICE ####################################################

    def getDataFromDiscordId(self,id):
        #ALSO ADDS USER BTW FUTURE ERIBYTE
        url = self.urlBase + '/getbyId/discord/'+str(id)

        #get data
        data = requests.get(url)

        #if none, add user
        if(data.text is None or data.text ==""):
            data = self.addXpbyDiscordId(0,id,False)
        else:
            data = data.json()


        #return the data
        return data

    def getDataFromTwitchdId(self,id):
        #ALSO ADDS USER BTW FUTURE ERIBYTE
        url = self.urlBase + '/getbyId/twitch/'+str(id)

        #get data
        data = requests.get(url)

        if(data.text is None or data.text ==""):
            return  self.addXpbyTwitchId(0,id,False)
        else:
            return data.json()  

    def getDataFromYoutubeId(self,id):
        #ALSO ADDS USER BTW FUTURE ERIBYTE
        url = self.urlBase + '/getbyId/youtube/'+str(id)

        #get data
        data = requests.get(url)

        if(data.text is None or data.text ==""):
            return self.addXpbyYoutubeId(0,id,False)
        else:
            return data.json()


    ######################### GET ASSOCIATED #######################################################
        
    def getAssociatedFromTwitch(self,id):
        url = self.urlBase + '/GetAllAccountsAssociated/twitch/'+str(id)

        #get data
        data = requests.get(url)

        #if none, add user
        if(data.text is None or data.text ==""):
            data = [self.addXpbyTwitchId(0,id,False)]
        else:
            data = data.json()


        #return the data
        return data
    
    def getAssociatedFromDiscord(self,id):
        url = self.urlBase + '/GetAllAccountsAssociated/discord/'+str(id)

        #get data
        data = requests.get(url)

        #if none, add user
        if(data.text is None or data.text ==""):
            data = [self.addXpbyDiscordId(0,id,False)]
        else:
            data = data.json()


        #return the data
        return data


    ################ ADD XP #######################################################

    def addXpbyDiscordId(self,xp,id,update):
        #get current time in okay enough format
        currentTime = str(time.time())[:-4]
        currentTime = ''.join(currentTime.split('.'))

        if(len(currentTime)==12):
            currentTime+='0'
        
        #data for update
        data = {"id":id,"xp":xp,"updateTime":update,"newTime":currentTime}

        #data to send update to
        url = self.urlBase + '/update/discord'

        #send request
        request = requests.post(url,json=data).json() 

        return request

    def addXpbyTwitchId(self,xp,id,update):
        #get current time in okay enough format
        currentTime = str(time.time())[:-4]
        currentTime = ''.join(currentTime.split('.'))

        if(len(currentTime)==12):
            currentTime+='0'
        
        #data for update
        data = {"id":id,"xp":xp,"updateTime":update,"newTime":currentTime}

        #data to send update to
        url = self.urlBase + '/update/twitch'

        #send request
        request = requests.post(url,json=data).json() 

        return request

    def addXpbyYoutubeId(self,xp,id,update):
        #get current time in okay enough format
        currentTime = str(time.time())[:-4]
        currentTime = ''.join(currentTime.split('.'))

        if(len(currentTime)==12):
            currentTime+='0'
        
        #data for update
        data = {"id":id,"xp":xp,"updateTime":update,"newTime":currentTime}

        #data to send update to
        url = self.urlBase + '/update/youtube'

        #send request
        request = requests.post(url,json=data).json() 

        return request

    def enoughTime(self,lastTime):
        #get current time
        currentTime = str(time.time())[:-4]
        currentTime = ''.join(currentTime.split('.'))

        if(len(currentTime)<13):
            currentTime = currentTime.ljust(13,'0')
        
        #how we tell if enough time has passed (a random 7-17 mins)
        bodgeTime = (12 + random.randint(-5,5))*60000 

        #real complicated logic to convert dates (man I fuckin hate dates)
        lastTime = datetime.datetime.timestamp(parse_timestamp(lastTime[:-5]))*1000

        #if it's been 7-17 minutes past the last update, update
        if(int(currentTime) > int(lastTime)+bodgeTime):
            return True 
        
        return False
    
def parse_timestamp(timestamp):
    return datetime.datetime(*[int(x) for x in re.findall(r'\d+', timestamp)],tzinfo=pytz.utc)