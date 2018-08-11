import uuid

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Activity:
  name: str
  uuid: str
  is_leaf: bool
  path: list


def create_new_activity(activities: Dict[str, Any],
                        activity_name: str) -> Optional[str]:
  def traverse(activity_node: Dict[str, Any], path: List[str] = None) -> str:
    if path is None:
      path = []

    if path:
      print(f"Current category: {'.'.join(path)}")
    else:
      print(f"Current category: [root of category tree]")

    nodes = []
    # TODO: have an option for creating new sub-categories if none of the
    # 1-n work.
    for i, (name, (sub_uuid, sub_activities)) in enumerate(activity_node.items()):
      print(f"  ({i+1}) {name}")
      nodes.append((name, sub_uuid, sub_activities))

    category = input("Which category? (press enter to create one here) ")
    if category:
      if category.isdigit():
        name, sub_uuid, sub_activities = nodes[int(category) - 1]
      elif category:
        name = category.lower()
        sub_uuid, sub_activities = activity_node[name]

      if sub_activities is None:
        uid = str(uuid.uuid4())
        activity_node[name] = (sub_uuid, {activity_name: (uid, None)})
        return uid
      else:
        return traverse(sub_activities, path=[*path, name])

    else:
      uid = str(uuid.uuid4())
      activity_node[activity_name] = (uid, None)
      return uid

  create = input(f"The activity '{activity_name}' does not exist. "
                 "Would you like to create it? (y/n) ")
  while create not in {'y', 'n'}:
    create = input(f"Invalid option '{create}'. Please use (y/n) ")

  if create.lower() == 'y':
    print("Category selection:")
    return traverse(activities)
  else:
    return None


def find_activity(activities: Dict, activity_name: str,
                  path: List[Activity]=None) -> Optional[Activity]:
  if path is None:
    path = []

  for name, (uuid, sub_activities) in activities.items():
    is_leaf = sub_activities is None
    if name == activity_name.lower():
      return Activity(name, uuid, is_leaf, path)

    if not is_leaf:
      found = find_activity(sub_activities, activity_name, [*path, name])
      if found is not None:
        return found
  return None


def get_activity_id(categories: Dict[str, Any],
                    category_name: str) -> Optional[str]:
  category_name = category_name.lower()
  category_path = category_name.split('/')
  if len(category_path) == 1:
    cat = find_activity(categories, category_name)

    if cat is None:
      return create_new_activity(categories, category_name)
    else:
      return cat.uuid
  else:
    # if category_name is in the form cat1/cat2/cat3/
    # create it & it's sub-categories, ala mkdir -p
    curr_categories = categories
    for i, cat_name in enumerate(category_path):
      if cat_name not in curr_categories:
        # we are not at a leaf, but none of the sub-categories match
        if category_path[i:] == []:
          raise ValueError(f"The category '{category_name}' already exists.")
        curr_categories[cat_name] = (
            str(uuid.uuid4()), create_categories(category_path[i + 1:]))
        break
      else:
        # we found a sub-category that matches
        uid, sub_categories = curr_categories[cat_name]

        if sub_categories is None:
          print('leaf')
          # we are at a leaf, but arrived here by following the path
          if category_path[i:] == []:
            raise ValueError(f"The category '{category_name}' already exists.")
          curr_categories[cat_name] = (uid,
                                       create_categories(category_path[i + 1:]))
          break
        else:
          curr_categories = sub_categories

  category = find_activity(categories, category_path[-1])
  if category is None:
    raise RuntimeError("Added new category but it doesn't exist.")
  return category.uuid


def create_categories(category_path: List[str]) -> Optional[Dict[str, Any]]:
  curr_cat: Optional[Dict] = None
  for cat in category_path[::-1]:
    curr_cat = {cat: (str(uuid.uuid4()), curr_cat)}
  return curr_cat
