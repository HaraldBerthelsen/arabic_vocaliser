#-*- coding: utf-8 -*-
import sys, codecs, os, re
from pyaramorph.pyaramorph import Analyzer
pyaramorph = Analyzer()

def preprocessBeforeBama(ar_text):
    return ar_text

def runBama(ar_text):
    #Has to be windows-1256 for BAMA?
    outfh = codecs.open("ptemp0.txt","w","windows-1256")
    outfh.write(ar_text)
    outfh.close()

    os.system("./bama/aramorph.sh ptemp0.txt ptemp1.txt 2> /dev/null")

    infh = codecs.open("ptemp1.txt","r")
    bama_pos = infh.read().strip()
    infh.close()

    return bama_pos

def runPyBama(ar_text):
    bama_pos_list = []
    for ar_word in ar_text.split(" "):
        bw_word = ar2bw(ar_word)

        results = pyaramorph.analyze(bw_word)
        #print "RESULTS FOR %s: %s" % (bw_word, results)
        if len(results) > 0:
            for res in results:

                print "RES:", res

                res_lines = res.split("\n")
                pos_line = res_lines[1].strip()
                pos_line = re.sub("pos:\s+", "", pos_line)
                bama_pos_list.append(pos_line)
        bama_pos_list.append("") #word separator!

    bama_pos = "\n".join(bama_pos_list)
    return bama_pos

#Todo: these two should be the same (= the second one), change following to allow
#word+analysis in both cases
def runPyBama2(ar_text):
    bama_pos_list = []
    for ar_word in ar_text.split(" "):
        bw_word = ar2bw(ar_word)
        bama_pos_list.append(bw_word)

        results = pyaramorph.analyze(bw_word)
        #print "RESULTS FOR %s: %s" % (bw_word, results)
        if len(results) > 0:
            for res in results:

                print "RES:", res

                res_lines = res.split("\n")
                solution_line = res_lines[0].strip()
                m = re.search(" ([^ \)]+)\)", solution_line)
                vocalised_word = m.group(1)
                pos_line = res_lines[1].strip()
                pos_line = re.sub("pos:\s+", "", pos_line)
                bama_pos_list.append(vocalised_word+" "+pos_line)
        bama_pos_list.append("") #word separator!

    bama_pos = "\n".join(bama_pos_list)
    return bama_pos

def convertBamaToSrilm(bama_pos):
    result = []
    #TODO what does this regexp mean?? I have no example at the moment with multiple sentences
    sentences = re.split("\p{P}\¡\n", bama_pos)
    for sentence in sentences:
        #sys.stderr.write("SENTENCE: "+sentence+"\n")
        #Double newlines separate words
        words = sentence.split("\n\n")

        if len(words) > 0:
            result.append("<s> *noevent*\n")
            for word in words:
                word = word.strip()
                #sys.stderr.write("WORD: "+word+"\n")
                #newline separates readings
                options = word.split("\n")

                #The first is the unvocalised word (using runPyBama2)
                options = options[1:]

                tagList = convertBAMAtag(options)

                optionsList = []
                for tag in tagList:
                    #Todo higher probability in case of TT and P
                    optionsString = "%s %.6f" % (tag, 1.0/len(tagList))
                    optionsList.append(optionsString)

                result.append("w %s\n" % " ".join(optionsList))
            result.append("</s> *noevent*\n")
        #result.append("<s> *noevent*\r\n</s> *noevent*\n")
        #the above is in case there is no word in the sentence?
    resultString = "".join(result).strip()

    return resultString

