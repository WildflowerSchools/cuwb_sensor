#!/bin/bash

# config for uploading things to Honeycomb
export CUWB_ROUTABLE_IP=0.0.0.0
export HONEYCOMB_URI=https://honeycomb.api.wildflower-tech.org/graphql
export HONEYCOMB_TOKEN_URI=https://wildflowerschools.auth0.com/oauth/token
export HONEYCOMB_AUDIENCE=https://honeycomb.api.wildflowerschools.org
export HONEYCOMB_CLIENT_ID=CLIENT_ID
export HONEYCOMB_CLIENT_SECRET=CLIENT_SECRET
HONEYCOMB_ENVIRONMENT=ENVIRONMENT

cd /data

echo "$(date) --| checking for logs to upload"

for LOG_PATH in /data/cuwb-sensor.log.*
do
    if [ ! -f "$LOG_PATH" ]; then continue; fi
    echo "$(date) --| processing ${LOG_PATH}"

    # pulls in a bit of metadata for the file time range
    END=$(tail -n 1 "${LOG_PATH}" | jq -r .timestamp)
    START=$(head -n 1 "${LOG_PATH}" | jq -r .timestamp)

    # unique object_ids for the measurements
    UNIDS=$(cat "${LOG_PATH}" | grep -oP 'object_id": "\K[0-9A-F:]*(?=.)' | sort | uniq)

    echo "$(date) --| found $($UNIDS | wc -w) unique serial numbers" 

    # loop over the ids and filter the log for each id and then each of those by measurement type
    # makes it easier to process the data downstream
    echo "$(date) --| filtering"
    for ID in $UNIDS
    do 
        grep "\"${ID}\"" "${LOG_PATH}" > "filtered-${START}-${ID}.mjson"
        grep 'status' "filtered-${START}-${ID}.mjson" > "status-${START}-${ID}.mjson"
        grep 'anchor_health' "filtered-${START}-${ID}.mjson" > "anchor_health-${START}-${ID}.mjson"
        grep 'position\|accelerometer' "filtered-${START}-${ID}.mjson" > "position-${START}-${ID}.mjson"
    done


    # loop over the ids again and send the files to the uploader to be sent to honeycomb
    for ID in $UNIDS
    do 
        if [ -s "anchor_health-${START}-${ID}.mjson" ]; then
            PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ python3 -m cuwb_sensor.tools upload --file "anchor_health-${START}-${ID}.mjson" --serial_number "${ID}" --start "${START}" --type anchor_health --environment_name_honeycomb "${HONEYCOMB_ENVIRONMENT}"
            echo "$(date) --| $ID has $(cat "anchor_health-${START}-${ID}.mjson" | wc -l) anchor_health entries"
        fi
        if [ -s "position-${START}-${ID}.mjson" ]; then
            PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ python3 -m cuwb_sensor.tools upload --file "position-${START}-${ID}.mjson" --serial_number "${ID}" --start "${START}" --type position --environment_name_honeycomb "${HONEYCOMB_ENVIRONMENT}"
            echo "$(date) --| $ID has $(cat "position-${START}-${ID}.mjson" | wc -l) position entries"
        fi
        if [ -s "status-${START}-${ID}.mjson" ]; then
            PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ python3 -m cuwb_sensor.tools upload --file "status-${START}-${ID}.mjson" --serial_number "${ID}" --start "${START}" --type status --environment_name_honeycomb "${HONEYCOMB_ENVIRONMENT}"
            echo "$(date) --| $ID has $(cat "status-${START}-${ID}.mjson" | wc -l) status entries"
        fi
        # rm "filtered-${START}-${ID}.mjson"
        rm "anchor_health-${START}-${ID}.mjson"
        rm "position-${START}-${ID}.mjson"
        rm "status-${START}-${ID}.mjson"
    done

    echo "$(date) --| cleaning up ${LOG_PATH}"
    mv "${LOG_PATH}" "$(dirname $LOG_PATH)/backups/${START}-$(basename $LOG_PATH)"
done
