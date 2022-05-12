import random
import os
import json


from .Node import Node
from .Edge import Edge
from .Graph import Graph

from .StandardsDocument import StandardsDocument

from types import SimpleNamespace

max_node_size = 25
min_node_size = 5


def build(documents, page_rank, suggested_words):
    standard_documents = {}
    reference_documents = {}
    ics_dict = {}

    min_page_rank_value = 100
    max_page_rank_value = -1
    if isinstance(page_rank, dict):
        for page_rank_key in page_rank.keys():
            page_rank_value = page_rank[page_rank_key]
            if page_rank_value < min_page_rank_value:
                min_page_rank_value = page_rank_value

            if page_rank_value > max_page_rank_value:
                max_page_rank_value = page_rank_value

    edges = []
    edges_id = []

    for document in documents:
        if isinstance(document, StandardsDocument):
            standard_documents[document.number] = document
            document_references = document.references
            for reference_key in document_references.keys():
                if reference_key in reference_documents.keys():
                    reference_set = reference_documents[reference_key]
                    reference_set.add(document.number)
                else:
                    reference_documents[reference_key] = {document.number}

                if (str(document.number) + "###" + str(reference_key)) not in edges_id and (
                        str(reference_key) + "###" + str(document.number)) not in edges_id:
                    edges_id.append(str(document.number) + "###" + str(reference_key))
                    edge = Edge(document.number, reference_key)
                    edges.append(edge)

            for entry in document.ics:
                if entry in ics_dict.keys():
                    ics_list = ics_dict[entry]
                    if isinstance(ics_list, list):
                        ics_list.append(document.number)
                else:
                    ics_dict[entry] = [document.number]

    nodes = []
    ics_color_dict = calculate_ics_color_dict(ics_dict)

    used_numbers = set()

    for standard_documents_key in standard_documents.keys():
        document = standard_documents[standard_documents_key]
        if standard_documents_key in ics_color_dict.keys():
            color = ics_color_dict[standard_documents_key]
        else:
            color = "#000000"
        if standard_documents_key not in used_numbers:
            tokens = document.tokens.most_common(1)
            most_common_number = 0
            if len(tokens) == 1:
                most_common_number = tokens[0][1]

            node = Node(standard_documents_key,
                        standard_documents_key,
                        calculate_size(page_rank[standard_documents_key], min_page_rank_value, max_page_rank_value),
                        color,
                        False,
                        dict(document.tokens),
                        page_rank[standard_documents_key],
                        0,
                        most_common_number)
            nodes.append(node)
            used_numbers.add(standard_documents_key)

    for reference_documents_key in reference_documents.keys():
        reference = reference_documents[reference_documents_key]
        if reference_documents_key in ics_color_dict.keys():
            color = ics_color_dict[reference_documents_key]
        else:
            color = "#000000"

        if reference_documents_key not in used_numbers:
            node = Node(reference_documents_key,
                        reference_documents_key,
                        calculate_size(page_rank[reference_documents_key], min_page_rank_value, max_page_rank_value),
                        color,
                        True,
                        dict(),
                        page_rank[reference_documents_key],
                        0,
                        0)
            nodes.append(node)
            used_numbers.add(reference_documents_key)

    graph = Graph(nodes, edges, suggested_words)
    return graph


def calculate_size(page_rank_value, min_page_rank_value, max_page_rank_value):
    m = page_rank_value - min_page_rank_value
    n = max_page_rank_value - min_page_rank_value
    if n > 0:
        ratio = m/n
    else:
        ratio = 0

    return min_node_size + ((max_node_size - min_node_size) * ratio)


def calculate_ics_color_dict(ics_dict):
    number_color_dict = {}
    for ics_key in ics_dict.keys():
        numbers = ics_dict[ics_key]
        color = "#" + ''.join([random.choice('ABCDEF0123456789') for _ in range(6)])
        if isinstance(numbers, list):
            for number in numbers:
                if number in number_color_dict.keys():
                    oldColor = number_color_dict[number]
                    if color != oldColor:
                        rand_colors = "#" + ''.join([random.choice('ABCDEF0123456789') for i in range(6)])
                        number_color_dict[number] = rand_colors
                else:
                    number_color_dict[number] = color

    return number_color_dict


def load(directory_path):
    file_path = os.path.join(directory_path, "graph.json")
    file = open(file_path, "r")
    data = json.load(file)
    file.close()
    return Graph(**data)
