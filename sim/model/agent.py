from __future__ import annotations
from controller.scheduler import Scheduler
from model.agent_state import AgentState
from model.grid_pos import GridPos
import logging


class Agent:
    num = 0
    """Class representing an agent
    Author: Konstantin Schlosser, Benedikt Beil, Andreas Stiglmeier"""

    def state(self) -> AgentState:
        return self.__infectionState

    def set_state(self, state: AgentState) -> None:
        self.__logger.debug(f"Changing state from {self.state()} to {state}")
        self.__infectionState = state
        self.__scheduler.update_gui_state(self.__grid_pos, state)

    def infected_count(self) -> int:
        return self.__infected_count

    def update_infected_count(self) -> None:
        self.__infected_count += 1

    def sick_days(self) -> int:
        return self.__sickDays

    def update_sick_days(self) -> None:
        self.__sickDays += 1

    def incubation_days(self) -> int:
        return self.__incubationDays

    def update_incubation_days(self) -> None:
        self.__incubationDays += 1

    def get_pos(self) -> GridPos:
        return self.__grid_pos

    def get_scheduler(self) -> Scheduler:
        return self.__scheduler

    def is_quarantined(self) -> bool:
        return self.__quarantined

    def set_quarantined(self, quarantined: bool) -> None:
        self.__quarantined = quarantined

    def set_pos(self, grid_pos: GridPos) -> None:
        self.__logger.debug(
            f"Moving agent from {self.__grid_pos.row()},{self.__grid_pos.col()} to {grid_pos.row()},{grid_pos.col()}")
        self.__grid_pos = grid_pos
        self.__scheduler.update_gui_state(self.__grid_pos, self.__infectionState)

    def grid(self):
        """
        Returns the grid on which this agent is located.
        :return: Grid
        """
        return self.__grid

    def __init__(self, scheduler: Scheduler, grid_pos: GridPos, agent_state: AgentState, grid):
        self.__logger = logging.getLogger(f"Agent{Agent.num}")
        Agent.num += 1
        self.__scheduler = scheduler
        self.__infectionState = agent_state
        self.__grid = grid

        self.__sickDays = 0
        self.__incubationDays = 0
        self.__infected_count = 0

        self.__grid_pos = grid_pos
        self.__scheduler.update_gui_state(self.__grid_pos, agent_state)
        self.__logger.debug("Agent created, sent update")
        self.__quarantined = False
