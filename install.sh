#!/bin/bash


echo "setting up logrotate for the logs"

cat <<EOF > /etc/logrotate.d/cuwb_sensor
/data/cuwb-sensor.log {
  rotate 100
  missingok
  maxsize 50M
  notifempty
  create
  postrotate
    systemctl stop cuwb-sensor.service
    systemctl restart cuwb-sensor.service
  endscript
}

/data/scheduler.log {
  rotate 5
  missingok
  maxsize 10M
  notifempty
  create
}

/data/uploader.log {
  rotate 5
  missingok
  maxsize 10M
  notifempty
  create
}
EOF
