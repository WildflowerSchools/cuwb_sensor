#!/bin/bash

# config for uploading things to Honeycomb
source /usr/lib/wildflower/cuwb_sensor/environment.env

SENSOR_LOG_DIR="/data"

if [ "${SENSOR_LOG_DIR}" == "${SENSOR_LOG_DIR#/}" ]; then echo "Absolute path required"; exit 0; fi

SENSOR_LOG_BACKUP_DIR="${SENSOR_LOG_DIR}/cuwb_backups"
SENSOR_LOG_UPLOAD_DIR="${SENSOR_LOG_DIR}/cuwb_uploads"
SENSOR_LOG_STAGING_DIR="${SENSOR_LOG_DIR}/cuwb_staging/$(date +%s)"

mkdir -p ${SENSOR_LOG_BACKUP_DIR}
mkdir -p ${SENSOR_LOG_UPLOAD_DIR}
mkdir -p ${SENSOR_LOG_STAGING_DIR}

echo "${SENSOR_LOG_DIR}/cuwb-sensor.log.*"
echo "${SENSOR_LOG_STAGING_DIR}/"
mv ${SENSOR_LOG_DIR}/cuwb-sensor.log.* ${SENSOR_LOG_STAGING_DIR}/

echo "$(date) --| checking for logs to upload"

for LOG_PATH in ${SENSOR_LOG_STAGING_DIR}/cuwb-sensor.log.*
do
    if [ ! -f "${LOG_PATH}" ]; then continue; fi
    echo "$(date) --| processing ${LOG_PATH}"

    # pulls in a bit of metadata for the file time range
    END=$(tail -n 1 "${LOG_PATH}" | jq -r .timestamp)
    START=$(head -n 1 "${LOG_PATH}" | jq -r .timestamp)

    # unique object_ids for the measurements
    UNIDS=$(cat "${LOG_PATH}" | sed -n 's/^.*object_id\":[[:space:]]\"\([0-9A-F:]*\).*$/\1/p' | sort | uniq)

    echo "$(date) --| found $(echo ${UNIDS} | wc -w) unique serial numbers"

    # loop over the ids and filter the log for each id and then each of those by measurement type
    # makes it easier to process the data downstream
    echo "$(date) --| filtering"
    for ID in $UNIDS
    do
        filtered_log_path="${SENSOR_LOG_UPLOAD_DIR}/filtered-${START}-${ID}.mjson"
        status_log_path="${SENSOR_LOG_UPLOAD_DIR}/status-${START}-${ID}.mjson"
        anchor_health_log_path="${SENSOR_LOG_UPLOAD_DIR}/anchor_health-${START}-${ID}.mjson"
        position_log_path="${SENSOR_LOG_UPLOAD_DIR}/position-${START}-${ID}.mjson"
        gyroscope_log_path="${SENSOR_LOG_UPLOAD_DIR}/gyroscope-${START}-${ID}.mjson"
        magnetometer_log_path="${SENSOR_LOG_UPLOAD_DIR}/magnetometer-${START}-${ID}.mjson"

        grep "\"${ID}\"" "${LOG_PATH}" > "${filtered_log_path}"
        grep 'status' "${filtered_log_path}" > "${status_log_path}"
        grep 'anchor_health' "${filtered_log_path}" > "${anchor_health_log_path}"
        grep 'position\|accelerometer' "${filtered_log_path}" > "${position_log_path}"
        grep 'gyroscope' "${filtered_log_path}" > "${gyroscope_log_path}"
        grep 'magnetometer' "${filtered_log_path}" > "${magnetometer_log_path}"
    done

    # loop over the ids again and send the files to the uploader to be sent to honeycomb
    for ID in $UNIDS
    do
        filtered_log_path="${SENSOR_LOG_UPLOAD_DIR}/filtered-${START}-${ID}.mjson"
        status_log_path="${SENSOR_LOG_UPLOAD_DIR}/status-${START}-${ID}.mjson"
        anchor_health_log_path="${SENSOR_LOG_UPLOAD_DIR}/anchor_health-${START}-${ID}.mjson"
        position_log_path="${SENSOR_LOG_UPLOAD_DIR}/position-${START}-${ID}.mjson"
        gyroscope_log_path="${SENSOR_LOG_UPLOAD_DIR}/gyroscope-${START}-${ID}.mjson"
        magnetometer_log_path="${SENSOR_LOG_UPLOAD_DIR}/magnetometer-${START}-${ID}.mjson"

        if [ -s "${anchor_health_log_path}" ]; then
            PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ /usr/bin/python3 -m cuwb_sensor.tools upload --file "${anchor_health_log_path}" --serial_number "${ID}" --start "${START}" --type anchor_health --environment_name_honeycomb "${HONEYCOMB_ENVIRONMENT}"
            echo "$(date) --| $ID has $(cat ${anchor_health_log_path} | wc -l) anchor_health entries"
        fi
        if [ -s "${position_log_path}" ]; then
            PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ /usr/bin/python3 -m cuwb_sensor.tools upload --file "${position_log_path}" --serial_number "${ID}" --start "${START}" --type position --environment_name_honeycomb "${HONEYCOMB_ENVIRONMENT}"
            echo "$(date) --| $ID has $(cat "${position_log_path}" | wc -l) position entries"
        fi
        if [ -s "${status_log_path}" ]; then
            PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ /usr/bin/python3 -m cuwb_sensor.tools upload --file "${status_log_path}" --serial_number "${ID}" --start "${START}" --type status --environment_name_honeycomb "${HONEYCOMB_ENVIRONMENT}"
            echo "$(date) --| $ID has $(cat "${status_log_path}" | wc -l) status entries"
        fi
        if [ -s "${gyroscope_log_path}" ]; then
            PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ /usr/bin/python3 -m cuwb_sensor.tools upload --file "${gyroscope_log_path}" --serial_number "${ID}" --start "${START}" --type status --environment_name_honeycomb "${HONEYCOMB_ENVIRONMENT}"
            echo "$(date) --| $ID has $(cat "${gyroscope_log_path}" | wc -l) gyroscope entries"
        fi
        if [ -s "${magnetometer_log_path}" ]; then
            PYTHONPATH=$PYTHONPATH:/usr/lib/wildflower/cuwb_sensor/ /usr/bin/python3 -m cuwb_sensor.tools upload --file "${magnetometer_log_path}" --serial_number "${ID}" --start "${START}" --type status --environment_name_honeycomb "${HONEYCOMB_ENVIRONMENT}"
            echo "$(date) --| $ID has $(cat "${magnetometer_log_path}" | wc -l) magnetometer entries"
        fi
        rm "${filtered_log_path}"
        rm "${anchor_health_log_path}"
        rm "${position_log_path}"
        rm "${status_log_path}"
        rm "${gyroscope_log_path}"
        rm "${magnetometer_log_path}"
    done

    echo "$(date) --| backing up ${LOG_PATH}"
    mv "${LOG_PATH}" "${SENSOR_LOG_BACKUP_DIR}/${START}-$(basename $LOG_PATH)"
done

echo "$(date) --| cleaning up ${SENSOR_LOG_BACKUP_DIR}"
find "${SENSOR_LOG_BACKUP_DIR}/" -type f -mtime +7 -exec rm {} \;