def convertBAMAtag(options):

    optionsList = []

    for option in options:
        sys.stderr.write("OPTION: %s, type: %s\n" % (option, type(option)))

        #using runPyBama2 there is "word analysis" in each, only the analysis is wanted here
        if " " in option:
            option = option.split(" ")[1]

        P = False
        N = False
        D = False
        V = False
        I = False
        T = False
        A = False
        C = False
        DP = False

        BAMATags = option.split("+")
        for BAMATag in BAMATags:

            #sys.stderr.write("BAMATag: "+BAMATag+"\n")

            #If there is no bama tag at all
            #TODO mark this in some way, it means a words should be added to the dictionary
            if not "/" in BAMATag:
                continue

            curTag = BAMATag.split("/")[1]

            if curTag == "P" or curTag == "PREP":
                P = True
            elif curTag == "N" or curTag == "ADJ" or curTag == "NOUN" or curTag == "NOUN_PROP" or curTag == "PROP_NOUN":
                N = True
            elif curTag == "VPR" or curTag == "VERB_PERFECT":
                V = True
            elif curTag == "VI" or curTag == "VERB_IMPERFECT":
                V = True
                I = True
            elif curTag == "VIM" or curTag == "VERB_IMPERATIVE":
                I = True
            elif curTag == "D" or curTag == "DET":
                D = True
            elif curTag == "ABBREV":
                A = True
            elif curTag == "CONJ":
                C = True
            else:
                T = True
            
        if N:
            if D:
                if P:
                    optionsList.append("P+NDG")
                else:
                    optionsList.append("NDG")
                    optionsList.append("NDN")
                    optionsList.append("NDA")
            else:
                if P:
                    optionsList.append("P+NUG")
                else:
                    optionsList.append("NUG")
                    optionsList.append("NUN")
                    optionsList.append("NUA")
        elif V:
            if I:
                optionsList.append("VIJ")
                optionsList.append("VIS")
                optionsList.append("VID")
            else:
                optionsList.append("VPR")
        elif I:
            optionsList.append("VIM")
        elif P:
            if T:
                optionsList.append("P")
            else:
                #optionsList.append("TT") error?? TT is not in POSNgrams/vocab
                optionsList.append("T")
        elif A:
            optionsList.append("A")
        else:
            optionsList.append("T")

        #sys.stderr.write("OPTIONSLIST: "+str(optionsList)+"\n")

    if "A" in optionsList and not "P" in optionsList:
        optionsList.append("T")

    #remove duplicates
    optionsList = list(set(optionsList))
    if "A" in optionsList:
        optionsList.remove("A")

    return optionsList


def runSRILM(srilm_pos):
    outfh = codecs.open("ptemp2.txt","w")
    outfh.write(srilm_pos)
    outfh.close()

    os.system("./ngram/hidden-ngram -lm ngram/POSNgrams/taggerNgram4.txt -order 4 -text-map ptemp2.txt -hidden-vocab ngram/POSNgrams/vocab.txt > ptemp2a.txt")

    infh = codecs.open("ptemp2a.txt","r")
    srilm_pos = infh.read()
    infh.close()
    return srilm_pos

def removeSentenceBoundaries(res):
    res = re.sub("</s>", "", res).strip()
    res = re.sub("<s>", "", res)
    res = re.sub("\n", "*noevent*", res)
    res = re.sub(" +", " ", res).strip()
    res = re.sub("w ", "", res).strip()

    outfh = codecs.open("ptemp3.txt","w")
    outfh.write(res)
    outfh.close()

    return res;

def runBamaWithTags(ar_text):
    #Has to be windows-1256 for BAMA
    outfh = codecs.open("ptemp4.txt","w","windows-1256")
    outfh.write(ar_text)
    outfh.close()

    os.system("./bama/aramorphWithTags.sh ptemp4.txt ptemp5.txt 2> /dev/null")

    infh = codecs.open("ptemp5.txt","r")
    bama_pos = infh.read()
    infh.close()

    return bama_pos

