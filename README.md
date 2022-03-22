# SatCheck

Repo with some code to look for satellites in Breakthrough Listen Data. Modified from: https://github.com/stevecroft/bl-interns/blob/master/chrismurphy/find_satellites.py

## Setup to run findSats
You must add the password for spacetrack queries to your .bashrc file using the following steps in a bash terminal
```
sudo nano ~/.bashrc
```
Then add to the bottom the line
```
export SAPECTRACK_PASS="{Password}"
```
where you replace {Password} with your password. Then exit nano and type
```
source ~/.bashrc
```
