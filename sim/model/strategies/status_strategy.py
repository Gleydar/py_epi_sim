import numpy as np
from controller.events import Events
from controller.scheduler import Scheduler
from model.agent import Agent
from model.agent_state import AgentState
from model.environmentmetric import EnvironmentMetric
from model.grid_pos import GridPos
from model.state import SimState


class StatusStrategy:
    state = AgentState.EMPTY
    """Basic 'interface' class for all status change strategies
     Author: Konstantin Schlosser"""

    def execute(self, agent: Agent, state: SimState) -> None:
        """
        Executes the status change.
        :param agent: Agent whose status is to be changed
        :param state: Status or current setting of the application. Whether and which status change is made depends on this object.
        :return: Nothing
        """
        pass


class DefaultInfectionStrategy(StatusStrategy):
    """Default Strategy for infecting agents.
    Autor: Andreas Stiglmeier, Benedikt Beil, Konstantin Schlosser"""

    def execute(self, agent: Agent, state: SimState) -> None:
        if agent.is_quarantined():
            return

        if agent.state() is AgentState.INFECTIVE or AgentState.INCUBATION:
            infection_radius = state.infection_env_radius()
            infection_env_size = infection_radius * 2 + 1
            size = agent.grid().get_size()
            check_list = list()
            grid_pos = agent.get_pos()
            x = grid_pos.row()
            y = grid_pos.col()

            if state.infection_env_metric() == EnvironmentMetric.MANHATTAN:
                for r in range(0, infection_env_size):
                    offset = abs(infection_radius - r)
                    check_row = y - infection_radius + r
                    for c in range(offset, infection_env_size - offset):
                        check_column = x - infection_radius + c
                        check_list.append((check_column, check_row))

            elif state.infection_env_metric() == EnvironmentMetric.EUCLIDEAN:
                for r in range(0, infection_env_size):
                    check_row = y - infection_radius + r
                    for c in range(0, infection_env_size):
                        check_column = x - infection_radius + c
                        distance = np.round(np.sqrt((infection_radius - r) ** 2 + (infection_radius - c) ** 2))
                        if 0 < distance <= infection_radius:
                            check_list.append((check_column, check_row))

            else:
                raise ValueError('Metric not implemented')

            check_list = list(filter(lambda pos: 0 <= pos[0] < size and 0 <= pos[1] < size, check_list))

            for check_pos in check_list:
                to_check = agent.grid().get_agent(GridPos(np.uint(check_pos[0]), np.uint(check_pos[1])))
                if to_check is not None and to_check.state() is AgentState.SUSCEPTIBLE:
                    if np.random.random() < state.infection_prob():
                        if state.incubation_period_enabled():
                            to_check.set_state(AgentState.INCUBATION)
                        else:
                            to_check.set_state(AgentState.INFECTIVE)
                        agent.update_infected_count()


class DefaultRemoveStrategy(StatusStrategy):
    """Default Strategy for removing agents.
    Autor: Andreas Stiglmeier, Benedikt Beil, Konstantin Schlosser"""

    def execute(self, agent: Agent, state: SimState) -> None:
        if agent.state() is not AgentState.INFECTIVE:
            return

        if np.random.random() < state.remove_prob():
            agent.set_state(AgentState.REMOVED)
        else:
            agent.update_sick_days()


class LethalityStatusStrategy(StatusStrategy):
    """Strategy that calculates the probability that the agents either die or become immune instead of being removed.
    Author: Konstantin Schlosser"""

    def execute(self, agent: Agent, state: SimState) -> None:
        """Basically the same method as in the DefaultStatusStrategy, but adding the lethality check.
        :param agent Agent to update
        :param state State the simulation is in"""
        if agent.state() is not AgentState.INFECTIVE:
            return

        if np.random.random() < state.remove_prob():
            if np.random.random() < state.lethality():
                agent.set_state(AgentState.DEAD)
            else:
                agent.set_state(AgentState.IMMUNE)
        else:
            agent.update_sick_days()


class VaccineStatusStrategy(StatusStrategy):
    """Strategy that vaccinates agents after a configurable amount of time.
    Author: Konstantin Schlosser, Benjamin Eder"""
    days = 0

    def execute(self, agent: Agent, state: SimState) -> None:
        """Updates the agents 'vaccine' before executing other checks"""
        if agent.state() == AgentState.SUSCEPTIBLE and self.days == state.vaccine_time() \
                and np.random.random() < state.vaccine_share():
            agent.set_state(AgentState.IMMUNE)

    def __next_step(self, state) -> None:
        """Event handler to count up the number of days
        :param state Ignored"""
        self.days += 1

    def __reset(self, state) -> None:
        self.days = 0

    def __delete__(self, instance):
        from controller.provider import active_provider
        active_provider.get_scheduler().get_observable().off(Events.NEXT_STEP.value, self.__next_step)
        active_provider.get_scheduler().get_observable().off(Events.RESET.value, self.__reset)

    def __init__(self, scheduler: Scheduler):
        scheduler.register_handler(Events.PRE_NEXT_STEP, self.__next_step)
        scheduler.register_handler(Events.RESET, self.__reset)
        super().__init__()


class IncubationStatusStrategy(DefaultInfectionStrategy):
    """Strategy, which sets an agent infective after a configurable amount of time
    Author: Konstantin Schlosser, Beil Benedikt"""

    def execute(self, agent: Agent, state: SimState) -> None:
        if agent.state() is not AgentState.INCUBATION:
            return

        if agent.incubation_days() is state.incubation_period():
            agent.set_state(AgentState.INFECTIVE)
        else:
            agent.update_incubation_days()


class QuarantineStatusStrategy(StatusStrategy):
    """Strategy that isolates a given share of infected people once they get infected
    Author: Andreas Stiglmeier"""

    def execute(self, agent: Agent, state: SimState) -> None:
        """
        Isolate (Remove from Grid) a given share of infected people for the sickness-duration.
        Afterwards they need to be added again to the Grid as removed/dead/immune.
        """
        if agent.is_quarantined():
            if agent.state() is AgentState.DEAD or agent.state() is AgentState.IMMUNE or agent.state() is AgentState.REMOVED:

                grid = agent.grid()
                for row in range(grid.get_size()):
                    for col in range(grid.get_size()):
                        grid_pos = GridPos(np.uint(row), np.uint(col))
                        if not grid.is_occupied(grid_pos):
                            grid.set_agent(agent, grid_pos)
                            agent.set_pos(grid_pos)
                            agent.set_quarantined(False)
                            agent.grid().get_quarantinedAgents().remove(agent)
                            state.add_to_quarantined_count(-1)
                            return

        else:
            isolate_share = state.quarantine_share()  # Share of infected cells to isolate
            infected = state.infected_count()

            if agent.state() == AgentState.INFECTIVE and state.get_quarantined_count() < isolate_share * (
                    infected + state.get_quarantined_count()):
                agent.set_quarantined(True)
                agent.grid().get_quarantinedAgents().append(agent)
                agent.grid().set_agent(None, agent.get_pos())
                agent.get_scheduler().update_gui_state(agent.get_pos(), AgentState.EMPTY)
                state.add_to_quarantined_count(1)

    def __reset(self, state) -> None:
        isolated_count = 0

    def __delete__(self, instance):
        from controller.provider import active_provider
        active_provider.get_scheduler().get_observable().off(Events.RESET.value, self.__reset)

    def __init__(self, scheduler: Scheduler):
        scheduler.register_handler(Events.RESET, self.__reset)
        super().__init__()