def filterBamaWithTags(bama_pos, srilm_pos):

    #What is right? It sounds odd to me with case endings but who am I to judge..
    addCaseEndings = False

    taggedBAMA = bama_pos.split("\n\n")
    taggedWords = srilm_pos.split(" ")
    i = 0
    res = []

    #Punctuation can affect this
    #    while i < len(taggedBAMA):
    while i < len(taggedWords):
        options = taggedBAMA[i].strip().split("\n")
        pos = taggedWords[i]

        #sys.stderr.write(options[0]+" "+pos+"\n")

        #unvocalised word
        res.append(options[0])

        for option in options[1:]:
            (voc, bama_tag) = option.split(" ")
            sys.stderr.write("V: %s, T: %s\n" % (voc, bama_tag))
            tags = convertBAMAtag([bama_tag])
            sys.stderr.write("Word: %s, Tags: %s, Pos: %s\n" % (voc, tags, pos))
            #add the vocalised form if the tag matches
            if pos in tags:
                #TODO also add stuff to do with gemination after Al, and case endings

                # ktb #unvocalised word above
                # kataba #I don't think they should appear twice?
                # kataba
                # kutiba
                # kutiba
                
                # AlTfl
                # AlT~ifolu
                # AlT~ifol
                # AlT~afalu
                # AlT~afal
                
                # AlwZyfp
                # AlowaZiyfapu
                # AlowaZiyfap


                #If it's a definite noun
                sun_letters = "tTdDsSzZlrn\$\*"
                if "ND" in pos:
                    #can there be an l before the def art l? preposition!

                    if re.search("^([^l]+)l(["+sun_letters+"])(.+)$", voc):
                        #def.art + sun letter
                        #AlTifol -> AlT~ifol
                        newVoc = re.sub("^([^l]+)l(["+sun_letters+"])(.+)$", r"\1l\2~\3", voc)
                        sys.stderr.write("newVoc (sun): "+newVoc+"\n")
                    else:
                        #def.art + moon letter
                        newVoc = re.sub("^([^l]+)l(.)(.+)$", r"\1lo\2\3", voc)
                        sys.stderr.write("newVoc (moon): "+newVoc+"\n")

                    if addCaseEndings:
                        if "NDG" in pos:
                            #genitive, add -i
                            res.append(newVoc+"i")
                        elif "NDA" in pos:
                            #accusative, add -a
                            res.append(newVoc+"a")
                        elif "NDN" in pos:
                            #nominative, add -u
                            res.append(newVoc+"u")

                    #adding newVoc after inflected, to get same output as FinalDiacritizer
                    res.append(newVoc)



                
                elif "NU" in pos:
                    if addCaseEndings:
                        if "NUG" in pos:
                            #genitive, add -i
                            res.append(voc+"i")
                        elif "NUA" in pos:
                            #accusative, add -a
                            res.append(voc+"a")
                        elif "NUN" in pos:
                            #nominative, add -u
                            res.append(voc+"u")
                    res.append(voc)
                    
                else:
                    #if it's not a noun
                    res.append(voc)
                

            else:
                sys.stderr.write("REMOVING %s %s - does not match %s\n" % (voc, tags, pos))
        res.append("")


        i += 1
        
    outfh = codecs.open("ptemp6.txt","w")
    outfh.write("\n".join(res).strip())
    outfh.close()

    return "\n".join(res).strip()



transliterate = {}

transliterate["'"] = u"ء"
transliterate["|"] = u"آ"
transliterate[">"] = u"أ"
transliterate["&"] = u"ؤ"
transliterate["<"] = u"إ"
transliterate["}"] = u"ئ"
transliterate["A"] = u"ا"
transliterate["b"] = u"ب"
transliterate["p"] = u"ة"
transliterate["t"] = u"ت"
transliterate["v"] = u"ث"
transliterate["j"] = u"ج"
transliterate["H"] = u"ح"
transliterate["x"] = u"خ"
transliterate["d"] = u"د"
transliterate["*"] = u"ذ"
transliterate["r"] = u"ر"
transliterate["z"] = u"ز"
transliterate["s"] = u"س"
transliterate["$"] = u"ش"
transliterate["S"] = u"ص"
transliterate["D"] = u"ض"
transliterate["T"] = u"ط"
transliterate["Z"] = u"ظ"
transliterate["E"] = u"ع"
transliterate["g"] = u"غ"
transliterate["f"] = u"ف"
transliterate["q"] = u"ق"
transliterate["k"] = u"ك"
transliterate["l"] = u"ل"
transliterate["m"] = u"م"
transliterate["n"] = u"ن"
transliterate["h"] = u"ه"
transliterate["w"] = u"و"
transliterate["Y"] = u"ى"
transliterate["y"] = u"ي"
transliterate["P"] = u"ب"
transliterate["J"] = u"ج"
transliterate["V"] = u"ف"
transliterate["G"] = u"ق"

