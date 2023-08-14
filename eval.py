# import package ...
import math
import sys



def eval(trecrunFile, qrelsFile, outputFile):
    # to read trecrunFile
    query_results = {}
    # format -> {query : {docID: [rank, score, run_text]}}

    with open(trecrunFile, 'r') as f:
        for line in f:
            parts = line.split()
            query_name = parts[0]
            # parts[1] -> skip
            doc_id = parts[2]
            rank = int(parts[3])
            score = float(parts[4])
            run_text = parts[5]
            if query_name not in query_results:
                query_results[query_name] = {}
            query_results[query_name][doc_id] = [rank, score, run_text]

    # to read qrelsFile
    qrels = {}
    # format -> {queryname : {docID: relevance for that doc query pair}}
    # query_name in trecrun file is corresponding to query here

    with open(qrelsFile, 'r') as f:
        for line in f:
            query, _, doc_id, relevance = line.strip().split()
            if query not in qrels:
                qrels[query] = {}
            qrels[query][doc_id] = int(relevance)

    query_stats = {}
    # format -> {query_name : [numRel, relFound, rr, p@10, recall@10, F1@10, P@20% recall]}

    # calculating NDCG @ 20
    for q in list(query_results.keys()):

        # calculating DCG
        dcg = 0
        for doc in list(query_results[q].keys())[0:20]:
            if query_results[q][doc][0] <= 20:
                if doc in list(qrels[q].keys()):
                    if query_results[q][doc][0] > 1:
                        dcg += qrels[q][doc] / math.log2(query_results[q][doc][0])
                    elif query_results[q][doc][0] == 1:
                        dcg += qrels[q][doc]
                else:
                    dcg += 0

        # calculating IDCG
        dict_ret = {}
        for doc in list(qrels[q].keys()):
            dict_ret[doc] = qrels[q][doc]

        # sorting in decreasing order of relevance
        sorted_tuples = sorted(dict_ret.items(), key=lambda item: -item[1])
        sorted_dict = {k: v for k, v in sorted_tuples}

        idcg = 0
        i = 1
        for d in list(sorted_dict.keys())[0:20]:
            if i <= 20:
                if math.log2(i) != 0:
                    idcg += sorted_dict[d] / math.log2(i)
                else:
                    idcg += sorted_dict[d]
                i += 1

        # calculating NDCG
        if idcg != 0:
            ndcg = dcg / idcg
        query_stats[q] = [ndcg]

    # calculating numRel
    for q in list(query_results.keys()):
        count = 0
        if q in list(qrels.keys()):
            for doc in list(qrels[q].keys()):
                if qrels[q][doc] > 0:
                    count += 1
        query_stats[q].append(count)
        if count == 0:
            query_stats[q][0] = 0

    # calculating relFound
    for q in list(query_results.keys()):
        count = 0
        if q in list(qrels.keys()):
            for doc in (qrels[q].keys()):
                if qrels[q][doc] > 0:
                    if q in list(query_results.keys()) and doc in list(query_results[q].keys()):
                        count += 1
        query_stats[q].append(count)

    # calculating reciprocal rank
    for q in list(query_results.keys()):
        if query_stats[q][2] == 0:
            query_stats[q].append(0)
        else:
            for doc in list(query_results[q].keys()):
                if q in list(qrels.keys()) and doc in list(qrels[q].keys()) and qrels[q][doc] > 0:
                    rr = 1 / query_results[q][doc][0]
                    break
            query_stats[q].append(rr)

    # calculating precision @ 10
    for q in list(query_results.keys()):
        list_till_ten = []
        count = 0
        for doc in list(query_results[q].keys()):
            if count < 10:
                list_till_ten.append(doc)
                count += 1
        rel = 0
        for docu in list_till_ten:
            if q in list(qrels.keys()) and docu in list(qrels[q].keys()) and qrels[q][docu] > 0:
                rel += 1
        p_at_ten = rel / 10
        query_stats[q].append(p_at_ten)

    # calculating recall @ 10
    for q in list(query_results.keys()):
        if query_stats[q][1] == 0:
            query_stats[q].append(0)
        else:
            total_rel = []
            for doc in list(query_results[q].keys()):
                if doc in list(qrels[q].keys()) and qrels[q][doc] > 0:
                    total_rel.append(doc)
            rel_in_ten = 0
            for rel_doc in total_rel:
                if query_results[q][rel_doc][0] in range(1, 11):
                    rel_in_ten += 1
            recall = rel_in_ten / query_stats[q][1]
            query_stats[q].append(recall)

    # calculating F1@10
    for q in list(query_results.keys()):
        if query_stats[q][4] == 0 or query_stats[q][5] == 0:
            query_stats[q].append(0)
        else:
            f1_at_ten = (2 * query_stats[q][4] * query_stats[q][5]) / (query_stats[q][4] + query_stats[q][5])
            query_stats[q].append(f1_at_ten)

    # # calculating P@20% recall
    for q in list(query_results.keys()):
        if query_stats[q][1] == 0:
            query_stats[q].append(0)
        else:
            p = []
            count = 0
            rel = 0
            for doc in list(query_results[q].keys()):
                count += 1
                if doc in list(qrels[q].keys()) and qrels[q][doc] > 0:
                    rel += 1
                    recall = rel / query_stats[q][1]
                    if recall >= 0.20:
                        p.append(rel/count)
            if len(p) != 0:
                query_stats[q].append(max(p))
            else:
                query_stats[q].append(0)

    # calculating average precision
    for q in list(query_results.keys()):
        retrieved = 0
        rel_so_far = 0
        recall = 0
        p_sum = 0
        rel_docs_not_retrieved = sum([1 for doc in qrels[q] if qrels[q][doc] > 0 and doc not in query_results[q]])
        for doc in list(query_results[q].keys()):
            retrieved += 1
            if doc in list(qrels[q].keys()) and qrels[q][doc] > 0:
                rel_so_far += 1
            if query_stats[q][1] != 0:
                new_recall = rel_so_far / query_stats[q][1]
                if new_recall != recall:
                    p_at_k = rel_so_far / retrieved
                    p_sum += p_at_k
                    recall = new_recall
        if rel_so_far > 0:
            average_precision = p_sum / query_stats[q][1]
        else:
            average_precision = 0
        query_stats[q].append(average_precision)


    sum_ndcg = 0
    sum_numrel = 0
    sum_relfound = 0
    sum_rr = 0
    sum_p = 0
    sum_r = 0
    sum_f_one = 0
    sum_p_perc = 0
    sum_ap = 0

    for q in query_stats.keys():
        sum_ndcg += query_stats[q][0]
        sum_numrel += query_stats[q][1]
        sum_relfound += query_stats[q][2]
        sum_rr += query_stats[q][3]
        sum_p += query_stats[q][4]
        sum_r += query_stats[q][5]
        sum_f_one += query_stats[q][6]
        sum_p_perc += query_stats[q][7]
        sum_ap += query_stats[q][8]

    l = len(list(query_stats.keys()))
    if l != 0:
        mndcg = sum_ndcg / l
        mnumrel = sum_numrel
        mrelfound = sum_relfound
        mrr = sum_rr / l
        mp = sum_p / l
        mr = sum_r / l
        mfone = sum_f_one / l
        mpatperc = sum_p_perc / l
        map = sum_ap / l

    with open(outputFile, 'w') as wr:
        for q in list(query_stats.keys()):
            wr.write("NDCG@20" + " " + str(q) + " " + "{:.4f}".format(query_stats[q][0]) + "\n")
            wr.write("numRel" + " " + str(q) + " " + str(query_stats[q][1]) + "\n")
            wr.write("relFound" + " " + str(q) + " " + str(query_stats[q][2]) + "\n")
            wr.write("RR" + " " + str(q) + " " + "{:.4f}".format(query_stats[q][3]) + "\n")
            wr.write("P@10" + " " + str(q) + " " + "{:.4f}".format(query_stats[q][4]) + "\n")
            wr.write("R@10" + " " + str(q) + " " + "{:.4f}".format(query_stats[q][5]) + "\n")
            wr.write("F1@10" + " " + str(q) + " " + "{:.4f}".format(query_stats[q][6]) + "\n")
            wr.write("P@20%" + " " + str(q) + " " + "{:.4f}".format(query_stats[q][7]) + "\n")
            wr.write("AP" + " " + str(q) + " " + "{:.4f}".format(query_stats[q][8]) + "\n")
        wr.write("NDCG@20" + " " + "all" + " " + "{:.4f}".format(mndcg) + "\n")
        wr.write("numRel" + " " + "all" + " " + str(mnumrel) + "\n")
        wr.write("relFound" + " " + "all" + " " + str(mrelfound) + "\n")
        wr.write("MRR" + " " + "all" + " " + "{:.4f}".format(mrr) + "\n")
        wr.write("P@10" + " " + "all" + " " + "{:.4f}".format(mp) + "\n")
        wr.write("R@10" + " " + "all" + " " + "{:.4f}".format(mr) + "\n")
        wr.write("F1@10" + " " + "all" + " " + "{:.4f}".format(mfone) + "\n")
        wr.write("P@20%" + " " + "all" + " " + "{:.4f}".format(mpatperc) + "\n")
        wr.write("MAP" + " " + "all" + " " + "{:.4f}".format(map))

    return


if __name__ == '__main__':
    argv_len = len(sys.argv)
    runFile = sys.argv[1] if argv_len >= 2 else "msmarcofull-ql.trecrun"
    qrelsFile = sys.argv[2] if argv_len >= 3 else "msmarco.qrels"
    outputFile = sys.argv[3] if argv_len >= 4 else "ql.eval"

    eval(runFile, qrelsFile, outputFile)
