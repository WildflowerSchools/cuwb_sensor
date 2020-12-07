"""
Generic scheduler with probes, start/stop, etc.

Schedule objects can be scheduled in one of two ways. 

Event
===================================

Events are actions that occur at specific times throughout the week. Each event defines an action that should
be executed at that time.

events:
- time: 07:00
  days: [0, 1, 2, 3, 4]
  timezone: "US/Eastern"
  action: scale-down-thing
- time: 17:30
  days: [0, 1, 2, 3, 4]
  timezone: "US/Eastern"
  action: scale-up-thing
- time: 09:00
  days: [5]
  timezone: "US/Eastern"
  action: scale-down-thing

Binary
===================================

A binary schedule is based on the idea that a initiation occurs at a certain time and ends at a certain time.
They have start and end times and specify three actions, start, end, and probe. Start defines the action to
start the activity. End would tear it down. And probe defines an action that tests if the expected state is
currently active.

schedules:
- start: 07:00
  end: 17:30
  days: [0, 1, 2, 3, 4]
  timezone: "US/Eastern"
  actions:
    start: start-collector
    end: stop-collector
    probe: test-collector


Actions
===================================

Actions are a simple structure, they define a manifest and the command to do with it. They can also define a 
probe command, which tests a state.

actions:
  start-collector:
    type: py
    import: module.schedule
    call: start_collector
    args:
    - "now"
  stop-collector:
    type: py
    import: module.schedule
    call: stop_collector
  test-collector:
    type: py
    import: module.schedule
    call: stop_collector
    on_failure: start-collector
  scale-up-thing:
    type: py
    import: module.schedule
    call: scale_collector
    args:
    - 10
  scale-down-thing:
    type: py
    import: module.schedule
    call: scale_collector
    args:
    - 0

"""
from datetime import datetime
import logging
import os


import pytz
import yaml


ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]


logger = logging.getLogger('scheduler')

logger.setLevel(os.environ.get("LOG_LEVEL", logging.DEBUG))
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s - %(message)s'))
logger.addHandler(handler)


def add_5(time):
    h, m = time.split(":")
    h = int(h)
    m = int(m)
    m += 5
    if m >= 60:
        h += 1
        m = m % 60
        if h >= 24:
            h = 0
    return f'{h:02}:{m:02}'


def should_be_running_now(schedule):
    if today_in(schedule):
        start = schedule.get("start-time")
        timezone = pytz.timezone(schedule.get("timezone", "US/Central"))
        end = schedule.get("end-time")
        local = hour_min_now(timezone)
        if local >= start and local <= end:
            return True
    return False


def parse_action(action):
    action_type = action.get("type")
    if action_type == "status":
        return ExpectedStatus.from_dict(action)
    if action_type == "create":
        return CreateOperation.from_dict(action)
    if action_type == "patch":
        return PatchOperation.from_dict(action)
    if action_type == "delete":
        return DeleteOperation.from_dict(action)


class Action(object):

    def __init__(self,  mod, call, args, on_failure=None):
        self.mod = mod
        self.call = call
        self.args = args
        self.on_failure = on_failure
        if mod is None or call is None:
            raise Exception("import or call was not set")

    def execute(self, brazil):
        logger.info(f"executing a action {self.mod}:{self.call} with {self.args}")
        status = status_check(self.kubetype, self.name, self.namespace)
        for field in self.fields:
            if not field.evaluate(status):
                logger.info(f"{self.kubetype}/{self.name} in {self.namespace} is out of compliance")
                if self.on_failure:
                    brazil.execute_action(self.on_failure)
                else:
                    logger.info(f"no failure action provided")
                break

    @classmethod
    def from_dict(cls, the_dict):
        on_failure = the_dict.get("on_failure")
        mod = the_dict.get("import")
        call = the_dict.get("call")
        args = the_dict.get("args", [])
        return cls(mod, call, args, on_failure=on_failure)



