import math
import random

def is_probably_prime(n):
    if not isinstance(n, int):
        return False

    if n < 0:
        n = -n

    if n in [0, 1]:
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

    
            
