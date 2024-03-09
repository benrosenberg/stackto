# BNF grammar for StackTo

```
program ::= statement statement'

statement' ::= statement | comment | EMPTY

statement ::= stmt SEMICOLON

stmt ::= if | marker | goto | assignment | output

if ::= IF expression THEN ifbody

ifbody ::= goto | assignment | output

expression ::= LBRACKET explist RBRACKET | inputkeyword

explist ::= atom atom'

atom ::= variablename | bool | string | number | op

atom' ::= atom | EMPTY

string ::= doublequotedstring | singlequotedstring

op ::= unop | binop | trinop | nop

marker ::= MARK markername

goto ::= GOTO markername

assignment ::= SET variablename expression

output ::= OUTPUT variablename

comment ::= /#.*/

inputkeyword ::= 'input' | 'inputnum'

unop ::= '#' | '~' | '!' | '?' | 'num' | 'splat' | 'dup' | 'drop' | 'str' | 'round' | 'sum' | 'prod' | 'type'

binop ::= '<' | '>' | '<=' | '>=' | '=' | '==' | '<>' | '!=' | '&' | '^' | '|' | '+' | '-' | '*' | '/' | '//' | '%' | '@' | ':' | 'swap' | 'nth' | 'min' | 'max' | 'split'

trinop ::= 'setnth'

nop ::= '\' | 'dropn' | 'top' | 'topn' | 'rand'

bool ::= /(f|false|t|true)/

variablename ::= /\$([a-zA-Z][a-zA-Z0-9\_]*)/

doublequotedstring ::= /"(?:[^"])*"/

singlequotedstring ::= /'(?:[^'])*'/

number ::= /-?(\d+)\.?(\d+)?/

markername ::= /([a-zA-Z][a-zA_Z0-9\_]*)/
```