import math
import random

try:
    import sympy
except ImportError:
    pass

class Library():
    def __init__(self):
        try:
            self.CONSTANTS = {'deg': sympy.pi/180,
                              '1': sympy.GoldenRatio,
                              '2': sympy.E,
                              '3': sympy.pi}

            self.is_probably_prime = sympy.ntheory.isprime

        except NameError:
            self.CONSTANTS = {'deg': math.pi/180,
                              '1': (1 + 5**.5)/2,
                              '2': math.e,
                              '3': math.pi}

            self.is_probably_prime = self._is_probably_prime

        try:
            self.gcd = __import__("fractions").gcd
        except AttributeError:
            pass

    def __getattr__(self, name):
        try:
            return getattr(sympy, name)
        except (AttributeError, NameError):
            try:
                return getattr(math, name)
            except AttributeError:
                return self.__getattribute__(name)

    def _is_probably_prime(self, n):
        n = int(n)

        if n < 2:
            return False

        if n in [2, 3]:
            return True

        # Miller Rabin
        s = 0
        d = n-1

        while d%2 == 0:
            d //= 2
            s += 1

        k = 10 + math.log(n)//math.log(4)
        witness_count = 0

        while witness_count < k:
            continue_ = False
            a = random.randint(2, n-2)
            x = pow(a, d, n)

            if x == 1 or x == n-1:
                witness_count += 1
                continue

            for _ in range(s-1):
                x = pow(x, 2, n)

                if x == 1:
                    return False

                if x == n-1:
                    continue_ = True
                    break

            if not continue_:
                return False

            witness_count += 1

        return True

    def to_degrees(self, elem):
        return elem / self.CONSTANTS['deg']

    def to_radians(self, elem):
        return elem * self.CONSTANTS['deg']
            
