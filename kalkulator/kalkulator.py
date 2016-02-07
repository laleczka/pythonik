# -*- coding: cp1250 -*-
import abc
import re
import string


class Expression(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def evaluate(self, env, strict = False):
        raise NotImplementedError
    
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

class Operation(Expression):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def sign(self):
        raise NotImplementedError
    def __init__(self, left, right):
        self._left = left
        self._right = right
    def __repr__(self):
        return '({0} {1} {2})'.format(str(self._left), self.sign, str(self._right))
    def __hash__(self):
        return hash(self._left) ^ hash(self._right)
    def __eq__(self, other):
        if isinstance(other, type(self)):
            return (self._left == other._left) and (self._right == other._right)
        return False
    @abc.abstractmethod
    def apply_operation(self, left_elements, right_elements):
        raise NotImplementedError
    @abc.abstractmethod
    def apply_op_to_equal_args(self, arg):
        raise NotImplementedError

    def evaluate(self, env, strict = False):
        left = self._left.evaluate(env, strict=strict)
        right = self._right.evaluate(env, strict=strict)
        if isinstance(left, Set) and isinstance(right, Set):
            return self.apply_operation(left._elements, right._elements)
        elif left == right:
            return self.apply_op_to_equal_args(left)
        else:
            return type(self)(left, right)
    
class Sum(Operation):
    @property
    def sign(self):
        return 'u'
    def apply_op_to_equal_args(self, arg):
        return arg
    def apply_operation(self, left_elements, right_elements):
        return Set(left_elements | right_elements)

class Intersection(Operation):
    @property
    def sign(self):
        return 'n'
    def apply_op_to_equal_args(self, arg):
        return arg
    def apply_operation(self, left_elements, right_elements):
        return Set(left_elements & right_elements)

class RelativeComplement(Operation):
    @property
    def sign(self):
        return '\\'
    def apply_op_to_equal_args(self, arg):
        return Set(set())
    def apply_operation(self, left_elements, right_elements):
        return Set(left_elements - right_elements)
    
class CartesianProduct(Operation):
    @property
    def sign(self):
        return 'x'
    def apply_op_to_equal_args(self, arg):
        return CartesianProduct(arg, arg)
    def apply_operation(self, left_elements, right_elements):
        big_set = set()
        for l in left_elements:
            for r in right_elements:
                big_set.add(Set({l,r}))
        return Set(big_set)
    
class Tokenizer(object):
    def __init__(self):
        self._tokens = []
            
    def tokenize(self, text):
        self._tokens = []
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


class Parser(object):
    operations = {
        'u': Sum,
        'n': Intersection,
        '\\': RelativeComplement,
        'x': CartesianProduct}

    def __init__(self):
        self._stack = []

    def try_parse_operation(self, expression):
        if self._stack and self._stack[-1] in self.operations:
            op = self._stack.pop()
            if not self._stack:
                raise Exception('Wrong expression.')
            self._stack.append(self.operations[op](self._stack.pop(), expression))
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
                    raise Exception('Wrong expression.')
            elif i == ')':
                if len(self._stack)>1 and self._stack[-2] == '(':
                    a = self._stack.pop()
                    self._stack.pop()
                    self.try_parse_operation(a)
                else:
                    raise Exception('Wrong expression.')
            else:
                raise Exception('Wrong expression.')
                    
        if len(self._stack) != 1:
            print self._stack
            raise Exception('Incorrect statement.')
        if not isinstance(self._stack[0], Expression):
            raise Exception('Incorrect statement.')
        return self._stack[0]

    def parse_print_statement(self, tokens):
        if tokens and tokens[0] == '$':
            return self.parse_expression(tokens[1:])
        raise Exception('Incorrect print statement.')

    def parse_assignment(self, tokens):
        if len(tokens) > 1 and tokens[1] in ['=', '=:']:
            name = tokens[0]
            return name, self.parse_expression(tokens[2:])
        raise Exception('Incorrect assigment.')

class Calculator(object):
    def __init__(self):
        self._env = {}
        self._tokenizer = Tokenizer()
        self._parser = Parser()
        
    def read_string(self, text):
        if re.match(r'^\$\s*[\\{}()A-Zunx 0-9]+$', text):
            try:
                tokens = self._tokenizer.tokenize(text)
                expr = self._parser.parse_print_statement(tokens)
                print expr.evaluate(self._env)
            except Exception, e:
                print str(e)                    
        elif re.match(r'^[A-Z]+\s*=\s*[\\{}()A-Zunx 0-9]+', text):
            try:
                tokens = self._tokenizer.tokenize(text)
                name, expr = self._parser.parse_assignment(tokens)
                self._env[name] = expr.evaluate(self._env, True)
            except Exception, e:
                print str(e)
        elif re.match(r'^[A-Z]+\s*=:\s*[\\{}()A-Zunx 0-9]+', text):
            try:  
                tokens = self._tokenizer.tokenize(text)
                name, expr = self._parser.parse_assignment(tokens)
                self._env[name] = expr
            except Exception, e:
                print str(e)
        else:
            print "Incorrect expression."

    def calculate(self):
        while True:
            a = raw_input()
            self.read_string(a)

if __name__ == '__main__':
    cal = Calculator()
    cal.calculate()
