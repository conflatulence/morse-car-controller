
from math import pi

class Position:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

def clamp(min_val, max_val, val):
    if val < min_val:
        return min_val
    if val > max_val:
        return max_val
    return val

def wrap_radians(v):
    while v >= pi:
        v -= 2*pi
    while v < -pi:
        v += 2*pi
    return v

def recursive_round(d, n):
    if type(d) is float:
        return round(d, n)
    
    elif type(d) is dict:        
        for k in d:
            d[k] = recursive_round(d[k], n)
        return d    

    elif type(d) in (list, tuple):
        return [recursive_round(v, n) for v in d]
    
    else:
        return d


