# Epidemic simulator

## Preface
This project was written for a university project for the seminar "Modelling and Simulation". For this project, we had to implement the widely used SIR-model and some extensions to it.

## SIR-Model 
Further information for the SIR-Model can be found on (Wikipedia)[https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology#The_SIR_model] or in our paper (in German)

## Installation

Make sure to have Python `>3.8.2` installed.

The following packages need to be installed aside from the Python standard library:

| Package | Version | Command |
| --- | --- | --- |
| `numpy` | `1.18` | `pip install numpy` |
| `PyQt5` | `5.14` | `pip install PyQt5` |
| `pyqtgraph` | `0.11.0rc0` | `pip install pyqtgraph` possibly, depending on the distro `pip install git+https://github.com/pyqtgraph/pyqtgraph@develop` is necessary |
| `observable` | `1.0.3` | `pip install observable` |

## Run the simulator

Run the following command on the terminal in the folder `sim`:

```bash
python main.py
```
