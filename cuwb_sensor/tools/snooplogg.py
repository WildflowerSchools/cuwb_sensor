import json

from database_connection import DatabaseConnection


class DatabaseConnectionSnoop(DatabaseConnection):
    """
    Class to define a DatabaseConnection to a CSV file
    """
    def write_datapoint_object_time_series(
        self,
        timestamp,
        object_id,
        data
    ):
        value_dict = {
            'timestamp': timestamp.isoformat(),
            'object_id': object_id
        }
        value_dict.update(data)
        value_dict['timestamp'] = value_dict['timestamp'].isoformat()
        print(json.dumps(value_dict))
