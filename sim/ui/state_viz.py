import pyqtgraph as pg
import config as cfg
import numpy as np
from model.state import SimState
from util.metric import calc_effective_reproduction_number, estimate_effective_reproduction_number

"""
AUTHOR: Benjamin Eder and Konstantin Schlosser (a little ;))
"""


class SimStateViz:
    """Visualizations for the current simulator state"""

    __r_points = []
    __r_estimate_points = []
    __sus_counts = []
    __inf_counts = []
    __rem_counts = []
    __ded_counts = []
    __imm_counts = []
    __inc_counts = []

    def __init__(self, state: SimState):
        """Create visualizations for the passed state"""
        self.state = state

        view: pg.GraphicsLayoutWidget = pg.GraphicsLayoutWidget()
        qGraphicsGridLayout = view.ci.layout
        qGraphicsGridLayout.setRowStretchFactor(0, 3)
        qGraphicsGridLayout.setRowStretchFactor(1, 3)
        qGraphicsGridLayout.setRowStretchFactor(2, 2)
        qGraphicsGridLayout.setRowStretchFactor(3, 2)
        qGraphicsGridLayout.setColumnStretchFactor(0, 0)
        qGraphicsGridLayout.setColumnStretchFactor(1, 999)

        # ROW 1

        # Build legend
        self.legend = pg.LegendItem()
        self.__update_legend()
        view.addItem(self.legend)

        # Build current state visualization
        view_box = view.addViewBox(rowspan=2, lockAspect=True)
        img_item = pg.ImageItem()
        view_box.addItem(img_item)
        view_box.invertY(True)

        view.nextRow()

        # ROW 2

        # Build stats
        self.stats = view.addLayout()
        self.__update_stats()

        view.nextRow()

        # ROW 3

        # Build time overview graph
        self.shares_plot = view.addPlot(colspan=2)
        self.shares_plot.setTitle('Population category shares over time')

        view.nextRow()

        # ROW 4

        # Build R time overview graph
        self.r_plot = view.addPlot(colspan=2)

        self.view = view
        self.img = img_item

    def elapsed_days(self) -> int:
        return len(self.__r_points) - 1

    def r_values(self) -> list:
        return self.__r_points

    def r_estimate_values(self) -> list:
        return self.__r_estimate_points

    def sus_counts(self) -> list:
        return self.__sus_counts

    def inf_counts(self) -> list:
        return self.__inf_counts

    def rem_counts(self) -> list:
        return self.__rem_counts

    def ded_counts(self) -> list:
        return self.__ded_counts

    def imm_counts(self) -> list:
        return self.__imm_counts

    def inc_counts(self) -> list:
        return self.__inc_counts

    def reset(self) -> None:
        self.__r_points = []
        self.__r_estimate_points = []
        self.calc_next_r()

        self.__sus_counts = []
        self.__inf_counts = []
        self.__rem_counts = []
        self.__ded_counts = []
        self.__imm_counts = []
        self.__inc_counts = []

        self.update(update_legend=True)

    def update(self, update_legend=False) -> None:
        """Tell the visualization to refresh based on the simulator state"""
        self.__update_shares_plot()
        self.__update_r_plot()
        self.__update_img()
        self.__update_stats()

        if update_legend:
            self.__update_legend()

    def __update_stats(self) -> None:
        container: pg.GraphicsLayout = self.stats

        container.clear()

        container.addLabel(f'Elapsed days: {self.elapsed_days()}')
        container.nextRow()
        container.addLabel(f'Susceptible: {self.state.susceptible_count()}')
        container.nextRow()
        container.addLabel(f'Infected: {self.state.infected_count()}')

        if self.state.lethality_toggle():
            container.nextRow()
            container.addLabel(f'Immune: {self.state.immune_count()}')
            container.nextRow()
            container.addLabel(f'Dead: {self.state.dead_count()}')
        else:
            container.nextRow()
            container.addLabel(f'Removed: {self.state.removed_count()}')

        if self.state.incubation_period_enabled():
            container.nextRow()
            container.addLabel(f'Incubation: {self.state.incubation_count()}')

        if self.state.quarantine_enabled():
            container.nextRow()
            container.addLabel(f'Quarantine: {self.state.get_quarantined_count()}')

    def __update_legend(self) -> None:
        self.legend.clear()

        self.legend.addItem(self.__build_legend_item(cfg.COLOR_NOT_OCCUPIED), 'Not occupied')
        self.legend.addItem(self.__build_legend_item(cfg.COLOR_SUSCEPTIBLE), 'Susceptible')
        self.legend.addItem(self.__build_legend_item(cfg.COLOR_INFECTED), 'Infected')

        if not self.state.lethality_toggle() and not self.state.vaccine_toggle():
            self.legend.addItem(self.__build_legend_item(cfg.COLOR_REMOVED), 'Removed')
        else:
            self.legend.addItem(self.__build_legend_item(cfg.COLOR_IMMUNE), 'Immune')
            self.legend.addItem(self.__build_legend_item(cfg.COLOR_DEAD), 'Dead')
        if self.state.incubation_period_enabled():
            self.legend.addItem(self.__build_legend_item(cfg.COLOR_INCUBATION), "Incubation")

        self.legend.setFixedHeight(150)

    def __update_img(self) -> None:
        self.img.setImage(self.state.data(), lut=np.array([
            cfg.COLOR_NOT_OCCUPIED,  # Empty cell
            cfg.COLOR_SUSCEPTIBLE,  # Susceptible
            cfg.COLOR_INFECTED,  # Infected
            cfg.COLOR_REMOVED,  # Removed
            cfg.COLOR_IMMUNE,  # Removed
            cfg.COLOR_DEAD,  # Removed
            cfg.COLOR_INCUBATION  # Removed
        ]), levels=(0.0, 6.0))

    def __update_shares_plot(self) -> None:
        """
        Draws the course of the simulation for the new values.
        Edited by Beil Benedikt vor the incubation line
        :return: Nothing
        """
        self.shares_plot.clear()

        sus_count = self.state.susceptible_count()
        inf_count = self.state.infected_count()
        rem_count = self.state.removed_count()
        imm_count = self.state.immune_count()
        ded_count = self.state.dead_count()
        inc_count = self.state.incubation_count()
        total_population = ded_count + imm_count + rem_count + sus_count + inf_count + inc_count
        share_sum = inf_count

        self.__inf_counts.append(share_sum / total_population)
        share_sum += inc_count
        self.__inc_counts.append(share_sum / total_population)
        share_sum += sus_count
        self.__sus_counts.append(share_sum / total_population)
        share_sum += rem_count
        self.__rem_counts.append(share_sum / total_population)
        share_sum += imm_count
        self.__imm_counts.append(share_sum / total_population)
        share_sum += ded_count
        self.__ded_counts.append(share_sum / total_population)

        x = np.arange(len(self.__sus_counts))

        self.shares_plot.setXRange(0, len(x))

        self.shares_plot.setLabel('bottom', 'Time in days')
        self.shares_plot.setLabel('left', 'Share')

        if not self.state.lethality_toggle() and not self.state.vaccine_toggle():
            # Removed line
            self.shares_plot.plot(x, self.__rem_counts, pen=cfg.COLOR_REMOVED, fillLevel=0,
                                  brush=cfg.COLOR_REMOVED)
        else:
            # Ded line
            self.shares_plot.plot(x, self.__ded_counts, pen=cfg.COLOR_DEAD, fillLevel=0,
                                  brush=cfg.COLOR_DEAD)
            # Immune line
            self.shares_plot.plot(x, self.__imm_counts, pen=cfg.COLOR_IMMUNE, fillLevel=0,
                                  brush=cfg.COLOR_IMMUNE)

        # Susceptible line
        self.shares_plot.plot(x, self.__sus_counts, pen=cfg.COLOR_SUSCEPTIBLE, fillLevel=0,
                              brush=cfg.COLOR_SUSCEPTIBLE)

        if self.state.incubation_period_enabled():
            # Incubation line
            self.shares_plot.plot(x, self.__inc_counts, pen=cfg.COLOR_INCUBATION, fillLevel=0,
                                  brush=cfg.COLOR_INCUBATION)

        # Infected line
        self.shares_plot.plot(x, self.__inf_counts, pen=cfg.COLOR_INFECTED, fillLevel=0,
                              brush=cfg.COLOR_INFECTED)

    def __update_r_plot(self) -> None:
        self.r_plot.clear()

        r_title_value = round(self.__r_points[len(self.__r_points) - 1] if len(self.__r_points) > 0 else 0,
                              2) if self.state.calculate_real_effective_reproduction_number() else round(
            self.__r_estimate_points[len(self.__r_estimate_points) - 1] if len(self.__r_estimate_points) > 0 else 0, 2)

        self.r_plot.setTitle(
            f'Effective reproduction number R̄ = {r_title_value}')

        x = np.arange(max(len(self.__r_points), len(self.__r_estimate_points)))

        self.r_plot.setXRange(0, len(x) if len(x) != 0 else 1)

        self.r_plot.setLabel('bottom', 'Time in days')

        self.r_plot.addLegend()

        if self.state.calculate_real_effective_reproduction_number():
            # Plot real R-values
            self.r_plot.plot(x, self.__r_points, pen=cfg.COLOR_EFFECTIVE_REPRODUCTION_NUMBER, fillLevel=0.0,
                             brush=(*cfg.COLOR_EFFECTIVE_REPRODUCTION_NUMBER, 100), name='R̄')

        # Plot estimated R-values
        self.r_plot.plot(x, self.__r_estimate_points, pen=cfg.COLOR_EFFECTIVE_REPRODUCTION_NUMBER_ESTIMATED,
                         name='R̄ estimate')

    def calc_next_r(self) -> None:
        if self.state.calculate_real_effective_reproduction_number() or len(self.__r_points) == 0:
            from controller.provider import active_provider

            # Calculate real R-value
            self.__r_points.append(calc_effective_reproduction_number(
                active_provider.get_grid(),
                remove_probability=self.state.remove_prob(),
                infection_probability=self.state.infection_prob(),
                infection_radius=self.state.infection_env_radius(),
                infection_metric=self.state.infection_env_metric()
            ))
        else:
            self.__r_points.append(0.0)  # To avoid errors when it is enabled in-flight

        # Calculate estimated R-value
        r_estimate = estimate_effective_reproduction_number(total_count=self.state.get_total_count(),
                                                            susceptible_count=self.state.susceptible_count(),
                                                            R0=self.__r_points[0])
        self.__r_estimate_points.append(r_estimate)

    def __build_legend_item(self, color) -> pg.PlotDataItem:
        return pg.PlotDataItem(
            symbol='s',
            symbolPen=(0, 0, 0),
            symbolBrush=color,
            symbolSize=20,
            pen=None
        )
