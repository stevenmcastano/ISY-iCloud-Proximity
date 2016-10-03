# ISY-iCloud-Proximity

<h4>Current Build Status:</h4>
Master:<br>
![Build Status Graphic](https://travis-ci.org/stevenmcastano/ISY-iCloud-Proximity.svg?branch=master "current build status")<br>
Dev:<br>
![Build Status Graphic](https://travis-ci.org/stevenmcastano/ISY-iCloud-Proximity.svg?branch=dev "current build status")<br>

<h4>Overview:</h4>
This python script reads your iOS device location from iCloud, calculates your distance to home and store that distance as a variable in a unviersal devices ISY contoller.

<h4>Basic Application Flow:</h4>
The script first reads all of it's configuration data from a file in the `conf` directory called `iphonelocation.ini`. It then make a connection to the MySQL database you've specified and creates the proper location data table if it doesn't already exist.

With the setting specified in the above mentioned .ini file, the script logs into the iCloud API and using your devices unique Apple assigned identifier reads it's current GPS coordinates. It then uses the lattitude and longitude of your home location to calculate the distance in miles between your home and your iOS device which is then displays on the screen in a table showing all your relevant information.

It then repeats this process in a loop. If the calculated distance is different from the previous loop, it sets a variable on the ISY to the distance in miles. <i>(*Note: Right now, the distance is truncated to 0 decimal places. Mean 1.145680 miles is reported to the ISY as 1 mile, and 1.958293 miles is ALSO reported as 1 mile. I can update this to rounding to the nearest mile is anyone feels it's important.)</i>

Sleep time variation: The script will check your iCloud GPS location once per minute, but this does have an effect on battery life. So after the script sees that you are move than 5 miles away it switches it's sleep time. Once you're more than 5 miles away the script sleeps for half the number of minutes as you are miles away. So if you are 20 miles from home, the script sleeps for 10 minutes and as your move closer or farther away from home, the script sleep time gets shorter of longer respectively.

<h4>Advanced Features:</h4>
Currently, the script has the ability to check variables on the ISY that you can use to keep track of whether or not a device is present on your WiFi network or can be seen by a Bluetooth radio. In this case, if your phone is on your home WiFi, or is within range of a Bluetooth beacon in your home, the script knows you (your iOS device) is home and it doesn't check your GPS signal at all, instead the loop sleeps for 5 minutes before checking to see if your phone is still on WiFi and/or in range of the Bluetooth beacon. If it is NOT, the script begins to check it's GPS position again exactly as decribed above.

<h4>Roadmap:</h4>
<br>Everything on my original plan/roadmap has been covered for the most part. There isn't much left:
1) Investigate checking battery level and suspend checking more than once per hour if it falls below a configurable threshold.

# Dependancies / Installation
You will need the following installed:<br>
1) Python 2.7<br>
2) Pythong Pip<br>
3) MySQL or equivilant (I use MariaDB)<BR>

# Usage
1) Install the dependancies listed above<br>
2) Clone this repository to your local computer/server<br>
3) Install MySQL and create a database to store your location data<br>
4) Run `pip install -r requrements.txt' to install all needed python modules<br>
5) Copy the iphonelocation.ini.sample file to iphonelocation.ini and enter the relevant data (You probably won't know the GUID for your Apple Device yet, but that's ok, you can leave that blank for now.<br>
6) Complete the `[database]` section of the config file with the hostname, port, database name, username and password of the MySQL database you've created<br>
7) Complete the `[ISY]` section of the configuration file. This is the username, password and connection settings to your Universal Device ISY controller.<br>
8) Determine what variable number your ISY with store your "distance to home" data in (This must be a variable of type "state".)<br>
9) Change to the 'tools; directory and run `python ./listdevices.py` and it will connect to the iCloud API using the credentials from the iphonelocation.ini file and list all the devices associated with your iCloud ID. Make sure the iCloud API settings in the iphonelocation.ini file are set, the listdevices.py script reads your login and password from there.
10) Copy and paste the long identifier number (GUID) from the device you'd like to track and past it into the iphonelocation.ini file as your `iCloudGUID`<br>
11) Go to [Google Maps](http://maps.google.com), search for your home address, click on the map right over your house and copy down the lattitude and longitude, you'll need to enter those in the iphonelocation.ini file in the `location_home_lat` and `location_home_long` sections<br>

Once all of these steps are complete, you should be able to change back to the top level directory and run `python ./iphonelocation.py` to start the script. By default all you will see if the INFO level messages on your screen which is just startup info and the table of coordinates that are read. To monitor more about the application run a `tail -f ./logs/iPhoneLoction.log` and you should see the full debug code of the script as it runs.
