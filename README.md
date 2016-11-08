# ISY-iCloud-Proximity

<h4>Current Build Status:</h4>
Master:<br>
![Build Status Graphic](https://travis-ci.org/stevenmcastano/ISY-iCloud-Proximity.svg?branch=master "current build status")<br>
Dev:<br>
![Build Status Graphic](https://travis-ci.org/stevenmcastano/ISY-iCloud-Proximity.svg?branch=dev "current build status")<br>

<h4>Overview:</h4><br>
This python script reads your iOS devices location from the iCloud API, calculates your distance to home and stores it in a variable on a Universal Devices ISY controller.<br>
<br>
<h4>Basic Application Flow:</h4><br>
The script first reads all of its configuration data from a file in the `conf` directory called `iphonelocation.ini`. It then makes a connection to the MySQL database you've specified and creates the proper location data table if it doesn't already exist.<br>
<br>
With the settings specified in the above mentioned .ini file, the script logs into the iCloud API and uses your devices unique Apple assigned identifier reads its current GPS coordinates. It then uses the latitude and longitude of your home location to calculate the distance in miles between your home and your iOS device which is then displayed on the screen in a table showing all your relevant information.<br>
<br>
It then repeats this process in a loop.<br>
<br>
If the calculated distance during a current loop is different from the previous loop, it calls the ISY API sets a variable value with the new distance. There are settings in the .ini file to control how many decimal places of precision are used.<br>
<br>
The script will check your iCloud GPS location once per minute, but this does have an effect on battery life, so after the script sees that you have moved more than 5 miles away it begins to vary its sleep time between update cycles. (This distance threshold is also configurable in the .ini file) Once you're more than 5 miles away the script sleeps for half the number of minutes as you are miles away. So if you are 20 miles from home, the script sleeps for 10 minutes and as your move closer or farther away from home, the script sleep time gets shorter of longer respectively. Also, by default, the sleep time is cut in half of its intended value if the script calculates that you are moving closer to your home location. This is done to ensure that you don’t arrive home between cycles and miss updating the ISY. The default value for this varied sleep distance is 4, meaning it’s 1 fourth of your distance from home. For example, if you are 20 miles from home and the script calculates that you’ve gotten closer to home since your last check, it will only sleep for 5 minutes as opposed to 10 should it calculate you were moving farther away or standing still. Also, the minimum default distance to have moved between cycles for the script to think you are moving is .5 miles. This setting is also configurable in the .ini file.<br>
<br>
For the most part, you can just fill in the `[database]`, `[ISY]`, `[iCloudAPI]` and `[device]` settings while leaving everything else at it’s defaults and the script should handle itself well.<br>
<br>
<h4>Advanced Features:</h4><br>
For a good description of the advanced features of the script like checking the ISY for Wifi or Bluetooth proximity as well as changing all the mathematical variable used in distance and timing calculations, see the descript of each setting in the `iphonelocation.ini` file.<br>
<br>
<h4>Roadmap:</h4><br>
Everything on my original plan/roadmap has been covered for the most part. There isn't much left:<br>
<br>
1)	Investigate checking battery level and suspend checking more than once per hour if it falls below a configurable threshold.<br>
<br>
<h4>Dependancies / Installation:</h4>
You will need the following installed:<br>
1) Python 2.7<br>
2) Python pip<br>
3) MySQL or equivalent (I use MariaDB)<br>
<br>
<h4>Usage:</h4>
1) Install the dependencies listed above<br>
2) Clone this repository to your local computer/server<br>
3) Install MySQL and create a database to store your location data<br>
4) Run `pip install -r requirements.txt` to install all needed python modules<br>
5) Copy the `iphonelocation.ini.sample` file to `iphonelocation.ini` and enter the relevant data (You probably won't know the GUID for your Apple device yet, but that's ok, you can leave that blank for now.<br>
6) Complete the `[database]` section of the config file with the hostname, port, database name, username and password of the MySQL database you've created<br>
7) Complete the `[ISY]` section of the configuration file. This is the username, password and connection settings to your Universal Devices ISY controller.<br>
8) Determine what variable number your ISY will store your "distance to home" data in (This must be a variable of type "state".)<br>
9) Change to the `tools` directory and run `python ./listdevices.py` and it will connect to the iCloud API using the credentials from the `iphonelocation.ini` file and list all the devices associated with your iCloud ID. Make sure the iCloud API settings in the `iphonelocation.ini` file are set, the `listdevices.py` script reads your login and password from there.<br>
10) Copy and paste the long identifier number (GUID) from the device you'd like to track and paste it into the `iphonelocation.ini` file as your `iCloudGUID`<br>
11) Go to Google Maps, search for your home address, click on the map right over your house and copy down the latitude and longitude, you'll need to enter those in the `iphonelocation.ini` file in the `location_home_lat` and `location_home_long` sections.<br>
12) Once all of these steps are complete, you should be able to change back to the top level directory and run `python ./iphonelocation.py` to start the script. By default, all you will see is the INFO level messages on your screen which is just startup info and the table of coordinates that are read. To monitor more as the application runs you can use the `tail` command, like `tail -f ./logs/iPhoneLoction.log` and you will see the full debug log of the running script.
