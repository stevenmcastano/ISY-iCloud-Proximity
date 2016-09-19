# ISY-iCloud-Proximity

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
The next items to be refined in future releases are the following:<br>
<b>1)</b> The is an `isOld` parameter returned by the iCloud API, right now we're reading it, but not using it to change script behavior. In future releases I'd like to configure the script so if the `isOld` is set to `True`, the script ignore that GPS data, sleeps for 1 minute and attempts to re-read the data again until it gets something that's current.<br>
<b>2)</b> Configurable sleep times and multipliers. Right now, sleeping for 1 minute when the device is withing 5 miles and sleeping for half the numeber of minutes as miles away for anything over 5 miles works for me perfect, but I would imagine different people have different use cases. I would like to add the sleep times, "close proximity" distance and time factor to the configuration file and let people change them as needed. Right now it's set because based on normal DRIVING behavior, even at a max speed decently OVER most of the US legal limits of 55, 65, even 70 miles per hour, you're not going to "outrun" the timer. You would have to time it nearly perfectly, and right after a check, drive 120 miles per hour to get home in order to arrive home before the script checks again. Point being, by road, this isn't possible. However, by flight it sure is. Take for example if you live on the east coast like I do, but you've flow out to the west coast, say, NY to LA... In the air, straight across the country, non-stop that's 2,441 miles. This means that while you're in LA, the script will only be checking your position for HALF that number of minutes. That's 1220 minutes approximately, or approximately once every 20 hours. It's only a 5 - 6 hour flight. So changes are, the script could check your GPS position while you're at the airport, you could fly home, and including taxis, subways, car travel, shuttle, etc... you could go door-to-door, LA back to NY in 7 - 9 hours, long before your script checks your position. For this reason, based on the small battery hit each lookup takes, I think a max sleep time of 1 hour would be more than sufficient. This feature would also be something in the configuration file as optional... I just know I would hate to return home from a long day of traveling only to find my AC isn't on, porch and driveway lights are all off, etc. From my calculations, on an iPhone 6s Plus, 24 iCloud GPS lookups barely uses 1% of the battery, that shouldn't make much of a difference for anyone.<br>
<b>3)</b> Different arrival and departure distances and math. Basically, I'd want the script to check my location fewer times when I'm moving away from home, maybe the normal 1/2 fraction works (half the number of minutes as distance), but on the way back home, to prevent any possibility of "outrunning" the script, if it detects your distance to home has gone down, meaning your getting close to home, it switches to 1/4 so it checks twice as often on your way back.

# Dependancies / Installation
The script is written in python 2.7, so start there, you'll need to install that. I also like to have python-pip or easy_install as well as it makes installing the following packages easier:

1) python-peewee (used for database connections)<br>
2) pyicloud (A python based library for interaction with the Apple iCloud API)<br>
3) geopy (A python library used to compute distance, speed, etc... from GPS coordinates)<BR>

# Usage
1) Install the dependancies above<br>
2) Clone this repository to your local computer/server<br>
3) Install MySQL and create a database to store your location data<br>
4) Copy the iphonelocation.ini.sample file to iphonelocation.ini and enter the relevant data (You probably won't know the GUID for your Apple Device yet, but that's ok, you can leave that blank for now.<br>
5) Complete the `[database]` section of the config file with the hostname, port, database name, username and password of the MySQL database you've created<br>
6) Complete the `[ISY]` section of the configuration file. This is the username, password and connection settings to your Universal Device ISY controller.<br>
7) Determine what variable number your ISY with store your "distance to home" data in (This must be a variable of type "state".)<br>
8) Change to the 'tools; directory and run `python ./listdevices.py` and it will connect to the iCloud API using the credentials from the iphonelocation.ini file and list all the devices associated with your iCloud ID. Make sure the iCloud API settings in the iphonelocation.ini file are set, the listdevices.py script reads your login and password from there.
9) Copy and paste the long identifier number (GUID) from the device you'd like to track and past it into the iphonelocation.ini file as your `iCloudGUID`<br>
10) Go to [Google Maps](http://maps.google.com), search for your home address, click on the map right over your house and copy down the lattitude and longitude, you'll need to enter those in the iphonelocation.ini file in the `location_home_lat` and `location_home_long` sections<br>

Once all of these steps are complete, you should be able to change page to the top level directory and to a `python ./iphonelocation.py` to start the script. By default all you will see if the INFO level messages on your screen which is just startup info and the table of coordinates that are read. To monitor more about the application run a `tail -f ./iPhoneLoction.log` and you should see the full debug code of the script as it runs.