#transliterate["{"] = u"ا" #//letter hamza al wasel
transliterate["_"] = u""#//not a letter

transliterate["F"] = u"ً" #an
transliterate["N"] = u"ٌ" #un
transliterate["K"] = u"ٍ" #in
#transliterate["a"] = u"َ " #a (broken)
transliterate["a"] = u"َ" #a 
transliterate["u"] = u"ُ" #u
transliterate["i"] = u"ِ" #i
transliterate["~"] = u"ّ" #
transliterate["o"] = u"ْ" #

ar2bw_map = {}
for bw in transliterate.keys():
    ar = transliterate[bw]
    #print "%s -> %s" % (ar, bw)
    ar2bw_map[ar] = bw


if u"ك" not in ar2bw_map:
    print "aaaaaaaaaaaaaaaaaaaaaaaaa"
    sys.exit()

def bw2ar(bw):

    ar_list = []
    for c in bw:
        if c in transliterate:
            ar_list.append(transliterate[c])
        else:
            sys.stderr.write("WARNING: bw2ar %s not found, replacing with comma\n" % c)
            ar_list.append(",")
    ar = "".join(ar_list)
    #sys.stderr.write("bw2ar: %s -> %s\n" % (bw,ar))
    return ar


def ar2bw(ar):
    bw_list = []
    for c in ar:
        if c in ar2bw_map:
            bw_list.append(ar2bw_map[c])
        else:
            sys.stderr.write("WARNING: ar2bw %s not found\n" % c)
    bw = "".join(bw_list)
    #sys.stderr.write("ar2bw: %s -> %s\n" % (ar,bw))
    return bw


