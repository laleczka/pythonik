# -*- coding: cp1250 -*-
import abc
import re
import string
import traceback

class Expression(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def evaluate(self, env, strict = False):
        pass

class Set(Expression):
    def __init__(self, elements):
        self._elements = elements
    def __repr__(self):
        return '{'+' '.join(str(i) for i in self._elements)+'}'
    def __eq__(self, other):
        if isinstance(other, Set):
            return self._elements == other._elements
        return False
    def __hash__(self):
        h = 0
        for e in self._elements:
            h ^= hash(e)
        return h
    def evaluate(self, env, strict = False):
        return Set(set(e.evaluate(env, strict=strict) for e in self._elements))

class Variable(Expression):
    def __init__(self, name):
        self._name = name
    def __repr__(self):
        return self._name
    def __eq__(self, other):
        if isinstance(other, Variable):
            return self._name == other._name
        return False
    def __hash__(self):
        return hash(self._name)
    def evaluate(self, env, strict = False):
        try:
            return env[self._name].evaluate(env, strict=False)
        except KeyError:
            if strict:
                raise Exception('Unknown variable {0}'.format(self._name))
            else:
                return self

class Constant(Expression):
    def __init__(self, value):
        self._value = int(value)
    def __repr__(self):
        return str(self._value)
    def __eq__(self, other):
        if isinstance(other, Constant):
            return self._value == other._value
        return False
    def __hash__(self):
        return hash(self._value)
    def evaluate(self, env, strict = False):
        return self
    
class Sum(Expression):
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} u {1})'.format(str(self._left),str(self._right))
    def __eq__(self, other):
        if isinstance(other, Sum):
            return (self._left == other._left) and (self._right == other._right)
        return False
    def __hash__(self):
        return hash(self._left) ^ hash(self._right)
    def evaluate(self, env, strict = False):
        left = self._left.evaluate(env, strict=strict)
        right = self._right.evaluate(env, strict=strict)
        if isinstance(left, Set) and isinstance(right, Set):
            return Set(left._elements | right._elements)
        else:
            return Sum(left, right)

class Intersection(Expression):
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} n {1})'.format(str(self._left),str(self._right))
    def __eq__(self, other):
        if isinstance(other, Intersection):
            return (self._left == other._left) and (self._right == other._right)
        return False
    def __hash__(self):
        return hash(self._left) ^ hash(self._right)
    def evaluate(self, env, strict = False):
        left = self._left.evaluate(env, strict=strict)
        right = self._right.evaluate(env, strict=strict)
        if isinstance(left, Set) and isinstance(right, Set):
            return Set(left._elements & right._elements)
        else:
            return Sum(left, right)

class RelativeComplement(Expression):
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} \ {1})'.format(str(self._left),str(self._right))
    def __eq__(self, other):
        if isinstance(other, RelativeComplement):
            return (self._left == other._left) and (self._right == other._right)
        return False
    def __hash__(self):
        return hash(self._left) ^ hash(self._right)
    def evaluate(self, env, strict = False):
        left = self._left.evaluate(env, strict=strict)
        right = self._right.evaluate(env, strict=strict)
        if isinstance(left, Set) and isinstance(right, Set):
            return Set(left._elements - right._elements)
        else:
            return Sum(left, right)
    
class CartesianProduct(Expression):
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} x {1})'.format(str(self._left),str(self._right))
    def __eq__(self, other):
        if isinstance(other, CartesianProduct):
            return (self._left == other._left) and (self._right == other._right)
        return False
    def __hash__(self):
        return hash(self._left) ^ hash(self._right)
    def evaluate(self, env, strict = False):
        left = self._left.evaluate(env, strict=strict)
        right = self._right.evaluate(env, strict=strict)
        if isinstance(left, Set) and isinstance(right, Set):
            big_set = set()
            for l in left._elements:
                for r in right._elements:
                    big_set.add(Set({l,r}))
            return Set(big_set)
        else:
            return CartesianProduct(left, right)
                
    
