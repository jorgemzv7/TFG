import spacy
from spacy import displacy
from tqdm import tqdm


# Parts of speech tagging con spacy
def pos(text_string):
    # Modelo de lenguaje en spacy
    nlp = spacy.load('es_core_news_lg')
    document = nlp(text_string)
    result = []
    for token in document:
        result.append("("+token.lemma_+", "+token.pos_+", "+token.dep_+")")
    displacy.serve(document, style="ent", host="127.0.0.1")
    return result


# Mesinesp files to spacy look alike format (.list)
def formatData(ttype):
    if input(f'Quiere reformatear los ficheros json de {ttype} '
             f'al formato spacy? (Introduzca una "Y" si lo desea): ') != "Y":
        return
    data = []
    if ttype == "training":
        path1 = "venv\\Spacy-folder\\Datasets\\training_set_subtrack1.json"
        path2 = "venv\\Spacy-folder\\Datasets\\entities_subtrack1_train.json"
        print("Creating training.list")
    elif ttype == "development":
        path1 = "venv\\Spacy-folder\\Datasets\\development_set_subtrack1.json"
        path2 = "venv\\Spacy-folder\\Datasets\\entities_subtrack1_development.json"
        print("Creating development.list")
    elif ttype == "test":
        path1 = "venv\\Spacy-folder\\Datasets\\test_set_subtrack1.json"
        path2 = "venv\\Spacy-folder\\Datasets\\entities_subtrack1_test.json"
        print("Creating test.list")
    else:
        print("mal escrito")
        return
    
    with open(path1, "r", encoding="UTF-8") as f:
        print("Charging names file...")
        text = eval(f.read())
    
    with open(path2, "r", encoding="UTF-8") as f:
        print("Charging entities file...")
        entities = eval(f.read())
    
    f = open(f"venv\\Spacy-folder\\Datasets\\{ttype}.list", "w", encoding="UTF-8")
    articles = text.get("articles")
    entities = entities.get("articles")
    for article in tqdm(articles):
        annotations = []
        article_id = article.get("id")
        articulo = article.get("abstractText")
        for entity in entities:
            if entity.get("id") == article_id:
                for diseases in entity.get("diseases"):             # diseases
                    start = diseases.get("start")
                    end = diseases.get("end")
                    annotation = tuple([int(start), int(end), "DISEASE"])
                    annotations.append(annotation)
                for diseases in entity.get("medications"):          # Medications
                    start = diseases.get("start")
                    end = diseases.get("end")
                    annotation = tuple([int(start), int(end), "MEDICATION"])
                    annotations.append(annotation)
                for diseases in entity.get("procedures"):           # Procedures
                    start = diseases.get("start")
                    end = diseases.get("end")
                    annotation = tuple([int(start), int(end), "PROCEDURE"])
                    annotations.append(annotation)
                for diseases in entity.get("symptoms"):             # Symptoms
                    start = diseases.get("start")
                    end = diseases.get("end")
                    annotation = tuple([int(start), int(end), "SYMPTOM"])
                    annotations.append(annotation)
                data.append(tuple([articulo, annotations]))
                break
    f.write(str(data))
    f.close()
    return


# Spacy look alike format (.list) to real spacy
def generateSpacy(ttype, times=10):
    if ttype == "training":
        path1 = "venv\\Spacy-folder\\Datasets\\training.list"
    elif ttype == "development":
        path1 = "venv\\Spacy-folder\\Datasets\\development.list"
        print("Creating development.spacy")
    elif ttype == "test":
        path1 = "venv\\Spacy-folder\\Datasets\\test.list"
        print("Creating test.spacy")
    else:
        print("mal escrito")
        return
    f = open(path1, "r", encoding="UTF-8")
    print(f"Charging {ttype}.list ...")
    training_data = eval(f.read())
    f.close()
    from spacy.tokens import DocBin

    nlp = spacy.blank("es")
    # the DocBin will store the example documents
    db = DocBin()
    skipped_spans, total = 0, 0
    if ttype != "training":
        for text, annotations in tqdm(training_data):
            doc = nlp(text)
            ents = []
            for start, end, label in annotations:
                span = doc.char_span(start_idx=start, end_idx=end, label=str(label), alignment_mode="contract")
                if span is not None:
                    ents.append(span)
                    total += 1
                else:
                    total += 1
                    skipped_spans += 1
            filtered = spacy.util.filter_spans(ents)  # THIS DOES THE TRICK
            doc.ents = filtered
            # doc.set_ents(ents)
            db.add(doc)
        print(f'Skipped {skipped_spans} None spans out of {total} spans '
              f'({100 * skipped_spans / total} %)')
        db.to_disk(f"venv\\Spacy-folder\\Datasets\\{ttype}.spacy")
        print(f"\n{ttype}.spacy created")
    else:                                           # Split in times doc bins
        print(f'Document is going to split in {times} docs of {int(len(training_data)/times)} entities')
        for part in range(6, 9):
            x = part*int(len(training_data)/times)
            if part == times-1:
                y = int(len(training_data))
            else:
                y = (part+1)*int(len(training_data)/times)
            print(f'Part {part}, entities {x}-{y}')
            for i in tqdm(range(x, y)):
                text, annotations = training_data[i][0], training_data[i][1]
                doc = nlp(text)
                ents = []
                for start, end, label in annotations:
                    span = doc.char_span(start_idx=start, end_idx=end, label=str(label), alignment_mode="expand")
                    if span is not None:
                        ents.append(span)
                    else:
                        skipped_spans += 1
                total += 1
                filtered = spacy.util.filter_spans(ents)  # THIS DOES THE TRICK
                doc.ents = filtered
                db.add(doc)
            print(f'Skipped {skipped_spans} None spans out of {total} spans '
                  f'({100 * skipped_spans / total} %)')

            db.to_disk(f"venv\\Spacy-folder\\Datasets\\training\\{ttype}{part}.spacy")
            print(f"\nvenv\\Spacy-folder\\Datasets\\{ttype}{part}.spacy created")
    return


def ner(text, model='best'):
    nlp = spacy.load(f"venv\\Spacy-folder\\Output\\model-{model}")
    doc = nlp(text)
    # print(15*'-' + '\t' + 'ML Module results' + '\t' + 15*'-')
    return doc


def show(doc):
    displacy.serve(doc, style="ent", host='127.0.0.1', port=5000)
    return

