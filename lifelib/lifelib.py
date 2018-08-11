from lifelib import activity_utils

import hjson
import os
import pkg_resources
import uuid

from datetime import datetime
from typing import Dict, Optional, Tuple


time_format = "%Y-%m-%d_%H:%M:%S"


def utc_time() -> str:
  return datetime.utcnow().strftime(time_format)


def utc_date() -> str:
  return datetime.utcnow().date().isoformat()


def elapsed_time_phrase(time: str) -> str:
  then = datetime.strptime(time, time_format)
  now = datetime.strptime(utc_time(), time_format)
  diff = now - then

  elapsed = int(diff.total_seconds())
  hours = elapsed // 3600
  minutes = (elapsed // 60) % 60
  seconds = elapsed % 60

  return f"{hours} hours {minutes} minutes and {seconds} seconds"


class TimelineError(RuntimeError):
  pass


class Timeline:
  """
  Handles state of current & other timelines.
  """
  current_state: Dict[str, str] = {}

  def __init__(self, username: str = None) -> None:
    if username is None:
      username = Timeline.default_user()

    self.username = username
    self.timeline = Timeline.load_timeline(self.username)

  def start(self, activity_name: str) -> None:
    # end any ongoing activity
    if self.current_activity() is not None:
      self.done()

    today = utc_date()

    # add new entry for today if one does not exist
    if today not in self.timeline["timeline"]:
      self.timeline["timeline"][today] = []

    # add activity to today's entry
    activity = {
        "id": self.get_activity_id(activity_name),
        "name": activity_name,
        "start": utc_time()
    }

    self.timeline["timeline"][today].append(activity)
    self.timeline["last_day"] = today

  def done(self) -> Tuple[str, str]:
    if self.current_activity() is None:
      raise TimelineError("No ongoing activity to finish.")

    last_day = self.timeline["last_day"]
    today = utc_date()

    # complete current activity and remove "last_day" field
    current_activity = self.timeline["timeline"][last_day][-1]
    current_activity["end"] = utc_time()
    del self.timeline["last_day"]

    # if this activity was started on a day other than today, make sure to
    # add a copy of this activity to today's entry on the timeline.
    if last_day != today:
      finished_activity = {**current_activity, "previous": True}
      self.timeline["timeline"][today] = [finished_activity]

    return (elapsed_time_phrase(current_activity["start"]),
            current_activity["name"])

  def current_activity(self) -> Optional[Dict[str, str]]:
    if "last_day" in self.timeline:
      return self.timeline["timeline"][self.timeline["last_day"]][-1]
    return None

  def get_activity_id(self, activity_name: str) -> str:
    try:
      activities = self.timeline["activities"]
      return str(activity_utils.get_activity_id(activities, activity_name))
    except ValueError as error:
      raise TimelineError(error)

  def print_status(self) -> None:
    print(f"Status for '{self.username}':")
    activity = self.current_activity()
    if activity is not None:
      category = activity_utils.find_activity(self.timeline["activities"],
                                          activity["name"])
      if category is None:
        raise TimelineError("Malformed timeline file. Category name "
                            f"'{activity['name']}' does not have corresponding "
                            "entry inside 'activities' dictionary.")
      path = category.path
      print(f"You are currently doing '{'/'.join(path)}/{activity['name']}'")
      phrase = elapsed_time_phrase(activity["start"])
      print(f"You have been doing so for {phrase}.")
    else:
      print(f"There is no ongoing activity.")

  def save_timeline_to_file(self) -> None:
    with open(Timeline.resource_filename("timelines",
                                         f"{self.username}.hjson"),
              "w") as timeline:
      timeline.write(hjson.dumps(self.timeline))

  @staticmethod
  def new_timeline(username) -> str:
    user_timeline = Timeline.resource_filename("timelines",
                                               f"{username}.hjson")
    if os.path.exists(user_timeline):
      raise TimelineError(f"User '{username}' already has a timeline.")

    with open(user_timeline, "w") as out:
      out.write(hjson.dumps(Timeline.blank_timeline()))
    return user_timeline

  @staticmethod
  def blank_timeline() -> Dict:
    with open(Timeline.resource_filename("blank_timeline.hjson")) as blank:
      return hjson.loads(blank.read())

  @staticmethod
  def resource_filename(*files) -> str:
    return pkg_resources.resource_filename("lifelib",
                                           os.path.join("data", *files))

  @staticmethod
  def load_timeline(username) -> Dict:
    try:
      with open(Timeline.resource_filename("timelines",
                                           f"{username}.hjson")) as timeline:
        return hjson.loads(timeline.read())
    except FileNotFoundError:
      raise TimelineError(f"User '{username}' does not exist.")

  @staticmethod
  def default_user():
    return Timeline.current_state["default_user"]

  @staticmethod
  def set_default_user(username) -> None:
    user_timeline = Timeline.resource_filename("timelines",
                                               f"{username}.hjson")
    if os.path.exists(user_timeline):
      Timeline.current_state["default_user"] = username
      Timeline.save_current_state_to_file()
    else:
      raise TimelineError(f"User '{username}' does not exist. "
                          "Create this user with the command"
                          f"\n\n    life --new '{username}'")

  @staticmethod
  def get_current_state_from_file() -> Dict[str, str]:
    with open(Timeline.resource_filename("state.hjson")) as state:
      return hjson.loads(state.read())

  @staticmethod
  def save_current_state_to_file() -> None:
    with open(Timeline.resource_filename("state.hjson"), "w") as state:
      state.write(hjson.dumps(Timeline.current_state))


Timeline.current_state = Timeline.get_current_state_from_file()
