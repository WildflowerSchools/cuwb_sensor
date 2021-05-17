#!/bin/bash

source /usr/lib/wildflower/cuwb_sensor/environment.env
export CUWB_NETWORK_NAME=$CUWB_NETWORK_NAME

PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ /usr/bin/python3 -m cuwb_sensor.tools network --name ${CUWB_NETWORK_NAME} --action start
