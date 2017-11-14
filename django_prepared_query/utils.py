from django.db.models.sql.where import WhereNode


def _traverse(node):
    for child_node in node.children:
        if isinstance(child_node, WhereNode):
            for n in _traverse(child_node):
                yield n
        else:
            yield child_node


def get_where_nodes(query):
    return _traverse(query.where)
