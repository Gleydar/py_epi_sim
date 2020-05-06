from enum import Enum


class Events(Enum):
    """Enum of all supported scheduler events
    Author: Konstantin Schlosser"""
    ERROR = "error"
    NEXT_STEP = "next_step"
    PRE_NEXT_STEP = "pre_next_step"
    AGENT_MOVEMENT = "agent_movement"
    STATUS_UPDATE = "status_update"
    REPAINT = "repaint"
    RESET = "reset"
    AGENT_CHANGE_GUI = "agent_change_gui"
