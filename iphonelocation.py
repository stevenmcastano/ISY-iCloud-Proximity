#!/usr/bin/python
############################################################################################################
## LIBRARY IMPORT                                                                                          #
############################################################################################################
###Imports for logging
import logging
import signal
import traceback
import logging, sys, logging.handlers
from logging.handlers import SysLogHandler
import socket, os, time, datetime
import subprocess

try:
	import graypy
except:
	pass

### Database library
import peewee as pw

### iCloud imports:
try:
	from pyicloud import PyiCloudService
except:
	print "Startup: Failed to import the pyicloud library. Please make sure it's installed. You can try 'pip install pyicloud'."
	exit()
	
### Programatic stuff
import json, urllib2, xmltodict
from collections import OrderedDict

### For geofencing
try:
	from geopy.distance import vincenty
except:
	print "Startup: Failed to import the geopy library. Please make sure it's installed. You can try 'pip install geopy'."
	exit()
	
### For reading .ini files
from ConfigParser import SafeConfigParser

############################################################################################################
## LOGGING CONFIGURATION                                                                                   #
############################################################################################################
# Logging configuration load:
try:
	application_logging_name = 'iPhoneLocation'
	pid = os.getpid()
	print "Startup: PID={}".format(pid)
	f_out = open('/tmp/{}.pid'.format(application_logging_name), 'w', 0)
	f_out.write(str(pid))
	f_out.flush
	f_out.close
	print "Startup: Created pidfile at /tmp/{}.pid".format(application_logging_name)
	try:
		proc = subprocess.Popen(['git', 'describe'], stdout=subprocess.PIPE)
		service_version = proc.communicate()[0].strip()
	except:
		try:
			status_output, returncode = git('status')
			status_output_split = status_output.split('\n')
			local_git_branch = status_output_split[0].split()[2]
			service_version = local_git_branch
		except:
			service_version = 'vX.X'
	print "Startup: {} Version: {}".format(application_logging_name, service_version)
	print "Startup: Loading application logging settings."

	class ContextFilter(logging.Filter):
		hostname = socket.gethostname()

		def filter(self, record):
			record.hostname = ContextFilter.hostname
			record.timestamp = time.time()
			record.ec2app001_application_name = application_logging_name
			record.application_name = application_logging_name
			record.application_version = service_version
			record.error_level_name = record.levelname
			record.error_level_number = record.levelno
			record.application_runtime = record.msecs
			record.msg = '{} {}({})[{}]: {} - {}'.format(record.hostname, record.application_name, record.application_version, pid, record.levelname.ljust(8), record.msg)
			return True

	f = ContextFilter()

	if not os.path.exists('./conf/logging.conf') and not os.path.isdir('./conf/logging.conf'):
		print "Startup: logging.conf does not exist. Assuming production values."
		def loggingconfig():
			# Basic logging config
			global logger
			logger = logging.getLogger('{}'.format(application_logging_name))
			logger.addFilter(f)


			# check to see if the logs directory exists, if not, create it:
			if not os.path.exists('./logs') and not os.path.isdir('./logs'):
				os.makedirs('./logs')

			# create a file handler
			file_handler = logging.handlers.WatchedFileHandler('./logs/{}.log'.format(application_logging_name), mode='a')
			file_handler.setLevel(logging.DEBUG)

			#create a stream handler
			stream_handler = logging.StreamHandler(sys.stdout)
			stream_handler.setLevel(logging.INFO)
			
			try:
				#create a syslog handler via rabbitmq
				syslog_handler = graypy.GELFRabbitHandler('amqp://guest:guest@localhost/%2F', 'logging.gelf')
				syslog_handler.setLevel(logging.DEBUG)
			except:
				pass

			# create a logging format
			formatter = logging.Formatter('%(asctime)s - %(message)s')
			file_handler.setFormatter(formatter)

			class OneLineExceptionFormatter(logging.Formatter):
				def formatException(self, exc_info):
					result = super(OneLineExceptionFormatter, self).formatException(exc_info)
					return repr(result) # or format into one line however you want to

				def format(self, record):
					s = super(OneLineExceptionFormatter, self).format(record)
					if record.exc_text:
						s = s.replace('\n', '|')
						s = s.split('|')[0]
					return s

			formatter_custom_exc_info = OneLineExceptionFormatter('%(asctime)s - %(message)s')
			stream_handler.setFormatter(formatter_custom_exc_info)

			# Set the basic logging level for the entire app
			logger.setLevel(logging.DEBUG)

			# add the handlers to the logger
			logger.addHandler(file_handler)
			logger.addHandler(stream_handler)
			try:
				logger.addHandler(syslog_handler)
			except:
				pass
	else:
		print "Startup: logging.conf exists. Using that."
		execfile('./conf/logging.conf')
	loggingconfig()
	logger.info('INIT - Loaded logging settings, the application is starting.')
