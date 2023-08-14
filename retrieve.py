# import package ...
import sys
import math
import json
import gzip

global_d = None
global_c = None
global_sas_or = None
global_sas_bm = None

def buildIndex(inputFile):
    # Your function start here ...

    # Opening JSON file
    with gzip.open(inputFile, 'rt') as file:
        lines = file.read()
    j_dict = json.loads(lines)
    articles_list = j_dict["corpus"]
    inv_index = {}
    for article in articles_list:
        terms = article["text"].split(" ")
        count = 0
        for t in terms:
            if t not in inv_index:
                inv_index[t] = {}
                inv_index[t][article["storyID"]] = []
            if article["storyID"] not in list(inv_index[t]):
                inv_index[t][article["storyID"]] = [count]
            else:
                inv_index[t][article["storyID"]].append(count)
            count += 1

    # print(inv_index["united"]["8951-id_6"])
    return inv_index


def find_successors(arr):
    first_array = arr[0]
    for x in first_array:
        successor_found = False
        for j in range(1, len(arr)):
            if x + 1 in arr[j]:
                x += 1
                successor_found = True
            else:
                successor_found = False
                break
        if successor_found is True:
            return True
    return False


def num_successors(arr):
    first_array = arr[0]
    count = 0
    for x in first_array:
        successor_found = False
        for j in range(1, len(arr)):
            if x + 1 in arr[j]:
                x += 1
                successor_found = True
            else:
                break
        if successor_found is True:
            count += 1
    return count


def find_intersection(arr):
    if not arr:  # Handle empty array case
        return set()

    result = arr[0]
    for s in arr[1:]:
        result = result.intersection(s)

    return result


def find_union(arr):
    result = set()
    for s in arr:
        result = result.union(s)

    return result


def c(inputFile):
    global global_c
    count = 0
    with gzip.open(inputFile, 'rt') as file:
        lines = file.read()
    j_dict = json.loads(lines)
    articles_list = j_dict["corpus"]
    for art in articles_list:
        art_list = art["text"].split(" ")
        new_array = remove_empty_strings(art_list)
        count += len(new_array)
    global_c = count
    return

def remove_empty_strings(arr):
    return [x for x in arr if x != '']

def d(inputFile):
    global global_d
    doc_len_list = {}
    with gzip.open(inputFile, 'rt') as file:
        lines = file.read()
    j_dict = json.loads(lines)
    articles_list = j_dict["corpus"]
    for art in articles_list:
        art_list = art["text"].split(" ")
        new_array = remove_empty_strings(art_list)
        doc_len_list[art["storyID"]] = len(new_array)
    global_d = doc_len_list
    return


