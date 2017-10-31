import json


def writejson(path, jd):
    with open(path, 'w') as outfile:
        json.dump(jd, outfile, indent=2,
                  sort_keys=True, separators=(',', ':'))


def getjson(path):
    with open(path) as fn:
        jd = json.load(fn)
    return jd


if __name__ == "__main__":
    factoids = getjson("new_factoid_db.json")
    wordsearches = getjson("new_wordsearch_db.json")
    new_db = factoids + wordsearches
    writejson("new_db.json", new_db)
