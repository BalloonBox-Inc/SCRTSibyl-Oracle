from operator import mul


def dot_product(l1, l2):
    return sum(map(mul, l1, l2))
