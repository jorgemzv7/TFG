import json
import string
import nltk
import pandas as pd
import pdf2text
from tqdm import tqdm
import operator
from os import listdir
import DictionaryModule as umls
import MLModule


PATH = "C:\\Users\\Jorge\\Documents\\Clase\\TFG\\Infomes\\"


# Eliminacion de datos personales y características propias de los informes del H12O
def clearPersonalData(txt):
    # divido en palabras
    tokens = nltk.word_tokenize(txt, language="spanish")
    # eliminacion de datos personales y de fecha (empezamos tras motivo de consulta)
    n = tokens.index("Motivo")
    for i in range(0, n + 4):
        tokens.pop(0)
    # eliminacion de datos del hospital (direccion y telefono)
    n = tokens.index("Avenida")
    for x in range(0, 16):
        tokens.pop(n)
    # eliminacion palabras > 31 letras (hileras de caracteres no imprimibles)
    for word in tokens:
        if len(word) > 31:
            tokens.remove(word)
    # Las ultimas 2 palabras son inútiles
    tokens.pop(-1)
    tokens.pop(-1)
    return " ".join(tokens)


# Limpieza del texto, eliminacion de signos de puntuacion, etc.
def clean(txt, clear_stopwords=True):
    # Elimino datos personales y características propias de los informes del H12O
    new_text = clearPersonalData(txt)
    # divido en palabras
    new_text = nltk.word_tokenize(new_text.casefold(), language="spanish")
    # Elimincación de signos de puntuación
    for i in string.punctuation:
        new_text = [x for x in new_text if x != i]
    """# Elimino numeros sueltos
    new_text = [x for x in new_text if not x.isdigit()]"""
    # Eliminamos las stopwords
    if clear_stopwords:
        stopwords = umls.getStopWords()
        for word in stopwords:
            while word in new_text:
                new_text.remove(word)
    return new_text


# Genera un diccionario ordenado tipo {palabra: n_apariciones}
def listOfWords(token_list):
    res = dict.fromkeys(token_list)
    for x in res.keys():
        res.update({x: token_list.count(x)})
    sort = sorted(res.items(), key=operator.itemgetter(1), reverse=True)
    res.clear()
    for x in sort:
        res.update({x[0]: x[1]})
    return res


# Genera a partir de una lista una lista de n-gramas
def ngrams(token_list, num):
    if num < 1:
        return token_list
    res = []
    for x in range(0, len(token_list)):
        if x <= (len(token_list)-num):
            tmp = []
            for y in range(x, (x+num)):
                tmp.append(token_list[y])
            new = ' '.join(y for y in tmp)
            res.append(new)
    return res


# Rellena el primer vector para igualarlo en tamaño al segundo
def sameSize(vect1, vect2, relleno):
    len1 = len(vect1)
    len2 = len(vect2)
    for i in range(len1, len2):
        vect1.append(relleno)
    return vect1


# Devuelve un diccionario con los ngramas (4-1) más frecuentes
def topWords(token_list, min_appearance=2):
    tetragrams = ngrams(token_list, 4)
    trigrams = ngrams(token_list, 3)
    bigrams = ngrams(token_list, 2)
    unigrams = ngrams(token_list, 1)

    conjunto = tetragrams
    conjunto.extend(trigrams)
    conjunto.extend(bigrams)
    conjunto.extend(unigrams)
    conjunto = [x for x in conjunto if conjunto.count(x) >= min_appearance]
    conjunto = listOfWords(conjunto)

    return conjunto


