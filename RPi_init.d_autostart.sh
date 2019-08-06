
#! /bin/sh
# /etc/init.d/garage_monitor 

### BEGIN INIT INFO
# Provides:          garage_monitor
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Starts the python script 'RPi_GarageMonitor' used to monitor the door and detect motion
# Description:       Starts the python script 'RPi_GarageMonitor' used to monitor the door and detect motion
### END INIT INFO

case "$1" in
  start)
    echo "Starting RPi_GarageMonitor"
    /usr/bin/python /home/pi/src/RPi_GPIOEventProcessor/GarageEventProcessor.py -g /home/pi/src/RPi_GPIOEventProcessor/GPIO.json -e /home/pi/src/RPi_GPIOEventProcessor/EventTriggers.json -l /home/pi/garageDoorLog.txt -u https://data.sparkfun.com/input/[public url]?private_key=[privatekey] -a /home/pi/src/RPi_GPIOEventProcessor/actionDefs.json
    ;;
  stop)
    echo "Stopping RPi_GarageMonitor"
    ;;
  *)
    echo "Usage: /etc/init.d/noip {start|stop}"
    exit 1
    ;;
esac

exit 0
