#!/bin/bash

if [ ! -f environment.env ]; then
    echo "'environment.env' does not exist, must be created and populated with secrets"
    exit 10
fi


APP_LOCATION=/usr/lib/wildflower/cuwb_sensor/
DATA_LOCATION=/data/

echo "installing app at $APP_LOCATION"
mkdir -p $APP_LOCATION

cp -r cuwb_sensor $APP_LOCATION
cp -r scripts/run.sh $APP_LOCATION
cp -r environment.env $APP_LOCATION


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


ehco "installing uploader at $DATA_LOCATION"
mkdir -p $DATA_LOCATION
cp scripts/upload.sh $DATA_LOCATION


echo "installing services"
cp service/cuwb-sensor.service /etc/systemd/cuwb-sensor.service
systemctl daemon-reload
systemctl enable cuwb-sensor.service



echo "setting up cron"

cat <<EOF > /etc/cron.d/cuwb-sensor
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

*/10 * * * * root /usr/sbin/logrotate /etc/logrotate.conf

4,14,24,34,44,54 * * * 1-5 root /data/upload.sh >> /data/uploader.log
* * * * *    root /usr/lib/wildflower/cuwb_sensor/scheduler.sh >> /data/scheduler.log
EOF

systemctl restart cron.service