# Ejecuta el programa con el indice en hash
def run(max_words=75, doc="", model='best'):
    docs = [(PATH + doc) for doc in listdir(PATH)]
    n = int(input(f"Elija el numero del archivo que desea procesar [0-{len(docs)-1}]: "))
    while n > len(docs)-1 or n < 0:
        n = int(input(f"El numero debe ser entre 0 y {len(docs)}: "))
    # umls.createHashIndex()    # Opción para regenerar el diccionario hash
    print("Procesando archivo...")
    with open("venv\\index.json") as file:
        index = json.load(file)
        file.close()

    # Convertimos nuestro pdf a texto
    original_text = pdf2text.convert(docs[n])
    # Limpiamos nuestro texto de elementos indeseados
    tokens = clean(original_text, clear_stopwords=True)
    # print(f'Tokens limpios: {tokens}')

    # Reconocimiento token por token
    terms, cuis, defs = [], [], []
    for i in range(0, len(tokens)):
        for j in range(max_words+1):                 # Desde términos de una palabra hasta max_words palabras
            if i < len(tokens)-j:                    # Puedo buscar conceptos de hasta j palabras
                if j == 0:
                    term = tokens[i]                # Palabra inicial
                else:
                    term += " " + tokens[i+j]       # Anexo más palabras
                res = index.get(term)                       # Búsqueda en índice
                if res is not None:            # MATCH!
                    terms.append(term)
                    cuis.append(res[0])
                    defs.append(res[1])
    print(f'\nEncontrados {len(terms)} términos UMLS en el documento de entre {len(tokens)} tokens analizados')
    # Módulo de ML analiza el texto original
    doc = MLModule.ner(original_text, model=model)
    # Preparo los datos para su output
    sources = []
    for i in range(len(cuis)):
        sources.append("Dictionary Module")
    totalTerms = terms
    for term in list(doc.ents):
        totalTerms.append(term)
        sources.append("ML Module")
    cuis = sameSize(cuis, totalTerms, "--")
    defs = sameSize(defs, totalTerms, "--")
    data = {
        "Término": terms,
        "Fuente": sources,
        "CUI": cuis,
        "Definición en UMLS": defs
    }
    df = pd.DataFrame(data)
    # Almacena en el .csv el resultado completo de ambos módulos
    df.to_excel("data.xlsx", index=False)
    print("Resultados del proceso NER almacenados en el archivo data.xlsx")
    # Mostrar resultado del módulo ML en el navegador
    MLModule.show(doc)
    return


# Ejecuta el programa
def run2():
    # En PATH se encuentran los informes ecográficos
    docs = [(PATH + doc) for doc in listdir(PATH)]
    n = int(input(f"Elija el numero del archivo que desea procesar [0-{len(docs)-1}]: "))
    while n > len(docs)-1 or n < 0:
        n = int(input(f"El numero debe ser entre 0 y {len(docs)}: "))
    # Convertimos nuestro pdf a texto
    original_text = pdf2text.convert(docs[n])
    # Limpiamos nuestro texto de elementos indeseados
    tokens = clean(original_text, clear_stopwords=False)
    # Opción de regenerar diccionarios
    umls.createDictionaries()
    print("Cargando diccionarios...")
    f = open("venv\\main_index.txt", "r", encoding="UTF-8")
    g = open("venv\\trigger_index.txt", "r", encoding="UTF-8")
    mainDict = umls.dic2list(f.read())
    triggerDict = umls.dic2list(g.read())
    f.close()
    g.close()
    if len(mainDict) != len(triggerDict):
        print("Error: Los diccionarios son de distinta longitud")
        exit(1)

    print("Diccionados cargados\nProcesando archivo...")
    # Reconocimiento token por token
    matches = {}        # Uso un diccionaruio clave = string, valor = umlscode porque los string de conceptos son unicos
    for i in tqdm(range(0, len(tokens))):
        for j in range(0, len(triggerDict)):
            if triggerDict[j][0] == tokens[i]:         # Posible match
                concepto = tokens[i]
                triggerNum = triggerDict[j][1]-1
                aux = 1
                while triggerNum > 0 and i+aux < len(tokens):
                    if tokens[i+aux] != mainDict[j][0][aux]:
                        break
                    concepto = concepto + " " + tokens[i+aux]
                    aux += 1
                    triggerNum -= 1
                if triggerNum == 0:                 # Match!
                    matches.update({concepto: mainDict[j][1]})
                    # print(f'Match!: \nConcepto: {concepto}\nLista en indice: {mainDict[j]}')
    print(f'\n{len(matches)} matches en el documento\n')
    print(pd.Series(matches))
    MLModule.ner(original_text)
    return matches


# Opciones de muestra para pandas
pd.options.display.max_rows = None
pd.options.display.max_columns = None
pd.set_option('display.max_colwidth', None)

# print("Texto limpio:\n" + str(tokens))
# print("Palabras ordenadas por frecuencia: \n" + str(listOfWords(tokens)))
# print("N-gramas (1-4) ordenados por frecuencia (>1 aparición) : \n" + str(pd.Series(topWords(tokens)))) # Top n-gramas
# print("Stopwords("+str(umls.getStopWords().count)+"):\n" + str(sorted(umls.getStopWords())))
# print(f'{nltk.pos_tag("motivo de consulta: control por hidrops fetal".split(" "), "universal")} NLTK')
# print(f'{pos("motivo de consulta: control por hidrops fetal")} SPACY')
# print(f'{umls.findConceptRE("cromosomopatía")}')


run(max_words=73, model='best')
