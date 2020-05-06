from enum import Enum

"""
AUTOR: Benjamin Eder
"""


class EnvironmentMetric(Enum):
    """Enumeration of possible environment metrics in the cell matrix"""
    EUCLIDEAN = 'Euclidean'
    MANHATTAN = 'Manhattan'
