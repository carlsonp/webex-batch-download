import urllib2, os, sys, math
from time import sleep
from xml.dom import minidom
from datetime import datetime, timedelta
from dateutil import parser
from selenium import webdriver #this is used to interface with Firefox
import settings #settings.py

#https://developer.cisco.com/media/webex-xml-api/25GlobalRequestElementsinSecurityContext.html

#https://developer.cisco.com/media/webex-xml-api/Preface.html


def getUserID(WebExID, password):
	#https://developer.cisco.com/media/webex-xml-api/38GetUser.html
	reqXML = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n";
	reqXML += "<serv:message xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">";
	reqXML += "<header>\r\n";
	reqXML += "<securityContext>\r\n";
	reqXML += "<webExID>" + WebExID + "</webExID>\r\n";
	reqXML += "<password>" + password + "</password>\r\n";
	reqXML += "<siteID>" + settings.SITEID + "</siteID>\r\n";
	reqXML += "</securityContext>\r\n";
	reqXML += "</header>\r\n";
	reqXML += "<body>\r\n";
	reqXML += "<bodyContent xsi:type=\"java:com.webex.service.binding.user.GetUser\">";
	reqXML += "<webExId>" + WebExID + "</webExId>\r\n";
	reqXML += "</bodyContent>\r\n";
	reqXML += "</body>\r\n";
	reqXML += "</serv:message>\r\n";

	req = urllib2.Request(settings.XML_SERVER_URL, reqXML)

	try:
		response = urllib2.urlopen(req)
		xmldoc = minidom.parseString(response.read())
		collection = xmldoc.documentElement
	
		return collection.getElementsByTagName("use:userId")[0].firstChild.nodeValue
	except urllib2.URLError, e:
		print "URL connection error: ", e.reason, ": are you connected to the Internet?"
		sys.exit(1)
	except Exception:
		print "Generic error in urlopen()."
		sys.exit(1)

def downloadRecording(WebExID, password):
	#https://developer.cisco.com/media/webex-xml-api/48LstRecording.html
	reqXML = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n";
	reqXML += "<serv:message xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">";
	reqXML += "<header>\r\n";
	reqXML += "<securityContext>\r\n";
	reqXML += "<webExID>" + WebExID + "</webExID>\r\n";
	reqXML += "<password>" + password + "</password>\r\n";
	reqXML += "<siteID>" + settings.SITEID + "</siteID>\r\n";
	reqXML += "</securityContext>\r\n";
	reqXML += "</header>\r\n";
	reqXML += "<body>\r\n";
	reqXML += "<bodyContent xsi:type=\"java:com.webex.service.binding.ep.LstRecording\">";
	reqXML += "<listControl>";
	reqXML += "<startFrom>0</startFrom>";
	reqXML += "<maximumNum>500</maximumNum>"; #TODO: this is currently hardcoded, could be an issue later
	reqXML += "</listControl>";
	reqXML += "<returnSessionDetails>true</returnSessionDetails>";
	reqXML += "<serviceTypes>";
	reqXML += "<serviceType>TrainingCenter</serviceType>";
	reqXML += "</serviceTypes>";
	reqXML += "</bodyContent>\r\n";
	reqXML += "</body>\r\n";
	reqXML += "</serv:message>\r\n";

	req = urllib2.Request(settings.XML_SERVER_URL, reqXML)

	try:
		response = urllib2.urlopen(req)
		xmldoc = minidom.parseString(response.read())
		collection = xmldoc.documentElement
	except urllib2.URLError, e:
		print "URL connection error: ", e.reason, ": are you connected to the Internet?"
		sys.exit(1)
	except Exception:
		print "Generic error in urlopen()."
		sys.exit(1)

	#keep some stats to return
	downloaded = 0
	skipped = 0
	deleted = 0

	for node in collection.getElementsByTagName("ep:recording"):
		#convert creation time to Python datetime object type
		creationdate = parser.parse(str(node.getElementsByTagName("ep:createTime")[0].firstChild.nodeValue))
		#only grab recordings that are X days old based on the user setting
		if creationdate < (datetime.now() - timedelta(days=settings.SESSION_LIMIT)):
			classname = node.getElementsByTagName("ep:name")[0].firstChild.nodeValue
			downloadURL = node.getElementsByTagName("ep:fileURL")[0].firstChild.nodeValue

			#create sub-folder if it doesn't exist
			download_dir = os.path.join(settings.DOWNLOAD_FOLDER, WebExID)
			if not os.path.exists(download_dir):
				os.makedirs(download_dir)

			#for some reason we have to re-setup a profile every single time Firefox is launched, otherwise
			#it throws Errno 2 for user.js
			profile = webdriver.FirefoxProfile()
			profile.set_preference("browser.download.folderList", 2) #0=desktop, 1=default download folder, 2=user specified
			profile.set_preference("browser.download.manager.showWhenStarting", False)
			profile.set_preference("browser.helperApps.alwaysAsk.force", False)
			profile.set_preference("pdfjs.disabled", True)
			profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/bin;application/arf;application/octet-stream;")
			#not sure why all these settings are needed but otherwise it just downloads to the home directory...
			#https://stackoverflow.com/questions/18521636/selenium-dosent-set-downloaddir-in-firefoxprofile
			profile.set_preference("browser.download.downloadDir", download_dir)
			profile.set_preference("browser.download.dir", download_dir)
			profile.set_preference("browser.download.defaultFolder", download_dir)

			driver = webdriver.Firefox(firefox_profile=profile)

			driver.get(downloadURL)

			#wait until the browser has processed all the javascript and loading stuff
			#TODO: hopefully the download has started, this is really hacky... is there a better way?
			sleep(25) #25 seconds

			download_done = False
			while(not download_done):
				filenames = os.listdir(download_dir)
				part_file_exists = False
				for filename in filenames:
					if os.path.isfile(os.path.join(download_dir, filename)) and filename.endswith(".part"):
						part_file_exists = True

				if part_file_exists:
					sleep(1) #1 second
				else:
					download_done = True

			#.quit() closes browser window and safely ends session
			#.close() close browser window
			driver.quit() #quit Firefox and close down profile
			
			#check reported file size from XML against our download
			xml_size = float(node.getElementsByTagName("ep:size")[0].firstChild.nodeValue)
			filename = node.getElementsByTagName("ep:name")[0].firstChild.nodeValue
			downloaded_size = getFileSizeMB(os.path.join(settings.DOWNLOAD_FOLDER, WebExID, filename+".arf"))
			#run a small check, as long as we're within 5 MB of the file size we're good
			if abs(downloaded_size - xml_size) > 5:
				print "Error: Downloaded file size for: ", filename, " does not match the reported value."
				sys.exit(1)

			if settings.DELETE_SESSIONS or settings.DELETE_SESSIONS in ["true", "True"]:
				#delete the session off the WebEx server
				deleteRecording(WebExID, password, node.getElementsByTagName("ep:recordingID")[0].firstChild.nodeValue)
				deleted += 1

			downloaded += 1
		else:
			skipped += 1

	return downloaded, skipped, deleted

