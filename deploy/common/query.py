def find(function, sequence, default=None):
    for s in sequence:
        if function(s):
            return s
    return default
