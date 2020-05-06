from __future__ import annotations
from numpy import uint
from observable import Observable
from controller.events import Events
from controller.scheduler import Scheduler
from model.agent_state import AgentState
from model.grid import Grid
from model.grid_pos import GridPos
from model.state import SimState
from model.strategies.movement_strategy import MovementStrategy, DefaultMovementStrategy
from model.strategies.status_strategy import LethalityStatusStrategy, \
    VaccineStatusStrategy, IncubationStatusStrategy, DefaultInfectionStrategy, DefaultRemoveStrategy, \
    QuarantineStatusStrategy


class Provider:
    """Provider class to pass dependencies to created objects
     Author: Konstantin Schlosser"""
    __scheduler = Scheduler()
    __grid = None

    def set_grid(self, grid: Grid) -> None:
        self.__grid = grid

    def get_grid(self) -> Grid:
        return self.__grid

    def get_movement_strategy(self) -> MovementStrategy:
        """Gets the curently active movement strategy
        :return the Movement Strategy"""
        return self.__movement_strategy

    def set_movement_strategy(self, strategy) -> None:
        self.__movement_strategy = strategy

    def get_scheduler(self) -> Scheduler:
        """Returns the Scheduler instance
        :return the Scheduler instance"""
        return self.__scheduler

    def get_observable(self) -> Observable:
        """Returns the schedulers Observable. This is useful if you need to register your own handler.
        :return the active Observer"""
        return self.__scheduler.get_observable()

    def get_status_strategies(self) -> dict:
        return self.__status_strategies

    def __reset(self, state: SimState) -> None:
        if self.get_grid() is not None:
            self.get_grid().remove_listeners()
        new_grid = Grid(self.__scheduler)
        new_grid.reset(state)
        self.set_grid(new_grid)
        total_count = 0
        for row in range(self.__grid.get_size()):
            for col in range(self.__grid.get_size()):
                if self.__grid.get_agent(GridPos(uint(row), uint(col))) is not None:
                    total_count += 1
        state.set_beginning_total_count(total_count)

    def __init__(self):

        """The status strategies are initialized here.
        The lambda expression is given the current state to determine if it should be active, currently"""
        # ADD YOUR STRATEGIES HERE!
        quarantinestrategy = QuarantineStatusStrategy(self.get_scheduler())
        self.__status_strategies = {
            AgentState.SUSCEPTIBLE: [
                (VaccineStatusStrategy(self.get_scheduler()), lambda state: state.vaccine_toggle()),
                (IncubationStatusStrategy(), lambda state: state.incubation_period_enabled()),
            ],
            AgentState.INFECTIVE: [
                (quarantinestrategy, lambda state: state.quarantine_enabled()),
                (DefaultInfectionStrategy(), lambda state: True),
                (LethalityStatusStrategy(), lambda state: state.lethality_toggle()),
                (DefaultRemoveStrategy(), lambda state: not state.lethality_toggle()),
            ],
            AgentState.INCUBATION: [
                (DefaultInfectionStrategy(), lambda state: True),
                (IncubationStatusStrategy(), lambda state: state.incubation_period_enabled()),
            ],
            AgentState.IMMUNE: [
                (quarantinestrategy, lambda state: state.quarantine_enabled()),
            ],
            AgentState.DEAD: [
                (quarantinestrategy, lambda state: state.quarantine_enabled()),
            ],
            AgentState.REMOVED: [
                (quarantinestrategy, lambda state: state.quarantine_enabled()),
            ],
        }
        self.__scheduler.register_handler(Events.RESET, self.__reset)
        self.__movement_strategy = DefaultMovementStrategy()


active_provider = Provider()
