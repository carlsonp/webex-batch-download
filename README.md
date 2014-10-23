webex-batch-download
====================

Batch download [Cisco Webex](http://www.webex.com/) sessions.  Developed for [ISU ELO](http://www.elo.iastate.edu/101/) use.
Tested on Linux and Mac.

### Setup

* Install [pip](https://pypi.python.org/pypi/pip) for Python.
   * `sudo easy_install pip`
* Install [Python Selenium](http://www.seleniumhq.org/) bindings ([unofficial documentation](http://selenium-python.readthedocs.org/)).
   * `sudo pip install -U selenium`
* Edit the `settings.py` file and enter the appropriate information.
* Open a terminal, `cd` (change directory) to the appropriate location, and start the download.
   * `python batch-download.py`
   * *Don't close the Firefox windows that open!*
* Navigate to the download folder.  Your files are sorted based on the WebExID.


### Notes

* Hard-coded 500 download limit per Webex user at the moment...

### License

* GPLv3 (see `license.txt`)