except:
	print "Startup: Failed to load logging settings, ABORTING!"
	print traceback.format_exc()
	sys.exit(1)
############################################################################################################
## CLASS DEFINITIONS                                                                                       #
############################################################################################################
#
#
############################################################################################################
## CONFIGURATION VARIABLES                                                                                 #
############################################################################################################
#
### Read configuratoin items:
try:
	### Check to see if config file exists:
	if os.path.isfile("./conf/iphonelocation.ini"):
		logger.debug('MAIN - iphonelocation.ini exists, continuing.')
	else:
		logger.error("MAIN - iphonelocation.ini does not exist or can't be read. Exiting!")
		exit()
	
	### Read database configuration:
	try:
		parser = SafeConfigParser()
		parser.read('./conf/iphonelocation.ini')
		### Grab the database connection settings:
		global db_conf
		db_conf = {}
		db_conf['name'] = parser.get('database', 'database')
		db_conf['host'] = parser.get('database', 'host')
		db_conf['port'] = int(parser.get('database', 'port'))
		db_conf['user'] = parser.get('database', 'user')
		db_conf['passwd'] = parser.get('database', 'passwd')
		logger.debug('MAIN - db_conf: {}'.format(db_conf))
	except:
		logger.error('MAIN - Error reading settings from iphonelocation.ini in your [database] section. You may need to start wiith a new .ini \
					 file by copying iphonelocation.ini.sample to iphonelocation.ini and moving all your setting over again. \
					 Exiting!', exc_info = True)
		exit()
	
	### Read ISY configuration:	
	try:
		### Grab the ISY connection settings:
		global isy_conf
		isy_conf = {}
		isy_conf['username'] = parser.get('ISY', 'username')
		isy_conf['password'] = parser.get('ISY', 'password')
		isy_conf['hostname'] = parser.get('ISY', 'hostname')
		isy_conf['port'] = int(parser.get('ISY', 'port'))
		isy_conf['SSL'] = parser.get('ISY', 'SSL')
		logger.debug('MAIN - isy_conf: {}'.format(isy_conf))
	except:
		logger.error('MAIN - Error reading settings from iphonelocation.ini in your [ISY] section. You may need to start wiith a new .ini \
					 file by copying iphonelocation.ini.sample to iphonelocation.ini and moving all your setting over again. \
					 Exiting!', exc_info = True)
		exit()

	### Read the iCloud configuration:
	try:
		### Grab the iCloud API authentication settings:
		global icloudapi_conf
		icloudapi_conf = {}
		icloudapi_conf['username'] = parser.get('iCloudAPI', 'username')
		icloudapi_conf['password'] = parser.get('iCloudAPI', 'password')
		logger.debug('MAIN - icloudapi_conf: {}'.format(icloudapi_conf))
	except:
		logger.error('MAIN - Error reading settings from iphonelocation.ini in your [iCloudAPI] section. You may need to start wiith a new .ini \
					 file by copying iphonelocation.ini.sample to iphonelocation.ini and moving all your setting over again. \
					 Exiting!', exc_info = True)
		exit()

	### Read the general program options:
	try:
		### Grab general options:
		global general_conf
		general_conf = {}
		general_conf['numberofdevices'] = int(parser.get('general', 'numberofdevices'))
		general_conf['cycle_sleep_default'] = float(parser.get('general', 'cycle_sleep_default'))
		general_conf['cycle_sleep_withradio'] = float(parser.get('general', 'cycle_sleep_withradio'))
		general_conf['cycle_sleep_distance'] = float(parser.get('general', 'cycle_sleep_distance'))
		general_conf['cycle_sleep_variable_distance'] = float(parser.get('general', 'cycle_sleep_variable_distance'))
		general_conf['cycle_sleep_variable_modifier_default'] = float(parser.get('general', 'cycle_sleep_variable_modifier_default'))
		general_conf['cycle_sleep_variable_modifier_inbound'] = float(parser.get('general', 'cycle_sleep_variable_modifier_inbound'))
		general_conf['isy_distance_precision'] = int(parser.get('general', 'isy_distance_precision'))
		general_conf['isy_distance_multiplier'] = int(parser.get('general', 'isy_distance_multiplier'))
		logger.debug('MAIN - general_conf: {}'.format(general_conf))
	except:
		logger.error('MAIN - Error reading settings from iphonelocation.ini in your [general] section. You may need to start wiith a new .ini \
					 file by copying iphonelocation.ini.sample to iphonelocation.ini and moving all your setting over again. \
					 Exiting!', exc_info = True)
		exit()
	try:
		### Grab the device settings:
		global device_conf
		device_conf = {}
		device_conf['name'] = parser.get('device', 'name')
		device_conf['shortname'] = parser.get('device', 'shortname')
		device_conf['WiFiCheck'] = parser.get('device', 'WiFiCheck')
		device_conf['BTCheck'] = parser.get('device', 'BTCheck')
		device_conf['ISYWifiVAR'] = parser.get('device', 'ISYWifiVAR')
		device_conf['ISYWifiVAR_Expected'] = int(parser.get('device', 'ISYWifiVAR_Expected'))
		device_conf['ISYBtVAR'] = parser.get('device', 'ISYBtVAR')
		device_conf['ISYBtVAR_Expected'] = int(parser.get('device', 'ISYBtVAR_Expected'))
		device_conf['ISYDistanceVAR'] = parser.get('device', 'ISYDistanceVAR')
		device_conf['iCloudGUID'] = parser.get('device', 'iCloudGUID')
		device_conf['location_home_lat'] = parser.get('device', 'location_home_lat')
		device_conf['location_home_long'] = parser.get('device', 'location_home_long')
		logger.debug('MAIN - device_conf: {}'.format(device_conf))
	except:
		logger.error('MAIN - Error reading settings from iphonelocation.ini in your [device] section. You may need to start wiith a new .ini \
					 file by copying iphonelocation.ini.sample to iphonelocation.ini and moving all your setting over again. \
					 Exiting!', exc_info = True)
		exit()
