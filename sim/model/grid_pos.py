from numpy import uint


class GridPos:
    """
    Author: Beil Benedikt
    """

    def __init__(self, row: uint, col: uint):
        self.__row = row
        self.__col = col

    def row(self) -> uint:
        return self.__row

    def col(self) -> uint:
        return self.__col