def createBAMAMap(bama_filtered):

    
    ar_list = []
    for c in bama_filtered:
        if c == " " or c == "\n":
            ar_list.append(c)
        else:
            ar_list.append(bw2ar(c))

    #text = "".join(ar_list)
    text = bama_filtered

    res = []
    res.append("<s> *noevent*")

    entries = text.split("\n\n")
    for entry in entries:
        options = entry.split("\n")
        #options[0] is the unvocalised input, the rest are vocalised alternatives
        unvoc = options[0]
        options = options[1:]
        alts = []
        for char in unvoc:
            alts.append([])

        #If there are no options, means that the word was not given
        #any analysis by BAMA.
        #Add all possible alternatives to every letter and hope for the best
        if len(options) == 0:
            i = 0
            while i < len(unvoc):
                char = unvoc[i]
                alt = alts[i]
                if char in ["A"]:
                    diacritics = ["None"]
                else:
                    diacritics = ["None", "F", "N", "K", "a", "u", "i", "o", "~a", "~u", "~i"]
                for diacritic in diacritics:
                    alt.append(diacritic)
                i += 1

        for option in options:
            #sys.stderr.write(unvoc+" "+option+"\n")
            i = 0
            j = 1
            while i < len(unvoc):
                unvoc_char = unvoc[i]
                #sys.stderr.write("unvoc_char: "+unvoc_char+"\n")
                if j < len(option):
                    voc_char = option[j]
                    #sys.stderr.write("voc_char: "+voc_char+"\n")
                    #In Form1.cs in some cases all possible diacritics are appended.
                    #Why is that? In the example that happens for the first l in
                    #AlTfl, and for y in AlwZyfp
                    #Is it correct? It looks odd.
                    if voc_char in "FNKauio":                        
                        alts[i].append(voc_char)
                        j += 1
                    elif voc_char == "~":                        
                        #If shadda: look at following char too
                        #alts[i].append(voc_char)
                        j += 1
                        if j < len(option): 
                            next_voc_char = option[j]
                            if next_voc_char in "FNKauio":                        
                                alts[i].append("%s%s" % (voc_char,next_voc_char))
                                j += 1
                            else:
                                alts[i].append(voc_char)
                        else:
                            alts[i].append(voc_char)

                    else:
                        alts[i].append("None")
                        
                    j += 1
                else:
                    alts[i].append("None")

                i += 1

                
        #remove duplicates
        uniq_alts = []
        for alt in alts:
            alt = list(set(alt))
            uniq_alts.append(alt)
        alts = uniq_alts

        #sys.stderr.write(alts)


        #build result list..

        i = 0
        while i < len(unvoc):
            #sys.stderr.write("Char: "+unvoc[i]+"\n")
            #sys.stderr.write("DAlts: "+alts[i]+"\n")
            srilm_data = []
            srilm_data.append(bw2ar(unvoc[i]))
            for alt in alts[i]:
                if alt == "None":
                    srilm_data.append("<%s>" % "u")
                else:
                    srilm_data.append("<%s>" % bw2ar(alt) )

                srilm_data.append("%f" % float(1.0/len(alts[i])) )
            #sys.stderr.write(" ".join(srilm_data))

            res.append(" ".join(srilm_data))
            i += 1

        res.append("s *noevent*")

    res.append("</s> *noevent*")

    outfh = codecs.open("ptemp7.txt","w", "utf-8")
    outfh.write("\n".join(res))
    outfh.close()

    return "\n".join(res)


    




    

def runSRILMdiacritics(bama_map):
    outfh = codecs.open("ptemp7.txt","w", "utf-8")
    outfh.write(bama_map)
    outfh.close()

    os.system("./ngram/hidden-ngram -lm ngram/DiacNgrams/ngram5.txt -order 5 -text-map ptemp7.txt -hidden-vocab ngram/DiacNgrams/vocab.txt > ptemp8.txt")

    infh = codecs.open("ptemp8.txt","r")
    srilm_diacritics = infh.read()
    infh.close()
    return srilm_diacritics


def cleanOutput(srilm_diacritics):
    #Trivial processing of the SRILM n-gram output.
    output = srilm_diacritics

    sys.stderr.write("BEFORE: "+output+"\n")

    output = re.sub("<s> ", "", output)
    output = re.sub(" </s>", "", output)
    #output = re.sub("</s>", "", output)
    #output = re.sub(@"[\s]", "", output)
    output = re.sub("\s", "", output)
    output = re.sub("s", " ", output)
    output = re.sub("<u>", "", output)
    #output = re.sub("(.noevent.)", "", output)
    #output = re.sub("([\w])<([\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670]+)>", "$1$2", output)

    output = re.sub("(.)<([^>]+)>", r"\1\2", output)

    #For punctuation
    #sys.stderr.write("BEFORE: "+output+"\n")
    output = re.sub("unk<[^>]+>", ",", output)
    output = re.sub("unk", ",", output)


    sys.stderr.write("AFTER:  "+output+"\n")

    #output = re.sub("[\\s]*(\\p{P})[\\s]*", " \1 ", output)
    output = re.sub("\s+", " ", output)

    outfh = codecs.open("ptemp9.txt","w")
    outfh.write(output)
    outfh.close()

    return output;





###########################################################################