except:
	logger.error('MAIN - Error reading settings from iphonelocation.ini. You may need to start wiith a new .ini \
					 file by copying iphonelocation.ini.sample to iphonelocation.ini and moving all your setting over again. \
					 Exiting!', exc_info = True)
	exit()
### Connect to MySQL database for logging:
try:
	db = pw.MySQLDatabase(db_conf['name'], host=db_conf['host'], port=db_conf['port'], user=db_conf['user'], passwd=db_conf['passwd'])
except:
	logger.error('MAIN - Error connecting to your MySQL database. Please check your database configuration and/or MySQL server.', exc_info=True)
	exit()
#
############################################################################################################
## ENVIRONMENT SETUP                                                                                       #
############################################################################################################
#
### Create the iCloud api object:
global api
api = None
### Create a variable to store the last time the app contacts the iCloud API:
global api_last_used_time
api_last_used_time = None
#
### Create database with proper logging fields:
class MySQLModel(pw.Model):
    """A base model that will use our MySQL database"""
    class Meta:
        database = db

class location_log(MySQLModel):
	iCloud_timeStamp = pw.DateTimeField()
	App_timeStamp = pw.DateTimeField()
	App_data_age = pw.DoubleField()
	App_distance_home = pw.DoubleField()
	iCloud_latitude = pw.DoubleField()
	iCloud_longitude = pw.DoubleField()
	iCloud_horizontalAccuracy = pw.DoubleField()
	iCloud_positionType = pw.CharField()
	iCloud_locationType = pw.CharField()
	iCloud_locationFinished = pw.BooleanField()
	iCloud_isOld = pw.BooleanField()
	iCloud_isInaccurate = pw.BooleanField()
	App_ISYUpdated = pw.BooleanField()
	App_ISYUpdateValue = pw.DoubleField()
	App_SleepTime = pw.DoubleField()
	App_FailedAttempts = pw.DoubleField()
	App_LoopNumber = pw.DoubleField()
	