class Tokenizer(object):
    def __init__(self):
        self._tokens = []
            
    def tokenize(self, text): 
        while len(text)>0:
            a = re.match('^([A-Z]+)|(=:)|([0-9]+)', text)
            if a:
                self._tokens.append(a.group())
                text = text[len(a.group()):]
                continue
            b = re.match('\s+',text)
            if b:
                text = text[len(b.group()):]
                continue
            if text[0] in ['=', '{', '}', 'u', 'n', '\\', 'x', '(', ')', '$']:
                self._tokens.append(text[0])
                text = text[1:]
                continue
            raise Exception('Invalid string: "{0}"'.format(text))            
        return self._tokens

operations = {
    'u': Sum,
    'n': Intersection,
    '\\': RelativeComplement,
    'x': CartesianProduct
    }

class Parser(object):
    def __init__(self):
        self._stack = []

    def try_parse_operation(self, expression):
        if self._stack and self._stack[-1] in operations:
            op = self._stack.pop()
            if not self._stack:
                raise Exception('Zle wyrazenie1')
            self._stack.append(operations[op](self._stack.pop(), expression))
        else:
            self._stack.append(expression)

    def parse_expression(self, tokens):
        self._stack = []
        for i in tokens:
            if i in ['{', 'u', 'n', '\\', 'x', '(']:
                self._stack.append(i)
            elif re.match('^[0-9]+$',i):
                self.try_parse_operation(Constant(i))
            elif re.match('^[A-Z]+$',i):
                self.try_parse_operation(Variable(i))                
            elif i == '}':
                values = []
                while self._stack and self._stack[-1] != '{':
                    values.append(self._stack.pop())
                if self._stack:
                    self._stack.pop()
                    set_a = Set(set(values[::-1]))
                    self.try_parse_operation(set_a)
                else:
                    raise Exception('Zle wyrazenie3')
            elif i == ')':
                if len(self._stack)>1 and self._stack[-2] == '(':
                    a = self._stack.pop()
                    self._stack.pop()
                    self.try_parse_operation(a)
                else:
                    raise Exception('Zle wyrazenie8')
            else:
                raise Exception('Zle wyrazenie9')
                    
        if len(self._stack) != 1:
            print self._stack
            raise Exception('Zle wyrazenie4')
        return self._stack[0]

    def parse_print_statement(self, tokens):
        if tokens and tokens[0] == '$':
            return self.parse_expression(tokens[1:])
        raise Exception('Zle wyrazenie wyświetlania')

    def parse_assignment(self, tokens):
        if len(tokens) > 1 and tokens[1] in ['=', '=:']:
            name = tokens[0]
            return name, self.parse_expression(tokens[2:])
        raise Exception('Zle wyrazenie przypisania')

class Calculator(object):
    def __init__(self):
        self._env = {}
        
    def read_string(self, text):
        if re.match(r'^\$\s*[\\{}()A-Zunx 0-9]+$', text):
            print 'To jest wyświetlenie'
            try:
                tokenizer = Tokenizer()
                tokens = tokenizer.tokenize(text)
                parser = Parser()
                expr = parser.parse_print_statement(tokens)
                print expr.evaluate(self._env)
            except Exception, e:
                print str(e)                    
        elif re.match(r'^[A-Z]+\s*=\s*[\\{}()A-Zunx 0-9]+', text):
            print 'To jest przypisanie bez odroczenia'
            try:
                tokenizer = Tokenizer()
                tokens = tokenizer.tokenize(text)
                parser = Parser()
                name, expr = parser.parse_assignment(tokens)
                self._env[name] = expr.evaluate(self._env, True)
            except Exception, e:
                print str(e)
                traceback.print_exc()
        elif re.match(r'^[A-Z]+\s*=:\s*[\\{}()A-Zunx 0-9]+', text):
            print 'To jest przypisanie z odroczeniem'
            try:
                tokenizer = Tokenizer()
                tokens = tokenizer.tokenize(text)
                parser = Parser()
                name, expr = parser.parse_assignment(tokens)
                self._env[name] = expr
            except Exception, e:
                print str(e)
        else:
            print 'To jest nieprawidłowe wyrażenie'

cal = Calculator()
while True:
    a = raw_input()
    cal.read_string(a)
