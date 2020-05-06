from unittest import TestCase
from numpy import uint
from model.grid import Grid
from model.grid_pos import GridPos
from model.agent_state import AgentState
from controller.scheduler import Scheduler


class TestGrid(TestCase):
    """
    Author: Beil Benedikt
    """

    def test_is_fully_occupied_True(self):
        sut = self.__get_sut()
        sut.place_agents_on_the_field(uint(100), uint(100), 2523, 1, 0)
        self.assertTrue(sut.is_fully_occupied())

    def test_is_fully_occupied_False(self):
        sut = self.__get_sut()
        sut.place_agents_on_the_field(uint(10), uint(10), 325, 0.99, 0)
        self.assertFalse(sut.is_fully_occupied())

    def test_is_occupied(self):
        sut = self.__get_sut()
        sut.init_empty_grid(uint(100), uint(100))
        test_pos = GridPos(uint(0), uint(0))
        sut.spawn_agent(test_pos, AgentState.SUSCEPTIBLE)
        self.assertTrue(sut.is_occupied(test_pos))
        self.assertFalse(sut.is_occupied(GridPos(uint(0), uint(1))))
        self.assertFalse(sut.is_occupied(GridPos(uint(1), uint(0))))
        self.assertFalse(sut.is_occupied(GridPos(uint(1), uint(1))))
        self.assertFalse(sut.is_occupied(GridPos(uint(99), uint(99))))
        self.assertFalse(sut.is_occupied(GridPos(uint(99), uint(0))))
        self.assertFalse(sut.is_occupied(GridPos(uint(0), uint(99))))

    def __get_sut(self) -> Grid:
        return Grid(Scheduler())
