import os
import zipfile
import shutil

import numpy as np
import fitz

import spacy
import re
from spacy.tokenizer import Tokenizer
from spacy.matcher import Matcher

import uuid
import collections

from pathlib import Path
from io import StringIO

from os.path import exists

import json

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from PyPDF2 import PdfFileReader, PdfFileWriter

from langdetect import detect


months_de = [
    "januar",
    "februar",
    "märz",
    "april",
    "mai",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "dezember"
]

months_en = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december"
]

din_text = "DIN Deutsches Institut für Normung e. V. · Jede Art der Vervielfältigung, auch auszugsweise, nur mit Genehmigung des DIN Deutsches Institut für Normung e. V., Berlin, gestattet. Alleinverkauf der Spezifikationen durch Beuth Verlag GmbH, 10772 Berlin"
din_website = "www.din.de"
beuth_website = "www.beuth.de"

false_words = [
    "din",
    "cen",
    "beuth",
    "norm",
    "spec",
    "iso",
    "iec",
    "siehe"
]



def get_directory_path(directory_id):
    return os.path.join(os.path.join(os.path.abspath(os.path.join(__file__, "..")), "archives"), directory_id)


def directory_exists(directory_path):
    return Path(directory_path).is_dir()


def create_index_file(directory_path):
    data = {
        "hasFinished": False,
        "files_ready": 0,
        "files_all": 0
    }
    json_string = json.dumps(data)
    file_path = os.path.join(directory_path, "index.json")
    file = open(file_path, "x")
    file.write(json_string)
    file.close()


def index_file_exists(directory_path):
    file_path = os.path.join(directory_path, "index.json")
    return exists(file_path)


def graph_file_exists(directory_path):
    file_path = os.path.join(directory_path, "graph.json")
    return exists(file_path)


def read_index_file(directory_path):
    file_path = os.path.join(directory_path, "index.json")
    file = open(file_path, "r")
    data = json.load(file)
    file.close()
    return data


def update_index_file(directory_path, files_ready, files_all):
    file_path = os.path.join(directory_path, "index.json")

    hasFinished = False
    if files_ready == files_all:
        hasFinished = True

    with open(file_path, "r") as jsonFile:
        data = json.load(jsonFile)

    data["hasFinished"] = hasFinished
    data["files_ready"] = files_ready
    data["files_all"] = files_all

    with open(file_path, "w") as jsonFile:
        json.dump(data, jsonFile)


def unzip_archive(archive_path, directory_id):
    paths = archive_path.split("/")

    module_dir = os.path.dirname(__file__)
    absolute_path = os.path.abspath(os.path.join(module_dir, os.pardir))

    for path in paths:
        absolute_path = os.path.join(absolute_path, path)

    directory_path = os.path.join(
        os.path.join(os.path.abspath(os.path.join(__file__, "..")), "archives"), directory_id)

    Path(directory_path).mkdir(parents=True, exist_ok=True)

    zip_obj = zipfile.ZipFile(absolute_path, 'r')
    for member in zip_obj.namelist():
        filename = os.path.basename(member)

        if not filename:
            continue

        source = zip_obj.open(member)
        target = open(os.path.join(directory_path, filename), "wb")
        shutil.copyfileobj(source, target)

        # target.close()

        # jooo = open(os.path.join(directory_path, filename), "rb")
        # inputFile = PdfFileReader(jooo)
        # if inputFile.isEncrypted:
        #   inputFile.decrypt('')

        # outputFile = PdfFileWriter()

        # for page_number in range(inputFile.getNumPages()):
        #    page = inputFile.getPage(page_number)
        #    max_x = float(page.trimBox.getUpperRight_x())
        #    max_y = float(page.trimBox.getUpperRight_y())
        #    page.trimBox.lowerLeft = (max_x * 0.05, 0)
        #    page.trimBox.upperRight = (max_x * 0.95, max_y)
        #    outputFile.addPage(page)

        # directory_path_1 = os.path.join(os.path.abspath(os.path.join(__file__, "..")), "tmp")
        # tmp_file_id = str(uuid.uuid4())
        # tmp_file_path = os.path.join(directory_path, tmp_file_id + ".pdf")
        # outputStream = open(tmp_file_path, "wb")
        # outputFile.write(outputStream)
        # outputStream.close()

        # jooo.close()
        # os.remove(os.path.join(directory_path, filename))

    return directory_path


def get_pdf_files(directory_path):
    files = []
    for file in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file)
        if os.path.isfile(file_path) and (file_path.endswith(".pdf") or file_path.endswith(".PDF")):
            files.append(file_path)

    return files


