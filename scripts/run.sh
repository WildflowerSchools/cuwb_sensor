#!/bin/bash
source /usr/lib/wildflower/cuwb_sensor/environment.env

export CUWB_ROUTABLE_IP=$CUWB_ROUTABLE_IP
export CUWB_NETWORK_NAME=$CUWB_NETWORK_NAME
export HONEYCOMB_URI=$HONEYCOMB_URI
export HONEYCOMB_TOKEN_URI=$HONEYCOMB_TOKEN_URI
export HONEYCOMB_AUDIENCE=$HONEYCOMB_AUDIENCE
export HONEYCOMB_CLIENT_ID=$HONEYCOMB_CLIENT_ID
export HONEYCOMB_CLIENT_SECRET=$HONEYCOMB_CLIENT_SECRET
export HONEYCOMB_ENVIRONMENT=$HONEYCOMB_ENVIRONMENT


PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ python3 -m cuwb_sensor.tools collect --consumer stdout > /data/cuwb-sensor.log
