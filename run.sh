#!/bin/bash

PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ python3 -m cuwb_sensor.tools collect --consumer stdout > /data/cuwb-sensor.log
