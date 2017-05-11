#
# mathutilities.py
#
# Copyright © 2006, 2011-2013, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
A set of functions originally available at the following website:

http://www.phys.uu.nl/~haque/computing/WPark_recipes_in_python.html

As of November, 2011 the website appears to have vanished. Its contents appear
to be reproduced here:

http://www.physics.rutgers.edu/~masud/computing/WPark_recipes_in_python.html
"""

# System imports
import cmath
import math

# -----------------------------------------------------------------------------

#
# Functions
#

def asReal(x, delta=1.0e-5):
    """
    If the given value is real, just return it. If it's complex and its
    imaginary coefficient is close enough to zero then return just the real
    coefficient. Otherwise return the same value.
    
    >>> asReal(0.25)
    0.25
    >>> asReal(0.25+0.0001j)
    (0.25+0.0001j)
    >>> asReal(0.25+0.0001j, delta=0.001)
    0.25
    """
    
    if abs(x.imag) <= abs(delta):
        return x.real
    
    return x

def cbrt(x):
    """
    Takes the cube root of a real number.
    
    >>> print(cbrt(27.0))
    3.0
    >>> print(cbrt(-27.0))
    -3.0
    """
    
    if x >= 0: 
        return math.pow(x, 1 / 3)
    else:
        return -math.pow(abs(x), 1 / 3)

def closeEnough(a, b, delta=1.0e-5):
    """
    Checks the two scalar values for essential equality.
    
    >>> n1, n2 = 1000, 1001
    >>> closeEnough(n1 / n2, n2 / n1)
    False
    >>> closeEnough(n1 / n2, n2 / n1, delta=0.01)
    True
    >>> closeEnough(1e400,1e400)
    True
    """
    
    if abs(a) == float("+inf") and abs(b) == float("+inf"):
        return True
    
    return abs(a - b) <= abs(delta)

def closeEnoughSpan(n, low=0.0, high=1.0, delta=1.0e-5):
    """
    Checks if n is within the specified span, or within delta of its outer
    edges.
    
    >>> closeEnoughSpan(0.5)
    True
    >>> closeEnoughSpan(6.01, 0, 6)
    False
    >>> closeEnoughSpan(6.01, 0, 6, delta=0.5)
    True
    >>> closeEnoughSpan(6.01, 6, 0, delta=0.5)
    True
    """
    
    delta = abs(delta)
    
    if low > high:
        return high - delta <= n <= low + delta
    
    return low - delta <= n <= high + delta

def closeEnoughXY(p1, p2, delta=1.0e-5):
    """
    Checks the two points for essential equality.
    
    >>> p1 = _makePt(4.001, -3.999)
    >>> p2 = _makePt(4, -4)
    >>> closeEnoughXY(p1, p2)
    False
    >>> closeEnoughXY(p1, p2, delta=0.01)
    True
    """
    
    delta = abs(delta)
    return (abs(p1.x - p2.x) <= delta) and (abs(p1.y - p2.y) <= delta)

def cubic(a, b, c, d=None):
    """
    Solves a cubic equation with real coefficients. If d is None the equation
    is x^3 + ax^2 + bx + c = 0; else it's ax^3 + bx^2 + cx + d = 0.
    
    The first returned root will always be real; the other two might not be.
    
    >>> print(cubic(-1, -10, -8))
    (4, -1, -2)
    >>> print(cubic(2, 0, 0, -54))
    (3, (-1.5+2.598076211353316j), (-1.5-2.598076211353316j))
    >>> print(cubic(0.000001, 1, 3, -54))
    (6, -9, -9)
    >>> print(cubic(0.000001, 0.000001, 0, -4))
    ()
    """
    
    if d is not None:
        if zeroEnough(a):
            # this is actually a quadratic
            roots = quadratic(b, c, d)
            
            if roots:
                return roots + (roots[-1],)
            
            return ()
        
        a, b, c = b / a, c / a, d / a
    
    t = a / 3
    p, q = b - 3 * t**2, c - b * t + 2 * t**3
    u, v = quadratic(q, -(p / 3) ** 3)
    
    if u.imag:  # complex cubic root
        r, w = polar(u.real, u.imag)
        y1 = 2 * cbrt(r) * math.cos(w / 3)
    
    else:  # real root
        y1 = cbrt(u) + cbrt(v)
    
    y2, y3 = quadratic(y1, p + y1**2)
    
    return (
      intIfPossible(y1 - t),
      intIfPossible(y2 - t),
      intIfPossible(y3 - t))

def fixedToFloat(x):
    """
    Returns a floating-point number for a given 16.16 fixed point number.
    >>> print(fixedToFloat(0x00010000))
    1.0
    >>> print(fixedToFloat(0xFFFF8000))
    -0.5
    >>> fixedToFloat(0x100000000)
    Traceback (most recent call last):
      ...
    ValueError: Value 4294967296 out of range of valid 16.16 fixed point numbers.
    >>> fixedToFloat(-1)
    Traceback (most recent call last):
      ...
    ValueError: Value -1 out of range of valid 16.16 fixed point numbers.
    """
    if not 0 <= x <= 0xFFFFFFFF:
        raise ValueError('Value %r out of range of valid 16.16 '
                         'fixed point numbers.' % (x,))
    # if the 16.16 sign bit is set, restore all sign bits above that
    if x & 0x80000000:
        x -= 0x100000000

    # divide by 2^16 to get a normal float
    x /= 0x10000

    return x


def floatToFixed(x, forceUnsigned=False):
    """
    Returns an integer with the 16.16 Fixed representation of the specified
    floating-point number. If forceUnsigned is True, the returned value will
    always be positive (i.e. it could be added to a StringWriter with an
    unsigned 'L' format).
    
    >>> print("%X" % (floatToFixed(1.5),))
    18000
    >>> print("%X" % (floatToFixed(-1.5),))
    -18000
    >>> print("%X" % (floatToFixed(-1.5, forceUnsigned=True),))
    FFFE8000
    >>> floatToFixed(32768.0)
    Traceback (most recent call last):
      ...
    ValueError: Value 32768.0 cannot be converted to Fixed!
    """
    
    n = int(round(x * 65536.0))
    
    if n > 0x7FFFFFFF or n < -0x80000000:
        raise ValueError("Value %r cannot be converted to Fixed!" % (x,))
    
    if n < 0 and forceUnsigned:
        n += 0x100000000
    
    return n

def intIfPossible(n, delta=1.0e-5):
    """
    If n is within delta of an integral value, that value is returned.
    Otherwise, n is returned unaltered.
    
    >>> intIfPossible(0.999999999)
    1
    >>> intIfPossible(0.999999999, delta=1.0e-14)
    0.999999999
    
    Note that this works on complex numbers as well, for both the real and
    imaginary part:
    
    >>> c = -1.9999999999 + 3.0000000001j
    >>> intIfPossible(c)
    (-2+3j)
    >>> intIfPossible(c, delta=1.0e-15)
    (-1.9999999999+3.0000000001j)
    """
    
    delta = abs(delta)
    nReal = n.real
    nImag = n.imag
    
    r = round(nReal)
    
    if abs(r - nReal) <= delta:
        nReal = r
    
    r = round(nImag)
    
    if abs(r - nImag) <= delta:
        nImag = r
    
    if nImag:
        return complex(nReal, nImag)
    
    return nReal

def newton(func, funcd, x, TOL=1e-10):
    """
    Use Newton-Raphson method to determine a root of the specified function.
    The func argument should be a callable that takes a single argument. The
    funcd argument should be a callable that is the derivative of func. The x
    argument should be an initial guess. The tolerance TOL controls how close a
    root needs to be for the process to end.
    
    >>> f = (lambda x: (x ** 7) - 5 * (x ** 5) + 14)
    >>> fd = (lambda x: 7 * (x ** 6) - 25 * (x ** 4))
    >>> newton(f, fd, 1)
    1.343874001627126
    """
    
    f, fd = func(x), funcd(x)
    
    while True:
        dx = f / fd
        
        if abs(dx) < TOL * (1 + abs(x)):
            return x - dx
        
        x = x - dx
        f, fd = func(x), funcd(x)

def polar(x, y, deg=False):
    """
    Converts the specified (x, y) into (r, theta). The returned angle will be
    in degrees if deg is True, and in radians otherwise.
    
    >>> polar(4, 4, True)
    (5.656854249492381, 45.0)
    >>> polar(-4, 4, True)
    (5.656854249492381, 135.0)
    >>> polar(4, -4, True)
    (5.656854249492381, -45.0)
    >>> polar(-4, -4, True)
    (5.656854249492381, -135.0)
    >>> polar(2, 1, False)
    (2.23606797749979, 0.4636476090008061)
    """
    
    r = math.hypot(x, y)
    angle = math.atan2(y, x)
    
    if deg:
        return (r, math.degrees(angle))
    
    return (r, angle)

def polyderiv(a):
    """
    Finds the first derivative of the specified polynomial. The a[0] term
    is the zero-order coefficient, the a[1] term is the first-order, etc.
    
    Returns a tuple with the derivative.
    
    >>> polyderiv((3, 1, -2))  # that's -2x^2 + x + 3
    (1, -4)
    """
    
    return tuple(i * a[i] for i in range(1, len(a)))

def polyeval(a, x):
    """
    Numerically evaluates a polynomial. a[0] is the zero-order coefficient,
    a[1] the first-order coefficient, and so on. Returns the value.
    
    >>> polyeval((3, 1, -2), -2)  # that's -2x^2 + x + 3
    -7
    """
    
    p = 0
    
    for coef in reversed(a):
        p = p * x + coef
    
    return p

def polyinteg(a):
    """
    Given a tuple of coefficients (zero-order first) for a polynomial, return a
    new tuple for the results of the integrated polynomial. This is intended to
    be used in a definite integral evaluation, so no constant term is added.
    
    >>> polyinteg((2, 12, -15, 8))
    (0, 2.0, 6.0, -5.0, 2.0)
    """
    
    return (0,) + tuple(n / (i + 1) for i, n in enumerate(a))

def polymul(a, b):
    """
    Given the coefficients for two polynomials (which are expressed as tuples
    with the zero-order coefficient first), returns a tuple representing the
    coefficients of the product.
    
    >>> polymul((1, 2, -1), (3, -3))
    (3, 3, -9, 3)
    """
    
    vZero = [0] * (len(a) + len(b) - 1)
    vSum = list(vZero)
    
    for i, row in enumerate(b):
        vThis = list(vZero)
        
        for j, n in enumerate(a):
            vThis[i+j] = row * n
        
        vSum = [n + m for n, m in zip(vSum, vThis)]
    
    return tuple(vSum)

def polyreduce(a, root):
    """
    Given the specified root of the specified polynomial, returns a new
    polynomial of the next lower degree by factoring out the root.
    
    >>> polyreduce((-8, -10, -1, 1), 4)
    (2, 3, 1)
    """
    
    c, p = [], 0
    
    for coef in reversed(a):
        p = p * root + coef
        c.append(p)
    
    c.reverse()
    return tuple(c[1:])

def quadratic(a, b, c=None):
    """
    Solves a quadratic equation with real coefficients. If c is None the
    equation is x^2 + ax + b = 0; otherwise the equation is ax^2 + bx + c = 0.
    The two roots (real or complex) are returned.
    
    >>> print(quadratic(4, -12))
    (2, -6)
    >>> print(quadratic(6, 13))
    ((-3+2j), (-3-2j))
    >>> print(quadratic(-2, 5, -8))
    ((1.25+1.5612494995995996j), (1.25-1.5612494995995996j))
    >>> print(quadratic(0, 2, -4))
    (2, 2)
    >>> print(quadratic(0, 0, 1))
    ()
    """
    
    if c is not None:
        if zeroEnough(a):
            # degenerate quadratic bx + c = 0
            if zeroEnough(b):
                # raise ValueError("Degenerate quadratic!")
                return ()
            
            r = intIfPossible(-c / b)
            return (r, r)
        
        a, b = b / a, c / a
    
    t = a / 2
    r = (t ** 2) - b
    
    if r >= 0:          # real roots
        y1 = math.sqrt(r)
    else:               # complex roots
        y1 = cmath.sqrt(r)
    
    y2 = -y1
    return (intIfPossible(y1 - t), intIfPossible(y2 - t))

def quartic(a, b, c, d, e):
    """
    Return a tuple of roots solving the specified quartic equation.
    
    >>> print(quartic(1, -9, 12, 44, -48))
    (6, 4, 1, -2)
    
    >>> for n in quartic(1, 0, 0, 0, 16): print(n)
    (1.4142135623730951+1.414213562373095j)
    (-1.4142135623730951-1.414213562373095j)
    (1.4142135623730951-1.414213562373095j)
    (-1.4142135623730951+1.414213562373095j)
    
    >>> print(quartic(0, 9, 12, 44, -48))
    (0.8063449925565387, (-1.069839162944936+2.338728705532393j), (-1.069839162944936-2.338728705532393j))
    
    >>> print(quartic(3, 9, 12, 24, -48))
    ((-0.4563109873079236-2.2302850160798746j), (-0.4563109873079236+2.2302850160798746j), 1, -3.0873780253841523)
    
    >>> tstVals = [-5, -1, 0, 1, 4]
    >>> for t in itertools.product(tstVals, repeat=5):
    ...   u = quartic(*t)
    """
    
    if a == 0:
        return cubic(b, c, d, e)
    
    if a != 1:
        b /= a
        c /= a
        d /= a
        e /= a
        a = 1
    
    s = cmath.sqrt
    alpha = c - (3 * b * b / 8)
    beta = d + ((b ** 3) / 8) - (b * c / 2)
    gamma = e - (3 * (b ** 4) / 256) + (b * b * c / 16) - (b * d / 4)
    constPart = -b / 4
    
    if zeroEnough(beta):
        inside = s(alpha * alpha - 4 * gamma)
        underPlus = s((inside - alpha) / 2)
        underMinus = s((-inside - alpha) / 2)
        
        return tuple((
          intIfPossible(constPart + underPlus),
          intIfPossible(constPart - underPlus),
          intIfPossible(constPart + underMinus),
          intIfPossible(constPart - underMinus)))
    
    p = -((alpha * alpha) / 12 + gamma)
    q = ((alpha * gamma) / 3) - ((alpha * alpha * alpha) / 108) - ((beta * beta) / 8)
    r = (-q / 2) + s(((q * q) / 4) + ((p * p * p) / 27))
    u = r ** (1 / 3)
    
    if zeroEnough(u):
        y = u - (5 * alpha / 6) - (q ** (1 /3))
    else:
        y = u - (5 * alpha / 6) - (p / (3 * u))
    
    w = s(alpha + 2 * y)
    underPlus = s(-((3 * alpha) + (2 * y) + ((2 * beta) / w)))
    underMinus = s(-((3 * alpha) + (2 * y) - ((2 * beta) / w)))
    
    return tuple((
      intIfPossible(constPart + ((w + underPlus) / 2)),
      intIfPossible(constPart + ((w - underPlus) / 2)),
      intIfPossible(constPart + ((-w + underMinus) / 2)),
      intIfPossible(constPart + ((-w - underMinus) / 2))))

def zeroEnough(x, delta=1.0e-5):
    """
    Returns True if x is sufficiently close to zero.
    
    >>> zeroEnough(0.001)
    False
    >>> zeroEnough(0.001, delta=0.01)
    True
    
    This function works for complex numbers too:
    
    >>> zeroEnough(0.00000001+0.00000001j)
    True
    >>> zeroEnough(0.00000001+0.00000001j, delta=1.0e-15)
    False
    """
    
    delta = abs(delta)
    return (abs(x.real) <= delta) and (abs(x.imag) <= delta)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import itertools
    
    def _makePt(x, y):
        from fontio3.fontmath import point
        
        return point.Point(x, y)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
