#!/usr/bin/python
############################################################################################################
## LIBRARY IMPORT                                                                                          #
############################################################################################################
### For reading .ini files
from ConfigParser import SafeConfigParser
### iCloud imports:
from pyicloud import PyiCloudService
### For reading .ini files
from ConfigParser import SafeConfigParser
### Other stuff:
import os, time, traceback, json
############################################################################################################
## CONFIGURATION VARIABLES                                                                                 #
############################################################################################################
#
### Check to see if config file exists:
if os.path.isfile("../conf/iphonelocation.ini"):
	print 'iphonelocation.ini exists, continuing.'
else:
	print '''iphonelocation.ini does not exist or can't be read. Exiting!'''
	exit()
### Read configuratoin items:
try:
	parser = SafeConfigParser()
	parser.read('../conf/iphonelocation.ini')
	### Grab the iCloud API authentication settings:
	global icloudapi_conf
	icloudapi_conf = {}
	icloudapi_conf['username'] = parser.get('iCloudAPI', 'username')
	icloudapi_conf['password'] = parser.get('iCloudAPI', 'password')
except:
	print 'Reading settings from iphonelocation.ini failed. Exiting!'
	traceback.print_exc()
	exit()
	
############################################################################################################
## ENVIRONMENT SETUP                                                                                       #
############################################################################################################
#
### Create the iCloud api object:
global api
api = None
#
############################################################################################################
## FUNCTION DEFINITIONS                                                                                    #
############################################################################################################
#
def api_login():
	try:
		global api
		global api_last_used_time
		#logger.debug('API_LOGIN - Clearing the current login data.')
		api = None
		print 'Authenticatin to the iCloud API.'
		api = PyiCloudService(icloudapi_conf['username'], icloudapi_conf['password'])
		#api_last_used_time = datetime.datetime.now()
		#logger.debug('API_LOGIN - Sleep for 3 seconds to let login process.')
		time.sleep(3)
	except:
		#logger.warn('API_LOGIN - Authentication to iCloud API failed.', exc_info=True)
		print 'Logging into the iCloud API failed.'
		traceback.print_exc()
	return
#
def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )
#
def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data
#############################################################################################################
## SCRIPT EXECUTION                                                                                         #
#############################################################################################################
#
### Authenticate to the API:
api_login()
### Get the device data via json:
device_string = str(api.devices)
device_string = device_string.replace(",", "\n")
device_string = device_string.replace("{", "")
device_string = device_string.replace("}", "")
print 'Devices:\n {}'.format(device_string)











