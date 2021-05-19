import os
import socket

import click

from cuwb_sensor.collector import CUWBCollector
from cuwb_sensor.network_contract import AnchorsDegradedException, Contract
from cuwb_sensor.tools.alert import send_email
from cuwb_sensor.tools.logging import logger
from cuwb_sensor.tools.snooplogg import DatabaseConnectionSnoop


def get_local_ip(routable_ip='8.8.8.8'):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((routable_ip, 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


@click.group()
@click.pass_context
def main(ctx):
    pass


@main.command()
@click.pass_context
@click.option('--consumer', help='the consumer type, supports `stdout`, `csv`, or `honeycomb` at this time')
@click.option('--environment_name_honeycomb', help='name of the environment in honeycomb, required for using the honeycomb consumer')
@click.option('--path_csv', help='path for csv file output, required for using the csv consumer')
@click.option('--ip', help='Socket ip for the CUWB network. (defaults to CUWB_SOCKET_IP env or 239.255.76.67)')
@click.option('--port', help='Socket port for the CUWB network. (defaults to CUWB_SOCKET_PORT env or 7667)')
@click.option('--route_ip', help='IP that the interface should route to. (defaults to CUWB_SOCKET_PORT env or 8.8.8.8)')
def collect(ctx, consumer, environment_name_honeycomb=None, path_csv=None, ip=None, port=None, route_ip=None):
    if consumer not in ['csv', 'honeycomb', 'stdout']:
        raise ValueError('consumer must be `csv` or `honeycomb`')
    if consumer == 'honeycomb':
        from database_connection_honeycomb import DatabaseConnectionHoneycomb
        database_connection = DatabaseConnectionHoneycomb(
            environment_name_honeycomb=environment_name_honeycomb,
            object_type_honeycomb="DEVICE",
            object_id_field_name_honeycomb="serial_number"
        )
    elif consumer == 'stdout':
        database_connection = DatabaseConnectionSnoop()
    elif consumer == 'csv':
        from database_connection.csv import DatabaseConnectionCSV
        database_connection = DatabaseConnectionCSV(
            path_csv,
            data_field_names=[
                "battery_percentage",
                "memory",
                "minutes_remaining",
                "processor_usage",
                'anchor_count',
                'average_quality',
                'bad_paired_anchors',
                'beacons_discarded',
                'beacons_late',
                'beacons_reported',
                'flags',
                'interanchor_comms_error_code',
                'interface_id',
                'name',
                'network_time',
                'pressure',
                'quality',
                'quaternion_type',
                'report_period',
                'scale',
                'smoothing',
                'temperature',
                'ticks_reported',
                'timed_rxs_reported',
                'type',
                'w',
                'x',
                'y',
                'z',
            ],
        )
    ip = ip if ip else os.environ.get('CUWB_SOCKET_IP', '239.255.76.67')
    port = port if port else os.environ.get('CUWB_SOCKET_PORT', 7667)
    interface = route_ip if route_ip else get_local_ip(os.environ.get('CUWB_ROUTABLE_IP', '8.8.8.8'))
    with CUWBCollector(ip, int(port), interface) as collector:
        for bit in collector:
            if bit:
                if consumer == 'honeycomb':
                    bit['timestamp'] = bit['timestamp'].isoformat()
                database_connection.write_datapoint_object_time_series(
                    timestamp=bit.get("timestamp"),
                    object_id=bit.get("serial_number"),
                    data=bit
                )


@main.command()
@click.pass_context
@click.option('--name', help='name of the network')
@click.option('--action', help='start or stop')
def network(ctx, name, action):
    contract = Contract(name)
    if action == "start":
        contract.ensure_network_is_running()
    elif action == "stop":
        contract.ensure_network_is_stopped()


@main.command()
@click.option('--name', help='name of the network')
def check_network_health(name):
    contract = Contract(name)
    try:
        contract.check_network_health()
        logger.info(f"`{name}` network healthy")
    except AnchorsDegradedException as e:
        message = f"CUWB Network '{name}' reporting unexpected state:\n\n"

        message += "\n".join([f'\t• {err_msg}' for err_msg in e.error_messages])

        send_email(to="innovation-alerts@wildflowerschools.org",
                   subject=f"CUWB Network `{name}` in Degraded State",
                   message=message)

        logger.error(e)


@main.command()
@click.pass_context
@click.option('--file', help='path to the file to upload')
@click.option('--serial_number', help='serial_number for the device')
@click.option('--start', help='starting timestamp')
@click.option('--type', help='type of measurement(s)')
@click.option('--environment_name_honeycomb', help='name of the environment in honeycomb, required for using the honeycomb consumer')
def upload(ctx, environment_name_honeycomb, file, serial_number, start, type):
    from database_connection_honeycomb import DatabaseConnectionHoneycomb
    database_connection = DatabaseConnectionHoneycomb(
        environment_name_honeycomb=environment_name_honeycomb,
        object_type_honeycomb="DEVICE",
        object_id_field_name_honeycomb="serial_number"
    )
    with open(file, 'r') as fp:
        database_connection.write_datapoint_object_time_series(
            timestamp=start,
            object_id=serial_number,
            data=fp.read()
        )


if __name__ == '__main__':
    main()
