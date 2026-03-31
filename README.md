# Agent-Based Model Simulations

This repository contains a Fashion Trend Model (FTM), a Demographic Transition Model (DTM), and their fused framework (FTDTM) to simulate fashion trend dynamics with population dynamics

## Setup Instructions

Follow these steps to set up your local environment, install the dependencies, and run the simulation notebook.

### 1. Create a Virtual Environment
Open your terminal, navigate to the root directory of this project, and run:
```bash
python -m venv ftdtm
```

### 2. Activate the Virtual Environment
Activate the environment to ensure packages are installed locally rather than globally.


  ```bash
  source ftdtm/bin/activate
  ```

### 3. Install Requirements
With the virtual environment active, install the required packages:
```bash
pip install -r requirements.txt
```

### 4. Run the Simulation
Launch Jupyter Notebook to open and execute the simulation:
```bash
jupyter notebook simulation.ipynb
```