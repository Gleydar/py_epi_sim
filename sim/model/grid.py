import logging
import time

import numpy as np
from numpy import uint

from controller.events import Events
from controller.scheduler import Scheduler
from model.agent import Agent
from model.agent_state import AgentState
from model.grid_pos import GridPos
from model.state import SimState


class Grid:
    """Class representing the grid on which the agents move
    Author: Konstantin Schlosser, Andreas Stiglmeier"""

    def get_agent(self, grid_pos: GridPos) -> Agent:
        return self.__grid[grid_pos.row()][grid_pos.col()]

    def is_occupied(self, grid_pos: GridPos) -> bool:
        """
        Edited by Benedikt Beil
        :param grid_pos:
        :return: Whether the field is occupied.
        """
        if self.get_agent(grid_pos) is None:
            return False

        if self.get_agent(grid_pos).state() == AgentState.EMPTY:
            return False
        return True

    def is_fully_occupied(self) -> bool:
        """
        Author: Beil Benedikt
        :return: Whether the whole grid is occupied
        """
        for i in range(self.get_size()):
            for j in range(self.get_size()):
                if not self.is_occupied(GridPos(uint(i), uint(j))):
                    return False
        return True

    def set_agent(self, agent: Agent, grid_pos: GridPos) -> None:
        self.__grid[grid_pos.row()][grid_pos.col()] = agent

    def move_agent(self, old_pos: GridPos, new_pos: GridPos) -> None:
        if self.is_fully_occupied():
            self.__logger.error("All fields are occupied.")
            raise Exception("All fields are occupied. No agent can move.")

        if self.is_occupied(new_pos):
            self.__logger.error("The field is already occupied.")
            raise Exception("The field is already occupied.")

        copy = self.get_agent(new_pos)
        agent = self.get_agent(old_pos)
        self.set_agent(agent, new_pos)
        self.set_agent(copy, old_pos)
        if copy is not None:
            copy.set_pos(old_pos)
        else:
            self.__scheduler.update_gui_state(old_pos, AgentState.EMPTY)
        agent.set_pos(new_pos)

    def get_size(self) -> int:
        return len(self.__grid[0])

    def get_quarantinedAgents(self):
        return self._quarantined_agents

    def init_listeners(self) -> None:
        self.__scheduler.register_handler(Events.AGENT_MOVEMENT, self.on_move_update)
        self.__scheduler.register_handler(Events.STATUS_UPDATE, self.on_status_update)

    def remove_listeners(self) -> None:
        if self.__scheduler.get_observable().is_registered(Events.AGENT_MOVEMENT.value, self.on_move_update):
            self.__scheduler.get_observable().off(Events.AGENT_MOVEMENT.value, self.on_move_update)
        if self.__scheduler.get_observable().is_registered(Events.STATUS_UPDATE.value, self.on_status_update):
            self.__scheduler.get_observable().off(Events.STATUS_UPDATE.value, self.on_status_update)

    def exec_for_agents_in_rand_order(self, exec) -> None:
        """Executes the updates in a random order for all agents.
        Author: Benjamin Eder"""
        if self.__grid is None:
            return

        agents = [None] * (self.get_size() ** 2)

        a = 0
        for i in range(self.get_size()):
            for j in range(self.get_size()):
                agents[a] = self.__grid[i][j]
                a += 1

        for i in self.rs.choice(len(agents), len(agents), replace=False):
            agent = agents[i]
            if agent is not None:
                exec(agent)

    def on_move_update(self, state: SimState) -> None:
        from controller.provider import active_provider

        t1 = time.time_ns()
        self.exec_for_agents_in_rand_order(
            lambda agent: active_provider.get_movement_strategy().move_agent(agent, state))
        t2 = time.time_ns()
        self.__logger.info(f'Movement update took {(t2 - t1) / 1000 / 1000}ms')

    def on_status_update(self, state: SimState) -> None:
        from controller.provider import active_provider
        strategies = active_provider.get_status_strategies()
        filtered = dict()
        for key in strategies:
            strat = strategies[key]
            filtered[key] = list(filter(lambda item: item[1](state), strat))

        def execute_all(agent: Agent):
            try:
                func_list = filtered[agent.state()]
                for func in func_list:
                    func[0].execute(agent, state)
            except KeyError:
                pass
        self.exec_for_agents_in_rand_order(execute_all)
        for agent in self._quarantined_agents:
            execute_all(agent)

    def init_empty_grid(self, width: uint, length: uint) -> None:
        """
        Author: Beil Benedikt
        :param width:
        :param length:
        :return:
        """
        self.__grid = None
        self.__grid = [[None for j in range(width)] for i in range(length)]

    def spawn_agent(self, grid_pos: GridPos, agent_state: AgentState) -> None:
        """
        Create an agent with the status at the position, if it is not already occupied.
        Author: Beil Benedikt
        :param grid_pos:
        :param agent_state:
        :return: Nothing
        """
        if self.is_occupied(grid_pos):
            raise ValueError("This field is already occupied. No agent can be created here. ")
        self.set_agent(Agent(self.__scheduler, grid_pos, agent_state, self), grid_pos)

    def place_agents_on_the_field(self, width: uint, length: uint, seed: int, susceptible_share: float,
                                  infected_share: float):
        """Inital placements of agents on the field.
        Author: Benjamin Eder, Konstantin Schlosser"""
        if self.__grid is None:
            self.init_empty_grid(width, length)
        np.random.seed(seed)
        self.rs = np.random.RandomState(
            np.random._mt19937.MT19937(np.random._bit_generator.SeedSequence(seed)))

        total_num_of_fields = width * length

        # Fill shares randomly in the underlying data
        choice = self.rs.choice(
            total_num_of_fields,
            int(np.round((susceptible_share + infected_share) * total_num_of_fields)),
            replace=False
        )
        susceptible_count = int(round(susceptible_share * total_num_of_fields))

        for i in choice[:susceptible_count]:
            row = uint(i // width)
            col = uint(i % length)
            self.spawn_agent(GridPos(row, col), AgentState.SUSCEPTIBLE)

        for i in choice[susceptible_count:]:
            row = uint(i // width)
            col = uint(i % length)
            self.spawn_agent(GridPos(row, col), AgentState.INFECTIVE)

    def reset(self, state: SimState) -> None:
        self.place_agents_on_the_field(state.size(), state.size(), state.get_seed(), state.susceptible_share(),
                                       state.infected_share())

    def __init__(self, scheduler: Scheduler):
        self.__id = np.random.randint(0, 10000)
        self.__scheduler = scheduler
        self.__logger = logging.getLogger("grid")
        self.init_listeners()
        self.__grid = None
        self._quarantined_agents = []
