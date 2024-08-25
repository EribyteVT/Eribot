import requests

class EncryptDecryptWrapper:
    def __init__(self,env,password):
        self.env = env
        if(env == "PROD"):
            self.urlBase = 'http://10.96.46.46:5000'

        elif(env == "LOCAL"):
            self.urlBase = 'http://127.0.0.1:5000'
            
        elif(env == "DEV"):
            self.urlBase = 'http://10.0.0.6:5000'

        elif (env == "K8S_TEST_DEPLOY"):
            self.urlBase = "http://10.96.46.46:5000"

        else:
            raise Exception("ERROR, ENV NOT SET")
        
        self.encrypt_password = password

    def decrypt(self,crypt,salt):
        data = {"encrypted":crypt,"salt":salt,"password":self.encrypt_password}
        response = requests.post(self.urlBase+"/decrypt",json=data)
        
        return response.json()