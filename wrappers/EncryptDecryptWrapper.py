import requests

class EncryptDecryptWrapper:
    def __init__(self,urlBase,password):
        self.urlBase = urlBase
        
        self.encrypt_password = password

    def decrypt(self,crypt,salt):
        data = {"encrypted":crypt,"salt":salt,"password":self.encrypt_password}
        response = requests.post(self.urlBase+"/decrypt",json=data)
        
        return response.json()