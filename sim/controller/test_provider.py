from unittest import TestCase
from observable import Observable
from controller.provider import Provider
from controller.scheduler import Scheduler
from model.grid import Grid


class TestProvider(TestCase):
    """
    Author: Beil Benedikt
    """

    def test_get_grid(self):
        sut = self.__create_sut()
        self.assertIs(sut.get_grid(), None)

        grid = Grid(Scheduler())
        sut.set_grid(grid)
        self.assertIs(sut.get_grid(), grid)

    def test_get_scheduler(self):
        sut = self.__create_sut()
        self.assertIsInstance(sut.get_scheduler(), Scheduler)

    def test_get_observable(self):
        sut = self.__create_sut()
        self.assertIsInstance(sut.get_observable(), Observable)

    def __create_sut(self):
        return Provider()
