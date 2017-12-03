from django.db.models.sql.where import WhereNode
from django.db.models.sql.query import Query
from django.db.models.fields.related_lookups import RelatedIn, RelatedLookupMixin


def _traverse(node):
    for child_node in node.children:
        if isinstance(child_node, WhereNode):
            for n, _ in _traverse(child_node):
                yield n, False
        elif isinstance(child_node, (RelatedIn, RelatedLookupMixin)):
            if isinstance(child_node.rhs, Query):
                for n, _ in _traverse(child_node.rhs.where):
                    yield n, True
            else:
                yield child_node, False
        else:
            yield child_node, False


def get_where_nodes(query):
    return _traverse(query.where)
