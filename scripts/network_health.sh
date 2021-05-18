#!/bin/bash

source /usr/lib/wildflower/cuwb_sensor/environment.env
export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
export CUWB_NETWORK_NAME=$CUWB_NETWORK_NAME

PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ /usr/bin/python3 -m cuwb_sensor.tools check-network-health --name ${CUWB_NETWORK_NAME}
