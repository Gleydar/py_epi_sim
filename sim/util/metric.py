import numpy as np

from model.agent_state import AgentState
from model.environmentmetric import EnvironmentMetric
from model.grid import Grid
from model.grid_pos import GridPos

"""
AUTHOR: Benjamin Eder
"""


def calc_effective_reproduction_number(
        grid: Grid,
        remove_probability=0.6,
        infection_probability=0.2,
        infection_radius=1,
        infection_metric=EnvironmentMetric.MANHATTAN
) -> float:
    """
    Calculate the effective reproduction number R
    """

    mean_infection_duration = 1 / remove_probability

    size = grid.get_size()
    infection_env_size = infection_radius * 2 + 1

    # Find all infected cells
    infection_counts = []
    for row in range(size):
        for column in range(size):
            agent = grid.get_agent(GridPos(np.uint(row), np.uint(column)))
            if agent is not None and agent.state() is AgentState.INFECTIVE:
                # Is an infected cell -> Count number of infectable (susceptible) cells in the near environment
                infectable_count = 0

                if infection_metric == EnvironmentMetric.MANHATTAN:
                    for r in range(0, infection_env_size):
                        offset = abs(infection_radius - r)
                        check_row = row - infection_radius + r
                        for c in range(offset, infection_env_size - offset):
                            check_column = column - infection_radius + c

                            if check_row < 0 or check_column < 0 or check_row >= size or check_column >= size:
                                continue

                            other_agent = grid.get_agent(GridPos(np.uint(check_row), np.uint(check_column)))
                            if other_agent is not None and other_agent.state() is AgentState.SUSCEPTIBLE:
                                infectable_count += 1
                elif infection_metric == EnvironmentMetric.EUCLIDEAN:
                    for r in range(0, infection_env_size):
                        check_row = row - infection_radius + r
                        for c in range(0, infection_env_size):
                            check_column = column - infection_radius + c

                            if check_row < 0 or check_column < 0 or check_row >= size or check_column >= size:
                                continue

                            distance = np.round(
                                np.sqrt((infection_radius - r) ** 2 + (infection_radius - c) ** 2))
                            if distance > 0 and distance <= infection_radius:
                                other_agent = grid.get_agent(GridPos(np.uint(check_row), np.uint(check_column)))
                                if other_agent is not None and other_agent.state() is AgentState.SUSCEPTIBLE:
                                    infectable_count += 1

                # Check how many people already have been infected by the person
                already_infected_count = agent.infected_count()

                # Check how many days the agent is already infected
                already_infected_time = agent.sick_days()

                # Estimate how many more days the agent will be infected
                infection_time_estimate = max(round(mean_infection_duration - already_infected_time), 1)  # The agent will live at least one more day

                # Estimate how many more people are going to be infected by that agent
                infection_estimate = infection_time_estimate * infectable_count * infection_probability

                # Sum up all the actual and estimated infection by that agent
                total_estimated_infections = already_infected_count + infection_estimate

                infection_counts.append(total_estimated_infections)

    return np.array(infection_counts).mean() if len(infection_counts) > 0 else 0


def estimate_effective_reproduction_number(susceptible_count: int, total_count: int, R0: float = 1.0) -> float:
    return R0 * (susceptible_count / total_count)
