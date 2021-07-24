import json


def read_json(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)


def write_json(dict_obj, filepath):
    with open(filepath, 'w') as file:
        json.dump(dict_obj, file, indent=4)


def rw_json(dict_obj, filepath):
    try:
        db = read_json(filepath)
    except FileNotFoundError:
        db = {}
    db.update(dict_obj)
    write_json(db, filepath)
