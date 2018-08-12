from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class Activity:
  name: str
  uuid: str
  is_leaf: bool
  path: Tuple[str, ...]


class UserExitError(RuntimeError):
  pass


def new_uuid() -> str:
  import uuid
  return str(uuid.uuid4())


def create_new_activity(activity_node: Dict[str, Any],
                        activity_name: str) -> Activity:
  def create_new_activity_(activity_node: Dict[str, Any],
                           path: Tuple[str, ...] = ()):
    if path:
      print(f"Current activity path: {'.'.join(path)}")
    else:
      print(f"Current activity path: [root of activity tree]")

    nodes = list(activity_node.items())
    for i, (name, _) in enumerate(nodes):
      print(f"  ({i+1}) {name}")

    choice = input("Which sub-activity? (press enter to create a it here) ")
    if choice:
      if choice.isdigit():
        choice_name, (choice_uuid, sub_activities) = nodes[int(choice) - 1]
      else:
        choice_name = choice.lower()
        choice_uuid, sub_activities = activity_node[choice_name]

      if sub_activities is None:
        # the chosen sub-activity is a leaf, so we have to give it
        # a new child node. So, we create a uuid for the activity we are
        # creating and add it to the chosen sub-activity
        new_activity_uuid = new_uuid()
        activity_node[choice_name] = (
            choice_uuid, {activity_name: (new_activity_uuid, None)})
        return Activity(name=activity_name,
                        uuid=new_activity_uuid,
                        is_leaf=False,
                        path=path)
      else:
        # the chosen sub-activity is not a leaf, so keep traversing
        return create_new_activity_(sub_activities, path=(*path, choice_name))
    else:
      # creating the sub-activity here
      new_activity_uuid = new_uuid()
      activity_node[activity_name] = (new_activity_uuid, None)
      return Activity(name=activity_name,
                      uuid=new_activity_uuid,
                      is_leaf=False,
                      path=path)

  choice = input(f"The activity '{activity_name}' does not exist. "
                 "Would you like to create it? (y/n) ")
  while choice not in {'y', 'n'}:
    choice = input(f"Invalid option '{choice}'. Please use (y/n) ")

  if choice == 'y':
    print("Activity selection:")
    return create_new_activity_(activity_node)
  else:
    raise UserExitError("User cancelled activity creation.")


def find_activity(activities: Dict,
                  name: Optional[str] = None,
                  uuid: Optional[str] = None,
                  path: Tuple[str, ...] = ()) -> Optional[Activity]:
  def create_compare_func(name: Optional[str],
                          uuid: Optional[str]) -> Callable[[str, str], bool]:
    if (name and uuid) or ({name, uuid} == {None}):
      raise ValueError(
          "find_activity: must pass exactly one of 'name' or 'uuid'.")
    if name:
      return lambda name_, _: name_ == name
    return lambda _, uuid_: uuid_ == uuid

  # TODO handle activities with the same name
  is_key = create_compare_func(name, uuid)

  for test_name, (test_uuid, sub_activities) in activities.items():
    is_leaf = sub_activities is None
    if is_key(test_name, test_uuid):
      return Activity(test_name, test_uuid, is_leaf, path)

    if not is_leaf:
      found = find_activity(sub_activities, name, uuid, (*path, test_name))
      if found is not None:
        return found
  return None


def get_activity_id(activities: Dict[str, Any],
                    activity_name: str) -> str:
  activity_name = activity_name.lower()
  path = activity_name.split('/')

  if len(path) == 1:
    activity = find_activity(activities, activity_name)

    if activity is None:
      return create_new_activity(activities, activity_name).uuid
    else:
      return activity.uuid
  else:
    # if activity_name is in the form cat1/cat2/cat3/
    # create it & it's sub-activities, ala mkdir -p
    activity_node = activities
    for i, name in enumerate(path):
      if name not in activity_node:
        # we're not a leaf, but none of the sub-activities match
        # make the rest of the path
        if path[i:] == []:
          raise ValueError(f"The activity '{activity_name}' already exists.")
        activity_node[name] = (new_uuid(), create_activity_path(path[i + 1:]))
        break

      else:
        # we found a sub-activity that matches
        uuid, sub_activities = activities[name]

        if sub_activities is None:
          # we are at a leaf, but arrived here by following the path
          # make the rest of the path
          if path[i:] == []:
            raise ValueError(f"The activity '{activity_name}' already exists.")
          activity_node[name] = (uuid, create_activity_path(path[i + 1:]))
          break

        else:
          # we are not at a leaf, keep looking
          activity_node = sub_activities

  activity = find_activity(activities, path[-1])
  if activity is None:
    raise RuntimeError("Added new activity but it doesn't exist.")
  return activity.uuid


def create_activity_path(activity_path: List[str]) -> Optional[Dict[str, Any]]:
  activity_node: Optional[Dict] = None
  for name in reversed(activity_path):
    activity_node = {name: (new_uuid(), activity_node)}
  return activity_node
