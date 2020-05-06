"""
AUTHOR: Benjamin Eder
"""

########################
# GLOBAL CONFIGURATION #
########################
import logging

DEFAULT_LOG_LEVEL = logging.INFO

# Default values
DEFAULT_SIZE = 100  # Default size of the state matrix
DEFAULT_SUSCEPTIBLE_SHARE = 0.69  # Default share of susceptible cells
DEFAULT_INFECTED_SHARE = 0.01  # Default share of infected cells
DEFAULT_INFECTION_PROB = 0.2  # Default probability to get infected
DEFAULT_REMOVE_PROB = 0.6  # Default probability to get recover or die

# Color configuration
COLOR_NOT_OCCUPIED = (255, 255, 255)
COLOR_SUSCEPTIBLE = (51, 205, 255)
COLOR_INFECTED = (255, 51, 102)
COLOR_REMOVED = (153, 153, 153)
COLOR_IMMUNE = (51, 255, 153)
COLOR_DEAD = (153, 153, 153)
COLOR_INCUBATION = (247, 127, 0)
COLOR_EFFECTIVE_REPRODUCTION_NUMBER = (100, 120, 140)
COLOR_EFFECTIVE_REPRODUCTION_NUMBER_ESTIMATED = (255, 204, 51)

# Theme configuration
IS_DARK_MODE = True
BACKGROUND_COLOR = (0, 0, 0) if IS_DARK_MODE else (255, 255, 255)
BACKGROUND_CARD_COLOR = (40, 40, 40) if IS_DARK_MODE else (240, 240, 240)
BACKGROUND_LIGHT_COLOR = (60, 60, 60) if IS_DARK_MODE else (220, 220, 220)
BACKGROUND_SPACER_COLOR = (82, 98, 104) if IS_DARK_MODE else (150, 160, 180)
FOREGROUND_COLOR = (255, 255, 255) if IS_DARK_MODE else (20, 20, 20)
ACCENT_COLOR = (255, 51, 102)
ACCENT_BRIGHTER_COLOR = (255, 102, 140)

BATCH_RUN_ENABLED = False
BATCH_RUN_ITERATIONS = 100
BATCH_RESULT_FILE = 'BATCH_RESULT.txt'

