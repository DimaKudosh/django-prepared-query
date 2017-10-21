import random
import string
from django.db.models.sql.where import WhereNode


def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


def _traverse(node):
    for child_node in node.children:
        if isinstance(child_node, WhereNode):
            for n in _traverse(child_node):
                yield n
        else:
            yield child_node


def get_where_nodes(query):
    return _traverse(query.where)
