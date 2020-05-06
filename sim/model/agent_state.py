from enum import Enum


class AgentState(Enum):
    """Possible states the agent can be in. Can be extended for further functionality.
    Author: Konstantin Schlosser"""
    EMPTY = 0
    SUSCEPTIBLE = 1
    INFECTIVE = 2
    REMOVED = 3
    IMMUNE = 4
    DEAD = 5
    INCUBATION = 6