def vocalise(ar_text):
    # 1a) preprocessBeforeBama > temp0.txt
    # 1) Run BAMA to get postags (In: arabic (w1256), Out: bw (w1252) (Det måste tydligen vara windows-1256 för att Bama ska fungera..)
    # aramorph.sh temp0.txt temp1.txt

    ar_text = preprocessBeforeBama(ar_text)
    #bama_pos = runBama(ar_text)
    bama_pos = runPyBama2(ar_text)
    sys.stderr.write("------BAMA output-----\n")
    sys.stderr.write(bama_pos)
    sys.stderr.write("\n----------------------\n")


    #sys.exit()


    # 2a) convert format for srilm > temp2.txt
    # 2) run the hmm tagger "hidden-ngram.exe" to get the most likely sequence of tags
    # hidden-ngram_hb -lm POSNgrams/taggerNgram4.txt -order 4 -text-map temp2.txt -hidden-vocab POSNgrams/vocab.txt
    # 2b) removeSentenceBoundaries > temp3.txt
    
    srilm_pos = convertBamaToSrilm(bama_pos)
    #sys.stderr.write("-----SRILM input------\n")
    #sys.stderr.write(srilm_pos)
    #sys.stderr.write("\n----------------------\n")
    
    srilm_pos = runSRILM(srilm_pos)
    #sys.stderr.write("-----SRILM output-----\n")
    #sys.stderr.write(srilm_pos)
    #sys.stderr.write("\n----------------------\n")
    
    srilm_pos = removeSentenceBoundaries(srilm_pos)
    #sys.stderr.write("-----SRILM output-----\n")
    #sys.stderr.write(srilm_pos)
    #sys.stderr.write("\n----------------------\n")
    
    # 3a) preprocessBeforeBama > temp4.txt 
    # 3) Run BAMA again now with the tags (vad är det för skillnad mot 1? temp0 och temp4 är likadana. temp1 och temp5 är lite olika, men samma innehåll egentligen)
    # aramorphWithTags.sh temp4.txt temp5.txt
    # 3b) temp5+temp3 > temp6 (behåll bara rätt tag enligt temp3)
    
    #HB I don't see an important difference between aramorph.pl and aramorphWithTags.pl?
    #Trying to run the same again here. If it works, no need to run it twice?
    #No, ok now, but clean it up TODO
    #bama_pos = runBamaWithTags(ar_text)
    #bama_pos = runPyBama2(ar_text)
    sys.stderr.write("----- Bama output (2) -----\n")
    sys.stderr.write(bama_pos)
    sys.stderr.write("\n-------------------------\n")

    bama_filtered = filterBamaWithTags(bama_pos, srilm_pos)
    sys.stderr.write("-----Filtered output-----\n")
    sys.stderr.write(bama_filtered)
    sys.stderr.write("\n-------------------------\n")
    
    # 4a) createBAMAMap temp6 > temp7
    # 4) run diacritics ngram.
    # hidden-ngram_hb -lm DiacNgrams/ngram5.txt -order 5 -text-map temp7.txt -hidden-vocab DiacNgrams/vocab.txt
    # > temp8
    # 4b) mergeOutput (rensar utdata på taggar osv så bara vokaliserad text blir kvar)
    # > temp9
    
    bama_map = createBAMAMap(bama_filtered)
    sys.stderr.write("----- Srilm input   -----\n")
    sys.stderr.write(bama_map)
    sys.stderr.write("\n-------------------------\n")
    
    srilm_diacritics = runSRILMdiacritics(bama_map)
    only_vocalised = cleanOutput(srilm_diacritics)
    return only_vocalised


################################################################



if len(sys.argv) > 1 and sys.argv[1] == "server":
    print "hejsan"
    from flask import Flask, request
    app = Flask(__name__)

    @app.route("/vocalise", methods=['GET'])
    def voc():
        ar_text = request.args.get('text', '')
        print "INPUT TEXT:", ar_text
        return vocalise(ar_text)

    if __name__ == "__main__":
        app.run(debug=True, port=8080)

else:
    #ar_text = u"كتب الطفل الوظيفة"
    #ar_text = sys.stdin.read()
    ar_text = codecs.getreader("utf-8")(sys.stdin).read().strip()
    vocalised = vocalise(ar_text)
    print vocalised

