#!/bin/bash

if [ ! -f environment.env ]; then
    echo "'environment.env' does not exist, must be created and populated with secrets"
    exit 10
fi


APP_LOCATION=/usr/lib/wildflower/cuwb_sensor/
DATA_LOCATION=/data/

echo "installing app at $APP_LOCATION"
mkdir -p $APP_LOCATION

echo "installing pip requirements"

pip3 install -r requirements.txt

cp -r cuwb_sensor $APP_LOCATION
cp -r environment.env $APP_LOCATION
cp -rp scripts/network_health.sh $APP_LOCATION
cp -rp scripts/startnetwork.sh $APP_LOCATION
cp -rp scripts/stopnetwork.sh $APP_LOCATION

echo "setting up logrotate for the logs"

cat <<EOF > /etc/logrotate.d/cuwb_sensor
/data/scheduler.log {
  rotate 5
  missingok
  maxsize 10M
  notifempty
  create
}

/data/network_health.log {
  rotate 5
  missingok
  maxsize 10M
  notifempty
  create
}
EOF

echo "setting up cron"

cat <<EOF > /etc/cron.d/cuwb-sensor
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

*/10 * * * * root /usr/sbin/logrotate /etc/logrotate.conf

0 4 * * *    root /usr/lib/wildflower/cuwb_sensor/stopnetwork.sh >> /data/scheduler.log 2>&1
5 4 * * *    root /usr/lib/wildflower/cuwb_sensor/startnetwork.sh >> /data/scheduler.log 2>&1
*/5 * * * *    root /usr/lib/wildflower/cuwb_sensor/network_health.sh >> /data/network_health.log 2>&1
EOF

systemctl restart cron.service

