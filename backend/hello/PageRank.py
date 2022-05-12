import numpy as np

from .StandardsDocument import StandardsDocument


class PageRank:
    alpha = 0.15
    iterations = 7

    def __init__(self, documents):
        items = {}
        standard_documents = {}
        reference_documents = {}

        for document in documents:
            if isinstance(document, StandardsDocument):
                items[document.number] = "TITLE"
                standard_documents[document.number] = document
                document_references = document.references
                for reference_key in document_references.keys():
                    items[reference_key] = document_references[reference_key]
                    if reference_key in reference_documents.keys():
                        reference_set = reference_documents[reference_key]
                        reference_set.add(document.number)
                    else:
                        reference_documents[reference_key] = {document.number}

        matrix = []
        position_dict = {}
        counter = 0
        for item_key in items.keys():
            row = []
            if item_key in standard_documents.keys():
                document = standard_documents[item_key]
                references = document.references
                for column_key in items.keys():
                    if column_key in references.keys():
                        row.append(1 / (len(references)))
                    else:
                        row.append(0)
            else:
                if item_key in reference_documents.keys():
                    references = reference_documents[item_key]
                    for column_key in items.keys():
                        if column_key in references:
                            row.append(1 / (len(references)))
                        else:
                            row.append(0)

            matrix.append(row)
            position_dict[item_key] = counter
            counter = counter + 1

        refactored_matrix = []
        for row_counter in range(len(matrix)):
            new_row = []
            for row in matrix:
                new_row.append(row[row_counter])
            refactored_matrix.append(new_row)

        pagerank = self.__calc_page_rank(refactored_matrix, self.iterations)

        result = {}
        for key in position_dict:
            result[key] = pagerank[position_dict[key]]

        self.results = result

    def __calc_page_rank(self, matrix, iterations):
        dumped_matrix = np.multiply(matrix, (1 - self.alpha))

        if iterations > 0:
            intermediate = np.matmul(dumped_matrix, self.__calc_page_rank(matrix, iterations - 1))
        else:
            start_vector = [1 / len(matrix) for _ in range(len(matrix))]
            start_vector_array = np.array(start_vector)
            intermediate = np.matmul(dumped_matrix, start_vector_array)

        dumping_vector = [self.alpha / len(matrix) for _ in range(len(matrix))]
        dumping_vector_array = np.array(dumping_vector)

        return np.add(intermediate, dumping_vector_array)
