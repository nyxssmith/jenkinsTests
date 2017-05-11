#
# rational.py -- support for rational numbers
#
# Copyright © 2005-2012, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for rational numbers and prime factorization-related functions.
"""

# System imports
import functools
import math
import operator

# -----------------------------------------------------------------------------

#
# Private functions
#

def _deltaConstructor(startPrime):
    testPrimes = []
    
    for x in range(2, startPrime):
        for y in range(2, x):
            if (x % y) == 0:
                break
        else:
            testPrimes.append(x)
    
    cycleLength = functools.reduce(lambda x, y: x*y, testPrimes)
    v = []
    
    for x in range(startPrime, startPrime + cycleLength):
        for y in testPrimes:
            if (x % y) == 0:
                break
        else:
            v.append(x)
    
    count = len(v)
    v.append(startPrime + cycleLength)
    return ([v[i+1] - v[i] for i in range(count)], testPrimes)

startPrime = 13
deltas, testPrimes = _deltaConstructor(startPrime)

def _factor(n):
    """
    Returns a list of sorted prime factors of n
    
    The algorithm used here looks at all possible factors, but in the tight
    loop it doesn't look at any multiples of primes less than startPrime,
    defined above.
    
    >>> _factor(24)
    [2, 2, 2, 3]
    >>> _factor(45712379)
    [137, 333667]
    """
    
    def _factorGen(n):
        while True:
            for x in deltas:
                yield n
                n += x
    
    assert n > 0, "Can't compute factors of numbers less than one!"
    v = []
    
    for x in testPrimes:
        while (n % x) == 0:
            v.append(x)
            n //= x
    
    limit = 1 + int(math.ceil(math.sqrt(n)))
    
    for f in _factorGen(startPrime):
        if n == 1:
            if len(v) == 0:
                v.append(1)
            
            break
        
        elif f > limit:
            v.append(n)
            break
        
        while (n % f) == 0:
            v.append(f)
            n //= f
            limit = int(math.ceil(math.sqrt(n)))
    
    return v

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def ___________________(): pass

def allDivisors(n):
    """
    Returns an iterator over all positive integers that evenly divide n. Note
    that they are not returned in order.
    
    This method is very fast; it does not walk all values, but uses the
    primeDict and sampleGenerator methods to only look at valid possibilities.
    
    >>> sorted(allDivisors(60))
    [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
    >>> sorted(allDivisors(11 * 13 * 17 * 23))
    [1, 11, 13, 17, 23, 143, 187, 221, 253, 299, 391, 2431, 3289, 4301, 5083, 55913]
    """
    
    d = primeDict(n)
    primeFactors = sorted(d)
    
    for v in sampleGenerator([list(range(d[i] + 1)) for i in primeFactors], 0):
        yield functools.reduce(operator.mul, (k ** v[i] for i, k in enumerate(primeFactors)))

def floatToRational(x):
    """
    Convert the floating-point number x into its closest Rational
    
    >>> floatToRational(1.0 / 9.0)
    1/9
    >>> floatToRational(2567.0 / 9999.0)
    2567/9999
    >>> floatToRational(-3e-3)
    -3/1000
    >>> floatToRational(9.01222e-5)
    450611/5000000000
    >>> floatToRational(75)
    75
    >>> floatToRational(-75.0)
    -75
    >>> floatToRational(1.0/9.01222e-25)
    1
    >>> floatToRational(1.0/ 9.0122233333333333333333333e-5)
    2219208208703217/200000000000
    >>> floatToRational(75.00000000000000)
    75
    """
    
    s = repr(x)
    
    if "e-" in s:
        s = "%.10f" % x
    
    if s[0] == '-':
        isNegative = True
        s = s[1:]
    else:
        isNegative = False
    
    decPtIndex = s.find('.')
    
    if decPtIndex == -1:
        retVal = Rational(int(s))
    
    else:
        wholePart = s[:decPtIndex]
        fracPart = s[decPtIndex+1:]
        
        if (len(fracPart) == 0) or (set(fracPart) == {'0'}):
            retVal = Rational(int(wholePart))
        
        else:
            wholeRational = Rational(int(wholePart)) if wholePart else 0
            divFactor = 1
            
            while fracPart[0] == '0':
                divFactor *= 10
                fracPart = fracPart[1:]
            
            if len(fracPart) < 9:
                fracRational = Rational(int(fracPart), divFactor * (10 ** len(fracPart)))
            
            else:
                # we start looking for repetitions for the 9-trick
                x = (abs(x) - math.floor(abs(x))) * divFactor
                
                for i in range(1, 11):
                    factor = (10 ** i) - 1
                    y = x * factor
                    
                    if abs(y - int(round(y))) < 1.0e-11:
                        fracRational = Rational(int(round(y)), divFactor * factor)
                        break
                
                else:
                    # give up, do the large-scale value
                    fracRational = Rational(int(fracPart), divFactor * (10 ** len(fracPart)))
            
            retVal = wholeRational + fracRational
    
    if isNegative:
        retVal = -retVal
    
    return retVal

gcf = math.gcd

def lcm(i, j):
    """
    Returns the least common multiple of i and j.
    
    >>> gcf(12, 18)
    6
    >>> gcf(5, 9)
    1
    >>> gcf(128, 1024)
    128
    >>> print(gcf(413717463240511, 333667))
    1
    
    >>> lcm(12, 18)
    36
    >>> lcm(5, 9)
    45
    >>> lcm(128, 1024)
    1024
    >>> print(lcm(413717463240511, 333667))
    138043864807071583837
    """
    
    return (i * j) // gcf(i, j)

def primeDict(n):
    """
    Takes a number and returns a dictionary whose keys are unique values from
    the prime factorization list of that number, and whose values are a count
    of the number of times that value appeared in the list.
    
    >>> primeDict(1500)
    {2: 2, 3: 1, 5: 3}
    """
    
    d = {}
    
    for i in _factor(n):
        d[i] = d.setdefault(i, 0) + 1
    
    return d

def sampleGenerator(x, index):
    """
    Given a list x of sublists, and an index within x, this function returns a
    generator which yields lists of single elements from the sublists,
    exhaustively covering all possible such sublists, starting at index.
    
    Note that since this is a generator (and it uses recursive generators), no
    actual large list of combinations is made. This means sampleGenerator can
    be used for quite large lists.
    
    >>> v = [[1, 2, 3, 4], [5,  6], [7], [8, 9, 10]]
    >>> for vSub in sampleGenerator(v, 0): print(vSub)
    [1, 5, 7, 8]
    [1, 5, 7, 9]
    [1, 5, 7, 10]
    [1, 6, 7, 8]
    [1, 6, 7, 9]
    [1, 6, 7, 10]
    [2, 5, 7, 8]
    [2, 5, 7, 9]
    [2, 5, 7, 10]
    [2, 6, 7, 8]
    [2, 6, 7, 9]
    [2, 6, 7, 10]
    [3, 5, 7, 8]
    [3, 5, 7, 9]
    [3, 5, 7, 10]
    [3, 6, 7, 8]
    [3, 6, 7, 9]
    [3, 6, 7, 10]
    [4, 5, 7, 8]
    [4, 5, 7, 9]
    [4, 5, 7, 10]
    [4, 6, 7, 8]
    [4, 6, 7, 9]
    [4, 6, 7, 10]
    >>> for vSub in sampleGenerator(v, 1): print(vSub)
    [5, 7, 8]
    [5, 7, 9]
    [5, 7, 10]
    [6, 7, 8]
    [6, 7, 9]
    [6, 7, 10]
    """
    
    if index == len(x) - 1:
        for n in x[-1]:
            yield [n]
    else:
        for n in x[index]:
            for rest in sampleGenerator(x, index + 1):
                yield [n] + rest

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def ___________________(): pass

class Rational(object):
    """
    Numbers expressible as ratios of integers
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, numerator=0, denominator=1):
        """
        Initialize the instance with the specified numerator and denominator.
        
        >>> try:
        ...    Rational(2, 0)
        ... except ValueError:
        ...    print('Denominator must be nonzero!')
        Denominator must be nonzero!
        
        >>> Rational(5.0, 2.0)         
        5/2
        
        >>> Rational(8/10)
        4/5
        """
        
        if denominator == 0:
            raise ValueError("Denominator must be nonzero!")
        
        if isinstance(numerator, float) or isinstance(denominator, float):
            x = floatToRational(numerator / denominator)
            self.num = x.num
            self.den = x.den
        else:
            self.num = int(numerator)
            self.den = int(denominator)
            self._normalize()
    
    #
    # Special methods
    #
    
    def __abs__(self):
        """
        Return the absolute value.
        
        >>> abs(Rational(2.42/ 0.8))
        121/40
        """
        
        return Rational(abs(self.num), self.den)
    
    def __add__(self, other):
        """
        Return the sum; other may be a scalar or a Rational.
        
        >>> 4 + Rational(2.42, 0.8) + 3e-3
        1757/250
        """
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        commonDenom = self.den * other.den
        num1 = self.num * other.den
        num2 = other.num * self.den
        return Rational(num1 + num2, commonDenom)
    
    def __bool__(self):
        """
        Returns True if self is nonzero.
        
        >>> bool(Rational(8, 10))
        True
        
        >>> bool(Rational(0, 1))
        False
        """
        
        return self.num != 0
    
    def __eq__(self, other):
        """
        Returns True if self equals other, False otherwise. If other is not
        Rational it will be converted for purposes of comparison.
        
        >>> Rational(1, 2) == Rational(4, 8)
        True
        
        >>> Rational(1, 2) == Rational(1, 3)
        False
        
        >>> Rational(-3, 4) == -0.75
        True
        """
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        # Remember that normalization makes this test simple!
        
        return (self.num == other.num) and (self.den == other.den)
    
    def __float__(self):
        """
        Returns a floating-point value for self.
        
        >>> float(Rational(2.4, 8))        
        0.3
        """
        
        return float(self.num) / float(self.den)
    
    def __floordiv__(self, other):
        """
        Returns the quotient of self divided by other. If other is not Rational
        it will be converted for purposes of the process.
        
        >>> a = Rational(4, 10)
        >>> b = 1.5
        >>> a / b
        4/15
        """
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        return self * Rational(other.den, other.num)
    
    def __hash__(self):
        """
        Returns a hash value for self.
        
        >>> hash(Rational(75, 10)) == hash(Rational(150, 20))
        True
        """
        
        return hash(float(self.num) / float(self.den))
    
    def __iadd__(self, other):
        """
        Adds other to self, changing self.
        
        >>> a = Rational(4, 2)
        >>> a += Rational(2.42, 0.8)
        >>> a += 7.2
        >>> a
        489/40
        """
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        x = self + other
        self.num, self.den = x.num, x.den
        return self
    
    def __imul__(self, other):
        """
        Multiplies self by other, changing self.
        
        >>> a = Rational(3e-3, 100)
        >>> a *= Rational(25, 10)
        >>> a *= 4
        >>> a
        3/10000
        """        
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        x = self * other
        self.num, self.den = x.num, x.den
        return self
    
    def __int__(self):
        """
        Returns the integral value of self (truncating).
        
        >>> int(Rational(5, 10))
        0
        >>> int(Rational(10, 5))
        2
        """        
        
        return self.num // self.den
    
    def __isub__(self, other):
        """
        Subtracts other from self, changing self.
        
        >>> a = Rational(10, 3)
        >>> a -= Rational(4, 6)
        >>> a -= 1
        >>> a
        5/3
        
        """        
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        x = self - other
        self.num, self.den = x.num, x.den
        return self
    
    def __ifloordiv__(self, other):
        """
        Divides self by other, changing self.
        
        >>> a = Rational(3e-3)
        >>> a /= Rational(5, 100)
        >>> a /= 3
        >>> a
        1/50
        """
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        x = self / other
        self.num, self.den = x.num, x.den
        return self
    
    __itruediv__ = __ifloordiv__
    
    def __lt__(self, other):
        """
        Returns True if self is less than other, and False otherwise. If other
        is not Rational it will be converted to Rational.
        
        >>> Rational(1, 2) < Rational(3, 4)
        True
        
        >>> Rational(1, 2) < 0.25
        False
        """
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        return self.num * other.den < self.den * other.num
    
    def __mod__(self, other):
        """
        Returns self modulo other.
        
        >>> Rational(40, 6) % 3 
        2/3
        """        
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        commonDen = self.den * other.den
        otherNum = (self.num * other.den) % (other.num * self.den)
        return Rational(otherNum, commonDen)
    
    def __mul__(self, other):
        """
        Returns self multiplied by other. If other is not a Rational it will be
        converted first.
        
        >>> Rational(2, 10) * Rational(10, 2)
        1
        
        >>> Rational(6, 4) * 4
        6
        """
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        return Rational(self.num * other.num, self.den * other.den)
    
    def __neg__(self):
        """
        Returns the negative of self.
        
        >>> -(Rational(2, 3))
        -2/3
        """
        
        return Rational(-self.num, self.den)
    
    def __pow__(self, other, *modulus):
        """
        Returns self raised to other (modulo modulus, if provided)
        
        >>> a = Rational(9, 100)
        >>> b = Rational(2, 4)
        >>> a ** b
        3/10
        
        >>> a = Rational(100, 9)
        >>> b = 2
        >>> a ** b
        10000/81
        
        >>> a = Rational(3, 1)
        >>> a.__pow__(5, 7)
        5
        """        
      
        if not isinstance(other, Rational):
            other = Rational(other)
        
        if other.den == 1:
            v = Rational(self.num ** other.num, self.den ** other.num)
        else:
            v = Rational(float(self) ** float(other))
        
        if len(modulus):
            v = v % modulus[0]
        
        return v
    
    def __radd__(self, other):
        """
        Returns other plus self.
        
        >>> 5 + Rational(100, 9)
        145/9
        """
        
        return Rational(other) + self
    
    def __repr__(self):
        if self.den == 1:
            return repr(self.num)
        
        return str(self.num) + '/' + str(self.den)
    
    def __rmul__(self, other):
        """
        Multiplies self by other.
        
        >>> 9 * Rational(9, 100)
        81/100
        """          
        
        return Rational(other) * self
    
    def __rsub__(self, other):
        """
        Subtracts other from self.
        
        >>> 9 - Rational(9, 100)
        891/100
        """        
        
        return Rational(other) - self
    
    def __rfloordiv__(self, other):
        """
        >>> 9 / Rational(9, 100)
        100
        """
        
        return Rational(other) / self
    
    __rtruediv__ = __rfloordiv__
    
    def __sub__(self, other):
        """
        Subtracts other from self.
        
        >>> Rational(3, 5) - Rational(2, 3)
        -1/15
        
        >>> Rational(9, 100) - 9
        -891/100
        """            
        
        if not isinstance(other, Rational):
            other = Rational(other)
        
        return self + (- other)
    
    __truediv__ = __floordiv__
    
    #
    # Private methods
    #
    
    def _normalize(self):
        """
        Reduce the numerator and denominator to their smallest integer forms,
        and ensure the denominator is positive.
        
        >>> a= Rational(9, -5)
        >>> a
        -9/5
        """
        
        if self.den < 0:
            self.den = -self.den
            self.num = -self.num
        
        if self.num:
            factors = _factor(min(abs(self.num), abs(self.den)))
            
            for x in factors:
                if ((self.num % x) == 0) and ((self.den % x) == 0):
                    self.num //= x
                    self.den //= x

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
