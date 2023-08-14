import sys
import re
import gzip
import urllib.parse
import matplotlib.pyplot as plt

def textProcessing(inputFile, outPrefix, tokenize, stoplist, stemming):

    with gzip.open(inputFile, 'rt') as file:
        lines = file.readlines()

    outputTokens = []

    # space separated tokenization
    if tokenize == "spaces":
        for line in lines:
            token_dict = []
            # The re.sub() method replaces one or more whitespace characters with a single space character.
            line = re.sub(r'\s+', ' ', line)

            # The strip() method removes any leading or trailing spaces from the line.
            tokens = line.strip().split(' ')
            if len(tokens) >= 1 and tokens[0] != "":
                for token in tokens:
                    token_list = []
                    token_list.append(token)
                    token_list.append(token)
                    token_dict.append(token_list)
            outputTokens.append(token_dict)

    elif tokenize == "fancy":
        for line in lines:
            token_dict = []  # will contain a list of original token and new tokens
            # Removing one or more whitespace characters with a single space character.
            line = re.sub(r'\s+', ' ', line)

            # Removing any leading or trailing spaces from the line.
            tokens = line.strip().split(' ')

            if len(tokens) >= 1 and tokens[0] != "":
                # further processing after space separation
                for token in tokens:
                    org_token = token
                    token_list = []
                    token_list.append(org_token)

                    if "https://" in token or "http://" in token:
                        # Token is a URL, treat it as a single token
                        parsed_url = urllib.parse.urlparse(token.rstrip(r'[-/:;,_=+*~()!@#$%^&*"<>\[\]\{\}\|\\?\s]+'))
                        url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
                        token_list.append(url)
                        if token != org_token:
                            token_list.append(token[len(url):])
                        token_dict.append(token_list)
                        continue

                    if all(re.match(r'^[0-9.,+-]*$', chars) for chars in token):
                        # removing trailing punctuation from numbers
                        token = re.sub(r'[/:;_=*~()!@#$%^&*"<>\[\]\{\}\|\\?\s]+(?![.,+-])', '', token)
                        token_list.append(token)
                        token_dict.append(token_list)
                        continue

                    # applying rules to all non-URLs
                    token = token.lower()

                    # squeezing out apostrophes
                    if "'" in token:
                        token = token.replace("'", "")

                    # treating abbreviations
                    if "." in token and not re.match(r'[-+]?\d+(\.\d+)?([-+]\d+(\.\d+)?)*|(\d+\.){3}\d+', token):
                        token = token.replace(".", "")

                    # processing hyphens
                    if "-" in token:
                        hyphen_sep = token.split("-")
                        token = token.replace("-", "")
                        for t in hyphen_sep:
                            if "." in t and not re.match(r'[-+]?\d+(\.\d+)?([-+]\d+(\.\d+)?)*|(\d+\.){3}\d+', t):
                                # treating abbreviations with hyphens
                                t = t.replace(".", "")
                            # remove trailing punctuation marks
                            t = re.sub(r'[\W_]+$', '', t)
                            # remove leading punctuation marks
                            t = re.sub(r'^[\W_]+', '', t)
                            token_list.append(t)
                        # remove trailing punctuation marks
                        token = re.sub(r'[^\w]+$', '', token)
                        # remove leading punctuation marks
                        token = re.sub(r'^[^\w]+', '', token)

                        token_list.append(token)
                        token_dict.append(token_list)
                    else:
                        # remove trailing punctuation marks
                        token = re.sub(r'[\W_]+$', '', token)
                        # remove leading punctuation marks
                        token = re.sub(r'^[\W_]+', '', token)
                        # treating other punctuation marks (except period, comma, hyphen) as word separator
                        token = re.sub(r'[^\w.-]', ' ', token)
                        token_list.extend(token.split())
                        token_dict.append(token_list)

            if len(token_dict) >= 1:
                outputTokens.append(token_dict)

    # outputTokens is the list of dictionaries of tokens of each line

    # performing stopping
    if stoplist == "yesStop":
        stop_list_tokens = ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "with"]
        for tokens_line in outputTokens:
            for token in tokens_line:
                k = 1
                while k < len(token):
                    to_check = token[k]
                    if to_check.isalpha() and to_check in stop_list_tokens:
                        token.remove(to_check)
                    else:
                        k += 1

    # performing stemming
    if stemming == "porterStem":
        vowels = ["a", "e", "i", "o", "u", "y"]
        # step_1a
        for tokens_line in outputTokens:
            for token in tokens_line:
                for i in range(1, len(token)):
                    to_stem = token[i]
                    if to_stem.endswith("sses"):
                        token[i] = to_stem[:-4] + "ss"
                    elif to_stem.endswith("ies") or to_stem.endswith("ied"):
                        if len(to_stem) > 4:
                            token[i] = to_stem[:-3] + "i"
                        else:
                            token[i] = to_stem[:-3] + "ie"
                    elif to_stem.endswith("ss") or to_stem.endswith("us"):
                        continue
                    elif to_stem.endswith("s"):
                        preceeding = to_stem[-2]
                        if preceeding in vowels:
                            if any((chars in vowels and chars != preceeding) for chars in to_stem[:-2]):
                                token[i] = to_stem[:-1]
                        else:
                            token[i] = to_stem[:-1]
                    else:
                        continue

        # Step 1b
        for tokens_line in outputTokens:
            for token in tokens_line:
                for i in range(1, len(token)):
                    to_stem = token[i]

                    # stemming for "eedly" or "eed"
                    if to_stem.endswith("eedly") or to_stem.endswith("eed"):
                        if to_stem.endswith("eedly"):
                            if len(to_stem) > 6:
                                if to_stem[:-5][-1] not in vowels:
                                    token[i] = to_stem[:-5] + "ee"
                        elif to_stem.endswith("eed"):
                            if len(to_stem) > 4:
                                if to_stem[:-3][-1] not in vowels:
                                    token[i] = to_stem[:-3] + "ee"
                        else:
                            continue

                    # stemming for "ed", "edly", "ing", or "ingly"
                    elif to_stem.endswith("ingly") or to_stem.endswith("edly") or to_stem.endswith("ing") or to_stem.endswith("ed"):
                        if to_stem.endswith("ingly"):
                            suf_index = to_stem.rindex("ingly")

                            # if the preceding stem part does contain a vowel
                            if any(alph in vowels for alph in to_stem[:suf_index]):

                                # deleting the ending
                                to_stem = to_stem[:suf_index]

                                if to_stem.endswith("at") or to_stem.endswith("bl") or to_stem.endswith("iz"):
                                    # adding e
                                    to_stem = to_stem + "e"

                                elif to_stem[-2:] in {'bb', 'dd', 'ff', 'gg', 'mm', 'nn', 'pp', 'rr', 'tt'}:
                                    # just removing the last character
                                    to_stem = to_stem[:len(to_stem)-1]

                                elif (len(to_stem) == 2 and to_stem[0] in vowels and to_stem[1] not in vowels) or ((to_stem[len(to_stem) - 1] not in vowels and to_stem[len(to_stem) - 1] != "w" and to_stem[len(to_stem) - 1] != "x") and to_stem[len(to_stem) - 2] in vowels and all(char not in vowels for char in to_stem[:len(to_stem) - 2])):
                                    to_stem = to_stem + "e"

                            else:
                                continue
                            token[i] = to_stem

                        elif to_stem.endswith("edly"):
                            suf_index = to_stem.rindex("edly")

                            # if the preceding stem part does contain a vowel
                            if any(alph in vowels for alph in to_stem[:suf_index]):

                                # deleting the ending
                                to_stem = to_stem[:suf_index]

                                if to_stem.endswith("at") or to_stem.endswith("bl") or to_stem.endswith("iz"):
                                    # adding e
                                    to_stem = to_stem + "e"

                                elif to_stem[-2:] in {'bb', 'dd', 'ff', 'gg', 'mm', 'nn', 'pp', 'rr', 'tt'}:
                                    # just removing the last character
                                    to_stem = to_stem[:len(to_stem)-1]

                                elif (len(to_stem) == 2 and to_stem[0] in vowels and to_stem[1] not in vowels) or ((to_stem[len(to_stem) - 1] not in vowels and to_stem[len(to_stem) - 1] != "w" and to_stem[len(to_stem) - 1] != "x") and to_stem[len(to_stem) - 2] in vowels and all(char not in vowels for char in to_stem[:len(to_stem) - 2])):
                                    to_stem = to_stem + "e"

                            else:
                                continue
                            token[i] = to_stem

                        elif to_stem.endswith("ing"):
                            suf_index = to_stem.rindex("ing")

                            # if the preceding stem part does contain a vowel
                            if any(alph in vowels for alph in to_stem[:suf_index]):

                                # deleting the ending
                                to_stem = to_stem[:suf_index]

                                if to_stem.endswith("at") or to_stem.endswith("bl") or to_stem.endswith("iz"):
                                    # adding e
                                    to_stem = to_stem + "e"

                                elif to_stem[-2:] in {'bb', 'dd', 'ff', 'gg', 'mm', 'nn', 'pp', 'rr', 'tt'}:
                                    # just removing the last character
                                    to_stem = to_stem[:len(to_stem) - 1]

                                elif (len(to_stem) == 2 and to_stem[0] in vowels and to_stem[1] not in vowels) or ((to_stem[len(to_stem) - 1] not in vowels and to_stem[len(to_stem) - 1] != "w" and to_stem[len(to_stem) - 1] != "x") and to_stem[len(to_stem) - 2] in vowels and all(char not in vowels for char in to_stem[:len(to_stem) - 2])):
                                    to_stem = to_stem + "e"

                            else:
                                continue
                            token[i] = to_stem

                        elif to_stem.endswith("ed"):
                            suf_index = to_stem.rindex("ed")

                            # if the preceding stem part does contain a vowel
                            if any(alph in vowels for alph in to_stem[:suf_index]):

                                # deleting the ending
                                to_stem = to_stem[:suf_index]

                                if to_stem.endswith("at") or to_stem.endswith("bl") or to_stem.endswith("iz"):
                                    # adding e
                                    to_stem = to_stem + "e"

                                elif to_stem[-2:] in {'bb', 'dd', 'ff', 'gg', 'mm', 'nn', 'pp', 'rr', 'tt'}:
                                    # just removing the last character
                                    to_stem = to_stem[:len(to_stem)-1]

                                elif (len(to_stem) == 2 and to_stem[0] in vowels and to_stem[1] not in vowels) or ((to_stem[len(to_stem)-1] not in vowels and to_stem[len(to_stem)-1] != "w" and to_stem[len(to_stem)-1] != "x") and to_stem[len(to_stem)-2] in vowels and all(char not in vowels for char in to_stem[:len(to_stem)-2])):
                                    to_stem = to_stem + "e"
                                else:
                                    token[i] = to_stem
                            else:
                                continue
                            token[i] = to_stem

        # Step 1c
        for tokens_line in outputTokens:
            for token in tokens_line:
                for i in range(1, len(token)):
                    to_stem = token[i]

                    if to_stem.endswith("y"):
                        if to_stem.endswith("y") and len(to_stem) > 2 and (to_stem[len(to_stem)-2] not in vowels):
                            to_stem = to_stem[:len(to_stem)-1] + "i"
                    else:
                        continue
                    token[i] = to_stem

    # writing output to files
    outputFileName = outPrefix + "-tokens.txt"
    outputFileNameHeaps = outPrefix + "-heaps.txt"
    outputFileNameStats = outPrefix + "-stats.txt"

    x_axis = [] # total words
    y_axis = [] # unique words/vocabulary
    with open(outputFileName, "w") as output:
        tens_count = 0
        unique = 0
        visited = {}
        for tokens_line in outputTokens:
            for token in tokens_line:
                if len(token) > 1:
                    output.write(token[0] + " ")
                    for i in range(1, len(token)-1):
                        tens_count += 1
                        mod_tokens = token[i]
                        output.write(mod_tokens+" ")
                        if token[i] not in list(visited.keys()):
                            visited[token[i]] = 1
                            unique += 1
                        else:
                            visited[token[i]] += 1
                    output.write(token[len(token)-1] + "\n")
                    tens_count += 1
                    if token[len(token)-1] not in visited:
                        unique += 1
                        visited[token[len(token)-1]] = 1
                    else:
                        visited[token[len(token) - 1]] += 1
                elif len(token) == 1:
                    output.write(token[0] + "\n")
                if tens_count % 10 == 0 and tens_count != 0:
                    x_axis.append(tens_count)
                    y_axis.append(unique)
                    outputFileNameHeaps = outputFilePrefix + "-heaps.txt"
                    with open(outputFileNameHeaps, "a") as output_heaps:
                        output_heaps.write(str(tens_count) + " " + str(unique) + "\n")
        last_open = open(outputFileNameHeaps, "a")
        last_open.write(str(tens_count) + " " + str(unique) + "\n")

        # writing to stats file
        sorted_tuples = sorted(visited.items(), key=lambda item: (-item[1], item[0]))
        sorted_dict = {k: v for k, v in sorted_tuples}

        with open(outputFileNameStats, "w") as outputStats:
            outputStats.write(str(tens_count) + "\n")
            outputStats.write(str(unique) + "\n")
            count = 0
            unique_tokens = list(sorted_dict.keys())
            if len(unique_tokens) >= 100:
                while count < 100:
                    outputStats.write(str(unique_tokens[count]) + " " + str(sorted_dict[unique_tokens[count]]) + "\n")
                    count += 1
            else:
                while count < len(unique_tokens):
                    outputStats.write(str(unique_tokens[count]) + " " + str(sorted_dict[unique_tokens[count]]) + "\n")
                    count += 1

        # creating heaps law graph -> unique-words vs total words
        # Create a plot using Matplotlib
        plt.plot(x_axis, y_axis)
        plt.title('Word Frequency Distribution')
        plt.xlabel('Words in Collection')
        plt.ylabel('Words in Vocabulary')

        # Save the plot as a JPG file
        plt.savefig('heaps.jpg')

    return


if __name__ == '__main__':
    # Read arguments from command line; or use sane defaults for IDE.
    argv_len = len(sys.argv)
    inputFile = sys.argv[1] if argv_len >= 2 else "sense-and-sensibility.gz"
    outputFilePrefix = sys.argv[2] if argv_len >= 3 else "SAS"
    tokenize_type = sys.argv[3] if argv_len >= 4 else "fancy"
    stoplist_type = sys.argv[4] if argv_len >= 5 else "yesStop"
    stemming_type = sys.argv[5] if argv_len >= 6 else "porterStem"

    # Below is stopword list
    stopword_lst = stopword_lst = ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
                    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the", "to",
                    "was", "were", "with"]

    textProcessing(inputFile, outputFilePrefix, tokenize_type, stoplist_type, stemming_type)
