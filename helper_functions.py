import json


def fork_it_up(message):
    swaps = [("fuck", "fork"), ("shit", "shirt"), ("ass", "ash")]
    for item in swaps:
        if item[0] in message:
            message.replace(item[0], item[1])
    return message


def syllable_count(text):
    words = text.split()
    total_syls = 0
    for word in words:
        total_syls += word_syllables(word)
    return total_syls


def word_syllables(word):
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
            if word.endswith("e"):
                count -= 1
    if count == 0:
        count += 1
    return count


def writejson(path, jd):
    with open(path, 'w') as outfile:
        json.dump(jd, outfile, indent=2,
                  sort_keys=True, separators=(',', ':'))


def getjson(path):
    with open(path) as fn:
        jd = json.load(fn)
    return jd
