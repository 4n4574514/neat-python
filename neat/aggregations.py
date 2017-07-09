"""
Has the built-in aggregation functions, methods for using them,
and methods for adding new user-defined ones.
"""
import sys
import warnings

from operator import mul

if sys.version_info[0] > 2:
    from functools import reduce

def product_aggregation(x): # note: `x` is a list or other iterable
    return reduce(mul, x, 1.0)

def sum_aggregation(x):
    return sum(x)

def max_aggregation(x):
    return max(x)

def min_aggregation(x):
    return min(x)

def maxabs_aggregation(x):
    return max(x, key=abs)


class AggregationFunctionSet(object):
    """Contains aggregation functions and methods to add and retrieve them."""
    
    def __init__(self, multiparameterset):
        self.multiparameterset = multiparameterset
        self.add('product', product_aggregation)
        self.add('sum', sum_aggregation)
        self.add('max', max_aggregation)
        self.add('min', min_aggregation)
        self.add('maxabs', maxabs_aggregation)

    def add(self, name, function, **kwargs):
        self.multiparameterset.add_func(name, function, 'aggregation', kwargs)

    def get(self, name):
        return self.multiparameterset.get_func(name, 'aggregation')

    def __getitem__(self, index):
        warnings.warn("Use get, not indexing ([{!r}]), for aggregation functions".format(index),
                      DeprecationWarning)
        return self.get(index)

    def is_valid(self, name):
        return self.multiparameterset.is_valid_func(name, 'aggregation')