# QT configuration
styleSheet = f"""
* {{
    color: rgb({FOREGROUND_COLOR[0]}, {FOREGROUND_COLOR[1]}, {FOREGROUND_COLOR[2]});
    font-size: 12pt;
    font-family: 'Manrope';
}}

QMainWindow {{
    background-color: rgb({BACKGROUND_COLOR[0]}, {BACKGROUND_COLOR[1]}, {BACKGROUND_COLOR[2]});
}}

QToolTip {{
    color: #333333;
}}

QPushButton {{
    background-color: rgb({ACCENT_COLOR[0]}, {ACCENT_COLOR[1]}, {ACCENT_COLOR[2]});
    color: white;
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: rgba({ACCENT_BRIGHTER_COLOR[0]}, {ACCENT_BRIGHTER_COLOR[1]}, {ACCENT_BRIGHTER_COLOR[2]}, 0.8);
}}

QPushButton:pressed {{
    background-color: rgb({ACCENT_BRIGHTER_COLOR[0]}, {ACCENT_BRIGHTER_COLOR[1]}, {ACCENT_BRIGHTER_COLOR[2]});
}}

QPushButton:disabled {{
    background-color: rgb({BACKGROUND_LIGHT_COLOR[0]}, {BACKGROUND_LIGHT_COLOR[1]}, {BACKGROUND_LIGHT_COLOR[2]});
    color: grey;
}}

QPushButton#iconbutton {{
    border-radius: 12px;
    qproperty-iconSize: 24px;
}}

QLineEdit {{
    background-color: rgb({BACKGROUND_LIGHT_COLOR[0]}, {BACKGROUND_LIGHT_COLOR[1]}, {BACKGROUND_LIGHT_COLOR[2]});
    border-radius: 10px;
}}

QSlider::groove:horizontal {{
    height: 3px;
    margin: 0px;
    background-color: rgb({BACKGROUND_LIGHT_COLOR[0]}, {BACKGROUND_LIGHT_COLOR[1]}, {BACKGROUND_LIGHT_COLOR[2]});
}}

QSlider::handle:horizontal {{
    background-color: rgb({ACCENT_COLOR[0]}, {ACCENT_COLOR[1]}, {ACCENT_COLOR[2]});
    width: 30px;
    height: 20px;
    line-height: 20px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 4px;
}}

QSlider::handle:horizontal:disabled {{
    background-color: grey;
}}

QFrame#horizontalsep {{
    background-color: transparent;
    color: rgb({BACKGROUND_COLOR[0]}, {BACKGROUND_COLOR[1]}, {BACKGROUND_COLOR[2]});
}}

QWidget#controls {{
    background-color: rgb({BACKGROUND_CARD_COLOR[0]}, {BACKGROUND_CARD_COLOR[1]}, {BACKGROUND_CARD_COLOR[2]});
}}

QLabel#heading {{
    background-color: rgb({BACKGROUND_LIGHT_COLOR[0]}, {BACKGROUND_LIGHT_COLOR[1]}, {BACKGROUND_LIGHT_COLOR[2]});
    font-size: 18pt;
    padding: 4px 5px;
    border-radius: 3px;
    margin: 5px 0;
}}

QComboBox {{
    background-color: rgb({BACKGROUND_LIGHT_COLOR[0]}, {BACKGROUND_LIGHT_COLOR[1]}, {BACKGROUND_LIGHT_COLOR[2]});
    border-radius: 3px;
    padding: 1px 10px 1px 10px;
    min-width: 6em;
}}

QComboBox:disabled {{
    color: grey;
}}

QComboBox::down-arrow {{
    image: url(res/arrow_down.png);
    width: 24px;
    height: 24px;
    margin-right: 10px;
}}

QComboBox::drop-down {{
    border: 0px;
}}

QComboBox QAbstractItemView {{
    background-color: rgb({BACKGROUND_LIGHT_COLOR[0]}, {BACKGROUND_LIGHT_COLOR[1]}, {BACKGROUND_LIGHT_COLOR[2]});
    selection-background-color: rgb({BACKGROUND_CARD_COLOR[0]}, {BACKGROUND_CARD_COLOR[1]}, {BACKGROUND_CARD_COLOR[2]});
}}

QCheckBox {{
    font-size: 10pt;
}}

QCheckBox:disabled {{
    color: grey;
}}

QSpinBox {{
    background-color: rgb({BACKGROUND_LIGHT_COLOR[0]}, {BACKGROUND_LIGHT_COLOR[1]}, {BACKGROUND_LIGHT_COLOR[2]});
    border: none;
    border-radius: 3px;
    padding-right: 15px; /* make room for the arrows */
}}

QSpinBox::disabled {{
    color: grey;
}}

QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right; /* position at the top right corner */

    width: 16px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
    border-radius: 3px;
    border: none;
}}

QSpinBox::up-button:hover {{
    background-color: rgb({ACCENT_COLOR[0]}, {ACCENT_COLOR[1]}, {ACCENT_COLOR[2]});
}}

QSpinBox::up-button:pressed {{
    background-color: rgba({ACCENT_COLOR[0]}, {ACCENT_COLOR[1]}, {ACCENT_COLOR[2]}, 0.7);
}}

QSpinBox::up-arrow {{
    image: url(res/arrow_up.png);
    width: 16px;
    height: 10px;
}}

QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right; /* position at bottom right corner */

    width: 16px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
    border-radius: 3px;
    border: none;
}}

QSpinBox::down-button:hover {{
    background-color: rgb({ACCENT_COLOR[0]}, {ACCENT_COLOR[1]}, {ACCENT_COLOR[2]});
}}

QSpinBox::down-button:pressed {{
    background-color: rgba({ACCENT_COLOR[0]}, {ACCENT_COLOR[1]}, {ACCENT_COLOR[2]}, 0.7);
}}

QSpinBox::down-arrow {{
    image: url(res/arrow_down.png);
    width: 16px;
    height: 10px;
}}

QAbstractScrollArea {{
    border: none;
}}

QAbstractScrollArea #scrollAreaWidgetContents {{
    background-color: rgb({BACKGROUND_CARD_COLOR[0]}, {BACKGROUND_CARD_COLOR[1]}, {BACKGROUND_CARD_COLOR[2]});
}}

QScrollBar:horizontal {{
    height: 15px;
    margin: 3px 15px 3px 15px;
    border: 1px transparent #2A2929;
    border-radius: 4px;
    background-color: transparent;
}}

QScrollBar::handle:horizontal {{
    background-color: rgba({FOREGROUND_COLOR[0]}, {FOREGROUND_COLOR[1]}, {FOREGROUND_COLOR[2]}, 0.2);
    min-width: 5px;
    border-radius: 4px;
}}

QScrollBar::add-line:horizontal {{
    margin: 0px 3px 0px 3px;
    border-image: url(:/qss_icons/rc/right_arrow_disabled.png);
    width: 10px;
    height: 10px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}}

QScrollBar::sub-line:horizontal {{
    margin: 0px 3px 0px 3px;
    border-image: url(:/qss_icons/rc/left_arrow_disabled.png);
    height: 10px;
    width: 10px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}}

QScrollBar::add-line:horizontal:hover,QScrollBar::add-line:horizontal:on {{
    border-image: url(:/qss_icons/rc/right_arrow.png);
    height: 10px;
    width: 10px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}}

QScrollBar::sub-line:horizontal:hover, QScrollBar::sub-line:horizontal:on {{
    border-image: url(:/qss_icons/rc/left_arrow.png);
    height: 10px;
    width: 10px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}}

QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal {{
    background: none;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 15px;
    margin: 15px 3px 15px 3px;
    border: 1px transparent #2A2929;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: rgba({FOREGROUND_COLOR[0]}, {FOREGROUND_COLOR[1]}, {FOREGROUND_COLOR[2]}, 0.2);
    min-height: 5px;
    border-radius: 4px;
}}

QScrollBar::sub-line:vertical {{
    margin: 3px 0px 3px 0px;
    border-image: url(:/qss_icons/rc/up_arrow_disabled.png);
    height: 10px;
    width: 10px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}}

QScrollBar::add-line:vertical {{
    margin: 3px 0px 3px 0px;
    border-image: url(:/qss_icons/rc/down_arrow_disabled.png);
    height: 10px;
    width: 10px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}}

QScrollBar::sub-line:vertical:hover,QScrollBar::sub-line:vertical:on {{
    border-image: url(:/qss_icons/rc/up_arrow.png);
    height: 10px;
    width: 10px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}}

QScrollBar::add-line:vertical:hover, QScrollBar::add-line:vertical:on {{
    border-image: url(:/qss_icons/rc/down_arrow.png);
    height: 10px;
    width: 10px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
    background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
"""

############################
# GLOBAL CONFIGURATION END #
############################
