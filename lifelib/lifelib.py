from lifelib import activity_utils
from lifelib.time_utils import elapsed_time_phrase, utc_date, utc_time

import hjson
import os
import pkg_resources

from typing import Any, Dict, Tuple


def load_state() -> Dict[str, str]:
  with open(resource_filename("state.hjson")) as state:
    return hjson.loads(state.read())


def save_state(state: Dict[str, str]) -> None:
  with open(resource_filename("state.hjson"), "w") as out:
    out.write(hjson.dumps(state))


def default_user() -> str:
  return load_state()["default_user"]


def set_default_user(username: str) -> None:
  if os.path.exists(resource_filename("timelines", f"{username}.hjson")):
    save_state({**load_state(), "default_user": username})
  else:
    raise TimelineError(f"User '{username}' does not exist. "
                        "Create this user with the command"
                        f"\n\n    life --new '{username}'")


def resource_filename(*files) -> str:
  return pkg_resources.resource_filename("lifelib",
                                         os.path.join("data", *files))


def blank_timeline() -> Dict:
  with open(resource_filename("blank_timeline.hjson")) as blank:
    return hjson.loads(blank.read())


def new_timeline(username) -> str:
  user_timeline = resource_filename("timelines", f"{username}.hjson")
  if os.path.exists(user_timeline):
    raise TimelineError(f"User '{username}' already has a timeline.")

  with open(user_timeline, "w") as out:
    out.write(hjson.dumps(blank_timeline()))
  return user_timeline


class TimelineError(RuntimeError):
  pass


class TimelineExit(RuntimeError):
  pass


class Timeline:
  """
  Handles state of current & other timelines.
  """

  def __init__(self, username: str = None) -> None:
    if username is None:
      username = default_user()

    self.username = username
    state = Timeline.load(self.username)
    self.timeline = state["timeline"]
    self.activities = state["activities"]
    self.last_day = state.get("last_day", None)

  def start(self, activity_name: str) -> None:
    # end any ongoing activity
    if self.is_active():
      self.done()

    today = utc_date()

    # add new date entry for today if one does not exist
    if today not in self.timeline:
      self.timeline[today] = []

    event_entry = {
        "id": self.get_activity_id(activity_name),
        "name": activity_name,
        "start": utc_time()
    }

    self.timeline[today].append(event_entry)
    self.last_day = today

  def done(self) -> Tuple[str, str]:
    if not self.is_active():
      raise TimelineError("No ongoing activity to finish.")

    # complete current activity
    current_event = self.current_event()
    current_event["end"] = utc_time()

    # if this event was started on a day other than today, make sure to
    # add a copy of this event to today's date entry on the timeline.
    today = utc_date()
    if self.last_day != today:
      self.timeline[today] = {**current_event, "previous": self.last_day}

    return (current_event["name"], current_event["start"])

  def is_active(self) -> bool:
    return self.last_day is not None

  def current_event(self) -> Dict[str, str]:
    if self.is_active():
      return self.timeline[self.last_day][-1]
    raise RuntimeError(
        "Timeline.current_event called without an ongoing event.")

  def get_activity_id(self, activity_name: str) -> str:
    try:
      return activity_utils.get_activity_id(self.activities, activity_name)
    except ValueError as error:
      raise TimelineError(error)
    except activity_utils.UserExitError as error:
      raise TimelineExit(error)

  def print_status(self) -> None:
    print(f"Status for '{self.username}':")
    if not self.is_active():
      print("There is no ongoing activity.")
    else:
      current_event = self.current_event()
      activity = activity_utils.find_activity(
          self.activities, uuid=current_event["id"])
      if activity is None:
        raise TimelineError("Malformed timeline file. Activity name "
                            f"'{current_event['name']}' does not have "
                            "corresponding entry inside 'activities' "
                            "dictionary.")
      print("You are currently doing "
            f"'{'/'.join(activity.path)}/{activity.name}'")

      phrase = elapsed_time_phrase(current_event["start"])
      print(f"You have been doing so for {phrase}.")

  def save_timeline_to_file(self) -> None:
    with open(resource_filename("timelines", f"{self.username}.hjson"),
              "w") as out:
      out_dict = {
          "timeline": self.timeline,
          "activities": self.activities,
          "last_day": self.last_day
      }
      out.write(hjson.dumps(out_dict))

  @staticmethod
  def load(username) -> Dict[str, Any]:
    try:
      with open(resource_filename("timelines",
                                  f"{username}.hjson")) as timeline:
        return hjson.loads(timeline.read())
    except FileNotFoundError:
      raise TimelineError(f"User '{username}' does not exist.")
