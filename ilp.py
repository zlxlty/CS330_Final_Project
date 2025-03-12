#!/usr/bin/env python

"""
ilp.py - Integer linear programming approximation scheduler.
This module uses an ILP formulation with the Gurobi optimizer to
schedule tasks by assigning jobs to valid frames within a hyperperiod.
"""

import json
import sys
from typing import Dict, Tuple, List, Optional, Any

from taskset import *
from scheduleralgorithm import *
from CyclicSchedulerAlgorithm import *
from schedule import ScheduleInterval, Schedule
from display import SchedulingDisplay

from gurobipy import Model, GRB
from math import lcm, gcd
from collections import defaultdict


#############################################################
# IlpScheduler class                                        #
#############################################################
class IlpScheduler(CyclicSchedulerAlgorithm):
    """
    An ILP-based scheduler that maps task jobs to valid time frames
    in order to construct a feasible schedule.
    """

    def __init__(self, taskSet: TaskSet) -> None:
        """
        Initialize the ILP scheduler.
        """
        super().__init__(taskSet)

    def _makeAssignmentDecision(self) -> Optional[Dict[int, List[Job]]]:
        """
        Formulate and solve the ILP model for job-to-frame assignment.
        - Decision variables x[i,j,k] indicate whether job j of task i is assigned to frame k.
        - Each job must be assigned exactly one valid frame.
        - The sum of the execution times of jobs assigned in a frame must not exceed the frame size.
        :return: A mapping from frame index k to the list of jobs assigned to that frame,
                 or None if no feasible solution is found.
        """
        model: Model = Model("CyclicExecutive")

        # Create decision variables x[i,j,k] (binary) for each valid (i, j, k) combination.
        x: Dict[Tuple[int, int, int], Any] = {}
        for (i, j), validFrames in self.validFrameMap.items():
            for k in validFrames:
                x[(i, j, k)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}_{k}")

        model.update()

        # Constraint 1: Each job must be scheduled in exactly one frame.
        for job in self.taskSet.jobs:
            i: int = job.task.id
            j: int = job.id
            model.addConstr(
                sum(x[(i, j, k)] for k in self.validFrameMap[(i, j)]) == 1,
                name=f"jobAssign_{i}_{j}",
            )

        # Constraint 2: For each frame, the total assigned work must not exceed the frame size.
        numFrames: int = self.hyperPeriod // self.frameSize
        for k in range(1, numFrames + 1):
            totalWork = 0
            for job in self.taskSet.jobs:
                i: int = job.task.id
                j: int = job.id
                # Only include jobs that can be assigned to frame k.
                if k in self.validFrameMap[(i, j)]:
                    totalWork += job.task.wcet * x[(i, j, k)]
            model.addConstr(totalWork <= self.frameSize, name=f"frameCap_{k}")

        # Dummy objective: minimize 0 (we only need a feasible solution).
        model.setObjective(0, GRB.MINIMIZE)
        model.optimize()

        # If a feasible assignment is found, extract the decision variables that are set.
        if model.status == GRB.OPTIMAL:
            assignedVars: List[str] = [
                var.varName for var in model.getVars() if var.x > 0.5
            ]
            intervalToJobs: Dict[int, List[Job]] = defaultdict(list)
            # Parse variable names to determine which job is assigned to which frame.
            for varName in assignedVars:
                _, i_str, j_str, k_str = varName.split("_")
                i, j, k = int(i_str), int(j_str), int(k_str)
                intervalToJobs[k].append(self.taskSet.getTaskById(i).getJobById(j))
            return intervalToJobs
        else:
            return None


#############################################################
# Main execution block                                      #
# When this file is run directly, load a taskset from a JSON  #
# file (default: "tasksets/ce_test2.json") and run the ILP     #
# scheduler to generate and display a schedule.             #
#############################################################

if __name__ == "__main__":
    # Determine the JSON file path from command-line arguments or use default.
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "tasksets/ce_test3.json"

    # Load the task set data from the specified file.
    with open(file_path) as json_data:
        data = json.load(json_data)

    # Initialize the task set.
    taskSet = TaskSet(data)

    # Print tasks and jobs for verification.
    taskSet.printTasks()
    taskSet.printJobs()

    # Create an instance of the ILP scheduler.
    ilp = IlpScheduler(taskSet)
    print(f"ilp.hyperPeriod: {ilp.hyperPeriod}")
    print(f"ilp.frameSize: {ilp.frameSize}")
    print(f"ilp.validFrameSet: {ilp.validFrameMap}")

    intervals = ilp._makeAssignmentDecision()
    print(intervals)

    # Build the complete schedule from time 0 to 20.
    schedule = ilp.buildSchedule(0, 20)

    # Print the schedule intervals (including idle intervals).
    schedule.printIntervals(displayIdle=True)

    # Validate the schedule by checking worst-case execution times and overall feasibility.
    print("\n// Validating the schedule:")
    schedule.checkWcets()
    schedule.checkFeasibility()

    # Display the schedule graphically.
    display = SchedulingDisplay(width=800, height=480, fps=33, scheduleData=schedule)
    display.run()
