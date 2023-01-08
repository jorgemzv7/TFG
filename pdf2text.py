from tika import parser  # pip install tika
import os


def convert(path):
    # Path does not exist
    if not os.path.exists(path):
        print("La ruta introducida: "+ path +" no existe")
        print("Introduzca una ruta que indique un informe en formato PDF")
        exit(2)
    # Path leads to a directory
    if os.path.isdir(path):
        print("Esta ruta conduce a un directorio")
        print("Introduzca una ruta que indique un informe en formato PDF")
        exit(2)
    
    # PyPDF2
    """reader = PdfFileReader(open(path, "rb"))
    n = reader.getNumPages()
    text = ""
    for x in range(n):
        page = reader.getPage(x)
        text = text + page.extractText()
    return text """
    # Tika (needs Java)
    raw = parser.from_file(path)
    return raw['content']