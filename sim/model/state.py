import numpy as np
from model.agent_state import AgentState
from model.environmentmetric import EnvironmentMetric

"""
AUTHOR: Benjamin Eder, Konstantin Schlosser
"""


class SimState:
    """State of the simulator"""

    __size = np.uint(0)
    __susceptible_share = 0
    __infected_share = 0
    __infection_prob = 0
    __remove_prob = 0
    __infection_env_radius = 1
    __infection_env_metric = EnvironmentMetric.MANHATTAN
    __speed = 500
    __mixing_value_m = 1.0
    __infected_count = 0
    __susceptible_count = 0
    __removed_count = 0
    __immune_count = 0
    __dead_count = 0
    __incubation_count = 0
    __calculate_real_effective_reproduction_number = True
    __lethality = 0
    __lethality_toggle = False
    __vaccine_time = 50
    __vaccine_share = 0.5
    __vaccine_toggle = False
    __movement_limit_enabled = False
    __movement_limit_high_distances_are_uncommon = False
    __movement_limit_radius = 3
    __movement_limit_metric = EnvironmentMetric.EUCLIDEAN
    __incubation_period_enabled = False
    __incubation_period = 5
    __quarantine_enabled = False
    __quarantine_share = 0.5
    __quarantined_count = 0
    __beginningTotalCount = 0

    def __init__(
            self,
            size=np.uint(100),
            susceptible_share=0.69,
            infected_share=0.01,
            infection_prob=0.2,
            remove_prob=0.6,
            lethality=0.03,
    ):
        self.__data = None
        self.__seed = None
        self.seed()

        self.set_size(size)
        self.set_susceptible_share(susceptible_share)
        self.set_infected_share(infected_share)
        self.set_infection_prob(infection_prob)
        self.set_remove_prob(remove_prob)
        self.set_lethality(lethality)

        self.reset()

    def get_quarantined_count(self) -> int:
        return self.__quarantined_count

    def add_to_quarantined_count(self, count):
        self.__quarantined_count += count

    def get_total_count(self) -> int:
        return self.__immune_count + self.__infected_count + self.__removed_count + self.__susceptible_count + self.__dead_count

    def get_beginning_total_count(self) -> int:
        return self.__beginningTotalCount

    def set_beginning_total_count(self, count: int) -> None:
        self.__beginningTotalCount = count

    def quarantine_enabled(self) -> bool:
        return self.__quarantine_enabled

    def set_quarantine_enabled(self, value: bool) -> None:
        self.__quarantine_enabled = value

    def quarantine_share(self) -> float:
        """Share [0.0; 1.0] of infected people that are isolated (in quarantine)"""
        return self.__quarantine_share

    def set_quarantine_share(self, value: float) -> None:
        self.__quarantine_share = value

    def incubation_period_enabled(self) -> bool:
        return self.__incubation_period_enabled

    def set_incubation_period_enabled(self, value: bool) -> None:
        self.__incubation_period_enabled = value

    def incubation_period(self) -> int:
        return self.__incubation_period

    def set_incubation_period(self, value: int) -> None:
        self.__incubation_period = value

    def movement_limit_enabled(self) -> bool:
        return self.__movement_limit_enabled

    def set_movement_limit_enabled(self, value: bool) -> None:
        self.__movement_limit_enabled = value

    def movement_limit_high_distances_are_uncommon(self) -> bool:
        return self.__movement_limit_high_distances_are_uncommon

    def set_movement_limit_high_distances_are_uncommon(self, value: bool) -> None:
        self.__movement_limit_high_distances_are_uncommon = value

    def movement_limit_radius(self) -> int:
        return self.__movement_limit_radius

    def set_movement_limit_radius(self, value: int) -> None:
        self.__movement_limit_radius = value

    def movement_limit_metric(self) -> EnvironmentMetric:
        return self.__movement_limit_metric

    def set_movement_limit_metric(self, value: EnvironmentMetric) -> None:
        self.__movement_limit_metric = value

    def calculate_real_effective_reproduction_number(self) -> bool:
        return self.__calculate_real_effective_reproduction_number

    def set_calculate_real_effective_reproduction_number(self, value: bool) -> None:
        self.__calculate_real_effective_reproduction_number = value

    def susceptible_count(self) -> int:
        return self.__susceptible_count

    def infected_count(self) -> int:
        return self.__infected_count

    def removed_count(self) -> int:
        return self.__removed_count

    def immune_count(self) -> int:
        return self.__immune_count

    def dead_count(self) -> int:
        return self.__dead_count

    def incubation_count(self) -> int:
        return self.__incubation_count

    def lethality_toggle(self) -> bool:
        return self.__lethality_toggle

    def set_lethality_toggle(self, lethality: bool) -> None:
        self.__lethality_toggle = lethality

    def vaccine_toggle(self) -> bool:
        return self.__vaccine_toggle

    def set_vaccine_toggle(self, value: bool) -> None:
        self.__vaccine_toggle = value

    def vaccine_time(self) -> int:
        return self.__vaccine_time

    def set_vaccine_time(self, time: int) -> None:
        self.__vaccine_time = time

    def vaccine_share(self) -> float:
        return self.__vaccine_share

    def set_vaccine_share(self, share: float) -> None:
        self.__vaccine_share = share

    def speed(self) -> int:
        """Get the ms per second to simulate with"""
        return self.__speed

    def set_speed(self, value: int) -> None:
        self.__speed = value

    def infection_env_radius(self) -> int:
        """Get the radius of the infection environment"""
        return self.__infection_env_radius

    def set_infection_env_radius(self, value: int = 1) -> None:
        self.__infection_env_radius = value

    def infection_env_metric(self) -> EnvironmentMetric:
        """Get the infection environment metric to use"""
        return self.__infection_env_metric

    def set_lethality(self, lethality: float) -> None:
        """Returns the currently active chance to die of the infection"""
        self.__lethality = lethality

    def lethality(self) -> float:
        """Returns the currently active chance to die of the infection"""
        return self.__lethality

    def set_infection_env_metric(self, value: EnvironmentMetric = EnvironmentMetric.MANHATTAN) -> None:
        self.__infection_env_metric = value

    def seed(self, seed: int = None) -> None:
        """Seed the random number generator used by this class"""
        if seed is None:
            seed = np.random.randint(999999999)  # Select random seed

        self.__seed = seed

    def get_seed(self) -> int:
        return self.__seed

    def get_mixing_value_m(self) -> float:
        return self.__mixing_value_m

    def set_mixing_value_m(self, value: float) -> None:
        self.__mixing_value_m = value

    def data(self) -> np.ndarray:
        """Image data used in the state visualization"""
        return self.__data

    def size(self) -> np.uint:
        """Current size (rows and columns) of the data matrix"""
        return self.__size

    def set_size(self, value: np.uint) -> None:
        if value < 1:
            raise ValueError('Size must be at least 1. Transferred size is {}'.format(value))
        self.__size = value
        self.__data = np.zeros((value, value))

    def infection_prob(self) -> float:
        """Probability for infected cells to infect nearby susceptible cells"""
        return self.__infection_prob

    def set_infection_prob(self, value: float) -> None:
        self.__infection_prob = value

    def remove_prob(self) -> float:
        """Probability for infected cells to either die or get immune"""
        return self.__remove_prob

    def set_remove_prob(self, value: float) -> None:
        self.__remove_prob = value

    def __check_shares_valid(self) -> None:
        share_sum = self.susceptible_share() + self.infected_share()
        if share_sum > 1.0:
            raise ValueError(
                'Shares must be lower or equal to 1.0. susceptible_share={} + infected_share={} = {}'.format(
                    self.susceptible_share(), self.infected_share(), share_sum))

    def susceptible_share(self) -> float:
        """Share of all cells which will be set to susceptible in the beginning of the simulation"""
        return self.__susceptible_share

    def set_susceptible_share(self, share: float = 0.69) -> None:
        if share < 0.0 or share > 1.0:
            raise ValueError('Susceptible share must be in range [0.0; 1.0], value was {}'.format(share))
        self.__check_shares_valid()

        self.__susceptible_share = share

    def infected_share(self) -> float:
        """Share of all cells which will be set to infected in the beginning of the simulation"""
        return self.__infected_share

    def set_infected_share(self, share: float = 0.69) -> None:
        if share < 0.0 or share > 1.0:
            raise ValueError('Susceptible share must be in range [0.0; 1.0], value was {}'.format(share))
        self.__check_shares_valid()

        self.__infected_share = share

    def agent_update(self, row: int, col: int, state: int) -> None:
        cur_state = self.__data[row][col]

        if state == AgentState.DEAD.value or cur_state == AgentState.DEAD.value:
            if state == AgentState.DEAD.value and cur_state != AgentState.DEAD.value:
                self.__dead_count += 1
            elif state != AgentState.DEAD.value and cur_state == AgentState.DEAD.value:
                self.__dead_count -= 1

        if state == AgentState.IMMUNE.value or cur_state == AgentState.IMMUNE.value:
            if state == AgentState.IMMUNE.value and cur_state != AgentState.IMMUNE.value:
                self.__immune_count += 1
            elif state != AgentState.IMMUNE.value and cur_state == AgentState.IMMUNE.value:
                self.__immune_count -= 1

        if state == AgentState.REMOVED.value or cur_state == AgentState.REMOVED.value:
            if state == AgentState.REMOVED.value and cur_state != AgentState.REMOVED.value:
                self.__removed_count += 1
            elif state != AgentState.REMOVED.value and cur_state == AgentState.REMOVED.value:
                self.__removed_count -= 1

        if state == AgentState.SUSCEPTIBLE.value or cur_state == AgentState.SUSCEPTIBLE.value:
            if state == AgentState.SUSCEPTIBLE.value and cur_state != AgentState.SUSCEPTIBLE.value:
                self.__susceptible_count += 1
            elif state != AgentState.SUSCEPTIBLE.value and cur_state == AgentState.SUSCEPTIBLE.value:
                self.__susceptible_count -= 1

        if state == AgentState.INFECTIVE.value or cur_state == AgentState.INFECTIVE.value:
            if state == AgentState.INFECTIVE.value and cur_state != AgentState.INFECTIVE.value:
                self.__infected_count += 1
            elif state != AgentState.INFECTIVE.value and cur_state == AgentState.INFECTIVE.value:
                self.__infected_count -= 1

        if state == AgentState.INCUBATION.value or cur_state == AgentState.INCUBATION.value:
            if state == AgentState.INCUBATION.value and cur_state != AgentState.INCUBATION.value:
                self.__incubation_count += 1
            elif state != AgentState.INCUBATION.value and cur_state == AgentState.INCUBATION.value:
                self.__incubation_count -= 1

        self.__data[row][col] = state

    def reset(self) -> None:
        self.__infected_count = 0
        self.__susceptible_count = 0
        self.__removed_count = 0
        self.__dead_count = 0
        self.__immune_count = 0
        self.__incubation_count = 0
        self.__data = np.zeros((self.size(), self.size()))
