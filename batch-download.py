#batch-download.py

import os, sys
import settings #settings.py
import util		#util.py


#create download directory if it doesn't exist
if not os.path.exists(settings.DOWNLOAD_FOLDER):
	os.makedirs(settings.DOWNLOAD_FOLDER)

#check to make sure download folder is empty
if not util.folderEmpty(settings.DOWNLOAD_FOLDER):
	print "Error: The download folder is not empty: ", settings.DOWNLOAD_FOLDER
	sys.exit(1)

print "******************************************"
print "Don't close the Firefox window that opens."
print "******************************************"

counter = 0
total_dl = 0
total_skipped = 0
for WebExID in settings.WEBEX_IDS:
	print "Percent done: %.2f %%" % float(float(counter)/float(len(settings.WEBEX_IDS)) * 100)
	userid = util.getUserID(WebExID, settings.PASSWORD)
	print "Starting download for: ", WebExID
	downloaded, skipped = util.downloadRecording(WebExID, settings.PASSWORD)
	print "Downloaded: ", downloaded
	print "Skipped: ", skipped
	total_dl += downloaded
	total_skipped += skipped
	counter += 1

print "Finished batch downloading."

print "Total stats breakdown:"
print "Total Downloads: ", total_dl
print "Total Skipped: ", total_skipped
print "Downloaded files are here: ", settings.DOWNLOAD_FOLDER
