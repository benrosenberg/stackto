import sys
import os
from itertools import tee
import graphviz
from interpreter import parse_content

def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def node_str(statement):
    return str(statement).replace(':', '..')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('please provide a filename to run')
        sys.exit(1)
    print('creating flowchart out of', sys.argv[1])
    with open(sys.argv[1], 'r') as f:
        filecontent = f.read()
    statements = parse_content(filecontent)

    print('statements:', statements)

    use_indices = False
    if not len(set(statements)) == len(statements):
        print('warning: non-unique statements detected!')
        print('adding indices to differentiate nodes')
        use_indices = True

    DEFAULT = 'oval'

    g = graphviz.Digraph('flowchart of ' + sys.argv[1].replace('\\', '\\\\'))

    g.attr(label=g.name)
    g.attr(labelloc='t')
    g.attr(fontsize='28')
    g.attr(fontname='Arial')

    g.attr('node', {'fontname':'Consolas'})
    g.attr('edge', {'fontname':'Consolas'})

    if use_indices:
        index = 0
        while index < len(statements):
            statements[index] = tuple(list(statements[index]) + [('index', index)])
            index += 1

    markers = set()
    for index,statement in enumerate(statements):
        statement_type, *args = statement
        if statement_type == 'mark':
            markers.add(args[0])
            g.attr('node', {'shape' : 'tab'})
            g.node(node_str(statement))
            g.attr('node', {'shape' : DEFAULT})

    for statement in statements:
        statement_type, *args = statement
        if statement_type in ['mark', 'outputvar', 'outputexp', 'set']:
            if statement_type == 'mark':
                continue
                # all markers already added as nodes
            if statement_type in ['outputvar', 'outputexp']:
                g.attr('node', {'shape' : 'note'})
                g.node(node_str(statement))
                g.attr('node', {'shape' : DEFAULT})
            if statement_type == 'set':
                g.attr('node', {'shape' : 'box3d'})
                g.node(node_str(statement))
                g.attr('node', {'shape' : DEFAULT})
        elif statement_type == 'goto':
            mark = args[0]
            if mark not in markers:
                raise SyntaxError('undefined mark: ' + mark)
            g.attr('node', {'shape' : 'oval'})
            g.node(node_str(statement))
            g.edge(node_str(statement), node_str(('mark', mark)))
            g.attr('node', {'shape' : DEFAULT})
        elif statement_type == 'if':
            guard, body = args
            g.attr('node', {'shape' : 'component'})
            g.node(node_str(statement))
            g.attr('node', {'shape' : DEFAULT})
            bodytype, *bodyargs = body
            if bodytype == 'goto':
                mark = bodyargs[0]
                if mark not in markers:
                    raise SyntaxError('undefined mark: ' + mark)
                g.edge(node_str(statement), node_str(('mark', mark)), 'True')
        else:
            raise ValueError('unknown statement type: ' + statement_type)

    for a,b in pairwise(statements):
        # print('pair [', a, ',', b, ']')
        a_type, *rest = a
        if a_type == 'if':
            _, body = rest
            bodytype, *_ = body
            if bodytype == 'goto':
                g.edge(node_str(a), node_str(b), 'False')
            else:
                g.edge(node_str(a), node_str(b))
        elif a_type == 'goto':
            continue
        else:
            g.edge(node_str(a), node_str(b))

    outfilename = 'flowchart_{}.gv'.format(sys.argv[1].split(os.path.sep)[-1])
    g.render(outfilename, format='png', engine='dot')

    print('done')