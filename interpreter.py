import sys
import re
import random
from itertools import product

DATA_TYPES = {'bool', 'number', 'string', 'list'}

# ? casts to bool, ! is not, ~ is unary minus, # is len(list)
# num casts to number, splat puts all the elements of the list into the stack
# dup duplicates the top element, drop drops the top element of the stack
# str casts to string, round rounds numbers to nearest int
UNOPS = {
    '#':{'list'},
    '~':{'number'}, 
    '!':{'bool'}, 
    '?':{'bool', 'number', 'string'},
    'num':{'bool', 'number', 'string'},
    'splat':{'list'},
    'dup':DATA_TYPES,
    'drop':DATA_TYPES,
    'str':DATA_TYPES,
    'round':{'number'},
    'sum':{'list'},
    'prod':{'list'},
    'type':DATA_TYPES
} 

def process_unop(token, stack):
    if len(stack) < 1:
        raise ValueError('unop: stack too short (height %s, need >= 1): %s' % (len(stack), stack))
    argtype, arg = stack.pop()
    typesig = argtype
    if not typesig in UNOPS[token]:
        raise SyntaxError('unop: %s cannot process type "%s"' % (token, argtype))
    if token == '#':            return stack + [('number', len(arg))]
    if token == '~':            return stack + [('number', -arg)]
    if token == '!':            return stack + [('bool', not arg)]
    if token == 'dup':          return stack + [(argtype, arg), (argtype, arg)]
    if token == 'drop':         return stack
    if token == '?':            return stack + [('bool', bool(arg))]
    if token == 'str':
        if argtype == 'list':
            return stack + [('string', '[%s]' % ', '.join(str(val) for _, val in arg))]
        else:                   return stack + [('string', str(arg))]
    if token == 'round':        return stack + [('number', round(arg, 0))]
    if token == 'num':
        if argtype == 'bool':   return stack + [('number', float(arg))]
        if argtype == 'number': return stack + [('number', arg)]
        if argtype == 'string':
            if is_number(arg):
                return stack + [('number', float(arg))]
            raise ValueError('unop: %s cannot be converted to type "number"' % arg)
    if token == 'splat':        return stack + arg
    if token == 'sum':
        total = 0
        for subtype, subarg in arg:
            if not subtype == 'number':
                raise ValueError('unop: %s of type %s cannot be processed as a number by "%s"' % (subarg, subtype, token))
            total += subarg
        return stack + [('number', total)]
    if token == 'prod':
        total = 1
        for subtype, subarg in arg:
            if not subtype == 'number':
                raise ValueError('unop: %s of type %s cannot be processed as a number by "%s"' % (subarg, subtype, token))
            total *= subarg
        return stack + [('number', total)]
    if token == 'type':         return stack + [('string', argtype)]
    raise SyntaxError('unop: %s cannot be processed as a unop' % token)

BINOPS = {
    '<':{('number', 'number')}, 
    '>':{('number', 'number')}, 
    '<=':{('number', 'number')}, 
    '>=':{('number', 'number')}, 
    '=':{p for p in product(DATA_TYPES, DATA_TYPES)},
    '==':{p for p in product(DATA_TYPES, DATA_TYPES)},
    '<>':{p for p in product(DATA_TYPES, DATA_TYPES)},
    '!=':{p for p in product(DATA_TYPES, DATA_TYPES)},
    '&':{('bool', 'bool')}, 
    '^':{('bool', 'bool')}, 
    '|':{('bool', 'bool')}, 
    '+':{('number', 'number'), ('string', 'string')}, 
    '-':{('number', 'number')}, 
    '*':{('number', 'number'), ('string', 'number')}, 
    '/':{('number', 'number')}, 
    '//':{('number', 'number')}, 
    '%':{('number', 'number')}, 
    '@':{('list', 'list')}, 
    ':':{p for p in product(['list'], DATA_TYPES)},
    'swap':{p for p in product(DATA_TYPES, DATA_TYPES)},
    'nth':{('list', 'number')},
    'min':{('number', 'number')},
    'max':{('number', 'number')},
    'split':{('string', 'string')}
}