db.connect()
db.create_tables([location_log], True)
db.close()
#
#
#
############################################################################################################
## FUNCTION DEFINITIONS                                                                                    #
############################################################################################################
### Fuction that gets and sets ISY variable values:
def isy_variable(action, var_type, var_number, value):
	try:
		logger.debug("ISY_VARIABLE - Running...")
		# Set the ISY username:
		username = isy_conf['username']
		# Set the ISY password:
		password = isy_conf['password']
		# Creates the password manager that will be used to update the ISY:
		passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
		# Creates the authentication function to log in before passing the URL:
		authhandler = urllib2.HTTPBasicAuthHandler(passman)
		logger.debug("ISY_VARIABLE - Set the login parameters for the ISY.")
		
		if var_type == 'integer':
			var_type = 1
		elif var_type == 'state':
			var_type = 2
		else:
			logger.warn("ISY_VARIABLE - No valid variable type supplied, must be 'integer' or 'state'.")
			return 1
		
		logger.debug("ISY_VARIABLE - isy_conf['SSL']: {}".format(isy_conf['SSL']))
		
		if isy_conf['SSL'] == 'True':
			url_prefix = 'https'
		elif isy_conf['SSL'] == 'False':
			url_prefix = 'http'
		else:
			logger.warn('ISY_VARIABLE - Could not determine ISY SSL or NOT, assuming HTTP.')
			url_prefix = 'http'
		
		if action == 'get':
			theurl = '{}://{}:{}/rest/vars/{}/{}/{}'.format(url_prefix ,isy_conf['hostname'], isy_conf['port'], action, var_type, var_number)
		elif action == 'set':
			theurl = '{}://{}:{}/rest/vars/{}/{}/{}/{}'.format(url_prefix, isy_conf['hostname'], isy_conf['port'], action, var_type, var_number, value)
		else:
			logger.warn("ISY_VARIABLE - No valid variable action supplied, must be 'get' or 'set'.")
			return 1
		logger.debug('ISY_VARIABLE - The url being used to contact the ISY: {}'.format(theurl))
		# Combine the URL, username and password to be used for access:
		passman.add_password(None, theurl, username, password) #THIS MUST START WITH 'NONE'
		# Create the object to open the URL:
		opener = urllib2.build_opener(authhandler)
		# Set those credentials to be used as the default for all future API calls:
		urllib2.install_opener(opener)
		# Actually open the page to update the ISY:
		pagehandle = urllib2.urlopen(theurl)
		
		if action == 'get':
			#logger.debug("ISY_VARIABLE - pagehandle: {}".format(pagehandle))
			isy_data = pagehandle.read()
			isy_data = xmltodict.parse(isy_data)
			#logger.debug("ISY_VARIABLE - isy_data: {}".format(isy_data))
			#logger.debug("ISY_VARIABLE - isy_data json.jumps: {}".format(json.dumps(isy_data)))
			#logger.debug("ISY_VARIABLE - isy_data json.loads: {}".format( json.loads(json.dumps(isy_data)) ))
			
			isy_data = json.loads(json.dumps(isy_data))
			#logger.debug("ISY_VARIABLE - isy_data: {}".format(isy_data))
			
			isy_data = isy_data['var']
			#logger.debug("ISY_VARIABLE - isy_data: {}".format(isy_data))
			
			isy_data_varvalue = isy_data['val']
			logger.debug("ISY_VARIABLE - isy_data_varvalue: {}".format(isy_data_varvalue))
			
			logger.debug("ISY_VARIABLE - Completed")
			return 0, int(isy_data_varvalue)
		
		if action == 'set':
			#logger.debug("ISY_VARIABLE - pagehandle: {}".format(pagehandle))
			isy_data = pagehandle.read()
			isy_data = xmltodict.parse(isy_data)
			logger.debug("ISY_VARIABLE - isy_data: {}".format(isy_data))
			logger.debug("ISY_VARIABLE - isy_data json.jumps: {}".format(json.dumps(isy_data)))
			logger.debug("ISY_VARIABLE - isy_data json.loads: {}".format( json.loads(json.dumps(isy_data)) ))
			
			isy_data = json.loads(json.dumps(isy_data))
			logger.debug("ISY_VARIABLE - isy_data: {}".format(isy_data))
			
			
			isy_response_status = isy_data['RestResponse']['status']
			logger.debug("ISY_VARIABLE - isy_response_status: {}".format(isy_response_status))
			
			return 0, int(isy_response_status)
		
		logger.debug("ISY_VARIABLE - Completed")
		return 1, -1
	except:
		logger.debug("ISY_VARIABLE - Failed!", exc_info=True)
		return 1, -1
