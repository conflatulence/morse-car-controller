
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

