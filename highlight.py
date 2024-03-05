import sys
import os
import argparse
from interpreter import parse_content, tokenize_exp, is_number
from interpreter import UNOPS, BINOPS, TRINOPS, NOPS

def combine_keys(*args):
    keys = set()
    for iterable in args:
        if type(iterable) == set:
            keys |= iterable
        elif type(iterable) == dict:
            keys |= set(iterable.keys())
        elif type(iterable) == list:
            keys |= set(iterable)
        else:
            raise ValueError('cannot get keys of type %s' % type(iterable))
    return keys

def hl_expr(exp):
    if exp == 'input': return '<span class="op">input</span>'
    brackets = '<span class="bracket">[</span>%s<span class="bracket">]</span>'
    inner = exp[1:-1]
    # empty expression, just return '[]'
    if not inner: return brackets % ''
    # highlight all tokens
    tokens = tokenize_exp(exp[1:-1])
    highlighted_tokens = []
    for token in tokens:
        if token[0] in ["'", '"']:
            highlighted_tokens.append('<span class="string">%s</span>' % token)
        elif token[0] == '$':
            highlighted_tokens.append('<span class="var">%s</span>' % token)
        elif is_number(token):
            highlighted_tokens.append('<span class="number">%s</span>' % token)
        elif token in combine_keys(UNOPS, BINOPS, TRINOPS, NOPS):
            highlighted_tokens.append('<span class="op">%s</span>' % token)
        elif token.lower() in ['f', 'false', 't', 'true']:
            highlighted_tokens.append('<span class="bool">%s</span>' % token)
        else:
            highlighted_tokens.append(token)
    return brackets % (' '.join(highlighted_tokens))

def hl_outputexp(args):
    return '<span class="kw-output">output</span> %s;' % hl_expr(args[0])

def hl_outputvar(args):
    return '<span class="kw-output">output</span> %s;' % ('<span class="var">$%s</span>' % args[0])

def hl_if(args):
    guard, body = args
    bodytype, *bodyargs = body
    if bodytype == 'set':       hl_body = hl_set(bodyargs)
    if bodytype == 'goto':      hl_body = hl_goto(bodyargs)
    if bodytype == 'outputexp': hl_body = hl_outputexp(bodyargs)
    if bodytype == 'outputvar': hl_body = hl_outputvar(bodyargs)
    hl_guard = hl_expr(guard)
    return '<span class="kw-if">if</span> %s <span class="kw-if">then</span>\n    %s' % (hl_guard, hl_body)

def hl_set(args):
    varname, exp = args
    hl_var = '<span class="var">$%s</span>' % varname
    hl_exp = hl_expr(exp)
    return '<span class="kw-set">set</span> %s %s;' % (hl_var, hl_exp)

def hl_mark(args):
    markname = args[0]
    return '<span class="kw-mark">mark</span> <span class="mark">%s</span>;' % markname

def hl_goto(args):
    markname = args[0]
    return '<span class="kw-goto">goto</span> <span class="mark">%s</span>;' % markname

def hl_comment(args):
    comment = args[0]
    return '<span class="comment">%s</span>' % comment

def highlight_statement(statement):
    statement_type, *args = statement
    if statement_type == 'comment':     return hl_comment(args)
    if statement_type == 'outputexp':   return hl_outputexp(args)
    if statement_type == 'outputvar':   return hl_outputvar(args)
    if statement_type == 'if':          return hl_if(args)
    if statement_type == 'set':         return hl_set(args)
    if statement_type == 'mark':        return hl_mark(args)
    if statement_type == 'goto':        return hl_goto(args)
    raise ValueError('unknown statement type: ' + statement_type)

def highlight_all(statement_list):
    out = '<code><pre>\n'
    for statement in statement_list:
        out += '%s\n' % highlight_statement(statement)
    return out + '</pre></code>'

STANDALONE_WRAPPER = '''
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="" xml:lang="">

<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  <title>%s</title>
  <style>%s</style>
</head>

<div class="generated-code">
%s
</div>
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a syntax-highlighted HTML file for a StackTo program.')
    parser.add_argument('infile', help='StackTo file to read from')
    parser.add_argument('-o', '--outfile', help='HTML file to write to', default=[None], required=False, nargs=1)
    parser.add_argument('-s', '--standalone', help='Whether to generate a standalone HTML file as opposed to a fragment', required=False, action='store_true')
    args = parser.parse_args()
    # print(args)
    infilename = getattr(args, 'infile')
    outfilename = getattr(args, 'outfile')[0]
    standalone = getattr(args, 'standalone')
    print('highlighting', infilename)
    with open(infilename, 'r') as f:
        filecontent = f.read()
    if outfilename is None:
        outfilename = 'highlighted_%s.html' % (infilename.split(os.path.sep)[-1])
    infilename = infilename.replace('\\', '/')
    statements = parse_content(filecontent, include_comments=True)
    # print('statements:', statements)

    highlighted = highlight_all(statements)

    if standalone:
        with open('style.css', 'r') as f:
            styling = f.read()
        highlighted = STANDALONE_WRAPPER % (infilename, styling, highlighted)

    with open(outfilename, 'w') as f:
        f.write(highlighted)

    print('generated', outfilename)