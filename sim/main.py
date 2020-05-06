import config as cfg
from PyQt5 import QtWidgets, QtCore
from model.state import SimState
from ui.ui import SimUi

"""
AUTHOR: Benjamin Eder
"""

# Initialize state
state = SimState(
    size=cfg.DEFAULT_SIZE,
    susceptible_share=cfg.DEFAULT_SUSCEPTIBLE_SHARE,
    infected_share=cfg.DEFAULT_INFECTED_SHARE,
    infection_prob=cfg.DEFAULT_INFECTION_PROB,
    remove_prob=cfg.DEFAULT_REMOVE_PROB
)

ui = SimUi(state)
ui.win.show()

# Start Qt event loop unless running in interactive mode
if __name__ == '__main__':
    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