def process_binop(token, stack):
    if len(stack) < 2:
        raise ValueError('binop: stack too short for "%s" (height %s, need >= 2): %s' % (token, len(stack), stack))
    argtype_b, arg_b = stack.pop()
    argtype_a, arg_a = stack.pop()
    typesig = (argtype_a, argtype_b)
    if not typesig in BINOPS[token]:
        raise SyntaxError('binop: %s cannot process types "%s"' % (token, typesig))
    if token == '<':                return stack + [('bool', arg_a < arg_b)]
    if token == '>':                return stack + [('bool', arg_a > arg_b)]
    if token == '<=':               return stack + [('bool', arg_a <= arg_b)]
    if token == '>=':               return stack + [('bool', arg_a >= arg_b)]
    if token in ('=', '=='):        return stack + [('bool', (argtype_a == argtype_b) and (arg_a == arg_b))]
    if token in ('!=', '<>'):       return stack + [('bool', argtype_a != argtype_b or arg_a != arg_b)]
    if token == '&':                return stack + [('bool', arg_a and arg_b)]
    if token == '^':                return stack + [('bool', arg_a ^ arg_b)]
    if token == '|':                return stack + [('bool', arg_a or arg_b)]
    if token == '+':
        if argtype_a == 'string':   return stack + [('string', arg_a + arg_b)]
        else:                       return stack + [('number', arg_a + arg_b)]
    if token == '-':                return stack + [('number', arg_a - arg_b)]
    if token == '/': 
        if arg_b == 0: raise ZeroDivisionError('binop: zero division (%s) between %s and %s' % (token, arg_a, arg_b)) 
        else:                       return stack + [('number', arg_a / arg_b)]
    if token == '//':
        if arg_b == 0: raise ZeroDivisionError('binop: zero division (%s) between %s and %s' % (token, arg_a, arg_b)) 
        else:                       return stack + [('number', arg_a // arg_b)]
    if token == '%':                return stack + [('number', arg_a % arg_b)]
    if token == '*':
        if argtype_a == 'string':
            n = int(arg_b)
            if n != arg_b: raise ValueError('binop: non-integer argument "%s" passed to binop "*" in string multiplication (string %s)' % (arg_b, arg_a))
            return stack + [(argtype_a, arg_a * n)]
        return stack + [(argtype_a, arg_a * arg_b)]
    if token == '@':                return stack + [('list', arg_a + arg_b)]
    if token == ':':                return stack + [('list', arg_a + [(argtype_b, arg_b)])]
    if token == 'swap':             return stack + [(argtype_b, arg_b), (argtype_a, arg_a)]
    if token == 'nth':
        n = int(arg_b)
        if n != arg_b: raise ValueError('binop: non-integer argument "%s" passed to binop "nth"' % arg_b)
        elif n >= len(arg_a): raise ValueError('binop: n "%s" greater than list length (%s) in binop "nth"' % (n, len(arg_a)))
        elif n < 0:
            raise ValueError('binop: %s cannot process negative list index "%s"' % (token, n))                       
        else:                       return stack + [arg_a[n]]
    if token == 'min':              return stack + [('number', min(arg_a, arg_b))]
    if token == 'max':              return stack + [('number', max(arg_a, arg_b))]
    if token == 'split':            return stack + [('list', [('string', element) for element in arg_a.split(arg_b)])]
    raise SyntaxError('binop: %s cannot be processed as a binop' % token)

TRINOPS = {}

def process_trinop(token, stack):
    if len(stack) < 3:
        raise ValueError('trinop: stack too short (height %s, need >= 3): %s' % (len(stack), stack))
    argtype_c, arg_c = stack.pop()
    argtype_b, arg_b = stack.pop()
    argtype_a, arg_a = stack.pop()
    typesig = (argtype_a, argtype_b, argtype_c)
    if not typesig in TRINOPS[token]:
        raise SyntaxError('trinop: %s cannot process type "%s"' % (token, typesig))
    raise SyntaxError('trinop: %s cannot be processed as a trinop' % token)

NOPS = { '\\', 'dropn', 'top', 'topn', 'rand' }
# '\' creates a list of the first n elements of the current stack and pushes it onto the stack
# e.g. 1 2 3 4 3 2 \ -> 1 2 3 [4,3]
# there are no list literals
# dropn drops the top n elements of the stack
# top drops all the elements of the stack below the top
# topn drops all the elements of the stack below the top n
# rand puts a random decimal between 0 and 1 on the stack

def process_nop(token, stack):
    if token not in NOPS:
        raise SyntaxError('nop: %s cannot be processed as an n-op' % token)
    if token == '\\':
        if len(stack) < 1:
            raise ValueError('nop: stack too short for op %s (height %s): %s' % (token, len(stack), stack))
        argtype, arg = stack.pop()
        if argtype != 'number':
            raise SyntaxError('nop: %s cannot process type %s as stack height' % (token, argtype))
        if not int(arg) == arg:
            raise SyntaxError('nop: %s cannot process non-integer %s as stack height' % (token, arg))
        length = int(arg)
        if len(stack) < length:
            raise ValueError('nop: stack too short for op %s and height %s (height left is %s): %s' % (token, length, len(stack), stack))
        if length < 0:
            raise ValueError('nop: %s cannot process negative stack height "%s"' % (token, length))
        if length == 0:
            return stack + [('list', [])]
        args = stack[-length:]
        return stack[:-length] + [('list', args)]
    elif token == 'dropn':
        if len(stack) < 1:
            raise ValueError('nop: stack too short for op %s (height %s): %s' % (token, len(stack), stack))
        argtype, arg = stack.pop()
        if argtype != 'number':
            raise SyntaxError('nop: %s cannot process type %s as stack height' % (token, argtype))
        if not int(arg) == arg:
            raise SyntaxError('nop: %s cannot process non-integer %s as stack height' % (token, arg))
        length = int(arg)
        if len(stack) < length:
            raise ValueError('nop: stack too short for op %s and height %s (height left is %s): %s' % (token, length, len(stack), stack))
        if length < 0:
            raise ValueError('nop: %s cannot process negative stack height "%s"' % (token, length))
        return stack[:-length]
    elif token == 'top':
        if len(stack) < 1:
            raise ValueError('nop: stack too short for op %s (height %s): %s' % (token, len(stack), stack))
        argtype, arg = stack.pop()
        return [(argtype, arg)]
    elif token == 'topn':
        if len(stack) < 1:
            raise ValueError('nop: stack too short for op %s (height %s): %s' % (token, len(stack), stack))
        argtype, arg = stack.pop()
        if argtype != 'number':
            raise SyntaxError('nop: %s cannot process type %s as stack height' % (token, argtype))
        if not int(arg) == arg:
            raise SyntaxError('nop: %s cannot process non-integer %s as stack height' % (token, arg))
        length = int(arg)
        if len(stack) < length:
            raise ValueError('nop: stack too short for op %s and height %s (height left is %s): %s' % (token, length, len(stack), stack))
        if length < 0:
            raise ValueError('nop: %s cannot process negative stack height "%s"' % (token, length))
        return stack[-length:]
    elif token == 'rand':
        return stack + [('number', random.random())]
    raise SyntaxError('nop: %s cannot be processed as an n-op' % token)

REGEX = {
    'var' : r'\$([a-zA-Z][a-zA-Z0-9\_]*)',
    'string_doublequote' : r'"(?:[^"])*"',
    'string_singlequote' : r"'(?:[^'])*'",
    'mark' : r'([a-zA-Z][a-zA_Z0-9\_]*)',
    'number' : r'-?(\d+)\.?(\d+)?'
}

def is_number(exp_token):
    # return ((exp_token[0] == '-' and exp_token[1:].isnumeric() 
    #         or (exp_token[1:].count('.') == 1 and exp_token[1:].replace('.','').isnumeric())) 
    #     or (exp_token.isnumeric() 
    #         or (exp_token.count('.') == 1 and exp_token.replace('.','').isnumeric())))
    r_number = REGEX['number']
    m = re.fullmatch(r_number, exp_token)
    return m is not None

def get_type(exp_token):
    # print('getting token type of', exp_token)
    # get type of an inter-expression string
    # returns (tokentype, parsed token)
    exp_token = exp_token.strip()
    if exp_token in ['f', 'false']:
        return 'bool', False
    if exp_token in ['t', 'true']:
        return 'bool', True
    if exp_token in UNOPS:
        return 'unop', exp_token
    if exp_token in BINOPS:
        return 'binop', exp_token
    if exp_token in TRINOPS:
        return 'trinop', exp_token
    if exp_token in NOPS:
        return 'nop', exp_token
    if is_number(exp_token):
        return 'number', float(exp_token)
    if exp_token[0] == '$':
        r_var = REGEX['var']
        m_var = re.fullmatch(r_var, exp_token)
        if not m_var:
            raise SyntaxError('type: invalid variable name "%s"' % exp_token)
        return 'var', m_var[1]
    if exp_token[0] == '"':
        r_string = REGEX['string_doublequote']
        m_string = re.fullmatch(r_string, exp_token)
        if not m_string:
            raise SyntaxError('type: invalid string syntax (%s)' % exp_token)
        return 'string', m_string[0][1:-1] # remove quotes
    if exp_token[0] == "'":
        r_string = REGEX['string_singlequote']
        m_string = re.fullmatch(r_string, exp_token)
        if not m_string:
            raise SyntaxError('type: invalid string syntax (%s)' % exp_token)
        return 'string', m_string[0][1:-1] # remove quotes
    raise ValueError('type: value of unknown type ' + exp_token)

def tokenize_exp(exp):
    # print('tokenizing `%s`' % exp)
    in_double_quote = False
    in_single_quote = False
    # need to explicitly close out strings
    # otherwise could end up starting single quoted strings
    # just_finished_string = False
    tokens = []
    current_token = ''
    index = 0
    while index < len(exp):
        # when in a string, continue until end delim seen
        c = exp[index]
        if in_double_quote:
            if c == '"':
                in_double_quote = False
            current_token += c
        elif in_single_quote:
            if c == "'":
                in_single_quote = False
            current_token += c
        else:
            # whitespace
            if c.strip() == '':
                if current_token:
                    tokens.append(current_token)
                current_token = ''
            else:
                if c in ['"', "'"] and index > 0 and exp[index-1].strip() != '':
                    # <token>"..." is not allowed - requires whitespace, e.g. <token> "..."
                    raise SyntaxError('tokenize exp: string starting without whitespace after previous item (...%s...)' % exp[max(0,index-5):min(index+5,len(exp))])
                if c == '"':
                    in_double_quote = True
                elif c == "'":
                    in_single_quote = True
                current_token += c
        index += 1
    if in_double_quote:
        raise SyntaxError('tokenize exp: expression ended while parsing double quoted string (...%s)' % exp[min(0,-5):])
    if in_single_quote:
        raise SyntaxError('tokenize exp: expression ended while parsing single quoted string (...%s)' % exp[min(0,-5):])
    if current_token:
        tokens.append(current_token)
    # print('tokenized %s into `%s`' % (exp, tokens))
    return tokens

def check_exp(exp):
    if exp.strip() == 'input': return 'input' # just get user input
    # make sure exp is formatted correctly and all terms are syntactically valid
    exp = exp.strip()
    assert exp[0] == '[' and exp[-1] == ']', 'check exp: missing delimiters "[" and/or "]" (%s)' % exp
    unmodified = exp
    exp = exp[1:-1].strip()
    if len(exp) == 0:
        raise SyntaxError('check exp: empty expression (%s)' % unmodified)
    # rework inter-expression tokenizing logic to allow spaces in strings
    tokens = tokenize_exp(exp)
    for token in tokens:
        get_type(token)
    return unmodified

def parse_exp(exp, variables):
    if exp.strip() == 'input': return ('string', input()) # just get user input
    # parse rpn expressions given current variable list
    exp = exp.strip()
    assert exp[0] == '[' and exp[-1] == ']', 'exp: missing delimiters "[" and/or "]" (%s)' % exp
    unmodified = exp
    exp = exp[1:-1]
    assert len(exp) > 0, 'exp: empty expression (%s)' % unmodified
    stack = []
    tokens = tokenize_exp(exp)
    for token in tokens:
        tokentype, token = get_type(token)
        if tokentype in DATA_TYPES:
            stack.append((tokentype, token))
        elif tokentype == 'var':
            if token not in variables:
                raise ValueError('exp: unknown variable "%s"' % token)
            tokentype, token = variables[token]
            stack.append((tokentype, token))
        elif tokentype == 'unop':
            stack = process_unop(token, stack)
        elif tokentype == 'binop':
            stack = process_binop(token, stack)
        elif tokentype == 'trinop':
            stack = process_trinop(token, stack)
        elif tokentype == 'nop':
            stack = process_nop(token, stack)
        else:
            raise SyntaxError('exp: unknown token type "%s"' % tokentype)
    if len(stack) > 1:
        raise ValueError('exp: stack ended with invalid length > 1 of %s (%s)' % (len(stack), stack))
    return stack[0]

def parse_output_stmt(rest):
    # match $(a..zA..Z)(a..zA..Z0..9)*
    rest = rest.strip()
    r = REGEX['var']
    m = re.fullmatch(r, rest)
    if m:
        return 'outputvar', m[1]
    # raise SyntaxError('output: invalid variable name "%s"' % rest)
    # didn't match var, try parsing as expression instead
    exp = check_exp(rest)
    return 'outputexp', exp

def parse_mark_stmt(rest):
    # match (a..zA..Z)(a..zA..Z0..9)*
    rest = rest.strip()
    r = REGEX['mark']
    m = re.fullmatch(r, rest)
    if not m:
        raise SyntaxError('mark: invalid mark name "%s"' % rest)
    return 'mark', m[1]

def parse_set_stmt(rest):
    # match varname expression
    rest = rest.strip()
    varname, rest = rest.split(sep=None, maxsplit=1)
    r = REGEX['var']
    m = re.fullmatch(r, varname)
    if not m:
        raise SyntaxError('set: invalid variable name "%s"' % varname)
    exp = check_exp(rest)
    return 'set', m[1], exp

def parse_goto_stmt(rest):
    # match (a..z)(a..z0..9_)*
    rest = rest.strip()
    r = REGEX['mark']
    m = re.fullmatch(r, rest)
    if not m:
        raise SyntaxError('goto: invalid mark name "%s"' % rest)
    return 'goto', m[1]

def parse_if_stmt(rest):
    # match exp THEN (goto mark | output varname | output exp | set varname exp)
    rest = rest.strip()
    assert 'then' in rest, 'if: missing "then" (%s) ' % rest
    guard, statement = rest.split('then')
    guard = guard.strip()
    statement = statement.strip()
    guard = check_exp(guard)
    first_token, rest = statement.split(sep=None, maxsplit=1)
    if first_token == 'goto':
        statement = parse_goto_stmt(rest)
    elif first_token == 'set':
        statement = parse_set_stmt(rest)
    elif first_token == 'output':
        statement = parse_output_stmt(rest)
    else:
        raise SyntaxError('if: unknown or prohibited statement type "%s"' % first_token)
    return 'if', guard, statement

def parse_statement(statement_string):
    statement_string = statement_string.strip()
    if statement_string.startswith('#'):
        return 'comment'
    if statement_string == '':
        return 'empty'
    # print('parsing statement', statement_string)
    try:
        first_token, rest = statement_string.split(sep=None, maxsplit=1)
    except:
        raise SyntaxError('parse error: stray single token (%s), expecting multi-token statement' % statement_string)
    if first_token == 'if':
        return parse_if_stmt(rest)
    elif first_token == 'output':
        return parse_output_stmt(rest)
    elif first_token == 'mark':
        return parse_mark_stmt(rest)
    elif first_token == 'set':
        return parse_set_stmt(rest)
    elif first_token == 'goto':
        return parse_goto_stmt(rest)
    else:
        raise ValueError('illegal statement start: ' + first_token)

def parse_statements(statement_strings, include_comments=False):
    # print('statement strings', statement_strings)
    statements = []
    statement_index = 0
    while statement_index < len(statement_strings):
        statement = statement_strings[statement_index]
        parsed = parse_statement(statement)
        if parsed == 'comment':
            # print('parsing comment', statement)
            statement = statement.strip()
            if include_comments:
                if '\n' in statement:
                    statements += [('comment', statement[:statement.find('\n')])]
                    statement_strings[statement_index] = statement[statement.find('\n')+1:]
                else: # single-line comment?
                    statements.append(('comment', statement.strip()))
                    statement_index += 1
            else:
                if '\n' in statement:
                    # continue removing comment lines until the last one
                    statement_strings[statement_index] = statement[statement.find('\n')+1:]
                else:
                    statement_index += 1
            continue
        if parsed == 'empty':
            if statement_index+1 == len(statement_strings):
                return statements
            print('warning: empty statement detected between statements (index {}: {}) and (index {}: {})'.format(
                statement_index-1, repr(statement_strings[statement_index-1]),
                statement_index+1, repr(statement_strings[statement_index+1])
            ))
        else:
            statements.append(parsed)
        statement_index += 1
    return statements

def process_statements(parsed_statements):
    marker_dict = {}
    # first pass - create marker dictionary
    for statement_index, statement in enumerate(parsed_statements):
        statement_type, *statement_args = statement
        if statement_type == 'mark':
            if len(statement_args) != 1:
                raise SyntaxError('mark: invalid number of arguments (should be 1, not %s): %s' % (len(statement_args), statement_args))
            markname = statement_args[0]
            if markname in marker_dict:
                raise SyntaxError('mark: duplicate marker "%s" (statements %s, %s)' % (markname, marker_dict[markname], statement_index))
            marker_dict[markname] = statement_index

    variable_dict = {}
    statement_index = 0
    # second pass - evaluate everything
    while statement_index < len(parsed_statements):
        statement_type, *statement_args = parsed_statements[statement_index]
        if statement_type == 'mark':
            pass
            # all marks already evaluated in first pass
        elif statement_type == 'outputvar':
            if len(statement_args) != 1:
                raise SyntaxError('output: invalid number of arguments (should be 1, not %s): %s' % (len(statement_args), statement_args))
            varname = statement_args[0]
            if varname not in variable_dict:
                raise ValueError('output: variable "%s" undefined' % varname)
            vartype, varvalue = variable_dict[varname]
            if vartype != 'string':
                print('<{} : {}>'.format(vartype, varvalue))
            else:
                print(varvalue)
        elif statement_type == 'outputexp':
            if len(statement_args) != 1:
                raise SyntaxError('output: invalid number of arguments (should be 1, not %s): %s' % (len(statement_args), statement_args))
            expression = statement_args[0]
            parsed_expression = parse_exp(expression, variable_dict)
            result_type, result_value = parsed_expression
            if result_type != 'string':
                print('<{} : {}>'.format(result_type, result_value))
            else:
                print(result_value)
        elif statement_type == 'set':
            if len(statement_args) != 2:
                raise SyntaxError('set: invalid number of arguments (should be 2, not %s): %s' % (len(statement_args), statement_args))
            varname, expression = statement_args
            parsed_expression = parse_exp(expression, variable_dict)
            variable_dict[varname] = parsed_expression
        elif statement_type == 'goto':
            if len(statement_args) != 1:
                raise SyntaxError('goto: invalid number of arguments (should be 1, not %s): %s' % (len(statement_args), statement_args))
            markname = statement_args[0]
            if markname not in marker_dict:
                raise ValueError('goto: mark "%s" undefined' % markname)
            markindex = marker_dict[markname]
            statement_index = markindex
            continue
        elif statement_type == 'if':
            if len(statement_args) != 2:
                raise SyntaxError('if: invalid number of arguments (should be 2, not %s): %s' % (len(statement_args), statement_args))
            guard, body = statement_args
            parsed_guard = parse_exp(guard, variable_dict)
            guardtype, guardvalue = parsed_guard
            if guardtype != 'bool':
                raise ValueError('if: invalid type of guard (should be bool, not %s): %s' % (guardtype, guardvalue))
            if guardvalue:
                body_statement_type, *body_statement_args = body
                # switch to outputvar, outputexp
                if body_statement_type == 'outputvar':
                    if len(body_statement_args) != 1:
                        raise SyntaxError('output: invalid number of arguments (should be 1, not %s): %s' % (len(body_statement_args), body_statement_args))
                    varname = body_statement_args[0]
                    if varname not in variable_dict:
                        raise ValueError('output: variable "%s" undefined' % varname)
                    vartype, varvalue = variable_dict[varname]
                    if vartype != 'string':
                        print('<{} : {}>'.format(vartype, varvalue))
                    else:
                        print(varvalue)
                elif body_statement_type == 'outputexp':
                    if len(body_statement_args) != 1:
                        raise SyntaxError('output: invalid number of arguments (should be 1, not %s): %s' % (len(body_statement_args), body_statement_args))
                    expression = body_statement_args[0]
                    parsed_expression = parse_exp(expression, variable_dict)
                    result_type, result_value = parsed_expression
                    if result_type != 'string':
                        print('<{} : {}>'.format(result_type, result_value))
                    else:
                        print(result_value)
                elif body_statement_type == 'set':
                    if len(body_statement_args) != 2:
                        raise SyntaxError('if set: invalid number of arguments (should be 2, not %s): %s' % (len(body_statement_args), body_statement_args))
                    varname, expression = body_statement_args
                    parsed_expression = parse_exp(expression, variable_dict)
                    variable_dict[varname] = parsed_expression
                elif body_statement_type == 'goto':
                    if len(body_statement_args) != 1:
                        raise SyntaxError('if goto: invalid number of arguments (should be 1, not %s): %s' % (len(body_statement_args), body_statement_args))
                    markname = body_statement_args[0]
                    if markname not in marker_dict:
                        raise ValueError('if goto: mark "%s" undefined' % markname)
                    markindex = marker_dict[markname]
                    statement_index = markindex
                    continue
                else:
                    raise SyntaxError('if: unknown or prohibited statement type "%s"' % body_statement_type)

        statement_index += 1

def parse_content(filecontent, include_comments=False):
    return parse_statements(filecontent.split(';'), include_comments=include_comments)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('please provide a filename to run')
        sys.exit(1)
    # print('running', sys.argv[1])
    with open(sys.argv[1], 'r') as f:
        filecontent = f.read()
    statements = parse_content(filecontent)
    # print('statements:', statements)

    process_statements(statements)

    # print('done')