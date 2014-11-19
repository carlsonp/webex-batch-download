#settings.py

XML_SERVER_URL = "https://yourhost.webex.com/WBXService/XMLService"
SITEID = "123456"
PASSWORD = "secret"
WEBEX_IDS = ["webex1", "webex2"]
DOWNLOAD_FOLDER = "/home/username/Desktop/webexdownloads/"
#don't download sessions less than X days old, set to 0 to download all
SESSION_LIMIT = 7 #default is one week
#this will delete the sessions after downloading them
#possible values: True or False
#***Be Extremely Careful With This Setting!!!***
DELETE_SESSIONS = False
