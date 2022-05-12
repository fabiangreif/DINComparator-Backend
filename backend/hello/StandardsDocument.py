import spacy
import re
import collections

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from io import StringIO
from langdetect import detect
from spacy.tokenizer import Tokenizer

import tabula
import pandas
from tabulate import tabulate


import csv


class StandardsDocument:
    characters_per_operation = 500000
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

    def __init__(self, file_path):
        self.file_path = file_path
        self.pages = self.__convert_pdf_to_pages()
        self.text = self.__preprocess_text(" ".join(self.pages))
        self.language = detect(self.text)
        self.__generate_tokens()
        self.__read_head()
        print("###")
        print(file_path)
        print("Found: " + str(self.found))
        print("Count: " + str(len(self.references.keys())))
        print(self.references.keys())
        print("###")

    def __convert_pdf_to_pages(self):
        file = open(self.file_path, 'rb')

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

    def __generate_tokens(self):
        if self.language == "de" or self.language == "en":
            space_language = 'de_core_news_sm'
            if self.language == "en":
                space_language = 'en_core_web_sm'

            nlp = spacy.load(space_language)

            prefix_re = spacy.util.compile_prefix_regex(nlp.Defaults.prefixes)
            suffix_re = spacy.util.compile_suffix_regex(nlp.Defaults.suffixes)
            infix_re = re.compile(r'''[-~]''')

            nlp.tokenizer = Tokenizer(nlp.vocab, prefix_search=prefix_re.search, suffix_search=suffix_re.search,
                                 infix_finditer=infix_re.finditer, token_match=None)

            text_splits = [self.text[index: index + self.characters_per_operation] for index in range(0, len(self.text), self.characters_per_operation)]

            word_counter = collections.Counter([])
            for text_split in text_splits:
                doc = nlp(text_split)
                filtered_tokens = [self.__preprocess_token(token) for token in doc if self.__is_token_allowed(token)]
                doc_words = collections.Counter(filtered_tokens)
                word_counter = word_counter + doc_words

            self.tokens = word_counter
            return

        self.tokens = collections.Counter([])

    def __is_token_allowed(self, token):
        if not token or not token.text.strip() \
                or token.is_stop \
                or token.is_punct \
                or not token.is_alpha \
                or len(token.lemma_.strip()) <= 2 \
                or self.__is_in_false_words_list(str(token.lemma_).strip().lower()):
            return False
        return True

    def __preprocess_token(self, token):
        return token.lemma_.strip().lower()

    def __is_in_false_words_list(self, token):
        for false_word in self.false_words:
            if false_word == token:
                return True
        return False

    def __preprocess_text(self, text):
        z = "RXh0ZXJuZSBlbGVrdHJvbmlzY2hlIEF1c2xlZ2VzdGVsbGUtQmV1dGgtQmF5ZXJpc2NoZXMgSG9j aHNjaHVsLUtvbnNvcnRpdW0gSFMgTcODwrxuY2hlbiAtIEJpYmxpb3RoZWstS2ROci40MDMzMTQ5 LUlELktCVkZIWTFUOUNSVFpVVU9RU0pLVFpPSS4xLTIwMjItMDEtMDcgMTM6Mjc6MzY= Externe elektronische Auslegestelle-Beuth-Bayerisches Hochschul-Konsortium HS München - Bibliothek-KdNr.4033149-ID.KBVFHY1T9CRTZUUOQSJKTZOI.1-2022-01-07"
        w = "Externe elektronische Auslegestelle-Beuth-Bayerisches Hochschul-Konsortium HS München - Bibliothek-KdNr."
        uu = "RXh0ZXJuZSBlbGVrdHJvbmlzY2hlIEF1c2xlZ2VzdGVsbGUtQmV1dGgtQmF5ZXJpc2NoZXMgSG9j aHNjaHVsLUtvbnNvcnRpdW0gSFMgTcODwrxuY2hlbiAtIEJpYmxpb3RoZWstS2ROci40MDMzMTQ5 LUlELktCVkZIWTFUOUNSVFpVVU9RU0pLVFpPSS4xLTIwMjItMDEtMDcgMTM6Mjc6MzY= Externe elektronische Auslegestelle-Beuth-Bayerisches Hochschul-Konsortium HS München - Bibliothek-KdNr."
        cool = "RXh0ZXJuZSBlbGVrdHJvbmlzY2hlIEF1c2xlZ2VzdGVsbGUtQmV1dGgtQmF5ZXJpc2NoZXMgSG9j"
        cooler = "aHNjaHVsLUtvbnNvcnRpdW0gSFMgTcODwrxuY2hlbiAtIEJpYmxpb3RoZWstS2ROci40MDMzMTQ5"
        nochcooler = "LUlELk4xSEtZVjE3TzJYNE9HMUdZTDFESUhaWi4yLTIwMjItMDEtMDcgMTM6MzY6MDA="

        sep = "___UHU___"
        text = text \
            .replace("\n", "[$&$]") \
            .replace(uu, sep) \
            .replace(z, sep) \
            .replace(cool, sep) \
            .replace(nochcooler, sep) \
            .replace(cooler, sep) \
            .replace(w, sep) \
            .replace(sep, "") \
            .replace("[$&$]", "\n")
        return text

    def __preprocess_text_1(self, text):
        z = "RXh0ZXJuZSBlbGVrdHJvbmlzY2hlIEF1c2xlZ2VzdGVsbGUtQmV1dGgtQmF5ZXJpc2NoZXMgSG9j aHNjaHVsLUtvbnNvcnRpdW0gSFMgTcODwrxuY2hlbiAtIEJpYmxpb3RoZWstS2ROci40MDMzMTQ5 LUlELktCVkZIWTFUOUNSVFpVVU9RU0pLVFpPSS4xLTIwMjItMDEtMDcgMTM6Mjc6MzY= Externe elektronische Auslegestelle-Beuth-Bayerisches Hochschul-Konsortium HS München - Bibliothek-KdNr.4033149-ID.KBVFHY1T9CRTZUUOQSJKTZOI.1-2022-01-07"
        w = "Externe elektronische Auslegestelle-Beuth-Bayerisches Hochschul-Konsortium HS München - Bibliothek-KdNr."
        uu = "RXh0ZXJuZSBlbGVrdHJvbmlzY2hlIEF1c2xlZ2VzdGVsbGUtQmV1dGgtQmF5ZXJpc2NoZXMgSG9j aHNjaHVsLUtvbnNvcnRpdW0gSFMgTcODwrxuY2hlbiAtIEJpYmxpb3RoZWstS2ROci40MDMzMTQ5 LUlELktCVkZIWTFUOUNSVFpVVU9RU0pLVFpPSS4xLTIwMjItMDEtMDcgMTM6Mjc6MzY= Externe elektronische Auslegestelle-Beuth-Bayerisches Hochschul-Konsortium HS München - Bibliothek-KdNr."
        cool = "RXh0ZXJuZSBlbGVrdHJvbmlzY2hlIEF1c2xlZ2VzdGVsbGUtQmV1dGgtQmF5ZXJpc2NoZXMgSG9j"
        cooler = "aHNjaHVsLUtvbnNvcnRpdW0gSFMgTcODwrxuY2hlbiAtIEJpYmxpb3RoZWstS2ROci40MDMzMTQ5"
        nochcooler = "LUlELk4xSEtZVjE3TzJYNE9HMUdZTDFESUhaWi4yLTIwMjItMDEtMDcgMTM6MzY6MDA="
        sep = "___UHU___"

        intermediate = str(text).replace("\n", "[$&$]")\
            .replace(uu, sep) \
            .replace(z, sep) \
            .replace(cool, sep) \
            .replace(nochcooler, sep) \
            .replace(cooler, sep) \
            .replace(w, sep) \
            .replace(sep, "")\
            .replace("  ", " ")\
            .strip()

        return "[$&$]" + intermediate + "[$&$]"

    def __read_head(self):
        self.__get_references()
        title_page_counter = self.__get_ics()
        self.__get_number(title_page_counter)

    def __get_references(self):
        sep = "[$&$]"
        content_pattern_de = r'(' \
                             r'(\B\[\$\&\$\]2 Normative Verweisungen\[\$\&\$\]\B)|' \
                             r'(\B\[\$\&\$\]2 Normative Verweisungen\[\$\&\$\]\b)|' \
                             r'(\b\[\$\&\$\]2 Normative Verweisungen\[\$\&\$\]\B)|' \
                             r'(\b\[\$\&\$\]2 Normative Verweisungen\[\$\&\$\]\b)|' \
                             r'(\B\[\$\&\$\]Normative Verweisungen\[\$\&\$\]\B)|' \
                             r'(\B\[\$\&\$\]Normative Verweisungen\[\$\&\$\]\b)|' \
                             r'(\b\[\$\&\$\]Normative Verweisungen\[\$\&\$\]\B)|' \
                             r'(\b\[\$\&\$\]Normative Verweisungen\[\$\&\$\]\b))' \
                             r'.+?(?=' \
                             r'(\[\$\&\$\]3 Begriffe)|' \
                             r'(\[\$\&\$\]3 Definitionen)|' \
                             r'(\[\$\&\$\]Begriffe)|' \
                             r'(\[\$\&\$\]Definitionen))'

        content_pattern_en = r'(' \
                             r'(\B\[\$\&\$\]2 Normative references\[\$\&\$\]\B)|' \
                             r'(\B\[\$\&\$\]2 Normative references\[\$\&\$\]\b)|' \
                             r'(\b\[\$\&\$\]2 Normative references\[\$\&\$\]\B)|' \
                             r'(\b\[\$\&\$\]2 Normative references\[\$\&\$\]\b)|' \
                             r'(\B\[\$\&\$\]Normative references\[\$\&\$\]\B)|' \
                             r'(\B\[\$\&\$\]Normative references\[\$\&\$\]\b)|' \
                             r'(\b\[\$\&\$\]Normative references\[\$\&\$\]\B)|' \
                             r'(\b\[\$\&\$\]Normative references\[\$\&\$\]\b))' \
                             r'.+?(?=' \
                             r'(\[\$\&\$\]3 Terms)|' \
                             r'(\[\$\&\$\]3 Definitions)|' \
                             r'(\[\$\&\$\]Terms)|' \
                             r'(\[\$\&\$\]Definitions))'

        patterns = [content_pattern_de, content_pattern_en]

        # reads table from pdf file
        #tabula.convert_into(self.file_path, str(self.file_path) + ".csv", output_format="csv", encoding='utf-8', spreadsheet=True, pages="all")

        #tabula.io.read_pdf(self.file_path, output_format=)

        refs = {}
        df = tabula.io.read_pdf(self.file_path, encoding='utf-8', pages='all')
        if isinstance(df, list):
            for data_frame in df:
                if isinstance(data_frame, pandas.DataFrame):
                    if data_frame.columns.size >= 3 and \
                            data_frame.columns.values[0] == "EN reference" and \
                            data_frame.columns.values[1] == "Reference in text" and \
                            data_frame.columns.values[2] == "Title":

                        intermediate_key = ""
                        intermediate_value = ""

                        for row in data_frame.values.tolist():
                            key = row[0]

                            if pandas.isna(key):
                                if intermediate_key == "":
                                    break
                                else:
                                    intermediate_value = intermediate_value + " " + str(row[2])
                            else:
                                if intermediate_key == "":
                                    intermediate_key = str(key)
                                    intermediate_value = str(row[2])
                                else:
                                    refs[intermediate_key] = intermediate_value
                                    intermediate_key = str(key)
                                    intermediate_value = str(row[2])

                        break

        print(refs)

        if len(refs.keys()) > 0:
            self.references = refs
            self.found = True
            return


        text = self.text.replace("\n", sep).replace("  ", " ").replace(" [$&$]", sep).replace("[$&$] ", sep)

        for pattern in patterns:
            text_matches = [x.group() for x in re.finditer(pattern, text)]
            print("PATTERN")

            if len(text_matches) == 1:
                page = text_matches[0]
            else:
                if len(text_matches) == 2:
                    page = text_matches[1]
                else:
                    continue

            page = page \
                .replace("[$&$]DIN", "[&$&]DIN") \
                .replace("[$&$]EN", "[&$&]EN") \
                .replace("[$&$]ISO", "[&$&]ISO") \
                .replace("[$&$]IEC", "[&$&]IEC") \
                .replace("[$&$]ETSI", "[&$&]ETSI") \
                .replace("[$&$]VDE", "[&$&]VDE") \
                .replace("[$&$]VdS", "[&$&]VdS") \
                .replace("[$&$]", " ")

            page = " ".join(page.split())
            page = page.replace("[&$&]", sep)
            page = page + sep

            #print(page)

            reference_pattern = r'(' \
                                r'(\bEN\b)|' \
                                r'(\bETSI\b)|' \
                                r'(\bVDE\b)|' \
                                r'(\bVdS\b)|' \
                                r'(\bDIN\b)|' \
                                r'(\bISO\b)|' \
                                r'(\bIEC\b)|' \
                                r'(\bCEN\b))' \
                                r'.+?(?=(' \
                                r'(\[\$\&\$\])|' \
                                r'(\.\[\$\&\$\])|' \
                                r'(\.)))'
            matches = [x.group() for x in re.finditer(reference_pattern, page)]
            results = {}

            for match in matches:
                ref = match.replace(sep, " ").replace("  ", " ").strip()
                splits = ref.split(",", 1)
                if len(splits) == 2:
                    results[str(splits[0]).replace("  ", " ").strip()] = str(splits[1]).replace("  ", " ").strip()

            print("######################################")
            print("OLD " + str(len(results)))
            print("######################################")

            if len(refs) == 0:
                self.references = results
            self.found = True

            return

        if len(refs) == 0:
            self.references = {}
        self.found = False

        print("######################################")
        #print(text)
        print("######################################")

    def __get_ics(self):
        pattern = r'(\bICS\b )' \
                  r'((([0-9]{2}\.[0-9]{3}\.[0-9]{2})|' \
                  r'([0-9]{2}\.[0-9]{3})|' \
                  r'([0-9]{2}))' \
                  r'([;] ))*' \
                  r'(([0-9]{2}\.[0-9]{3}\.[0-9]{2})|' \
                  r'([0-9]{2}\.[0-9]{3})|' \
                  r'([0-9]{2}))'

        val = ""

        counter = 0
        for page in self.pages:

            intermediate = ' '.join(self.__preprocess_text_1(page).split())
            val = val + intermediate
            matches = [x.group() for x in re.finditer(pattern, intermediate)]
            if len(matches) > 0:
                results = []
                for match in matches:
                    match = match.replace("ICS", "")
                    match = match.replace(";", "")
                    entries = list(filter(None, match.split()))
                    for entry in entries:
                        results.append(entry)
                self.ics = results
                return counter
            else:
                counter = counter + 1

        self.ics = []
        return -1

    def __get_number(self, page_counter):
        sep = "[$&$]"
        if page_counter > -1:
            text = self.pages[page_counter]
            text = self.__preprocess_text(text).replace("\n", sep).replace("  ", " ").replace(" [$&$]", sep).replace("[$&$] ", sep)
            pattern = r'(\bDIN\b|\bEN\b|\bISO\b).+?(?=(\[\$\&\$\]))'
            matches = [x.group() for x in re.finditer(pattern, text)]
            for match in matches:
                number = ' '.join(match.replace("[$&$]", " ").strip().split())
                if any(char.isdigit() for char in number):
                    self.number = number
                    return

            self.number = "EMPTY " + self.file_path
            print(text)
        else:
            page_numbers = len(self.pages)
            if page_numbers > 0:
                for index in range(page_numbers):
                    text = self.pages[index]
                    text = self.__preprocess_text(text).replace("\n", sep).replace("  ", " ").replace(" [$&$]", sep).replace("[$&$] ", sep)
                    pattern = r'(\bDIN\b|\bEN\b|\bISO\b).+?(?=(\[\$\&\$\]))'
                    matches = [x.group() for x in re.finditer(pattern, text)]
                    for match in matches:
                        number = ' '.join(match.replace("[$&$]", " ").strip().split())
                        if any(char.isdigit() for char in number):
                            self.number = number
                            return
                    else:
                        continue

                self.number = "EMPTY in LOOP" + self.file_path
                print("EMPTY in LOOP" + self.file_path + " not found")
            else:
                self.number = "EMPTY " + self.file_path
                print("EMPTY " + self.file_path + " not found")
