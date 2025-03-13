# Job Assignment in the Cyclic Executive Model

This repository contains the final project for the **CS330 Intro to Real-Time Programming** course. The project addresses the job assignment issue within the cyclic executive model, offering both a network flow approach (using the Edmonds-Karp algorithm) and an integer linear programming (ILP) approach to generate job assignments.

## Overview

The project workflow is as follows:
1. **Data Generation:**  
   Run `data_generation/generate_data.py` to create JSON files defining various tasksets.
2. **Job Assignment:**  
   - Run `flow.py` to generate job assignments and visualizations using the network flow method (Edmonds-Karp algorithm).  
   - Alternatively, run `ilp.py` to generate job assignments and visualizations using integer linear programming.
3. **Testing:**  
   Run `run_test.py` for different taskset sizes (specified by the `nTasks` parameter) to collect success rate and execution time data. Then, use the `consolidate_json_files()` function to merge all output JSONs into a single `data.json` file in the root directory.
4. **Visualization:**  
   Run `visualization.py` to visualize the combined data using the visualization module.

## Requirements

- **Python:** 3.12.8  
- **Environment Manager:** [Poetry](https://python-poetry.org/)  
- **Platform:** MacBook Air with an M2 chip (other platforms should work as well)

## Installation

1. **Install Poetry** (if not already installed):  
   Follow the instructions on the [Poetry website](https://python-poetry.org/docs/#installation).

2. **Clone the Repository:**
   ```bash
   git clone https://github.com/zlxlty/CS330_Final_Project.git
   cd CS330_Final_Project
   ```
3. **Activate the Virtual Environment**
   ```bash
   poetry shell
   ```
4. **Install Dependencies:**
   ```bash
   poetry install
   ```

## Usage
1. **Generate Taskset Data**  
   Change the `nTasks` parameter in the main section of `data_generation/generate_data.py` to the number of tasks you want in each taskset. Then, in the project's root directory run
   ```bash
   python data_generation/generate_data.py
   ```
   It will generate a `tasksets` folder containing
2. Generate Job Assignment