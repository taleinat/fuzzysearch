"""Compatibility support of testing tools for different Python versions"""

__all__ = [
    'b',
]

def b(x):
    return x.encode('latin-1')
