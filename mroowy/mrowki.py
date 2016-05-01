#-*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import time
import csv
import random
import bisect

def weighted_choice(values, weights):
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = random.random() * total
    i = bisect.bisect(cum_weights, x)
    if i == len(values):
        return random.choice(values)
    return values[i]

class Ant(object):
    symbol = u"\u2748"
    def __init__(self, initial_field):
        self._current_field = initial_field
        self._route = []
        self._food_found = False
    def __unicode__(self):
        return symbol
    def move_back(self):
        self._current_field = self._route.pop()
    def move_forward(self, next_field):
        self._route.append(self._current_field)
        self._current_field = next_field
        

class UsualField(object):
    symbol = u"\u2b1c"
    accessible = True
    letter = 'u'
    has_food = False
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
    accessible = False
    letter = 'r'

class FoodField(UsualField):
    symbol = u"\u25A3"
    letter = 'f'
    has_food = True

class Controler(object):
    def __init__(self, board, ant_no, sym_time, pheromone_con, deaden_time):
        self._board = board
        self._ants = [Ant(board._nest) for a in xrange(ant_no)]
        self._sym_time = sym_time
        self._pheromone_con = pheromone_con
        self._deaden_time = deaden_time
        
    def step(self):
        self.move_ants()
        self.update_ants_status()
        self.deaden_pheromone()
        self.spray_pheromone()
        self.update_time()

    def move_ants(self):
        for ant in self._ants:
            if ant._food_found:
                ant.move_back()
            else:
                possible_fields = self._board.get_possible_moves(ant._current_field)
                probabilites = [field._pheromone for field in possible_fields]
                ant.move_forward(weighted_choice(possible_fields, probabilites))

    def update_ants_status(self):
        for ant in self._ants:
            if ant._food_found:
                if ant._current_field == self._board._nest:
                    ant._food_found = False
            else:
                if ant._current_field.has_food:
                    ant._food_found = True

    def deaden_pheromone(self):
        for field in self._board.iter_fields():
            field._pheromone *= 0.5

    def spray_pheromone(self):
        for ant in self._ants:
            if ant._current_field != self._board._nest and ant._food_found:
                ant._current_field._pheromone = self._pheromone_con

    def update_time(self):
        self._sym_time -= 1

    def run(self):
##        fig = plt.figure()
##        ax = fig.add_subplot(111)
##        im = ax.imshow(self._board.get_pheromone_con())
##        plt.show(block=False)
        
        while self._sym_time:
##            time.sleep(0.5)
            self.step()
##            im.set_array(self._board.get_pheromone_con())
##            fig.canvas.draw()
    
            
class Board(object):
    def __init__(self, fields, nest_coords):
        self._fields = fields
        self._height = np.shape(fields)[0]
        self._width = np.shape(fields)[1]
        self._nest = fields[nest_coords[0],nest_coords[1]]

    def get_pheromone_con(self):
        return np.vectorize(lambda x: x._pheromone)(self._fields)

    def get_possible_moves(self, field):
        possible_coords = [[field._x, field._y-1], [field._x, field._y+1],
                           [field._x-1, field._y], [field._x+1, field._y],
                           [field._x-1, field._y-1], [field._x+1, field._y+1],
                           [field._x-1, field._y+1], [field._x+1, field._y-1]]
        
        possible_coords = [[x,y] for x, y in possible_coords
                           if (0 <= x < self._height) and (0 <= y < self._width)]
        
        possible_fields = [self._fields[x][y] for x,y in possible_coords if self._fields[x][y].accessible]
        return possible_fields                           
            
        
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
            nest = map(int, next(reader))
            for h, row in enumerate(reader):
                fields.append([cls.field_from_letter(letter, h, w) for w, letter in enumerate(row)])
        return cls(np.array(fields), nest)

    def write_to_file(self, path):
        with open(path, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow((self._nest._x, self._nest._y))
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
                if fields_draft[h,w] == 'n':
                    nest = [h,w]
                fields[h][w] = cls.field_from_letter(fields_draft[h,w], h, w)
                  
        return cls(fields, nest)
    
    def iter_fields(self):
        return self._fields.flat
    
    def __unicode__(self):
        u = u''
        for h in xrange(self._height):
            for w in xrange(self._width):
                u += unicode(self._fields[h][w])
            u += '\n'
        return u
        
        
b = Board.randomize(25, 25, 600, 10)
print b._nest
print unicode(b)
b.write_to_file('mrowisko01.csv')

c = Board.read_from_file('mrowisko01.csv')
print unicode(c)
print c._nest

controler = Controler(c, 1000, 1000, 50.0, 0)
controler.run()
##fig = plt.figure()
##ax = fig.add_subplot(111)
plt.imshow(c.get_pheromone_con())
##plt.pcolor(c.get_pheromone_con())
plt.show()
        
    