def runQueries(index, queriesFile, outputFile):
    global global_d
    global global_c
    global global_sas_or
    global global_sas_bm

    qfile = open(queriesFile, 'rt')
    qlines = qfile.read()
    qlist = qlines.split("\n")
    for i in range(0, len(qlist)):
        qlist[i] = qlist[i].split("\t")
    qlist.remove(qlist[len(qlist) - 1])

    with open(outputFile, "w") as wr:
        for query in qlist:
            if query[0].lower() == "and":  # if query type is "and"
                allPhrasesDocs = []
                for ph in query[2:]:
                    if " " not in ph:
                        relDocs = set()
                        for doc in list(index[ph].keys()):
                            relDocs.add(doc)
                        allPhrasesDocs.append(relDocs)
                    else:
                        terms = ph.split(" ")
                        indi_terms_docs = []
                        for t in terms:
                            x = set()
                            for doc in list(index[t].keys()):
                                x.add(doc)
                            indi_terms_docs.append(x)
                        all_terms_doc = find_intersection(
                            indi_terms_docs)  # set of docs containing all the words of phrase

                        rel_docs = set()  # Initialize the set for each phrase with spaces
                        for doc in list(all_terms_doc):
                            doc_pos = []  # positions of individual terms in every doc
                            for t in terms:
                                doc_pos.append(index[t][doc])
                            if find_successors(doc_pos):
                                rel_docs.add(doc)

                        allPhrasesDocs.append(rel_docs)

                and_ans = list(find_intersection(allPhrasesDocs))
                and_ans.sort()
                rank = 0
                for a in and_ans:
                    rank += 1
                    wr.write(query[1] + " " + "skip" + " " + a + " " + str(rank) + " " + "1.0000" + " " + "snimbali" + "\n")

            elif query[0].lower() == "or":  # if query type is "or"
                allPhrasesDocs = []
                for ph in query[2:]:
                    rel_docs = set()  # Initialize the set outside the loop
                    if " " not in ph:
                        for doc in list(index[ph].keys()):
                            rel_docs.add(doc)
                    else:
                        terms = ph.split(" ")
                        indi_terms_docs = []
                        for t in terms:
                            x = set()
                            for doc in list(index[t].keys()):
                                x.add(doc)
                            indi_terms_docs.append(x)
                        all_terms_doc = find_intersection(
                            indi_terms_docs)  # set of docs containing all the words of the phrase

                        for doc in list(all_terms_doc):
                            doc_pos = []  # positions of individual terms in every doc
                            for t in terms:
                                doc_pos.append(index[t][doc])
                            if find_successors(doc_pos):
                                rel_docs.add(doc)
                    allPhrasesDocs.append(rel_docs)
                or_ans = list(find_union(allPhrasesDocs))
                or_ans.sort()

                rank = 0
                for a in or_ans:
                    rank += 1
                    wr.write(query[1] + " " + "skip" + " " + a + " " + str(rank) + " " + "1.0000" + " " + "snimbali" + "\n")

            elif query[0].lower() == "ql":
                myu = 300
                C = global_c
                ql_ans = {}
                for doc in list(global_d.keys()):
                    ql = 0
                    D = global_d[doc]
                    contains_query_term = False  # Flag to check if document contains any query term
                    for ph in query[2:]:
                        if " " not in ph:
                            fq = 0  # Set fq to zero initially
                            if doc in index[ph].keys():
                                fq = len(index[ph][doc])  # freq of the query in the doc
                                contains_query_term = True  # Set the flag to True
                            cq = 0  # freq of the query in the collection
                            for d in index[ph].keys():
                                cq += len(index[ph][d])
                            ql += math.log((fq + (myu * (cq / C))) / (D + myu))
                    if contains_query_term:
                        ql_ans[doc] = ql

                sorted_tuples = sorted(ql_ans.items(), key=lambda item: (-item[1], item[0]))
                ql_ans = {k: v for k, v in sorted_tuples}
                rank = 0
                for a in ql_ans:
                    rank += 1
                    wr.write(query[1] + " " + "skip" + " " + str(a) + " " + str(rank) + " " + "{:.4f}".format(
                        ql_ans[a]) + " " + "snimbali" + "\n")

            elif query[0].lower() == "bm25":  # if query type is "bm25"
                k1 = 1.8
                k2 = 5
                b = 0.75
                N = len(global_d)  # number of documents
                s = 0
                for d in global_d.keys():
                    s += global_d[d]
                avg_doc_len = s / len(global_d)

                ansbm = {}
                for doc in list(global_d.keys()):
                    doc_len = global_d[doc]
                    bm25 = 0
                    for ph in query[2:]:
                        qf = query[2:].count(ph)  # frequency of term in the query
                        if " " not in ph:
                            n = len(list(index[ph].keys()))  # number of documents containing the phrase
                            if doc in index[ph].keys():
                                f = len(index[ph][doc])  # freq of a query in the doc
                                K = k1 * ((1 - b) + b * doc_len / avg_doc_len)
                                bm25 += math.log((N - n + 0.5) / (n + 0.5)) * ((k1 + 1) * f / (K + f)) * ((k2 + 1) * qf / (k2 + qf))

                        else:
                            terms = ph.split(" ")
                            rel_docs = set()
                            indi_terms_docs = []
                            for t in terms:
                                x = set()
                                for d in list(index[t].keys()):
                                    x.add(d)
                                indi_terms_docs.append(x)
                            all_terms_doc = find_intersection(
                                indi_terms_docs)  # set of docs containing all the words of phrase

                            for docu in list(all_terms_doc):
                                doc_pos = []  # positions of individual terms in every doc
                                for t in terms:
                                    doc_pos.append(index[t][docu])
                                if find_successors(doc_pos):
                                    rel_docs.add(docu)
                            n = len(rel_docs)
                            if doc in rel_docs:  # Checking if doc is in rel_docs set
                                pos = []
                                for t in terms:
                                    if doc in index[t].keys():  # Checking if doc is in index[t].keys()
                                        pos.append(index[t][doc])
                                if len(pos) != 0 and find_successors(pos):
                                    f = num_successors(pos) # of phrase (successor sets in pos)
                                    K = k1 * ((1 - b) + b * doc_len / avg_doc_len)
                                    bm25 += math.log((N - n + 0.5) / (n + 0.5)) * ((k1 + 1) * f / (K + f)) * ((k2 + 1) * qf / (k2 + qf))

                        if bm25 != 0:
                            ansbm[doc] = bm25

                sorted_tuples = sorted(ansbm.items(), key=lambda item: (-item[1], item[0]))
                bm_ans = {k: v for k, v in sorted_tuples}

                rank = 0
                for a in bm_ans:
                    rank += 1
                    wr.write(query[1] + " " + "skip" + " " + str(a) + " " + str(rank) + " " + "{:.4f}".format(bm_ans[a]) + " " + "snimbali" + "\n")
    qfile.close()
    return

if __name__ == '__main__':
    # Read arguments from command line, or use sane defaults for IDE.
    argv_len = len(sys.argv)
    inputFile = sys.argv[1] if argv_len >= 2 else "sciam.json.gz"
    queriesFile = sys.argv[2] if argv_len >= 3 else "P3train.tsv"
    outputFile = sys.argv[3] if argv_len >= 4 else "P3train.trecrun"

    index = buildIndex(inputFile)
    d(inputFile)
    c(inputFile)
    runQueries(index, queriesFile, outputFile)