def convert_pdf_to_string(file_path, page_length):
    output_string = StringIO()
    with open(file_path, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        resource_manager = PDFResourceManager()
        device = TextConverter(resource_manager, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(resource_manager, device)
        counter = 0
        for page in PDFPage.create_pages(doc):
            if page_length > counter:
                interpreter.process_page(page)
            counter = counter + 1

    return output_string.getvalue()


def convert_date(month, year):
    if month.lower() in months_en or month.lower() in months_de and year.isdigit() and 0 < int(year) < 2030:
        return month + " " + year
    else:
        return ""


def convert_document_numbers(document_numbers):
    results = []
    values = np.array(document_numbers)
    search_value = "DIN"

    ii = np.where(values == search_value)[0]
    count_ii = len(ii)

    if count_ii == 0:
        return results
    else:
        if count_ii == 1:
            results.append(" ".join(document_numbers))
            return results
        else:
            counter = 0
            for index in ii:
                if counter + 1 == len(ii):
                    number = " ".join(document_numbers[index:])
                    results.append(number)
                else:
                    number = " ".join(document_numbers[index:ii[counter + 1]])
                    results.append(number)
                counter = counter + 1
            return results


def get_max_ics_index(ics_list):
    counter = 0
    for value in ics_list:
        if can_convert_to_ics(value):
            counter = counter + 1
        else:
            break

    return counter


def can_convert_to_ics(value):
    if value.endswith(";"):
        value = value[:-1]

    splits = value.split(".", 2)

    if all(split.isdigit() for split in splits):
        return True
    else:
        return False


def convert_ics(ics_list):
    results = []
    for ics in ics_list:
        if ics.endswith(";"):
            ics = ics[:-1]
        results.append(ics)

    return results


def extract_titles(text):
    start_index_din_text = text.find(din_text)
    end_index_din_text = len(din_text) + start_index_din_text

    start_index_din_website = text.find(din_website)
    end_index_din_website = len(din_website) + start_index_din_website

    start_index_beuth_website = text.find(beuth_website)
    end_index_beuth_website = len(beuth_website) + start_index_beuth_website

    content = text[:start_index_din_text] + \
              text[end_index_din_text:start_index_din_website] + \
              text[end_index_din_website:start_index_beuth_website] + \
              text[end_index_beuth_website:]

    return content


def get_toc(filename):
    doc = fitz.open(filename)
    toc = doc.get_toc()

    dictionary = {}

    for toc_entry in toc:
        dictionary[str(toc_entry[1]).lower()] = {"chapter": toc_entry[0], "page": toc_entry[2]}

    return dictionary


def convert_pdf_to_page_list(file_path):
    file = open(file_path, 'rb')

    parser = PDFParser(file)
    doc = PDFDocument(parser)

    results = []

    for page in PDFPage.create_pages(doc):
        output_string = StringIO()
        resource_manager = PDFResourceManager()
        device = TextConverter(resource_manager, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(resource_manager, device)
        interpreter.process_page(page)
        results.append(output_string.getvalue())

    return results


def get_foreword(toc, pages):
    # first_key = list(colors)[0]
    # first_val = list(colors.values())[0]
    if "vorwort" in toc:
        index_foreword = list(toc.keys()).index("vorwort")
        index_next_chapter = index_foreword + 1

        foreword_entry = list(toc.values())[index_foreword]
        next_chapter_entry = list(toc.values())[index_next_chapter]

        foreword_page = int(foreword_entry["page"])
        next_chapter_page = int(next_chapter_entry["page"])

        foreword_pages = pages[foreword_page - 1:next_chapter_page - 1]

        return " ".join(foreword_pages)

    if "foreword" in toc:
        index_foreword = list(toc.keys()).index("foreword")
        index_next_chapter = index_foreword + 1

        foreword_entry = list(toc.values())[index_foreword]
        next_chapter_entry = list(toc.values())[index_next_chapter]

        foreword_page = int(foreword_entry["page"])
        next_chapter_page = int(next_chapter_entry["page"])

        foreword_pages = pages[foreword_page - 1:next_chapter_page - 1]

        return " ".join(foreword_pages)

    return ""


def get_foreword_index(toc):
    if "vorwort" in toc:
        return list(toc.keys()).index("vorwort")
    if "foreword" in toc:
        return list(toc.keys()).index("foreword")
    return -1


def get_scope_index(toc):
    if "1 anwendungsbereich" in toc:
        return list(toc.keys()).index("1 anwendungsbereich")
    if "1 scope" in toc:
        return list(toc.keys()).index("1 scope")
    return -1


def get_references_index(toc):
    if "2 normative verweisungen" in toc:
        return list(toc.keys()).index("2 normative verweisungen")
    if "2 normative references" in toc:
        return list(toc.keys()).index("2 normative references")
    return -1


def get_page_number(toc, index):
    entry = list(toc.values())[index]
    return int(entry["page"])


def calc_relevance_foreword(toc, page_list):
    foreword_index = get_foreword_index(toc)

    if foreword_index > -1:
        start_page = get_page_number(toc, foreword_index)
        end_page = get_page_number(toc, foreword_index + 1)

        if -1 < start_page <= end_page < len(page_list):
            foreword_pages = page_list[start_page:end_page]
            pages_count = len(foreword_pages)

            if pages_count > 0:
                return 100

    return 0


def calc_relevance_scope(toc, page_list):
    scope_index = get_scope_index(toc)

    if scope_index > -1:
        start_page = get_page_number(toc, scope_index)
        end_page = get_page_number(toc, scope_index + 1)

        if -1 < start_page <= end_page < len(page_list):
            scope_pages = page_list[start_page:end_page]
            pages_count = len(scope_pages)

            if pages_count > 0:
                return 1000

    return 0


def calc_relevance_references(toc, page_list):
    references_index = get_references_index(toc)

    if references_index > -1:
        start_page = get_page_number(toc, references_index)
        end_page = get_page_number(toc, references_index + 1)

        if -1 < start_page <= end_page < len(page_list):
            references_pages = page_list[start_page:end_page]
            pages_count = len(references_pages)

            if pages_count > 0:
                return 400

    return 0


def is_in_false_words_list(token1):
    for false_word in false_words:
        if false_word == token1:
            return True
    return False


def is_token_allowed(token1):
    if not token1 or not token1.text.strip() \
            or token1.is_stop \
            or token1.is_punct \
            or not token1.is_alpha \
            or len(token1.lemma_.strip()) <= 2 \
            or is_in_false_words_list(str(token1.lemma_).strip().lower()):
        return False
    return True


def preprocess_token(token1):
    return token1.lemma_.strip().lower()


def get_titles(page):
    results = []
    paragraphs = re.split(r"\n\n", page)
    counter = 0
    for paragraph in paragraphs:
        # print("#" + paragraph + "#")
        counter = counter + 1

        # if "—" in paragraph:
        # results.append(paragraph)
        #   continue
        # if "–" in paragraph:
        #   results.append(paragraph)
        #  continue

    return results


def crop_page(file_path, page_number):
    inputFile = PdfFileReader(open(file_path, "rb"))
    if inputFile.isEncrypted:
        inputFile.decrypt('')

    outputFile = PdfFileWriter()

    page = inputFile.getPage(page_number)
    max_x = float(page.cropBox.getUpperRight_x())
    max_y = float(page.cropBox.getUpperRight_y())

    page.cropBox.lowerLeft = (max_x * 0.1, max_y * 0.1)
    page.cropBox.upperRight = (max_x * 0.9, max_y * 0.85)

    outputFile.addPage(page)

    directory_path = os.path.join(os.path.abspath(os.path.join(__file__, "..")), "tmp")
    tmp_file_id = str(uuid.uuid4())
    tmp_file_path = os.path.join(directory_path, tmp_file_id + ".pdf")
    outputStream = open(tmp_file_path, "wb")
    outputFile.write(outputStream)
    outputStream.close()

    return tmp_file_path


def calculate_graph():
    result = {
        "nodes": [
            {
                "id": "doc1",
                "title": "Document 1",
                "size": 12
            },
            {
                "id": "doc2",
                "title": "Document 2",
                "size": 7
            },
            {
                "id": "doc3",
                "title": "Document 3",
                "size": 10
            },
            {
                "id": "doc4",
                "title": "Document 4",
                "size": 5
            }
        ],
        "edges": [
            {
                "left": "doc1",
                "right": "doc2"
            },
            {
                "left": "doc1",
                "right": "doc3"
            },
            {
                "left": "doc2",
                "right": "doc3"
            },
            {
                "left": "doc4",
                "right": "doc1"
            },
            {
                "left": "doc2",
                "right": "doc4"
            }
        ]
    }
    return result


def get_nlps(text):
    if text != "":
        language = detect(text)
        if language == "de" or language == "en":
            space_language = 'de_core_news_sm'
            if language == "en":
                space_language = 'en_core_web_sm'

            nlp = spacy.load(space_language)

            prefix_re = spacy.util.compile_prefix_regex(nlp.Defaults.prefixes)
            suffix_re = spacy.util.compile_suffix_regex(nlp.Defaults.suffixes)
            infix_re = re.compile(r'''[-~]''')

            nlp.tokenizer = Tokenizer(nlp.vocab, prefix_search=prefix_re.search, suffix_search=suffix_re.search,
                                      infix_finditer=infix_re.finditer, token_match=None)

            text_splits = [text[index: index + 500000] for index in
                           range(0, len(text), 500000)]

            word_counter = collections.Counter([])
            for text_split in text_splits:
                doc = nlp(text_split)
                filtered_tokens = [preprocess_token(token) for token in doc if is_token_allowed(token)]
                doc_words = collections.Counter(filtered_tokens)
                word_counter = word_counter + doc_words

            return word_counter

    return collections.Counter([])


def calc_relevance(file_path):
    page_list = convert_pdf_to_page_list(file_path)


    #common_words = word_counter.most_common(10)
    #common_words_two = word_counter.most_common(2)

    #very_most_common = word_counter.most_common(1)
    max_vorkommen = 1
    #if len(very_most_common) == 1:
        #max_vorkommen = word_counter.most_common(1)[0][1]

    items_dict = {}
    #for item in word_counter.items():
        #items_dict[item[0]] = item[1]



    result = {
        #"tenCommonWords": common_words,
        #"twoCommonWords": common_words_two,
        "max_vorkommen": max_vorkommen,
        "words": items_dict
    }
    return result
