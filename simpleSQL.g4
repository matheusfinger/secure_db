grammar SimpleSQL;

@parser::header {
from typing import List, Dict, Any
}

parse
    : select_statement EOF
    ;

select_statement
    : SELECT select_columns FROM table_name (WHERE where_condition)?
    ;

select_columns
    : '*' 
    | column_list
    ;

column_list
    : column_name (',' column_name)*
    ;

where_condition
    : expression
    ;

expression
    : column_name comparison_operator value
    ;

comparison_operator
    : '=' | '>' | '<' | '>=' | '<=' | '!='
    ;

table_name
    : IDENTIFIER
    ;

column_name
    : IDENTIFIER
    ;

value
    : STRING
    | NUMBER
    ;

SELECT : S E L E C T;
FROM : F R O M;
WHERE : W H E R E;

IDENTIFIER
    : [a-zA-Z_] [a-zA-Z0-9_]*
    ;

STRING
    : '\'' ( ~'\'' )* '\''
    ;

NUMBER
    : [0-9]+ ('.' [0-9]+)?
    ;

WS
    : [ \t\r\n]+ -> skip
    ;

fragment A : [aA];
fragment B : [bB];
fragment C : [cC];
fragment D : [dD];
fragment E : [eE];
fragment F : [fF];
fragment G : [gG];
fragment H : [hH];
fragment I : [iI];
fragment J : [jJ];
fragment K : [kK];
fragment L : [lL];
fragment M : [mM];
fragment N : [nN];
fragment O : [oO];
fragment P : [pP];
fragment Q : [qQ];
fragment R : [rR];
fragment S : [sS];
fragment T : [tT];
fragment U : [uU];
fragment V : [vV];
fragment W : [wW];
fragment X : [xX];
fragment Y : [yY];
fragment Z : [zZ];