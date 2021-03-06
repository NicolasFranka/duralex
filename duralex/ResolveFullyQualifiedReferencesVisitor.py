from duralex.alinea_parser import *

from AbstractVisitor import AbstractVisitor

class ResolveFullyQualifiedReferencesVisitor(AbstractVisitor):
    def __init__(self):
        self.ctx = []
        super(ResolveFullyQualifiedReferencesVisitor, self).__init__()

    def visit_node(self, node):
        if not self.resolve_fully_qualified_references(node):
            super(ResolveFullyQualifiedReferencesVisitor, self).visit_node(node)

    def resolve_fully_qualified_references(self, node):
        # If we are on an edit node that has edit ancestors
        # if 'type' in node and len(filter(lambda x : x['type'] == 'edit', get_node_ancestors(node))) > 0:
        #     # FIXME
        #     None

        # If we have an 'edit' node in an 'edit' node, the parent gives its
        # context to its descendants.
        if ('type' not in node or node['type'] not in AbstractVisitor.REF_TYPES) and len(node['children']) >= 1 and node['children'][0]['type'] == 'edit' and node['children'][0]['editType'] == 'edit':
            context = node['children'][0]['children'][0]
            remove_node(node, node['children'][0])
            self.ctx.append([copy_node(ctx_node, False) for ctx_node in filter_nodes(context, lambda x: x['type'] in AbstractVisitor.REF_TYPES)])
            for child in node['children']:
                self.visit_node(child)
            self.ctx.pop()
            return True
        # If we have a context and there is no ref type at all and we're not on a 'swap' edit
        elif len(self.ctx) > 0 and node['type'] == 'edit' and len(filter_nodes(node, lambda x : x['type'] in AbstractVisitor.REF_TYPES)) == 0:
            n = [copy_node(item) for sublist in self.ctx for item in sublist]
            n = sorted(n, key=lambda x : AbstractVisitor.REF_TYPES.index(x['type']))
            unshift_node(node, n[0])
            for i in range(1, len(n)):
                unshift_node(n[i - 1], n[i])
            return True
        # If we have a context and we're on root ref type
        elif len(self.ctx) > 0 and 'type' in node and node['type'] in AbstractVisitor.REF_TYPES and node['parent']['type'] not in AbstractVisitor.REF_TYPES:
            n = [copy_node(item) for sublist in self.ctx for item in sublist]
            n = sorted(n, key=lambda x : AbstractVisitor.REF_TYPES.index(x['type']))
            unshift_node(node['parent'], n[0])
            for i in range(1, len(n)):
                unshift_node(n[i - 1], n[i])
            remove_node(node['parent'], node)
            if node['type'] == 'incomplete-reference':
                if 'position' in node:
                    n[len(n) - 1]['position'] = node['position']
            else:
                unshift_node(n[len(n) - 1], node)
            return True
        # If we have multiple *-reference node in a single 'edit' node
        elif 'type' in node and node['type'] == 'edit' and len(filter_nodes(node, lambda x: x['type'] in AbstractVisitor.REF_TYPES and x['parent'] == node and len(filter_nodes(node, lambda y: y['type'] == x['type'])) == 1)) > 1:
            local_ctx = [copy_node(item) for item in filter_nodes(node, lambda x: x['type'] in AbstractVisitor.REF_TYPES)]
            for i in reversed(range(0, len(node['children']))):
                child = node['children'][i]
                if 'type' in child and child['type'] in AbstractVisitor.REF_TYPES:
                    remove_node(node, child)
            unshift_node(node, local_ctx[0])
            for i in range(1, len(local_ctx)):
                unshift_node(local_ctx[i - 1], local_ctx[i])
            return True

        return False