def folderEmpty(folder):
	#determines if the folder is empty or not
	if len(os.listdir(folder)) > 0:
		#this check is needed because Mac defaults to having a .DS_Store hidden file in the folder
		empty = True
		for item in os.listdir(folder):
			if not item.startswith(".") or not os.path.isfile(os.path.join(folder, item)):
				empty = False
	else:
		empty = True

	return empty

def getFileSizeMB(file):
	return float(os.path.getsize(file) / 1024) / 1024

def deleteRecording(WebExID, password, recordingID):
	#https://developer.cisco.com/media/webex-xml-api/43DelRecording.html
	reqXML = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n";
	reqXML += "<serv:message xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">";
	reqXML += "<header>\r\n";
	reqXML += "<securityContext>\r\n";
	reqXML += "<webExID>" + WebExID + "</webExID>\r\n";
	reqXML += "<password>" + password + "</password>\r\n";
	reqXML += "<siteID>" + settings.SITEID + "</siteID>\r\n";
	reqXML += "</securityContext>\r\n";
	reqXML += "</header>\r\n";
	reqXML += "<body>\r\n";
	reqXML += "<bodyContent xsi:type=\"java:com.webex.service.binding.ep.DelRecording\">";
	reqXML += "<recordingID>" + recordingID + "</recordingID>";
	reqXML += "<isServiceRecording>true</isServiceRecording>\r\n"; #this is very important and not in the documentation example
	reqXML += "</bodyContent>\r\n";
	reqXML += "</body>\r\n";
	reqXML += "</serv:message>\r\n";

	req = urllib2.Request(settings.XML_SERVER_URL, reqXML)

	try:
		response = urllib2.urlopen(req)
		xmldoc = minidom.parseString(response.read())
		collection = xmldoc.documentElement

		if collection.getElementsByTagName("serv:result")[0].firstChild.nodeValue != "SUCCESS":
			print "ERROR: Error deleting: ", recordingID, ", the server did not send SUCCESS back."
			sys.exit(1)
	except urllib2.URLError, e:
		print "URL connection error: ", e.reason, ": are you connected to the Internet?"
		sys.exit(1)
	except Exception:
		print "Generic error in urlopen()."
		sys.exit(1)
