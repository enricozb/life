from datetime import datetime


time_format = "%Y-%m-%d_%H:%M:%S"


def utc_date() -> str:
  return datetime.utcnow().date().isoformat()


def utc_time() -> str:
  return datetime.utcnow().strftime(time_format)


def elapsed_time_phrase(time: str) -> str:
  then = datetime.strptime(time, time_format)
  now = datetime.strptime(utc_time(), time_format)
  diff = now - then

  elapsed = int(diff.total_seconds())
  hours = elapsed // 3600
  minutes = (elapsed // 60) % 60
  seconds = elapsed % 60

  return f"{hours} hours {minutes} minutes and {seconds} seconds"
