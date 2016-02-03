# -*- coding: cp1250 -*-
import re
import string


class Set(object):
    def __init__(self, values):
        self._values = values
    def __repr__(self):
        return '{'+' '.join(str(i) for i in self._values)+'}'

class Variable(object):
    def __init__(self, name):
        self._name = name
    def __repr__(self):
        return self._name

class Constant(object):
    def __init__(self, value):
        self._value = int(value)
    def __repr__(self):
        return str(self._value)
    
class Sum(object):
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} u {1})'.format(str(self._left),str(self._right))

class Intersection(object):
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} n {1})'.format(str(self._left),str(self._right))
    
class RelativeComplement(object):
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} \ {1})'.format(str(self._left),str(self._right))
    
class CartesianProduct(object):
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} x {1})'.format(str(self._left),str(self._right))
    

def tokenize(text):
    tokens = []
    while len(text)>0:
        a = re.match('^[A-Z]+', text)
        if a:
            tokens.append(a.group())
            text = text[len(a.group()):]
            continue
        if text[0] in ['=', '{', '}', 'u', 'n', '\\', 'x', '(', ')']:
            tokens.append(text[0])
            text = text[1:]
            continue
        b = re.match('^[0-9]+',text)
        if b:
            tokens.append(b.group())
            text = text[len(b.group()):]
            continue
        c = re.match('\s+', text)
        if c:
            text = text[len(c.group()):]
            continue
        raise Exception('Invalid string: "{0}"'.format(text))
        
    return tokens

operations = {
    'u': Sum,
    'n': Intersection,
    '\\': RelativeComplement,
    'x': CartesianProduct
    }

def parse_expression(tokens):
    name = tokens[0]
    if tokens[1] != '=':
        raise Exception('Zle wyrazenie')
    stack = []
    for i in tokens[2:]:
        if i in ['{', 'u', 'n', '\\', 'x', '(']:
            stack.append(i)
        elif re.match('^[0-9]+$',i):
            if stack and stack[-1] in operations:
                op = stack.pop()
                if not stack:
                    raise Exception('Zle wyrazenie1')
                stack.append(operations[op](stack.pop(), Constant(i)))
            else:
                stack.append(Constant(i))

        elif re.match('^[A-Z]+$',i):
            if stack and stack[-1] in operations:
                op = stack.pop()
                if not stack:
                    raise Exception('Zle wyrazenie1')
                stack.append(operations[op](stack.pop(), Variable(i)))
            else:
                stack.append(Variable(i))
        elif i == '}':
            values = []
            while stack and stack[-1] != '{':
                values.append(stack.pop())
            if stack:
                stack.pop()
                set_a = Set(values[::-1])
                if stack and stack[-1] in operations:
                    op = stack.pop()
                    if not stack:
                        raise Exception('Zle wyrazenie2')
                    stack.append(operations[op](stack.pop(), set_a))
                else:
                    stack.append(set_a)        
            else:
                raise Exception('Zle wyrazenie3')
        elif i == ')':
            if len(stack)>1 and stack[-2] == '(':
                a = stack.pop()
                stack.pop()
                if stack and stack[-1] in operations:
                    op = stack.pop()
                    if not stack:
                        raise Exception('Zle wyrazenie7')
                    stack.append(operations[op](stack.pop(), a))
                else:
                    stack.append(a)
            else:
                raise Exception('Zle wyrazenie8')
        else:
            raise Exception('Zle wyrazenie9')
                
    if len(stack) != 1:
        print stack
        raise Exception('Zle wyrazenie4')
    return name, stack[0]
 
def read_string(text):
    if re.match(r'^\$ [A-Z]+$', text):
        print 'To jest wyświetlenie'
    elif re.match(r'^[A-Z]+ = [\\{}()A-Zunx 0-9]*', text):
        print 'To jest przypisanie bez odroczenia'
        try:
            tokens = tokenize(text)
            print parse_expression(tokens)
        except Exception, e:
            print str(e)
    elif re.match(r'^[A-Z]+ =: [\\{}()A-Zunx 0-9]*', text):
        print 'To jest przypisanie z odroczeniem'
    else:
        print 'To jest nieprawidłowe wyrażenie'
   # for i in text:
     #   print i

while True:
    a = raw_input()
    read_string(a)
