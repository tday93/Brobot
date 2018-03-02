import json


def fork_it_up(message):
    swaps = [("fuck", "fork"), ("shit", "shirt"), ("ass", "ash")]
    for item in swaps:
        if item[0] in message:
            message.replace(item[0], item[1])
    return message


def writejson(path, jd):
    with open(path, 'w') as outfile:
        json.dump(jd, outfile, indent=2,
                  sort_keys=True, separators=(',', ':'))


def getjson(path):
    with open(path) as fn:
        jd = json.load(fn)
    return jd