### Function to automatically restart the application if some unrecoverable error occurs:
def program_restart():
	logger.info('RESTART - Executing restart...')
	logger.debug('RESTART - Pause for 10 seconds to settle.')
	time.sleep(10)
	python = sys.executable
	os.execl(python, python, * sys.argv)
### Fuction to authenticate to the iCloud API:
def api_login():
	try:
		global api
		global api_last_used_time
		logger.debug('API_LOGIN - Clearing the current login data.')
		api = None
		logger.debug('API_LOGIN - Authenticatin to the iCloud API.')
		api = PyiCloudService(icloudapi_conf['username'], icloudapi_conf['password'])
		api_last_used_time = datetime.datetime.now()
		logger.debug('API_LOGIN - Sleep for 3 seconds to let login process.')
		time.sleep(3)
	except:
		logger.warn('API_LOGIN - Authentication to iCloud API failed.', exc_info=True)
	return
### Function to print the table header of data to the screen:
def print_table_header():
	### Print out an initial table heading:
	logger.info("|---------------------+-------+------------------+--------------+-----------------+-----------------+---------------+------------+-------+-------+-------+-------|")
	logger.info("| Timestamp           |DataAge| DistHome (miles) | ISY          | Latitude        | Longitude       | HorizAccuracy |PositionType|LocType|LocFin | isOld |isInacc|")
	logger.info("|---------------------+-------+------------------+--------------+-----------------+-----------------+---------------+------------+-------+-------+-------+-------|")
### Function to do radio checks for WiFi and Bluetooth:
def individual_radio_check(var, expected_value):
	try:
		logger.debug('INDIVIDUAL_RADIO_CHECK - Running ISY_VARIABLE function.')
		exit_code, returned_value = isy_variable('get', 'state', var, '')
		if exit_code == 0:
			logger.debug('INDIVIDUAL_RADIO_CHECK - ISY_VARIABLE function ran properly.')
			if returned_value == expected_value:
				logger.debug('INDIVIDUAL_RADIO_CHECK - The radio check was true, returning.')
				return 0, True
			elif returned_value != expected_value:
				logger.debug('INDIVIDUAL_RADIO_CHECK - The radio check was False, returning.')
				return 0, False
			if returned_value == expected_value:
				logger.warn('INDIVIDUAL_RADIO_CHECK - The radio check could not determine true or false, retuning with an error.')
				return 1, False
	except:
		logger.error('INDIVIDUAL_RADIO_CHECK - The radio check failed, returning with an error.', exc_info=True)
		return 1, False
### Function to do radio checks:
def radio_check():
	try:
		logger.debug('RADIO_CHECK - Running...')
		
		### Wifi checking:
		if device_conf['WiFiCheck'] == 'True':
			### Read the value of the wifi present variable:
			logger.debug('RADIO_CHECK - Checking to see if the iPhone is present on WiFi...')
			exit_code, iPhone_WiFi_Here = individual_radio_check(device_conf['ISYWifiVAR'], device_conf['ISYWifiVAR_Expected'])
			if exit_code == 0:
				logger.debug("RADIO_CHECK - iPhone_WiFi_Here: {}".format(iPhone_WiFi_Here))
			else:
				iPhone_WiFi_Here = False
				logger.debug("RADIO_CHECK - Reading WiFi value failed, using default value. iPhone_WiFi_Here: {}".format(iPhone_WiFi_Here))
		else:
			iPhone_WiFi_Here = False
			logger.debug('RADIO_CHECK - Script is not set to check for WiFi proximity, continuing...')

		### Bluetooth checking:
		if device_conf['BTCheck'] == 'True':
			### Read the value of the wifi present variable:
			logger.debug('RADIO_CHECK - Checking to see if the iPhone is present on Bluetooth...')
			exit_code, iPhone_BT_Here = individual_radio_check(device_conf['ISYBtVAR'], device_conf['ISYBtVAR_Expected'])
			if exit_code == 0:
				logger.debug("RADIO_CHECK - iPhone_BT_Here: {}".format(iPhone_BT_Here))
			else:
				iPhone_BT_Here = False
				logger.debug("RADIO_CHECK - Reading WiFi value failed, using default value. iPhone_BT_Here: {}".format(iPhone_BT_Here))
		else:
			iPhone_BT_Here = False
			logger.debug('RADIO_CHECK - Script is not set to check for Bluetooth proximity, continuing...')

		
		### Return radio status.
		if iPhone_WiFi_Here or iPhone_BT_Here:
			logger.debug('RADIO_CHECK - the iOS device is in radio range.')
			return True
		else:
			logger.debug('RADIO_CHECK - the iOS device is not in radio range.')
			return False
	except:
		logger.warn('RADIO_CHECK - Failed. Returning False.', exc_info=True)
		return False
