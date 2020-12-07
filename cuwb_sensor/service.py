import socket
import sys
from multiprocessing import Process
import os

import click
import yaml

from cuwb_sensor.tools.__main__ import _collect, _network

server_address = './cuwb_sensor_collector_socket'


def main(config_file):
    with open(config_file, 'r') as fp:
        config = yaml.safe_load(fp)

    print(config)
    # Make sure the socket does not already exist
    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen(1)

    while True:
        # Wait for a connection
        print('waiting for a connection')
        connection, client_address = sock.accept()
        try:
            print('message received')
            data = connection.recv(16).decode("utf8").strip()
            print('received "%s"' % data)
            if data:
                print('sending response to the client')
                connection.sendall(b'ok')
                if data == "logrotate":
                    pass
        finally:
            # Clean up the connection
            connection.close()

def message(msg):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    print('connecting to %s' % server_address)
    try:
        sock.connect(server_address)
        sock.sendall(" ".join(msg).encode('utf8'))
    except Exception as err:
        print(err)
        sys.exit(1)
