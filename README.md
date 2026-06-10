# Thermal Front Side Temperature Simulation

## Overview

This application models front side temperature, (T_f), as a function of supplied power percentage, (Z).

Two analytical models are included:
Simplified Model

Uses the direct analytical relationship:

This model produces a linear relationship between (T_f) and (Z).

### Quartic Dependence Model

Uses the full quartic equation

The quartic is solved analytically using Ferrari's Method and Cardano's Formula. No numerical root solvers are used.

## Features

* Simplified analytical model
* Full quartic analytical model
* Adjustable sample size
* CSV export
* Graph export

## Installation

Install required packages:

```bash
pip install -r requirements.txt
```

## Running

```bash
python thermal_front_temp_gui.py
```

## Inputs

| Parameter | Description          |
| --------- | -------------------- |
| τ         | Material thickness   |
| A         | Surface area         |
| k         | Thermal conductivity |
| εf        | Front emissivity     |
| εb        | Back emissivity      |
| Tb        | Back temperature     |
| Twall     | Wall temperature     |
| Pmax      | Maximum power        |
| Z         | Power percentage     |

## Notes

* Temperatures are expressed in Kelvin.
* The graph x axis always spans 0% to 100%.
* CSV export uses the selected sample size.
* Only analytical methods are used throughout the model.
