import hjson
import os
import pkg_resources

from datetime import datetime


time_format = "%Y-%m-%d_%H:%M:%S"


def utc_time():
  return datetime.utcnow().strftime(time_format)


def utc_date():
  return datetime.utcnow().date().isoformat()


def elapsed_time_phrase(time):
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

  def __init__(self, username=None):
    if username is None:
      username = Timeline.default_user()

    self.username = username
    self.timeline = Timeline.load_timeline(self.username)

  def __del__(self):
    self.save_timeline_to_file()

  def start(self, activity):
    # end any ongoing activity
    if self.current_activity() is not None:
      self.done()

    today = utc_date()

    # add new entry for today if one does not exist
    if today not in self.timeline["timeline"]:
      self.timeline["timeline"][today] = []

    # add activity to today's entry
    activity = {
        "id": activity,
        "start": utc_time()
    }
    self.timeline["timeline"][today].append(activity)
    self.timeline["last_day"] = today

  def done(self):
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
      self.timeline[today] = [finished_activity]

    return (elapsed_time_phrase(current_activity["start"]),
            current_activity["id"])

  def current_activity(self):
    if "last_day" in self.timeline:
      return self.timeline["timeline"][self.timeline["last_day"]][-1]

  def print_status(self):
    print(f"The current user is '{self.username}'")
    activity = self.current_activity()
    if activity is not None:
      print(f"You are currently doing '{activity['id']}'")
      phrase = elapsed_time_phrase(activity["start"])
      print(f"You have been doing so for {phrase}.")
    else:
      print(f"There is no ongoing activity.")

  def save_timeline_to_file(self):
    with open(Timeline.resource_filename("timelines",
                                         f"{self.username}.hjson"),
              "w") as timeline:
      return timeline.write(hjson.dumps(self.timeline))

  @staticmethod
  def new_timeline(username):
    user_timeline = Timeline.resource_filename("timelines",
                                               f"{username}.hjson")
    if os.path.exists(user_timeline):
      raise TimelineError(f"User '{username}' already has a timeline.")

    with open(user_timeline, "w") as out:
      out.write(hjson.dumps(Timeline.blank_timeline()))
    return user_timeline

  @staticmethod
  def blank_timeline():
    with open(Timeline.resource_filename("blank_timeline.hjson")) as blank:
      return hjson.loads(blank.read())

  @staticmethod
  def resource_filename(*files):
    return pkg_resources.resource_filename("lifelib",
                                           os.path.join("data", *files))

  @staticmethod
  def load_timeline(username):
    with open(Timeline.resource_filename("timelines",
                                         f"{username}.hjson")) as timeline:
      return hjson.loads(timeline.read())

  @staticmethod
  def default_user():
    return Timeline.current_state["default_user"]

  @staticmethod
  def set_default_user(username):
    Timeline.current_state["default_user"] = username
    Timeline.save_current_state_to_file()

  @staticmethod
  def get_current_state_from_file():
    with open(Timeline.resource_filename("state.hjson")) as state:
      return hjson.loads(state.read())

  @staticmethod
  def save_current_state_to_file():
    with open(Timeline.resource_filename("state.hjson"), "w") as state:
      return state.write(hjson.dumps(Timeline.current_state))


Timeline.current_state = Timeline.get_current_state_from_file()
