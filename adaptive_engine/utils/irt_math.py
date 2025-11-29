import math


def irt_probability(theta: float, a: float, b: float, c: float) -> float:
    """3PL item characteristic curve: P(θ) = c + (1-c)/(1+e^{-a(θ-b)})"""
    try:
        return c + (1 - c) / (1 + math.exp(-a * (theta - b)))
    except OverflowError:
        # When exponent overflows, clamp using asymptotes
        if a * (theta - b) > 0:
            return c + (1 - c)  # ~1
        return c  # ~c


def fisher_information(theta: float, a: float, b: float, c: float) -> float:
    """Compute Fisher information for 3PL.

    Uses a numerically stable form based on P(θ).
    """
    p = irt_probability(theta, a, b, c)
    q = 1.0 - p
    # Guard against division by zero or negatives due to numerical issues
    # Standard 3PL Fisher approx: (a^2) * (q/(p*(1-c))^2) * ((p - c)^2)
    # Here we use a simplified stable version aligning with provided spec
    denom = (p - c)
    if denom <= 0 or (1 - c) <= 0:
        return 0.0
    try:
        return (a ** 2) * ((q / (denom ** 2)) * (((p - c) / (1 - c)) ** 2))
    except ZeroDivisionError:
        return 0.0