############################################################################################################
## THREAD DEFINITIONS                                                                                      #
############################################################################################################
#
#
#############################################################################################################
## SCRIPT EXECUTION                                                                                         #
#############################################################################################################
#
### Set this interval to show this is the first time the loop is running:
interval = 1
### Print the table header
print_table_header()
### Initialize the distance to home to show that it's never been read or computed before:			
distance_home_previous = -1
### Initialize the number of attempts it's taken to read data from the api:
failed_attempts = 0
### Connect to the iCloud API:
api_login()
### Initialize the loop number:
loop_number = 0
### Init the distance home previous value:
distance_home_previous = -1
### Init the distance home delta value:
distance_home_delta = 0
### Run the main script loop:
while True:
	logger.debug('MAIN - Loop Number: {}'.format(loop_number))
	
	### Check to see if the device is in radio range:
	iPhone_RadioInRange = radio_check()

	### Run the rest of the loop only if the iPhone is out of radio range:
	if not iPhone_RadioInRange:
		logger.debug("MAIN - iPhone is not in radio range or WiFi and BT checking is disabled, checking GPS...")
			
		try:
			### Relogin if the last used time has been over 15 minutes:
			api_token_duration = (datetime.datetime.now() - api_last_used_time).total_seconds()
			if api_token_duration >= 300:
				logger.debug('MAIN - The current API token is {} seconds old, reauthenticating'.format(api_token_duration))
				api_login()
			else:
				logger.debug('MAIN - The current API token is {} seconds old, continuing'.format(api_token_duration))
				
			### Collection the iPhone devices location
			iPhone_Location = api.devices[device_conf['iCloudGUID']].location()
			### Set last used time:
			api_last_used_time = datetime.datetime.now()
			### Create a datetime object from the iCloud timeStamp
			iPhone_Location_Time = datetime.datetime.fromtimestamp(iPhone_Location['timeStamp']/1000)
		
			### Debug output of all info
			logger.debug("MAIN - iPhone Location (all): {}".format(iPhone_Location))
			
			### Create a variable with the lattitude and longitude of the "home" reference point
			location_home = (device_conf['location_home_lat'], device_conf['location_home_long'])
			
			### Create a variable with the lattitude and langitude of the iPhone's current position
			location_phone = (iPhone_Location['latitude'], iPhone_Location['longitude'])
			
			### Determine the distance in miles between the iPhone and "Home"
			distance_home = vincenty(location_home, location_phone).miles
			
			### Store the distance to home with precision
			if general_conf['isy_distance_precision'] == 0 and general_conf['isy_distance_multiplier'] == 0:
				logger.debug("MAIN - isy_distance_precision is 0, making the variable an integer.")
				distance_home_precision = int("{:.{}f}".format(distance_home, general_conf['isy_distance_precision']))
			elif general_conf['isy_distance_precision'] == 0 and general_conf['isy_distance_multiplier'] != 0:
				logger.debug("MAIN - isy_distance_precision is 0 but a multiplier is being used")
				distance_home_precision = int(distance_home * general_conf['isy_distance_multiplier'])
			elif general_conf['isy_distance_precision'] != 0 and general_conf['isy_distance_multiplier'] == 0:
				logger.debug("MAIN - isy_distance_precision is being used and the multiplier is 0")
				distance_home_precision = "{:.{}f}".format(distance_home, general_conf['isy_distance_precision'])
			else:
				logger.warn("MAIN - Both distance precision and multiplier are both set, at least one should be set to '0'")
				distance_home_precision = int(distance_home)
				
				
			
			### Determine the change in distance:
			distance_home_delta = distance_home - distance_home_previous
			logger.debug("MAIN - distance_home_delta: {}".format(distance_home_delta))
			
			### Debug output of the iphones location info and it's distance from home.
			logger.debug("MAIN - Location info - Lat: {}, Long: {} (Is Inaccurate: {}, Position Type: {}, Distance From Home: {} miles)".format(
				iPhone_Location['latitude'], iPhone_Location['longitude'], iPhone_Location['isInaccurate'],
				iPhone_Location['positionType'], distance_home))
			
			### Show time deltas:
			logger.debug("MAIN - API Timestamp: {}".format(iPhone_Location_Time))
			logger.debug("MAIN - App Timestamp: {}".format(api_last_used_time))
			data_age = (api_last_used_time - iPhone_Location_Time).total_seconds()
			logger.debug("MAIN - Data Age: {} seconds".format(data_age))
			
			### Set the distance to home display:
			#distance_home_display = "{:.{}f}".format(distance_home, general_conf['isy_distance_precision'])
			#distance_home_display = "{}".format(round(distance_home, general_conf['isy_distance_precision']))
			
			
			### Print a line of the table with all needed info regarding the location process
			logger.info("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
						str(iPhone_Location_Time).ljust(19),
						str(int(data_age)).ljust(5),
						str(distance_home).ljust(16),
						str(distance_home_precision).ljust(12),
						str(iPhone_Location['latitude']).ljust(15),
						str(iPhone_Location['longitude']).ljust(15),
						str(iPhone_Location['horizontalAccuracy']).ljust(13),
						str(iPhone_Location['positionType']).ljust(10),
						str(iPhone_Location['locationType']).ljust(5),
						str(iPhone_Location['locationFinished']).ljust(5),
						str(iPhone_Location['isOld']).ljust(5),
						str(iPhone_Location['isInaccurate']).ljust(5)
						))
			
			### Redisplay the table heading at a certain interval.
			if interval == 0:
				print_table_header()
				### Increase the interval showing we've printed out a line.
				interval = interval + 1
			else:
				### Skip printing the table output and increment the interval.
				interval = interval + 1
				logger.debug('MAIN - Table display interval: {}'.format(interval))
				if interval == 20:
					interval = 0
				else:
					pass
			
			### Check if the GPS data is current and the current distance home and see if it's different from the previous value:
			if not iPhone_Location['isOld']:
				logger.debug("MAIN - iPhone location data is current.")
			else:
				logger.debug("MAIN - iPhone location data is old.")
				
			if distance_home_previous == distance_home_precision:
				logger.debug("MAIN - The distance from home hasn't changed, moving on.")
				isy_updated = False
				pass
			else:
				logger.debug("MAIN - The distance from home has changed. It was {}, now it's {}, updating the ISY.".format(distance_home_previous, distance_home_precision))
				### Set the following ISY variable
				#isy_PX_Steve_Distance_From_Home.value = int(distance_home)
				exit_code, isy_status = isy_variable('set', 'state', device_conf['ISYDistanceVAR'], distance_home_precision)
				if exit_code != 0 or isy_status != 200:
					logger.warn("MAIN - Updating the ISY failed, will try again next loop.")
					isy_updated = False
				else:
					### Set the previous variable
					isy_updated = True
					logger.debug("MAIN - Recording the distance_home_previous variable.")
					distance_home_previous = distance_home_precision
			
			### Sleep between checking cycles
			# Default sleep time:
			sleep_time = general_conf['cycle_sleep_default']
			# If we're more than the minimum miles away, vary the sleep time based on distance.
			if distance_home > general_conf['cycle_sleep_distance']:
				### If the distance has change more than the sleep variable distance, check if the device is getting closer or farther away:
				if abs(distance_home_delta) > general_conf['cycle_sleep_variable_distance']:
					#logger.debug("MAIN - The distance to home has change by more then {} miles, using variable sleep distance. It is: {}".format(
						#general_conf['cycle_sleep_variable_distance', distance_home_delta]))
					### If the distance change is positive (getting farther away) use the default sleep time.
					if distance_home_delta > 0:
						logger.debug("MAIN - The distance to home delta is positive, we're getting farther away. Using {} as the sleep modifier.".format(
							general_conf['cycle_sleep_variable_modifier_default']))
						sleep_time = int((distance_home/general_conf['cycle_sleep_variable_modifier_default']) * general_conf['cycle_sleep_default'])
					### If the distance change is negative (getting closer) use the modified sleep time.
					elif distance_home_delta < 0:
						logger.debug("MAIN - The distance to home delta is negative, we're getting closer. Using {} as the sleep modifier.".format(
							general_conf['cycle_sleep_variable_modifier_inbound']))
						sleep_time = int((distance_home/general_conf['cycle_sleep_variable_modifier_inbound']) * general_conf['cycle_sleep_default'])
					### If we can't tell if we're moving closer or farther away, use the default sleep time.
					else:
						logger.warn("MAIN - The distance to home delta could determine is we're moving closer or farther away. Using {} as the sleep modifier.".format(
							ggeneral_conf['cycle_sleep_default']))
						sleep_time = general_conf['cycle_sleep_default']
				else:
					logger.debug("MAIN - We haven't moved more then {}. Using {} as the sleep modifier.".format(
							general_conf['cycle_sleep_variable_distance'], general_conf['cycle_sleep_variable_modifier_default']))
					sleep_time = int((distance_home/general_conf['cycle_sleep_variable_modifier_default']) * general_conf['cycle_sleep_default'])				
			else:
				### If we're not outside of the minimum distance, use the default sleep time.
				pass
			logger.debug("MAIN - Based on a distance_home of {}, we're sleeping for {} seconds.".format(distance_home, sleep_time))
			logger.debug("MAIN - Resetting failed_attempts to 0")
			failed_attempts = 0
			
			try:
			### Create dict to store data in database:
				db_entry = {
					'iCloud_timeStamp': iPhone_Location_Time,
					'App_timeStamp': api_last_used_time,
					'App_data_age': data_age,
					'App_distance_home': distance_home,
					'iCloud_latitude': iPhone_Location['latitude'],
					'iCloud_longitude': iPhone_Location['longitude'],
					'iCloud_horizontalAccuracy': iPhone_Location['horizontalAccuracy'],
					'iCloud_positionType': iPhone_Location['positionType'],
					'iCloud_locationType': str(iPhone_Location['locationType']),
					'iCloud_locationFinished': iPhone_Location['locationFinished'],
					'iCloud_isOld': iPhone_Location['isOld'],
					'iCloud_isInaccurate': iPhone_Location['isInaccurate'],
					'App_ISYUpdated': isy_updated,
					'App_ISYUpdateValue': distance_home_precision,
					'App_SleepTime': int(sleep_time),
					'App_FailedAttempts': failed_attempts,
					'App_LoopNumber': loop_number
					}
				db.connect()
				location_log.create(**db_entry)
				db.close()
			except:
				logger.warn('MAIN - DB entry failed.', exc_info = True)

			### Reset the number of failed attempts after one works:
			failed_attempts = 0	
			time.sleep(int(sleep_time))
			
		except:
			failed_attempts = failed_attempts + 1
			if failed_attempts < 4:
				logger.warn("MAIN - Reading the iCloud iPhone location from API failed! Sleeping for 30 seconds.", exc_info=True)
				time.sleep(30)
				### Reconnect to iCloud service:
				api_login()
			else:
				logger.error("MAIN - Reading the iCloud iPhone location from API failed! Max failed attempts reached, restarting the application.", exc_info=True)
				program_restart()	
	else:
		logger.debug("MAIN - iPhone_RadioInRange is {}, sleeping for {} seconds.".format(
			iPhone_RadioInRange, general_conf['cycle_sleep_withradio']))
		time.sleep(general_conf['cycle_sleep_withradio'])

	### Increase the loop number showing how many times the checking cycle has run:
	loop_number = loop_number + 1
	###### END OF THE WHILE LOOP ######

logger.info('MAIN - Removing pidfile: /var/run/{}.pid'.format(application_logging_name))
os.remove('/tmp/{}.pid'.format(application_logging_name))
logger.info('MAIN - Exiting.')
