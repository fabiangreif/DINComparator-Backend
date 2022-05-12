import collections
import os
import zipfile
import shutil
import json
import operator

from json import JSONEncoder
from pathlib import Path

from . import GraphBuilder
from .StandardsDocument import StandardsDocument
from .PageRank import PageRank


class RelevanceWorker:

    def __init__(self, directory_id, archive_path):
        self.directory_id = directory_id
        self.archive_path = archive_path

        self.__unzip_archive()
        self.__create_index_file()

    def create_result(self):
        files = self.__get_pdf_files()
        counter = 1
        documents = []

        fixed_tokens_list = []
        all_tokens_list = []

        for file_path in files:
            document = StandardsDocument(file_path)
            documents.append(document)
            most_common_2 = document.tokens.most_common(2)
            most_common_10 = document.tokens.most_common(10)

            fixed_tokens_list.append(most_common_2)
            all_tokens_list.append(most_common_10)

            print(str(counter) + "/" + str(len(files)))
            self.__update_index_file(counter, len(files))
            counter = counter + 1

        word_list_length = 4 * len(files)
        suggested_words = []

        fixed_tokens = [token[0] for token_list in fixed_tokens_list for token in token_list]
        all_tokens = [token for token_list in all_tokens_list for token in token_list]

        for fixed_token_value in fixed_tokens:
            suggested_words.append(fixed_token_value)

        token_list = []
        for token in all_tokens:
            for _ in (0, token[1]):
                token_list.append(token[0])

        rest_list_length = word_list_length - len(suggested_words)
        all_token_counter = collections.Counter(filter(lambda word: word not in suggested_words, token_list))
        rest_common_words = all_token_counter.most_common(rest_list_length)

        for token in rest_common_words:
            suggested_words.append(token[0])

        page_rank = PageRank(documents)
        graph = GraphBuilder.build(documents, page_rank.results, suggested_words)

        self.__create_graph_file(graph)

        return graph

    def __unzip_archive(self):
        paths = self.archive_path.split("/")

        module_dir = os.path.dirname(__file__)
        absolute_path = os.path.abspath(os.path.join(module_dir, os.pardir))

        for path in paths:
            absolute_path = os.path.join(absolute_path, path)

        directory_path = os.path.join(
            os.path.join(os.path.abspath(os.path.join(__file__, "..")), "archives"), self.directory_id)

        Path(directory_path).mkdir(parents=True, exist_ok=True)

        zip_obj = zipfile.ZipFile(absolute_path, 'r')
        for member in zip_obj.namelist():
            filename = os.path.basename(member)

            if not filename:
                continue

            source = zip_obj.open(member)
            target = open(os.path.join(directory_path, filename), "wb")
            shutil.copyfileobj(source, target)

        self.directory_path = directory_path

    def __create_index_file(self):
        data = {
            "hasFinished": False,
            "files_ready": 0,
            "files_all": 0
        }
        json_string = json.dumps(data)
        file_path = os.path.join(self.directory_path, "index.json")
        file = open(file_path, "x")
        file.write(json_string)
        file.close()

    def __get_pdf_files(self):
        files = []
        for file in os.listdir(self.directory_path):
            file_path = os.path.join(self.directory_path, file)
            if os.path.isfile(file_path) and (file_path.endswith(".pdf") or file_path.endswith(".PDF")):
                files.append(file_path)

        return files

    def __update_index_file(self, files_ready, files_all):
        file_path = os.path.join(self.directory_path, "index.json")

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

    def __create_graph_file(self, graph):
        json_string = json.dumps(graph, indent=4, cls=GraphEncoder)
        file_path = os.path.join(self.directory_path, "graph.json")
        file = open(file_path, "x")
        file.write(json_string)
        file.close()


class GraphEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