class ScheduleEntry(object):

    def __init__(self, start, end, days, start_action=None, end_action=None, probe_action=None):
        self.start = start
        self.end = end
        self.start_action = start_action
        self.end_action = end_action
        self.probe_action = probe_action
        self.days = days
        if self.days is None:
            self.days = ALL_DAYS

    @classmethod
    def from_dict(cls, the_dict):
        actions = the_dict.get("actions", {})
        props = {
            "start": the_dict.get("start"),
            "end": the_dict.get("end"),
            "days": the_dict.get("days"),
            "start_action": actions.get("start"),
            "end_action": actions.get("end"),
            "probe_action": actions.get("probe"),
        }
        return cls(**props)

    def _scheduled_for_today(self, today):
        return today.weekday() in self.days

    def evaluate(self, today, local, brazil):
        if self._scheduled_for_today(today):
            logger.debug("item scheduled for today")
            if self._should_start(local):
                logger.info(f"action {self.start_action} should execute now, schedule entry scheduled to start")
                brazil.execute_action(self.start_action)
            elif self._should_end(local):
                logger.info(f"action {self.end_action} should execute now, schedule entry scheduled to end")
                brazil.execute_action(self.end_action)
            elif self._should_be_running_now(local):
                logger.info(f"probe action {self.probe_action} should execute now, schedule entry should be running")
                brazil.execute_action(self.probe_action)
            else:
                logger.debug("out of range")

    def _should_start(self, local):
        if add_5(local) >= self.start and local <= self.start:
            return True
        return False

    def _should_end(self, local):
        if add_5(local) >= self.end and local <= self.end:
            return True
        return False

    def _should_be_running_now(self, local):
        if local >= self.start and local <= self.end:
            return True
        return False


class Event:

    def __init__(self, time, days, timezone, action=None):
        self.time = time
        self.days = days
        self.timezone = timezone
        self.action = action
        if self.days is None:
            self.days = ALL_DAYS

    @classmethod
    def from_dict(cls, the_dict):
        actions = the_dict.get("actions", {})
        props = {
            "time": the_dict.get("time"),
            "days": the_dict.get("days"),
            "timezone": the_dict.get("timezone"),
            "action": actions.get("saction"),
        }
        return cls(**props)

    def _scheduled_for_today(self, today):
        return today.weekday() in self.days

    def evaluate(self, today, local, brazil):
        if self._scheduled_for_today(today):
            logger.debug("item scheduled for today")
            if self._should_start(local):
                logger.info(f"action {self.start_action} should execute now, executing")
                brazil.execute_action(self.start_action)
            else:
                logger.info(f"action {self.start_action} should not execute now")

    def _should_start(self, local):
        if add_5(local) >= self.time and local <= self.time:
            return True
        return False


class Brazil(object):

    def __init__(self, timezone="US/Central"):
        self.actions = dict()
        self.events = list()
        self.schedules = list()
        self.timezone = timezone

    def evaluate(self):
        tz = pytz.timezone(self.timezone)
        now = datetime.now(pytz.UTC)
        local = now.astimezone(tz).strftime("%H:%M")
        logger.debug(f"local time is now {local}")

        for entry in self.schedules:
            entry.evaluate(now, local, self)

        for event in self.events:
            event.evaluate(now, local, self)

    def execute_action(self, action_name):
        if action_name in self.actions:
            action = self.actions.get(action_name)
            action.execute(self)
        else:
            logger.error(f"action {action_name} was not found, please check your configuration")


def load_schedules(file_path="schedule.yaml"):
    with open(file_path, 'r') as fp:
        shed = yaml.safe_load(fp)
    bureaucrat = Brazil(shed.get("timezone", "US/Central"))
    for name, action in shed.get("actions").items():
        bureaucrat.actions[name] = parse_action(action)

    for schedule in shed.get("schedules"):
        bureaucrat.schedules.append(ScheduleEntry.from_dict(schedule))

    for event in shed.get("events"):
        bureaucrat.events.append(Event.from_dict(event))

    return bureaucrat


def main():
    logger.info("================================= starting up ==================================")
    path = os.environ.get("CONFIG_PATH", "test/test_schedule.yaml")
    logger.info("loading schedules")
    bureaucrat = load_schedules(path)
    logger.info("evaluate schedules started")
    logger.info(bureaucrat.actions.keys())
    bureaucrat.evaluate()
    logger.info("evaluate schedules complete")
