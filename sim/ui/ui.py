import json
import os
import threading
import time
import numpy as np
import config as cfg
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets, QtGui, QtSvg
from PyQt5.QtCore import QThreadPool, pyqtSignal
import controller.events
import controller.scheduler
from controller.provider import active_provider
from model.environmentmetric import EnvironmentMetric
from model.state import SimState
from model.strategies.movement_strategy import LimitedMovementStrategy, DefaultMovementStrategy
from model.worker import Worker
from ui.state_viz import SimStateViz

"""
AUTHOR: Benjamin Eder, Konstantin Schlosser (a bit ;))
"""


class SimUi(QtCore.QObject):
    """Entry point for the simulator UI"""

    __repaint_signal = pyqtSignal()

    def __init__(self, state: SimState):
        super().__init__()
        self.state = state
        self.__paused = True
        self.__numOfInfected = 10000
        self.threadpool = QThreadPool()
        self.__event_stop = threading.Event()
        self.__event_ready = threading.Event()

        self.app = QtWidgets.QApplication([])
        app_icon = QtGui.QIcon()
        app_icon.addFile('res/icon.ico')
        self.app.setWindowIcon(app_icon)

        win = QtWidgets.QMainWindow(flags=QtCore.Qt.WindowFlags())
        QtGui.QFontDatabase.addApplicationFont('res/Manrope.ttf')
        win.setStyleSheet(cfg.styleSheet)

        self.root_widget = QtWidgets.QWidget()
        self.root_layout = QtWidgets.QHBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_widget.setLayout(self.root_layout)

        win.setCentralWidget(self.root_widget)
        win.setWindowTitle('Epidemic Simulator')
        win.resize(1200, 800)
        self.win = win

        # PyQtGraph configuration
        pg.setConfigOptions(
            imageAxisOrder='row-major',  # Interpret image data as row-major instead of col-major
            foreground=cfg.FOREGROUND_COLOR,
            background=cfg.BACKGROUND_COLOR,
            antialias=True
        )

        self.__build_controls()
        self.__build_visualizations()
        self.__build_settings()

        active_provider.get_scheduler().register_gui_handler(controller.events.Events.REPAINT,
                                                             self.__after_step_completion)
        self.__repaint_signal.connect(self.__repaint_viz)
        active_provider.get_scheduler().register_gui_handler(controller.events.Events.AGENT_CHANGE_GUI,
                                                             self.state.agent_update)
        active_provider.get_scheduler().trigger_gui_event(controller.events.Events.RESET, kw={"state": self.state})

    def __after_step_completion(self) -> None:
        self.state_viz.calc_next_r()

        # Repaint
        self.__event_ready.clear()
        self.__repaint_signal.emit()
        self.__event_ready.wait()

    def __repaint_viz(self) -> None:
        self.state_viz.update()
        self.__event_ready.set()

    def __run(self) -> None:
        """
        Triggers the event for the next step as long as the simulaiton has not finished.
        Author: Beil Benedikt, Benjamin Eder
        :return: Nothing
        """
        while not self.__event_stop.is_set() and (
                self.state.infected_count() > 0 or self.state.get_total_count() < self.state.get_beginning_total_count()):
            start = time.time_ns()

            active_provider.get_scheduler().trigger_gui_event(controller.scheduler.Events.NEXT_STEP,
                                                              {"state": self.state})

            took = (time.time_ns() - start) // 1000000

            speed = self.state.speed()
            if speed > 0:
                to_wait = speed - took

                if to_wait < 0:
                    print('WARNING: Simulation is too busy, consider slowing down the speed!')
                else:
                    QtCore.QThread.msleep(to_wait)  # Wait for the calculated time

        if not self.__paused:
            self.__pause_simulation()

    def __build_visualizations(self) -> None:
        self.state_viz = SimStateViz(self.state)
        self.root_layout.addWidget(self.state_viz.view)

    def __build_controls(self) -> None:
        size_slider, size_slider_layout = self.__build_size_slider()

        susceptible_share_slider, susceptible_share_slider_layout = self.__build_susceptible_share_slider(
            lambda: infected_share_slider)
        infected_share_slider, infected_share_slider_layout = self.__build_infected_share_slider(
            lambda: susceptible_share_slider)

        infection_prob_slider, infection_prob_slider_layout = self.__build_infection_prob_slider()
        remove_prob_slider, remove_prob_slider_layout = self.__build_remove_prob_slider()

        reseed_btn, _, seed_input_field_layout = self.__build_seed_input()

        # Reset button
        reset_btn = QtWidgets.QPushButton('Reset')

        def reset_clicked() -> None:
            if not self.__paused:
                pause_simulation()

            self.state.set_size(cfg.DEFAULT_SIZE)
            size_slider.setValue(cfg.DEFAULT_SIZE)

            self.state.set_infected_share(0)  # Prevent errors due to shares being more than 1.0 in sum
            self.state.set_susceptible_share(cfg.DEFAULT_SUSCEPTIBLE_SHARE)
            susceptible_share_slider.setValue(round(self.state.susceptible_share() * 100))

            self.state.set_infected_share(cfg.DEFAULT_INFECTED_SHARE)
            infected_share_slider.setValue(round(self.state.infected_share() * 100))

            self.state.set_infection_prob(cfg.DEFAULT_INFECTION_PROB)
            infection_prob_slider.setValue(round(self.state.infection_prob() * 100))

            self.state.set_remove_prob(cfg.DEFAULT_REMOVE_PROB)
            remove_prob_slider.setValue(round(self.state.remove_prob() * 100))

            self.state.reset()
            active_provider.get_scheduler().trigger_gui_event(controller.events.Events.RESET, kw={"state": self.state})
            self.state_viz.reset()

        reset_btn.clicked.connect(reset_clicked)

        # Next button
        next_icon = QtGui.QIcon('res/next.png')
        next_btn = QtWidgets.QPushButton(icon=next_icon)
        next_btn.setObjectName('iconbutton')
        next_btn.setToolTip('Go to next simulation step manually')

        def next_clicked() -> None:
            active_provider.get_scheduler().trigger_gui_event(controller.scheduler.Events.NEXT_STEP,
                                                              {"state": self.state})

        next_btn.clicked.connect(next_clicked)

        # Play button
        play_icon = QtGui.QIcon('res/play_arrow.png')
        pause_icon = QtGui.QIcon('res/pause.png')
        play_pause_btn = QtWidgets.QPushButton(icon=play_icon)
        play_pause_btn.setObjectName('iconbutton')
        play_pause_btn.setToolTip('Play/Pause simulation')

        def play() -> None:
            play_pause_btn.setIcon(pause_icon)
            next_btn.setEnabled(False)
            size_slider.setEnabled(False)
            infected_share_slider.setEnabled(False)
            susceptible_share_slider.setEnabled(False)

            self.__paused = False

            if cfg.BATCH_RUN_ENABLED:
                # Prepare results file
                try:
                    os.remove(cfg.BATCH_RESULT_FILE)
                except OSError:
                    pass

                with open(cfg.BATCH_RESULT_FILE, 'a+') as results_file:
                    results_file.write(f"""{{
\t\"config\": {{
\t\t\"size\": {self.state.size()},
\t\t\"susceptible_share\": {self.state.susceptible_share()},
\t\t\"infected_share\": {self.state.infected_share()},
\t\t\"infection_probability\": {self.state.infection_prob()},
\t\t\"remove_probability\": {self.state.remove_prob()},
\t\t\"movement_mixing\": {self.state.get_mixing_value_m()},
\t\t\"infection_env_radius\": {self.state.infection_env_radius()},
\t\t\"infection_env_metric\": \"{self.state.infection_env_metric().value}\",
\t\t\"calc_real_effective_reproduction_rate\": {str(self.state.calculate_real_effective_reproduction_number()).lower()},
\t\t\"breakdown_dead_immune_enabled\": {str(self.state.lethality_toggle()).lower()},
\t\t\"lethality\": {self.state.lethality()},
\t\t\"vaccine_enabled\": {str(self.state.vaccine_toggle()).lower()},
\t\t\"vaccine_time\": {self.state.vaccine_time()},
\t\t\"vaccine_share\": {self.state.vaccine_share()},
\t\t\"movement_limit_enabled\": {str(self.state.movement_limit_enabled()).lower()},
\t\t\"movement_limit_radius\": {self.state.movement_limit_radius()},
\t\t\"movement_limit_metric\": \"{self.state.movement_limit_metric().value}\",
\t\t\"movement_limit_high_distances_are_uncommon\": {str(self.state.movement_limit_high_distances_are_uncommon()).lower()},
\t\t\"incubation_period_enabled\": {str(self.state.incubation_period_enabled()).lower()},
\t\t\"incubation_period\": {self.state.incubation_period()},
\t\t\"quarantine_enabled\": {str(self.state.quarantine_enabled()).lower()},
\t\t\"quarantine_share\": {self.state.quarantine_share()}
\t}},
\t\"runs\": [
""")

                    # Run a batch of simulations
                    for i in range(cfg.BATCH_RUN_ITERATIONS):
                        print(f'Running batch job {i + 1} of {cfg.BATCH_RUN_ITERATIONS}...')
                        while self.state.infected_count() > 0 or self.state.get_total_count() < self.state.get_beginning_total_count():
                            active_provider.get_scheduler().trigger_gui_event(controller.scheduler.Events.NEXT_STEP,
                                                                              {"state": self.state})

                        results_file.write(f"""\t\t{{
\t\t\t\"iteration\": {i + 1},
\t\t\t\"seed\": {self.state.get_seed()},
\t\t\t\"elapsed_days\": {self.state_viz.elapsed_days()},
\t\t\t\"effective_reproduction_rates\": {json.dumps(self.state_viz.r_values())},
\t\t\t\"estimated_effective_reproduction_rates\": {json.dumps(self.state_viz.r_estimate_values())},
\t\t\t\"susceptible_counts\": {json.dumps(self.state_viz.sus_counts())},
\t\t\t\"infected_counts\": {json.dumps(self.state_viz.inf_counts())},
\t\t\t\"removed_counts\": {json.dumps(self.state_viz.rem_counts())},
\t\t\t\"dead_counts\": {json.dumps(self.state_viz.ded_counts())},
\t\t\t\"immune_counts\": {json.dumps(self.state_viz.imm_counts())},
\t\t\t\"incubated_counts\": {json.dumps(self.state_viz.inc_counts())}
\t\t}}{',' if i < cfg.BATCH_RUN_ITERATIONS - 1 else ''}
""")

                        self.state.seed()  # Reseed simulation

                        self.state.reset()
                        active_provider.get_scheduler().trigger_gui_event(controller.events.Events.RESET,
                                                                          kw={"state": self.state})
                        self.state_viz.reset()

                    results_file.write(f"""\t]
}}
""")
            else:
                self.__event_stop.clear()
                worker = Worker(self.__run)
                self.threadpool.start(worker)

        def pause_simulation() -> None:
            play_pause_btn.setIcon(play_icon)
            next_btn.setEnabled(True)
            size_slider.setEnabled(True)
            infected_share_slider.setEnabled(True)
            susceptible_share_slider.setEnabled(True)

            self.__paused = True

            self.__event_stop.set()

        self.__pause_simulation = lambda: pause_simulation()

        def toggle_play_pause() -> None:
            if self.__paused:
                play()
            else:
                pause_simulation()

        play_pause_btn.clicked.connect(toggle_play_pause)

        restart_icon = QtGui.QIcon('res/replay.png')
        restart_btn = QtWidgets.QPushButton(icon=restart_icon)
        restart_btn.setObjectName('iconbutton')
        restart_btn.setToolTip('Restart the simulation')

        def restart_clicked() -> None:
            if not self.__paused:
                pause_simulation()

            play_pause_btn.setIcon(play_icon)
            next_btn.setEnabled(True)

            self.state.reset()
            active_provider.get_scheduler().trigger_gui_event(controller.events.Events.RESET, kw={"state": self.state})
            self.state_viz.reset()

        self.__restart = lambda: restart_clicked()

        restart_btn.clicked.connect(restart_clicked)

        # Pause button
        pause_btn = QtWidgets.QPushButton(icon=pause_icon)
        pause_btn.setEnabled(False)

        # Speed slider
        speed_slider, speed_slider_layout = self.__build_speed_slider(pause_simulation)

        time_control_buttons_layout = QtWidgets.QHBoxLayout()
        time_control_buttons_layout.addStretch(1)
        time_control_buttons_layout.addWidget(next_btn)
        time_control_buttons_layout.addWidget(play_pause_btn)
        time_control_buttons_layout.addWidget(restart_btn)
        time_control_buttons_layout.addStretch(1)

        time_control_layout = QtWidgets.QVBoxLayout()
        time_control_layout.addLayout(time_control_buttons_layout)
        time_control_layout.addLayout(speed_slider_layout)

        # Add controls to layout
        controls_widget = QtWidgets.QWidget()
        controls_widget.setFixedWidth(300)
        controls_widget.setObjectName('controls')

        layout = QtWidgets.QVBoxLayout()
        controls_widget.setLayout(layout)

        logo_widget = QtWidgets.QWidget()
        logo_widget.setFixedHeight(200)
        logo_widget.setFixedWidth(200)
        logo_layout = QtWidgets.QHBoxLayout()
        logo = QtSvg.QSvgWidget('res/episim.svg')
        logo_layout.addWidget(logo)
        logo_widget.setLayout(logo_layout)
        layout.addWidget(logo_widget, alignment=QtCore.Qt.AlignHCenter)

        heading_label = QtWidgets.QLabel('Epidemic Simulator')
        heading_label.setObjectName('heading')
        layout.addWidget(heading_label, alignment=QtCore.Qt.AlignHCenter)

        layout.addStretch(1)

        layout.addLayout(size_slider_layout)

        layout.addWidget(self.__build_horizontal_separator())

        layout.addLayout(susceptible_share_slider_layout)
        layout.addLayout(infected_share_slider_layout)

        layout.addWidget(self.__build_horizontal_separator())

        layout.addLayout(infection_prob_slider_layout)
        layout.addLayout(remove_prob_slider_layout)

        layout.addStretch(1)

        layout.addLayout(time_control_layout)

        layout.addWidget(self.__build_horizontal_separator())

        layout.addLayout(seed_input_field_layout)

        layout.addWidget(reset_btn)

        self.root_layout.addWidget(controls_widget)

    def __build_horizontal_separator(self) -> QtWidgets.QFrame:
        line = QtWidgets.QFrame()

        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setObjectName('horizontalsep')

        return line

    def __build_size_slider(self) -> [QtWidgets.QSlider, QtWidgets.QVBoxLayout]:
        size_slider_layout = QtWidgets.QVBoxLayout()
        size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        size_slider.setMinimum(10)
        size_slider.setMaximum(1000)
        size_slider.setSingleStep(10)
        size_slider.setValue(self.state.size())

        def on_size_slider_value_change(value: int) -> None:
            size = round(value / size_slider.singleStep()) * size_slider.singleStep()
            size_slider.setValue(size)
            size_label.setText('Size: {}'.format(size))

        def on_size_slider_released() -> None:
            self.state.set_size(np.uint(size_slider.value()))

            self.state.reset()
            active_provider.get_scheduler().trigger_gui_event(controller.events.Events.RESET, kw={"state": self.state})
            self.state_viz.reset()

        size_slider.valueChanged.connect(on_size_slider_value_change)
        size_slider.sliderReleased.connect(on_size_slider_released)

        size_label = QtWidgets.QLabel('Size: {}'.format(self.state.size()))

        size_slider_layout.addWidget(size_label, alignment=QtCore.Qt.AlignHCenter)
        size_slider_layout.addWidget(size_slider)

        return size_slider, size_slider_layout

    def __build_speed_slider(self, change_callback) -> [QtWidgets.QSlider, QtWidgets.QVBoxLayout]:
        speed_slider_layout = QtWidgets.QVBoxLayout()
        speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        speed_slider.setMinimum(0)
        speed_slider.setMaximum(2000)
        speed_slider.setSingleStep(100)
        speed_slider.setValue(self.state.speed())

        def on_speed_change(value) -> None:
            speed = round(value / speed_slider.singleStep()) * speed_slider.singleStep()
            speed_slider.setValue(speed)
            speed_label.setText('Speed: {} ms/day'.format(speed) if speed > 0 else 'Speed: ASAP')

        def on_speed_slider_released() -> None:
            self.state.set_speed(speed_slider.value())
            change_callback()

        speed_slider.valueChanged.connect(on_speed_change)
        speed_slider.sliderReleased.connect(on_speed_slider_released)

        speed_label = QtWidgets.QLabel(
            'Speed: {} ms/day'.format(self.state.speed()) if self.state.speed() > 0 else 'Speed: ASAP')

        speed_slider_layout.addWidget(speed_label, alignment=QtCore.Qt.AlignHCenter)
        speed_slider_layout.addWidget(speed_slider)

        return speed_slider, speed_slider_layout

    def __build_susceptible_share_slider(self, infected_share_slider_supplier) -> [QtWidgets.QSlider,
                                                                                   QtWidgets.QVBoxLayout]:
        susceptible_slider_layout = QtWidgets.QVBoxLayout()
        susceptible_share_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        susceptible_share_slider.setMinimum(0)
        susceptible_share_slider.setMaximum(100)
        susceptible_share_slider.setSingleStep(1)
        susceptible_share_slider.setValue(round(self.state.susceptible_share() * 100))

        def on_susceptible_slider_value_change(value: int) -> None:
            share = value
            susceptible_share_slider.setValue(share)
            susceptible_share_label.setText('Susceptible share: {} %'.format(share))

        def on_susceptible_slider_released() -> None:
            new_share = susceptible_share_slider.value() / 100
            current_infected_share = self.state.infected_share()
            if new_share + current_infected_share > 1.0:
                self.state.set_infected_share(1.0 - new_share)
                infected_share_slider_supplier().setValue(round(self.state.infected_share() * 100))

            self.state.set_susceptible_share(new_share)

            self.state.reset()
            active_provider.get_scheduler().trigger_gui_event(controller.events.Events.RESET, kw={"state": self.state})
            self.state_viz.reset()

        susceptible_share_slider.valueChanged.connect(on_susceptible_slider_value_change)
        susceptible_share_slider.sliderReleased.connect(on_susceptible_slider_released)

        susceptible_share_label = QtWidgets.QLabel(
            'Susceptible share: {} %'.format(round(self.state.susceptible_share() * 100)))

        susceptible_slider_layout.addWidget(susceptible_share_label, alignment=QtCore.Qt.AlignHCenter)
        susceptible_slider_layout.addWidget(susceptible_share_slider)

        return susceptible_share_slider, susceptible_slider_layout

    def __build_infected_share_slider(self, susceptible_share_slider_supplier) -> [QtWidgets.QSlider,
                                                                                   QtWidgets.QVBoxLayout]:
        infected_slider_layout = QtWidgets.QVBoxLayout()
        infected_share_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        infected_share_slider.setMinimum(0)
        infected_share_slider.setMaximum(100)
        infected_share_slider.setSingleStep(1)
        infected_share_slider.setValue(round(self.state.infected_share() * 100))

        def on_infected_slider_value_change(value: int) -> None:
            share = value
            infected_share_slider.setValue(share)
            infected_share_label.setText('Infected share: {} %'.format(share))

        def on_infected_slider_released() -> None:
            new_share = infected_share_slider.value() / 100
            current_susceptible_share = self.state.susceptible_share()
            if new_share + current_susceptible_share > 1.0:
                self.state.set_susceptible_share(1.0 - new_share)
                susceptible_share_slider_supplier().setValue(round(self.state.susceptible_share() * 100))

            self.state.set_infected_share(new_share)

            self.state.reset()
            active_provider.get_scheduler().trigger_gui_event(controller.events.Events.RESET, kw={"state": self.state})
            self.state_viz.reset()

        infected_share_slider.valueChanged.connect(on_infected_slider_value_change)
        infected_share_slider.sliderReleased.connect(on_infected_slider_released)

        infected_share_label = QtWidgets.QLabel('Infected share: {} %'.format(round(self.state.infected_share() * 100)))

        infected_slider_layout.addWidget(infected_share_label, alignment=QtCore.Qt.AlignHCenter)
        infected_slider_layout.addWidget(infected_share_slider)

        return infected_share_slider, infected_slider_layout

    def __build_infection_prob_slider(self) -> [QtWidgets.QSlider, QtWidgets.QVBoxLayout]:
        infection_prob_slider_layout = QtWidgets.QVBoxLayout()
        infection_prob_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        infection_prob_slider.setMinimum(0)
        infection_prob_slider.setMaximum(100)
        infection_prob_slider.setSingleStep(1)
        infection_prob_slider.setValue(round(self.state.infection_prob() * 100))

        def on_infection_prob_slider_value_change(value: int) -> None:
            infection_prob_slider.setValue(value)
            infection_prob_slider_label.setText('Infection probability: {} %'.format(value))

        def on_infection_prob_slider_released() -> None:
            new_prob = infection_prob_slider.value() / 100
            self.state.set_infection_prob(new_prob)

        infection_prob_slider.valueChanged.connect(on_infection_prob_slider_value_change)
        infection_prob_slider.sliderReleased.connect(on_infection_prob_slider_released)

        infection_prob_slider_label = QtWidgets.QLabel(
            'Infection probability: {} %'.format(round(self.state.infection_prob() * 100)))

        infection_prob_slider_layout.addWidget(infection_prob_slider_label, alignment=QtCore.Qt.AlignHCenter)
        infection_prob_slider_layout.addWidget(infection_prob_slider)

        return infection_prob_slider, infection_prob_slider_layout

    def __build_remove_prob_slider(self) -> [QtWidgets.QSlider, QtWidgets.QVBoxLayout]:
        remove_prob_slider_layout = QtWidgets.QVBoxLayout()
        remove_prob_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        remove_prob_slider.setMinimum(0)
        remove_prob_slider.setMaximum(100)
        remove_prob_slider.setSingleStep(1)
        remove_prob_slider.setValue(round(self.state.remove_prob() * 100))

        def on_remove_prob_slider_value_change(value: int) -> None:
            remove_prob_slider.setValue(value)
            remove_prob_slider_label.setText('Remove probability: {} %'.format(value))
            if value > 0:
                mean_sickness_days_label.setText(
                    f'Mean sickness days (1/rem.-prob.) = {round(1 / (value / 100), 2)} days')
            else:
                mean_sickness_days_label.setText(f'Mean sickness days (1/rem.-prob.) = ∞ days')

        def on_remove_prob_slider_released() -> None:
            new_prob = remove_prob_slider.value() / 100
            self.state.set_remove_prob(new_prob)
            if self.state.remove_prob() > 0:
                mean_sickness_days_label.setText(
                    f'Mean sickness days (1/rem.-prob.) = {round(1 / self.state.remove_prob(), 2)} days')
            else:
                mean_sickness_days_label.setText(f'Mean sickness days (1/rem.-prob.) = ∞ days')

        remove_prob_slider.valueChanged.connect(on_remove_prob_slider_value_change)
        remove_prob_slider.sliderReleased.connect(on_remove_prob_slider_released)

        remove_prob_slider_label = QtWidgets.QLabel(
            'Remove probability: {} %'.format(round(self.state.remove_prob() * 100)))

        remove_prob_slider_layout.addWidget(remove_prob_slider_label, alignment=QtCore.Qt.AlignHCenter)
        remove_prob_slider_layout.addWidget(remove_prob_slider)

        mean_sickness_days_label = QtWidgets.QLabel(
            f'Mean sickness days (1/rem.-prob.) = {round(1 / self.state.remove_prob(), 2)} days')
        mean_sickness_days_label.setStyleSheet("font-size: 8pt")

        remove_prob_slider_layout.addWidget(mean_sickness_days_label, alignment=QtCore.Qt.AlignHCenter)

        return remove_prob_slider, remove_prob_slider_layout

    def __build_seed_input(self) -> [QtWidgets.QPushButton, QtWidgets.QLineEdit, QtWidgets.QHBoxLayout]:
        input = QtWidgets.QLineEdit()

        input.setValidator(QtGui.QIntValidator(0, 999999999))
        input.setText(f'{self.state.get_seed()}')

        def on_text_change(v) -> None:
            try:
                new_seed = int(v)
            except ValueError:
                new_seed = 0

            self.state.seed(new_seed)

        input.textChanged.connect(on_text_change)

        reseed_btn = QtWidgets.QPushButton('Reseed')

        def on_reseed() -> None:
            self.state.seed()
            input.setText(f'{self.state.get_seed()}')

        reseed_btn.clicked.connect(on_reseed)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Seed:'))
        layout.addWidget(input)
        layout.addWidget(reseed_btn)

        return reseed_btn, input, layout

    def __build_settings(self) -> None:
        controls_widget = QtWidgets.QWidget()
        controls_widget.setFixedWidth(320)
        controls_widget.setObjectName('controls')

        controls_layout = QtWidgets.QVBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_widget.setLayout(controls_layout)

        heading_label = QtWidgets.QLabel('Advanced Settings')
        heading_label.setObjectName('heading')
        controls_layout.addWidget(heading_label, alignment=QtCore.Qt.AlignHCenter)

        actual_settings_widget = QtWidgets.QWidget()
        actual_settings_widget.setObjectName('scrollAreaWidgetContents')
        layout = QtWidgets.QVBoxLayout()
        actual_settings_widget.setLayout(layout)

        scrollarea = QtWidgets.QScrollArea()
        scrollarea.setWidgetResizable(True)
        scrollarea.setWidget(actual_settings_widget)
        controls_layout.addWidget(scrollarea)

        infection_env_settings = self.__build_infection_environment_settings()
        layout.addLayout(infection_env_settings)

        layout.addWidget(self.__build_horizontal_separator())

        mixing_settings = self.__build_mixing_settings()
        layout.addLayout(mixing_settings)

        layout.addWidget(self.__build_horizontal_separator())

        _, removed_or_dead_immune_settings = self.__build_removed_or_dead_immune_distinction_checkbox(
            lambda enabled: self.__restart())
        layout.addLayout(removed_or_dead_immune_settings)

        layout.addWidget(self.__build_horizontal_separator())

        movement_limit_settings = self.__build_movement_limit_settings()
        layout.addLayout(movement_limit_settings)

        layout.addWidget(self.__build_horizontal_separator())

        incubation_and_sickness_settings = self.__build_incubation_and_sickness_settings(
            lambda enabled: self.__restart())
        layout.addLayout(incubation_and_sickness_settings)

        layout.addWidget(self.__build_horizontal_separator())

        quarantine_settings = self.__build_quarantine_settings(
            lambda enabled: self.__restart())
        layout.addLayout(quarantine_settings)

        layout.addWidget(self.__build_horizontal_separator())

        _, vaccine_settings = self.__build_vaccine_settings(
            lambda enabled: self.__restart())
        layout.addLayout(vaccine_settings)

        layout.addWidget(self.__build_horizontal_separator())

        _, r_settings = self.__build_r_settings()
        layout.addLayout(r_settings)

        layout.addStretch(1)

        self.root_layout.addWidget(controls_widget)

    def __build_infection_environment_settings(self) -> QtWidgets.QVBoxLayout:
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(QtWidgets.QLabel('Infection environment'), alignment=QtCore.Qt.AlignHCenter)

        sub_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(sub_layout)

        # Select for the environment metrix
        config_layout = QtWidgets.QVBoxLayout()
        config_layout.addStretch(1)
        sub_layout.addLayout(config_layout)

        metric_select = QtWidgets.QComboBox()
        metrics = [EnvironmentMetric.MANHATTAN, EnvironmentMetric.EUCLIDEAN]
        metric_select.addItems(map(lambda m: m.value, metrics))

        def on_metric_index_change(index) -> None:
            self.state.set_infection_env_metric(metrics[index])
            update_env_viz()

        metric_select.currentIndexChanged.connect(on_metric_index_change)
        config_layout.addWidget(metric_select)

        # Build radius slider
        radius_slider_layout = QtWidgets.QVBoxLayout()
        radius_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        radius_slider.setMinimum(1)
        radius_slider.setMaximum(5)
        radius_slider.setSingleStep(1)
        radius_slider.setValue(self.state.infection_env_radius())

        def on_radius_change(value) -> None:
            self.state.set_infection_env_radius(value)
            radius_label.setText('Radius: {}'.format(value))
            update_env_viz()

        radius_slider.valueChanged.connect(on_radius_change)

        radius_label = QtWidgets.QLabel('Radius: {}'.format(self.state.infection_env_radius()))
        radius_slider_layout.addWidget(radius_label, alignment=QtCore.Qt.AlignHCenter)
        radius_slider_layout.addWidget(radius_slider)

        config_layout.addLayout(radius_slider_layout)
        config_layout.addStretch(1)

        # Visualization of the environment
        gfx_widget = QtWidgets.QWidget()
        gfx_widget.setFixedSize(120, 120)
        gfx_p_layout = QtWidgets.QVBoxLayout()
        gfx_p_layout.setContentsMargins(0, 0, 0, 0)
        gfx_widget.setLayout(gfx_p_layout)
        gfx_layout = pg.GraphicsLayoutWidget()
        gfx_layout.setBackground(cfg.BACKGROUND_CARD_COLOR)
        gfx_p_layout.addWidget(gfx_layout)

        view_box = gfx_layout.addViewBox(lockAspect=True, enableMouse=False, enableMenu=False)
        env_img_item = pg.ImageItem()
        view_box.addItem(env_img_item)

        def update_env_viz() -> None:
            env_img = self.__generate_environment_img(
                metric=self.state.infection_env_metric(),
                radius=self.state.infection_env_radius(),
                img_scale=30 // self.state.infection_env_radius(),
                border_size=1
            )
            env_img_item.setImage(env_img)

        sub_layout.addWidget(gfx_widget, alignment=QtCore.Qt.AlignHCenter)

        update_env_viz()

        return layout

    def __generate_environment_img(
            self,
            metric=EnvironmentMetric.EUCLIDEAN,
            radius=1, img_scale=10,
            border_size=1
    ) -> np.ndarray:
        size = (radius + 1) * 2 + 1
        mask = np.ones(shape=(size, size))

        if metric is EnvironmentMetric.MANHATTAN:
            for row in range(1, size - 1):
                offset = abs((radius + 1) - row)
                for col in range(1 + offset, size - 1 - offset):
                    mask[row][col] = 2
        elif metric is EnvironmentMetric.EUCLIDEAN:
            for row in range(1, size - 1):
                for col in range(1, size - 1):
                    distance = np.round(np.sqrt((radius + 1 - row) ** 2 + (radius + 1 - col) ** 2))
                    if distance <= radius:
                        mask[row][col] = 2
        else:
            raise ValueError('EnvironmentMetric not implemented')

        # Set middle cell value (should symbolize infected cell)
        mask[radius + 1][radius + 1] = 3

        # Upscale mask and add border
        img_size = (size * img_scale) + (size - 1) * border_size
        img = np.zeros(shape=(img_size, img_size))

        for row in range(0, size):
            is_last_row = row == size - 1

            start_row = row * (img_scale + border_size)
            end_row = (row + 1) * (img_scale + border_size)
            if is_last_row:
                end_row -= border_size

            for col in range(0, size):
                is_last_col = col == size - 1

                start_col = col * (img_scale + border_size)
                end_col = (col + 1) * (img_scale + border_size)
                if is_last_col:
                    end_col -= border_size

                color = mask[row][col]

                for r in range(start_row, end_row):
                    for c in range(start_col, end_col):
                        if (not is_last_row and r >= end_row - border_size) \
                                or (not is_last_col and c >= end_col - border_size):
                            img[r][c] = 0
                        else:
                            img[r][c] = color

        return img

    def __build_mixing_settings(self) -> QtWidgets.QVBoxLayout:
        layout = QtWidgets.QVBoxLayout()
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setSingleStep(1)
        slider.setValue(round(self.state.get_mixing_value_m() * 100))

        def on_value_change(value: int) -> None:
            slider.setValue(value)
            label.setText('Movement mixing: {} %'.format(value))

        def on_released() -> None:
            new_v = slider.value() / 100
            self.state.set_mixing_value_m(new_v)

        slider.valueChanged.connect(on_value_change)
        slider.sliderReleased.connect(on_released)

        label = QtWidgets.QLabel(
            'Movement mixing: {} %'.format(round(self.state.get_mixing_value_m() * 100)))

        layout.addWidget(label, alignment=QtCore.Qt.AlignHCenter)
        layout.addWidget(slider)

        return layout

    def __build_r_settings(self) -> [QtWidgets.QCheckBox, QtWidgets.QHBoxLayout]:
        layout = QtWidgets.QHBoxLayout()

        checkbox = QtWidgets.QCheckBox('Calculate real R̄ (Performance sensitive)')
        checkbox.setChecked(self.state.calculate_real_effective_reproduction_number())

        def on_change(v) -> None:
            self.state.set_calculate_real_effective_reproduction_number(checkbox.isChecked())

        checkbox.stateChanged.connect(on_change)

        layout.addWidget(checkbox)

        return checkbox, layout

    def __build_removed_or_dead_immune_distinction_checkbox(self, callback) -> [QtWidgets.QCheckBox,
                                                                                QtWidgets.QVBoxLayout]:
        layout = QtWidgets.QVBoxLayout()

        checkbox = QtWidgets.QCheckBox('Breakdown removed in dead/immune')
        checkbox.setChecked(self.state.lethality_toggle())

        def on_change(v) -> None:
            self.state.set_lethality_toggle(checkbox.isChecked())
            slider.setEnabled(self.state.lethality_toggle())
            callback(v)

        checkbox.stateChanged.connect(on_change)

        layout.addWidget(checkbox)

        slider, lethality_slider_layout = self.__build_lethality_slider()
        layout.addLayout(lethality_slider_layout)

        slider.setEnabled(self.state.lethality_toggle())

        return checkbox, layout

    def __build_lethality_slider(self) -> [QtWidgets.QSlider, QtWidgets.QVBoxLayout]:
        layout = QtWidgets.QVBoxLayout()
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setSingleStep(1)
        slider.setValue(round(self.state.lethality() * 100))

        def on_value_change(value: int) -> None:
            slider.setValue(value)
            label.setText('Lethality: {} %'.format(value))

        def on_released() -> None:
            new_v = slider.value() / 100
            self.state.set_lethality(new_v)

        slider.valueChanged.connect(on_value_change)
        slider.sliderReleased.connect(on_released)

        label = QtWidgets.QLabel(
            'Lethality: {} %'.format(round(self.state.lethality() * 100)))

        layout.addWidget(label, alignment=QtCore.Qt.AlignHCenter)
        layout.addWidget(slider)

        return slider, layout

    def __build_vaccine_settings(self, callback) -> [QtWidgets.QCheckBox, QtWidgets.QVBoxLayout]:
        layout = QtWidgets.QVBoxLayout()

        checkbox = QtWidgets.QCheckBox('Vaccine')
        checkbox.setChecked(self.state.vaccine_toggle())

        def on_change(v) -> None:
            self.state.set_vaccine_toggle(checkbox.isChecked())
            slider.setEnabled(checkbox.isChecked())
            spinbox.setEnabled(checkbox.isChecked())

            callback(v)

        checkbox.stateChanged.connect(on_change)

        layout.addWidget(checkbox)

        spinbox, finish_spinbox_layout = self.__build_vaccine_finish_spinbox()
        spinbox.setEnabled(checkbox.isChecked())

        layout.addLayout(finish_spinbox_layout)

        slider, vaccine_share_slider_layout = self.__build_vaccine_share_slider()
        slider.setEnabled(checkbox.isChecked())

        layout.addLayout(vaccine_share_slider_layout)

        return checkbox, layout

    def __build_vaccine_finish_spinbox(self) -> [QtWidgets.QSpinBox, QtWidgets.QHBoxLayout]:
        layout = QtWidgets.QHBoxLayout()

        layout.addWidget(QtWidgets.QLabel('After days:'))

        spinbox = QtWidgets.QSpinBox()
        spinbox.setMinimum(0)
        spinbox.setMaximum(2500)
        spinbox.setSingleStep(1)
        spinbox.setValue(self.state.vaccine_time())

        def value_change() -> None:
            self.state.set_vaccine_time(spinbox.value())

        spinbox.valueChanged.connect(value_change)

        layout.addWidget(spinbox)

        return spinbox, layout

    def __build_vaccine_share_slider(self):
        layout = QtWidgets.QVBoxLayout()
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setSingleStep(1)
        slider.setValue(round(self.state.vaccine_share() * 100))

        def on_value_change(value):
            slider.setValue(value)
            label.setText('Vaccinated population share: {} %'.format(value))

        def on_released():
            new_v = slider.value() / 100
            self.state.set_vaccine_share(new_v)

        slider.valueChanged.connect(on_value_change)
        slider.sliderReleased.connect(on_released)

        label = QtWidgets.QLabel(
            'Vaccinated population share: {} %'.format(round(self.state.vaccine_share() * 100)))

        layout.addWidget(label, alignment=QtCore.Qt.AlignHCenter)
        layout.addWidget(slider)

        return slider, layout

    def __build_movement_limit_settings(self):
        layout = QtWidgets.QVBoxLayout()

        checkbox = QtWidgets.QCheckBox('Limit movements')
        checkbox.setChecked(self.state.movement_limit_enabled())

        def on_change(v):
            self.state.set_movement_limit_enabled(checkbox.isChecked())

            if v:
                active_provider.set_movement_strategy(LimitedMovementStrategy())
            else:
                active_provider.set_movement_strategy(DefaultMovementStrategy())

            metric_select.setEnabled(checkbox.isChecked())
            radius_slider.setEnabled(checkbox.isChecked())
            high_distance_cb.setEnabled(checkbox.isChecked())

        checkbox.stateChanged.connect(on_change)

        layout.addWidget(checkbox)

        sub_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(sub_layout)

        # Select for the environment metric
        config_layout = QtWidgets.QVBoxLayout()
        config_layout.addStretch(1)
        sub_layout.addLayout(config_layout)

        metric_select = QtWidgets.QComboBox()
        metrics = [EnvironmentMetric.EUCLIDEAN, EnvironmentMetric.MANHATTAN]
        metric_select.addItems(map(lambda m: m.value, metrics))

        def on_metric_index_change(index):
            self.state.set_movement_limit_metric(metrics[index])
            update_env_viz()

        metric_select.currentIndexChanged.connect(on_metric_index_change)
        metric_select.setEnabled(checkbox.isChecked())
        config_layout.addWidget(metric_select)

        # Build radius slider
        radius_slider_layout = QtWidgets.QVBoxLayout()
        radius_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        radius_slider.setMinimum(1)
        radius_slider.setMaximum(10)
        radius_slider.setSingleStep(1)
        radius_slider.setValue(self.state.movement_limit_radius())

        def on_radius_change(value):
            self.state.set_movement_limit_radius(value)
            radius_label.setText('Radius: {}'.format(value))
            update_env_viz()

        radius_slider.setEnabled(self.state.movement_limit_enabled())
        radius_slider.valueChanged.connect(on_radius_change)

        radius_label = QtWidgets.QLabel('Radius: {}'.format(self.state.movement_limit_radius()))
        radius_slider_layout.addWidget(radius_label, alignment=QtCore.Qt.AlignHCenter)
        radius_slider_layout.addWidget(radius_slider)

        config_layout.addLayout(radius_slider_layout)
        config_layout.addStretch(1)

        # Visualization of the environment
        gfx_widget = QtWidgets.QWidget()
        gfx_widget.setFixedSize(120, 120)
        gfx_p_layout = QtWidgets.QVBoxLayout()
        gfx_p_layout.setContentsMargins(0, 0, 0, 0)
        gfx_widget.setLayout(gfx_p_layout)
        gfx_layout = pg.GraphicsLayoutWidget()
        gfx_layout.setBackground(cfg.BACKGROUND_CARD_COLOR)
        gfx_p_layout.addWidget(gfx_layout)

        view_box = gfx_layout.addViewBox(lockAspect=True, enableMouse=False, enableMenu=False)
        env_img_item = pg.ImageItem()
        view_box.addItem(env_img_item)

        def update_env_viz():
            env_img = self.__generate_environment_img(
                metric=self.state.movement_limit_metric(),
                radius=self.state.movement_limit_radius(),
                img_scale=30 // self.state.movement_limit_radius(),
                border_size=1
            )
            env_img_item.setImage(env_img)

        sub_layout.addWidget(gfx_widget, alignment=QtCore.Qt.AlignHCenter)

        update_env_viz()

        # Checkbox - Far travels are uncommon
        high_distance_cb = QtWidgets.QCheckBox('Far travels are less probable')
        high_distance_cb.setChecked(self.state.movement_limit_high_distances_are_uncommon())
        high_distance_cb.setEnabled(checkbox.isChecked())

        def on_high_distance_cb_change(v):
            self.state.set_movement_limit_high_distances_are_uncommon(checkbox.isChecked())

        high_distance_cb.stateChanged.connect(on_high_distance_cb_change)

        layout.addWidget(high_distance_cb)

        return layout

    def __build_incubation_and_sickness_settings(self, callback):
        layout = QtWidgets.QVBoxLayout()

        checkbox = QtWidgets.QCheckBox('Incubation period')
        checkbox.setChecked(self.state.incubation_period_enabled())

        def on_change(v):
            self.state.set_incubation_period_enabled(checkbox.isChecked())

            spinbox.setEnabled(checkbox.isChecked())
            callback(v)

        checkbox.stateChanged.connect(on_change)

        layout.addWidget(checkbox)

        spinbox, incubation_time_sb_layout = self.__build_incubation_time_spinbox()
        spinbox.setEnabled(checkbox.isChecked())
        layout.addLayout(incubation_time_sb_layout)

        return layout

    def __build_incubation_time_spinbox(self):
        layout = QtWidgets.QHBoxLayout()

        layout.addWidget(QtWidgets.QLabel('Incubation period (in days):'))

        spinbox = QtWidgets.QSpinBox()
        spinbox.setMinimum(0)
        spinbox.setMaximum(100)
        spinbox.setSingleStep(1)
        spinbox.setValue(self.state.incubation_period())

        def value_change(v):
            self.state.set_incubation_period(spinbox.value())

        spinbox.valueChanged.connect(value_change)

        layout.addWidget(spinbox)

        return spinbox, layout

    def __build_quarantine_settings(self, callback):
        layout = QtWidgets.QVBoxLayout()

        checkbox = QtWidgets.QCheckBox('Quarantine (Isolation of infected)')
        checkbox.setChecked(self.state.quarantine_enabled())

        def on_change(v):
            self.state.set_quarantine_enabled(checkbox.isChecked())
            slider.setEnabled(checkbox.isChecked())
            callback(v)

        checkbox.stateChanged.connect(on_change)

        layout.addWidget(checkbox)

        slider, quarantine_share_slider_layout = self.__build_quarantine_share_slider()
        slider.setEnabled(False)
        layout.addLayout(quarantine_share_slider_layout)

        return layout

    def __build_quarantine_share_slider(self) -> [QtWidgets.QSlider, QtWidgets.QVBoxLayout]:
        layout = QtWidgets.QVBoxLayout()
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setSingleStep(1)
        slider.setValue(round(self.state.quarantine_share() * 100))

        def on_value_change(value: int) -> None:
            slider.setValue(value)
            label.setText('Isolated share of infected: {} %'.format(value))

        def on_released() -> None:
            new_v = slider.value() / 100
            self.state.set_quarantine_share(new_v)

        slider.valueChanged.connect(on_value_change)
        slider.sliderReleased.connect(on_released)

        label = QtWidgets.QLabel(
            'Isolated share of infected: {} %'.format(round(self.state.quarantine_share() * 100)))

        layout.addWidget(label, alignment=QtCore.Qt.AlignHCenter)
        layout.addWidget(slider)

        return slider, layout
