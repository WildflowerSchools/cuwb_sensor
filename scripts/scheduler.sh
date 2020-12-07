#!/bin/bash

source /usr/lib/wildflower/cuwb_sensor/environment.env

CURRENT=$(date -u +"%H:%M")
DOW=$(date -u +"%u")

START="12:29"
# START="00:00"
END="21:59"
# END="23:59"

if [[ $CURRENT > $START &&  $CURRENT < $END && '012345' == *${DOW}* ]]; then
    echo "$(date) should be running"
    PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ python3 -m cuwb_sensor.tools network --name $CUWB_NETWORK_NAME --action start
    if [ ! $(systemctl is-active cuwb-sensor.service) == "active" ]; then
        echo "$(date) is not running, starting"
        systemctl start cuwb-sensor.service
    fi
else
    echo "$(date) should not be running"
    PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ python3 -m cuwb_sensor.tools network --name $CUWB_NETWORK_NAME --action stop
    if [ $(systemctl is-active cuwb-sensor.service) == "active" ]; then
        echo "$(date) is running, stopping"
        systemctl stop cuwb-sensor.service
    fi
fi



