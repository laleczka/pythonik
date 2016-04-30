#-*- coding: utf-8 -*-
import numpy as np
import csv


class Ant(object):
    def __init__(self, board):
        self._actual_field = board._nest
        self._symbol = u"\u2748"
    def __unicode__(self):
        return u'\n'.join(self._symbol)
    def move(self):
        if self._actual_field == (4,13):
            return True
        else:
            return False
##    def __str__(self):
##        return str(self._actual_field)

class UsualField(object):
    symbol = u"\u2b1c"
    accessable = True
    letter = 'u'
    def __init__(self, x, y):
        self._x = x
        self._y = y
        self._pheromone = 0.0
    def __unicode__(self):
        return self.symbol
    
class NestField(UsualField):
    symbol = u"\u25A6"
    letter = 'n'

class RockField(UsualField):
    symbol = u"\u2b1b"
    accessable = False
    letter = 'r'

class FoodField(UsualField):
    symbol = u"\u25A3"
    letter = 'f'

class Controler(object):
    def run(self):
        for i in xrange(1):
            pass
            
class Board(object):
    def __init__(self, fields):
        self._fields = fields
        self._height = np.shape(fields)[0]
        self._width = np.shape(fields)[1]

    @staticmethod
    def field_from_letter(letter, h, w):
        if letter == 'n':
            return NestField(h,w)
        elif letter == 'f':
            return FoodField(h,w)
        elif letter == 'r':
            return RockField(h,w)
        else:
            return UsualField(h,w)

    @classmethod
    def read_from_file(cls, path):
        with open(path, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            fields = []
            for h, row in enumerate(reader):
                fields.append([cls.field_from_letter(letter, h, w) for w, letter in enumerate(row)])
        return cls(np.array(fields))

    def write_to_file(self, path):
        with open(path, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            for h in xrange(self._height):
                writer.writerow([i.letter for i in self._fields[h]])
    
    @classmethod
    def randomize(cls, height, width, food_con, rock_no):
        food_no = 1
        if food_con != 0:
            food_no += height * width / food_con
        usual_no = height * width - food_no - rock_no - 1
        fields_draft = np.array(['n'] + food_no * ['f'] + rock_no * ['r'] + usual_no *  ['u'])
        np.random.shuffle(fields_draft)
        fields_draft = fields_draft.reshape(height, width)
        
        fields = np.empty([height, width], dtype = object)
        
        for h in xrange(height):
            for w in xrange(width):
                fields[h][w] = cls.field_from_letter(fields_draft[h,w], h, w)
                  
        return cls(fields)
    
    def __unicode__(self):
        u = u''
        for h in xrange(self._height):
            for w in xrange(self._width):
                u += unicode(self._fields[h][w])
            u += '\n'
        return u
        
        
b = Board.randomize(10, 10, 0, 2)
print unicode(b)
b.write_to_file('mrowisko01.csv')

c = Board.read_from_file('mrowisko01.csv')
print unicode(c)


        
    

