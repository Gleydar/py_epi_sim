from observable import Observable, EventNotFound, HandlerNotFound
from controller.events import Events
from model.agent_state import AgentState
from model.state import SimState
from model.grid_pos import GridPos
import logging
import sys
import typing
import config as cfg


class Scheduler:
    main_observable: Observable = Observable()
    gui_observable: Observable = Observable()
    __logger = logging.getLogger("scheduler")

    """Scheduler class controlling the flow of the program
    Author: Konstantin Schlosser
    Events:
    - next_step: triggered by gui, initial event for all computation
    - agent_movement: triggered by scheduler, agents move
    - status_update: triggered by scheduler, agents update their status according to the neighbors
    - ... tba
    - repaint: last event for the chain, triggers gui repaint"""

    def update_gui_state(self, grid_pos: GridPos, agent_state: AgentState) -> None:
        self.trigger_gui_event(Events.AGENT_CHANGE_GUI,
                               {"row": grid_pos.row(), "col": grid_pos.col(), "state": agent_state.value})
        self.__logger.debug(f"Agent update, at position {grid_pos.row()},{grid_pos.col()}, new state: {agent_state}")

    def trigger_event(self, event: Events, kw: typing.Any = {}) -> None:
        try:
            self.main_observable.trigger(event.value, **kw)
        except HandlerNotFound as ex:
            self.trigger_event(Events.ERROR, {"message": ex})

    def trigger_gui_event(self, event: Events, kw: typing.Any = {}) -> None:
        try:
            self.gui_observable.trigger(event.value, **kw)
        except HandlerNotFound as ex:
            self.trigger_event(Events.ERROR, {"message": ex})

    def register_handler(self, event: Events, handlers: typing.Callable) -> None:
        try:
            self.main_observable.on(event.value, handlers)
        except EventNotFound as ex:
            self.trigger_event(Events.ERROR, {"message": ex})

    def register_gui_handler(self, event: Events, handlers: typing.Callable) -> None:
        try:
            self.gui_observable.on(event.value, handlers)
        except EventNotFound as ex:
            self.trigger_event(Events.ERROR, {"message": ex})

    def __error_handler(self, message) -> None:
        self.__logger.error(f"An error occurred: {message}")

    def __reset(self, **kw: typing.Any) -> None:
        self.__logger.info("Simulation was reset, propagating to main observable...")
        self.trigger_event(Events.RESET, kw)
        self.__logger.info("Finished creation, sending repaint...")
        self.trigger_gui_event(Events.REPAINT)

    def __next_gui_step(self, state: SimState) -> None:
        self.__logger.info("Next step triggered from gui, pre processing next step")
        self.trigger_event(Events.PRE_NEXT_STEP, {"state": state})
        self.__logger.info("Triggering next step")
        self.trigger_event(Events.NEXT_STEP, {"state": state})

    def __next_step(self, state: SimState) -> None:
        self.__logger.info("Next step triggered, starting agent movement")
        self.trigger_event(Events.AGENT_MOVEMENT, {"state": state})
        self.__logger.info("Agent movement finished, starting status update")
        self.trigger_event(Events.STATUS_UPDATE, {"state": state})
        self.__logger.info("Status update finished, starting additional events")
        self.__logger.info("Additional events finished. Starting repaint")
        self.trigger_gui_event(Events.REPAINT)

    def __initialize(self) -> None:
        self.__logger.info("Initializing new simulation...")

    def __init__(self):
        self.register_handler(Events.ERROR, self.__error_handler)
        self.register_handler(Events.NEXT_STEP, self.__next_step)
        self.register_gui_handler(Events.NEXT_STEP, self.__next_gui_step)
        self.register_gui_handler(Events.RESET, self.__reset)

    def get_observable(self) -> Observable:
        return self.main_observable


logging.basicConfig(stream=sys.stdout, level=cfg.DEFAULT_LOG_LEVEL)
