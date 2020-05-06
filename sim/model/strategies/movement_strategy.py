import random
import numpy as np
from scipy.stats import norm
from model.agent import Agent
from model.agent_state import AgentState
from model.environmentmetric import EnvironmentMetric
from model.state import SimState
from model.grid_pos import GridPos


class MovementStrategy:
    """Basic 'interface' for movement of agents.
     Author: Konstantin Schlosser"""

    def move_agent(self, agent: Agent, state: SimState):
        """Moves a specified agent according to the current implementation.
        :param agent: Agent to move
        :param state: Current simulation state & parameters"""
        pass

    def __init__(self):
        pass


def get_free_pos(grid) -> GridPos:
    """
    Returns a free position on the field, if there is one.
    Author: Beil Benedikt
    :param grid: Field, where a free position is to be searched.
    :return: A free prosition on the field, if there is one.
    """
    if grid.is_fully_occupied():
        raise Exception("The field is completely occupied. The agent cannot move. ")

    rand_x = np.uint(np.random.randint(low=0, high=grid.get_size()))
    rand_y = np.uint(np.random.randint(low=0, high=grid.get_size()))
    while grid.is_occupied(GridPos(rand_x, rand_y)):
        rand_x = np.uint(np.random.randint(low=0, high=grid.get_size()))
        rand_y = np.uint(np.random.randint(low=0, high=grid.get_size()))

    return GridPos(rand_x, rand_y)


def get_free_pos_limited(
        grid,
        pos: GridPos,
        radius: int = 1,
        metric: EnvironmentMetric = EnvironmentMetric.EUCLIDEAN,
) -> GridPos:
    """
    Get a free position on the grid only [radius] from the passed position.
    Autor: Benjamin Eder
    :param grid:
    :param pos:
    :param radius:
    :param metric:
    :return:
    """
    possible_positions = []

    env_size = radius * 2 + 1

    grid_size = grid.get_size()

    cur_row = int(pos.row())
    cur_col = int(pos.col())

    if metric == EnvironmentMetric.MANHATTAN:
        for r in range(0, env_size):
            offset = abs(radius - r)
            check_row = cur_row - radius + r
            for c in range(offset, env_size - offset):
                check_column = cur_col - radius + c
                possible_positions.append((check_row, check_column))
    elif metric == EnvironmentMetric.EUCLIDEAN:
        for r in range(0, env_size):
            check_row = cur_row - radius + r
            for c in range(0, env_size):
                check_column = cur_col - radius + c
                distance = np.round(np.sqrt((radius - r) ** 2 + (radius - c) ** 2))
                if 0 < distance <= radius:
                    possible_positions.append((check_row, check_column))
    else:
        raise ValueError('Metric not implemented')

    # Filter positions that are no more in the Grid or are already used
    possible_positions = list(
        filter(
            lambda pos: 0 <= pos[0] < grid_size and 0 <= pos[1] < grid_size
                        and (pos[0] != cur_row or pos[1] != cur_col)
                        and not grid.is_occupied(GridPos(np.uint(pos[0]), np.uint(pos[1]))),
            possible_positions
        )
    )

    if len(possible_positions) == 0:
        raise ValueError("No free positions available. ")

    random_choice = random.choice(possible_positions)
    return GridPos(np.uint(random_choice[0]), np.uint(random_choice[1]))


class DefaultMovementStrategy(MovementStrategy):
    """Current default strategy for movement. Long range movement only to free spaces.
    Author: Andreas Stiglmeier, Benedikt Beil, Konstantin Schlosser, Benjamin Eder"""

    def move_agent(self, agent: Agent, state: SimState) -> None:
        grid = agent.grid()
        if grid.is_fully_occupied():
            return

        if agent.state() is AgentState.DEAD or agent.is_quarantined():
            return  # We don't want zombies

        move_probability = np.random.randint(low=0, high=100)
        if move_probability <= state.get_mixing_value_m() * 100:
            new_grid_pos = get_free_pos(grid)
            old_grid_pos = agent.get_pos()
            grid.move_agent(old_grid_pos, new_grid_pos)


class LimitedMovementStrategy(MovementStrategy):
    """
    Limited movement strategy
    Author: Benjamin Eder
    """

    def move_agent(self, agent: Agent, state: SimState) -> None:
        grid = agent.grid()
        if grid.is_fully_occupied():
            return

        if agent.state() is AgentState.DEAD or agent.is_quarantined():
            return  # We don't want zombies

        move_probability = np.random.randint(low=0, high=100)
        if move_probability <= state.get_mixing_value_m() * 100:
            radius = state.movement_limit_radius()

            if state.movement_limit_high_distances_are_uncommon():
                # Recalculate radius -> lower radius is more probable
                mean = 0
                standard_deviation = radius / 3

                radius = min(max(1, int(
                    np.round(np.abs(norm.rvs(size=1, loc=mean, scale=standard_deviation)[0]))
                )), radius)

            try:
                new_grid_pos = get_free_pos_limited(
                    grid,
                    pos=agent.get_pos(),
                    radius=radius,
                    metric=state.movement_limit_metric(),
                )
                old_grid_pos = agent.get_pos()
                grid.move_agent(old_grid_pos, new_grid_pos)
            finally:
                return
