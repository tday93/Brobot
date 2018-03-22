import json


def write_json(obj, filepath):
    with open(filepath, "w") as fo:
        json.dump(obj, fo, separators=(", ", ": "), indent=2)


def read_json(filepath):
    with open(filepath, "r") as fn:
        fdb = json.load(fn)
        return fdb


if __name__ == "__main__":

    fdb = read_json("factoid_db.json")
    for f in fdb:
        f["trigger_chance"] = 100
    write_json(fdb, "new_factoid_db.json")
