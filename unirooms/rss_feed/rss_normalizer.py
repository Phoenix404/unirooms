import re
import os
import json
from datetime import datetime, timezone

# lecture_type = {'lect': 'LECT', 'lab': 'LAB', 'unknown': 'UNKNOWN'}
lecture_type = ['LECT', 'LAB', 'EXERCISE']


def normalize_feed(feed):
    lectures = []
    with open(os.getenv("ROOMS_JSON_FILE"), 'r') as f:
        rooms_db = json.load(f)
        f.close()
    for entry in feed.entries:
        entry = entry.summary
        entry = entry.split(' - ')
        if len(entry) < 5:
            continue

        # date and time
        date = entry[0]
        time = entry[1].split('-')
        if len(time) < 2:  # sometimes feed returns only start hour not end hour or just end hours. So we can ignore it
            continue
        start_time_timestamp = _datetime_str_to_timestamp(date, time[0])
        end_time_timestamp = _datetime_str_to_timestamp(date, time[1])

        # lecture title and type
        lect_type = _get_lecture_type(entry[2])
        if lect_type == "UNKNOWN":
            continue

        title = " ".join(entry[2].split(" ")[:-1])

        # location
        location = entry[3] + " "  # end white space is needed
        match_location = re.match("([A-Za-z]\d.[\d]{2}\s+)|([A-Za-z][0-9]{3}\s+)", location)

        if not match_location:
            continue
        building = location[0]
        floor = location[1]
        room = location[2:5].replace(".", "").strip()
        # lecturer
        lecturer = entry[4]
        room_id = building + floor + "." + room
        if room_id not in rooms_db:
            rooms_db[room_id] = {"last_used": start_time_timestamp, "is_active": 1}  # is_active in useless. Maybe in future it will be deprected
        else:
            rooms_db[room_id]["last_used"] = start_time_timestamp

        lecture_object = {
            "building": building,
            "floor": floor,
            "room": room,
            "start-timestamp": start_time_timestamp,
            "end-timestamp": end_time_timestamp,
            "title": title,
            "type": lect_type,
            "lecturer": lecturer
        }
        lectures.append(lecture_object)
    with open(os.getenv("ROOMS_JSON_FILE"), 'w') as f:
        json.dump(rooms_db, f, indent=4)
        f.close()
    return lectures


def _datetime_str_to_timestamp(date_str, time_str):
    date_str = date_str.split('.')
    day = int(date_str[0])
    month = int(date_str[1])
    year = int(date_str[2])

    time_str = time_str.split(':')
    hour = int(time_str[0])
    minute = int(time_str[1])

    d = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return datetime.timestamp(d)


def _get_lecture_type(title):
    words = title.split(" ")
    if len(words) == 0:
        return "UNKNOWN"
    lect_type = words[-1]
    if lect_type not in lecture_type:
        lect_type = "UNKNOWN"
    return lect_type
