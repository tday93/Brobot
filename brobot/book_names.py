import markovify


def wordcorpus(sep1, datain):

    d = str(datain)
    l1 = d.split(sep1)
    lo = []

    for l in l1:
        l = [c for c in l]
        lo.append(l)
    l2 = [x for x in lo if x != []]
    return l2


with open('data/bible_book_names.txt') as fn:
    names = fn.readlines()
    namestring = ' '.join(names)
    namestring = namestring.lower()
    namestring = namestring.replace('\n', ' ').replace('\r', ' ')
    corpus = wordcorpus(' ', namestring)

name_chain = markovify.Chain(corpus, 2)

# name_list = c.walk()
# name = "".join(name_list)
