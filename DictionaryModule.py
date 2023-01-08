import json
import re
import nltk
import string
from tqdm import tqdm

INICIO_MRCONSO = "C[0-9]{7}.*"
FIN_MRCONSO = ".*[||]"
PATH_UMLS = "C:\\Users\\Jorge\\Documents\\Clase\\TFG\\UMLS\\subset1"


# Dado cierto CUI devuelve todas sus propiedades
def findConceptRE(concept):
    f = open(f"{PATH_UMLS}\\MRCONSO.RRF", "r", encoding="UTF-8")
    mrconso = f.read()
    results = re.findall(INICIO_MRCONSO+concept+FIN_MRCONSO, mrconso)
    f.close()
    properties = {}
    if len(results) > 0:
        shortest = results[0]
        if len(results) > 1:
            for i in range(1, len(results)):
                if len(shortest) > len(results[i]):
                    shortest = results[i]
        properties = {
            "CUI":              shortest.split("|")[0],         # Unique identifier for concept
            "Term Status":      shortest.split("|")[2],
            "LUI":              shortest.split("|")[3],         # Unique identifier for term
            "String type":      shortest.split("|")[4],         # String type
            "SUI":              shortest.split("|")[5],         # Unique identifier for string
            "ISPreferred":      shortest.split("|")[6],         # Atom status - preferred (Y)
                                                                # or not (N) for this string within this concept
            "AUI":              shortest.split("|")[7],         # Atom unique ID
            "SAB":              shortest.split("|")[-8],        # Abbreviated sort name
            "TTY":              shortest.split("|")[-7],        # Abbreviation for term type in source vocabulary
                                                                    # p.e. PN (Metathesaurus Preferred Name)
                                                                    # or CD (Clinical Drug)
            "CODE":             shortest.split("|")[-6],        # Most useful source asserted identifier
                                                                # (if the source vocabulary has more than one identifier),
                                                                # or a Metathesaurus-generated source entry identifier
                                                                # (if the source vocabulary has none)
            "String":           shortest.split("|")[-5],        # String of the concept
            "SRL":              shortest.split("|")[-4],        # Source Restricction Level
            "SUPRESS":          shortest.split("|")[-3],        # Supressible flag
            "Definition":       getDefinitionsRE([shortest.split("|")[0]])[0]
        }
    return properties


# Dada cierta lista de CUI's devuelve sus definiciones
def getDefinitionsRE(cuis):
    f = open(f"{PATH_UMLS}\\MRDEF.RRF", "r", encoding="UTF-8")
    mrdef = f.read()
    f.close()
    results = []
    prevCui = ""
    for cui in tqdm(cuis):
        if cui != prevCui:
            result = re.search(cui+FIN_MRCONSO+FIN_MRCONSO, mrdef)
        if result is None:
            results.append("No definition in spanish UMLS")
        else:
            definition = result.group().split("|")[-4]
            results.append(definition)
    return results


# Crea un indice hash {concepto: [CUI, Def]}
def createHashIndex():
    if input(f'Quiere regenerar el diccionario hash? (Introduzca una "Y" si lo desea): ') != "Y":
        return
    print("Regenerando diccionario...")
    f = open(f"{PATH_UMLS}\\MRCONSO.RRF", "r", encoding="UTF-8")
    mrconso = f.read()
    f.close()
    # concepts is a list with every line in mrconso.rrf
    concepts = re.findall("C[0-9]{7}[|].*", mrconso)
    dictionary = {}
    cuis, terms = [], []
    max_words = 0
    print("Limpiando conceptos...")
    for i in tqdm(range(len(concepts))):
        cui = concepts[i].split("|")[0]  # cui = UMLSCODE
        concept_string = concepts[i].split("|")[-5].lower()
        stringList = clean(concept_string, clear_stopwords=True, stopwords=swords)
        if len(stringList) > max_words:
            max_words = len(stringList)
            longest = stringList
            longestCui = cui
        if len(stringList) > 0:
            cui = concepts[i].split("|")[0]  # cui = UMLSCODE
            cuis.append(cui)
            concept_string = " ".join(stringList)
            terms.append(concept_string)
    print("Obteniendo las definiciones de estos conceptos...")
    defs = getDefinitionsRE(cuis)
    print("Creando objetos hash...")
    for i in tqdm(range(len(cuis))):
        dictionary.update({terms[i]: [cuis[i], defs[i]]})
    print("Volcando objetos a index.json")
    with open("venv\\index.json", 'w') as file:
        json.dump(dictionary, file, indent=4)
        file.close()
    print(f'Created dictionaries with {len(concepts)} entries\nThe longest term has {max_words} words'
          f'\n Longest term: {longestCui} -> {longest}')
    return


def getStopWords():
    with open("venv\\stop_words.txt", "r") as f:
        text = f.read()
    word = ""
    lista = []
    for x in text:
        if x != "\n":
            word += x
        else:
            lista.append(word)
            word = ""
    for x in nltk.corpus.stopwords.words("spanish"):
        lista.append(x)
    lista = list(set(lista))   # Eliminamos duplicados
    return lista


# Los conceptos de umls pasan por un proceso de limpiado del texto similar
# al de los documentos que recibimos
# y ademas incluimos un metodo para
# generar normalizacion (“SRC1”/“SRC-1” -> “SRC 1”)
def clean(txt, stopwords, clear_stopwords=True):
    # convierto el texto a minúsculas y divido en palabras
    # new_text = nltk.word_tokenize(txt.casefold(), "spanish")
    new_text = txt.casefold().split(" ")
    # Si el concepto es un numero solo, lo elimino
    if len(new_text) == 1:
        new_text[0] = re.sub("\d+[,.]\d+", "", new_text[0])
        if new_text[0].isdigit():
            return []
    # Elimincación de signos de puntuación
    for i in string.punctuation:
        new_text = [x for x in new_text if x != i]
    # Elimino tambien la palabra fur (fecha ultima regla)
    new_text = [x for x in new_text if x != "fur"]
    # eliminacion caracteres > 31 letras
    for word in new_text:
        if len(word) > 31:
            new_text.remove(word)
    # Eliminamos las stopwords
    if clear_stopwords:
        for word in stopwords:
            while word in new_text:
                new_text.remove(word)
    return new_text


swords = getStopWords()
