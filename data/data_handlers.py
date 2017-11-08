import json


class DataHandler:

    def __init__(self):
        self.fdb = self.getjson("data/factoid_db.json")
        self.qdb = self.getjson("data/quotes.json")
        self.bands = self.getjson("data/bands.json")
        self.miscdata = self.getjson("data/miscdata.json")

    def cleanup(self):
        self.writejson("data/factoid_db.json", self.fdb)
        self.writejson("data/quotes.json", self.qdb)
        self.writejson("data/bands.json", self.bands)
        self.writejson("data/miscdata.json", self.miscdata)

    def writejson(self, path, jd):
        with open(path, 'w') as outfile:
            json.dump(jd, outfile, indent=2,
                      sort_keys=True, separators=(',', ':'))

    def getjson(self, path):
        with open(path) as fn:
            jd = json.load(fn)
        return jd
