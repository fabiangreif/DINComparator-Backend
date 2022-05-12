from django.shortcuts import render
from rest_framework import viewsets

from .Graph import Graph
from .GraphBuilder import calculate_size
from .RelevanceWorker import RelevanceWorker
from .functions import unzip_archive, get_pdf_files, calc_relevance, \
    get_directory_path, directory_exists, create_index_file, index_file_exists, read_index_file, update_index_file, \
    calculate_graph, get_nlps, graph_file_exists
from .serializers import TodoSerializer
import numpy as np

import random
from .models import Todo
from .models import Entry
from .models import Details
from .serializers import PostSerializer
from .models import Post
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from . import GraphBuilder

import collections

from django.http import JsonResponse

from .serializers import SearchRequestSerializer

from .Node import Node
from .Edge import Edge

from django.conf import settings

from django.http import HttpResponse

# Create your views here.

class TodoView(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    queryset = Todo.objects.all()


def index(request):
    return render(request, 'hello/index.html')


class TestView(APIView):

    def say_hello(request):
        return HttpResponse('Hello du moof ')


class StatusView(APIView):

    def get(self, request, *args, **kwargs):
        directory_id = request.GET['id']
        directory_path = get_directory_path(directory_id)
        if directory_exists(directory_path):
            if index_file_exists(directory_path):
                data = read_index_file(directory_path)
                return JsonResponse({
                    "directory_build": True,
                    "index_build": True,
                    "hasFinished": data["hasFinished"],
                    "files_ready": data["files_ready"],
                    "files_all": data["files_all"]
                }, safe=False)
            else:
                return JsonResponse({
                    "directory_build": True,
                    "index_build": False,
                    "hasFinished": False,
                    "files_ready": 0,
                    "files_all": 0
                }, safe=False)
        else:
            return JsonResponse({
                "directory_build": False,
                "index_build": False,
                "hasFinished": False,
                "files_ready": 0,
                "files_all": 0
            }, safe=False)


class RelView(APIView):

    def get(self, request, *args, **kwargs):
        directory_id = request.GET['id']
        keyWords = request.GET['keywords']
        directory_path = get_directory_path(directory_id)
        if directory_exists(directory_path):
            if index_file_exists(directory_path):
                data = read_index_file(directory_path)
                return JsonResponse({
                    "directory_build": True,
                    "index_build": True,
                    "hasFinished": data["hasFinished"],
                    "files_ready": data["files_ready"],
                    "files_all": data["files_all"]
                }, safe=False)
            else:
                return JsonResponse({
                    "directory_build": True,
                    "index_build": False,
                    "hasFinished": False,
                    "files_ready": 0,
                    "files_all": 0
                }, safe=False)
        else:
            return JsonResponse({
                "directory_build": False,
                "index_build": False,
                "hasFinished": False,
                "files_ready": 0,
                "files_all": 0
            }, safe=False)



class PostView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        directory_id = request.GET['id']
        keywords = request.GET['keywords']
        keywords_nlp = get_nlps(keywords)
        keyword_dict = dict(keywords_nlp)

        edges = []
        nodes = []
        suggested_words = []

        directory_path = get_directory_path(directory_id)
        if directory_exists(directory_path):
            if index_file_exists(directory_path) and graph_file_exists(directory_path):
                data = read_index_file(directory_path)
                if data["hasFinished"]:
                    graph_Data = GraphBuilder.load(directory_path)
                    if isinstance(graph_Data, Graph):

                        tf_list = {}
                        number_counter = {}
                        for keyword in keyword_dict.keys():
                            number_counter[keyword] = 0

                        for node in graph_Data.nodes:
                            tokens = node["tokens"]
                            most_common_number = node["most_common_number"]
                            tf_entry = {}
                            if isinstance(tokens, dict):
                                for keyword in keyword_dict.keys():
                                    if most_common_number > 0 and keyword in tokens.keys():
                                        tf_entry[keyword] = 0.5 + 0.5*(tokens[keyword] / most_common_number)
                                        number_counter[keyword] = number_counter[keyword] + 1
                                    else:
                                        tf_entry[keyword] = 0

                            else:
                                for keyword in keyword_dict.keys():
                                    tf_entry[keyword] = 0

                            tf_list[node["number"]] = tf_entry

                        for edge in graph_Data.edges:
                            edges.append({
                                "left": edge["left"],
                                "right": edge["right"]
                            })

                        for word in graph_Data.suggested_words:
                            suggested_words.append(word)

                        n = len(graph_Data.nodes)

                        for keyword in number_counter.keys():
                            val = number_counter[keyword]
                            if val > 0:
                                number_counter[keyword] = np.log(n / number_counter[keyword])
                            else:
                                number_counter[keyword] = 0

                        tf_idf_dict = {}
                        for node_number in tf_list.keys():
                            keywords_tf_values = tf_list[node_number]
                            intermediate = 0
                            for keywords_tf_value in keywords_tf_values.keys():
                                tf_value = keywords_tf_values[keywords_tf_value]
                                idf = number_counter[keywords_tf_value]

                                intermediate = intermediate + (tf_value * idf)
                            tf_idf_dict[node_number] = intermediate

                        total_tf_idf_value = 0
                        for key in tf_idf_dict.keys():
                            total_tf_idf_value = total_tf_idf_value + tf_idf_dict[key]

                        for key in tf_idf_dict.keys():
                            if total_tf_idf_value > 0:
                                tf_idf_dict[key] = tf_idf_dict[key]/total_tf_idf_value
                            else:
                                tf_idf_dict[key] = 0

                        alpha = 0.5

                        values = {}
                        for node in graph_Data.nodes:
                            tf_idf = tf_idf_dict[node["number"]]
                            pagerank = node["pagerank"]
                            val = ((1 - alpha) * tf_idf) + (alpha * pagerank)
                            values[node["number"]] = val

                        min_page_rank_value = 100
                        max_page_rank_value = -1

                        for key in values.keys():
                                rank_value = values[key]
                                if rank_value < min_page_rank_value:
                                    min_page_rank_value = rank_value

                                if rank_value > max_page_rank_value:
                                    max_page_rank_value = rank_value


                        for node in graph_Data.nodes:
                            val = values[node["number"]]
                            size = calculate_size(val, min_page_rank_value, max_page_rank_value)

                            nodes.append({
                                "id": node["number"],
                                "title": node["title"],
                                "size": size,
                                "color": node["color"],
                                "is_reference": node["is_reference"]
                            })

        res = {
            "nodes": nodes,
            "edges": edges,
            "commonWords": suggested_words

        }

        return JsonResponse(res, safe=False)


    def post(self, request, *args, **kwargs):

        request_serializer = SearchRequestSerializer(data=request.data)

        if request_serializer.is_valid():
            request_serializer.save()

            archive_path = str(request_serializer.data.get("archive"))
            directory_id = str(request_serializer.data.get("id"))
            keywords = str(request_serializer.data.get("keywords"))

            worker = RelevanceWorker(directory_id, archive_path)
            result = worker.create_result()

            edges = []
            for edge in result.edges:
                if isinstance(edge, Edge):
                    edges.append({
                        "left": edge.left,
                        "right": edge.right
                    })

            nodes = []
            for node in result.nodes:
                if isinstance(node, Node):
                    nodes.append({
                        "id": node.number,
                        "title": node.title,
                        "size": node.size,
                        "color": node.color,
                        "is_reference": node.is_reference
                    })

            res = {
                "nodes": nodes,
                "edges": edges,
                "commonWords": result.suggested_words

            }

            return JsonResponse(res, safe=False)
        else:
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
