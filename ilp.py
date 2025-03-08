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
from schedule import ScheduleInterval, Schedule
from display import SchedulingDisplay

from gurobipy import Model, GRB
from math import lcm, gcd
from collections import defaultdict


#############################################################
# IlpScheduler class                                        #
#############################################################
class IlpScheduler(SchedulerAlgorithm):
    """
    An ILP-based scheduler that maps task jobs to valid time frames
    in order to construct a feasible schedule.
    """

    def __init__(self, taskSet: TaskSet) -> None:
        """
        Initialize the ILP scheduler.
        - Computes the hyperperiod as the least common multiple of all task periods.
        - Determines a valid frame size that divides the hyperperiod.
        - Builds a mapping (validFrameMap) of each job (identified by task id and job id)
          to the set of frames in which it can be scheduled.
        """
        super().__init__(taskSet)
        self.hyperPeriod: int = self._getHyperPeriod()
        self.frameSize: int = self._getValidFrameSize()
        # Build valid frame set for each job:
        # For each job (i,j), validFrameMap[(i,j)] is a list of frame indices k
        # such that the whole frame k lies within the job's allowable time window.
        self.validFrameMap: Dict[Tuple[int, int], List[int]] = (
            self._buildValidFrameSet()
        )

    def _getHyperPeriod(self) -> int:
        """
        Calculate the hyperperiod, which is the least common multiple (LCM)
        of all task periods.
        :return: The hyperperiod as an integer.
        """
        return lcm(*[int(t.period) for t in self.taskSet.tasks.values()])

    def _buildValidFrameSet(self) -> Dict[Tuple[int, int], List[int]]:
        """
        Build a mapping of valid frames for each job.
        For each job, determine the frames k where the entire frame fits
        into the job's execution window: [(j-1)*period, j*period].
        :return: Dictionary mapping (task id, job id) to a list of valid frame indices.
        """
        valid_frame: Dict[Tuple[int, int], List[int]] = {}
        numFrames: int = self.hyperPeriod // self.frameSize

        # NOTE: The original code uses 'taskSet.jobs' without 'self'.
        # We assume that 'self.taskSet.jobs' is the intended reference.
        for job in self.taskSet.jobs:
            i: int = job.task.id
            j: int = job.id
            valid_frame[(i, j)] = []
            for k in range(1, numFrames + 1):
                p: int = job.task.period
                # Check if frame k lies completely within the job's period window.
                if (k - 1) * self.frameSize >= ((j - 1) * p) and k * self.frameSize <= (
                    j * p
                ):
                    valid_frame[(i, j)].append(k)
        return valid_frame

    def _isValidFrameSize(self, frameSize: int) -> bool:
        """
        Check if a given frame size is valid.
        A valid frame size must:
         - Divide the hyperperiod evenly.
         - Be at least as large as each task's worst-case execution time (wcet).
         - Satisfy the constraint: 2*frameSize - gcd(task.period, frameSize) <= task.relativeDeadline
        :param frameSize: The candidate frame size.
        :return: True if valid, False otherwise.
        """
        # Frame size must divide the hyperperiod.
        if self.hyperPeriod % frameSize != 0:
            return False

        # Check frame size against each task's wcet and deadline constraints.
        for task in self.taskSet.tasks.values():
            if frameSize < task.wcet:
                return False
            if (
                2 * frameSize - gcd(int(task.period), int(frameSize))
            ) > task.relativeDeadline:
                return False

        return True

    def _getValidFrameSize(self) -> int:
        """
        Determine a valid frame size by iterating from the hyperperiod downwards.
        The first candidate frame size that satisfies all constraints is returned.
        :return: A valid frame size as an integer.
        """
        for i in range(self.hyperPeriod, 1, -1):
            if self._isValidFrameSize(i):
                return i
        raise ValueError("No valid frame size found.")

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
        for (i, j), validFrame in self.validFrameMap.items():
            for k in validFrame:
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

    def buildSchedule(self, startTime: float, endTime: float) -> Schedule:
        """
        Build a complete schedule based on the ILP assignment decision.
        The schedule is constructed frame by frame:
         - Jobs are assigned to intervals within frames as decided by the ILP.
         - Idle intervals are added if the frame is not fully occupied.
         - The final idle interval is added at the end.
         - Post-processing sets interval end times and checks job completions.
        :param startTime: The starting time of the schedule.
        :param endTime: The ending time (or a deadline) for the schedule.
        :return: The constructed schedule object, or None if schedule is invalid.
        """
        intervalToJobs: Optional[Dict[int, List[Job]]] = self._makeAssignmentDecision()

        # If no feasible assignment is found, return None.
        if intervalToJobs is None:
            return None

        time: float = startTime
        self.schedule.startTime = time
        numFrames: int = self.hyperPeriod // self.frameSize

        # Process each frame in the hyperperiod.
        for k in range(1, numFrames + 1):
            jobs: List[Job] = intervalToJobs[k]
            # Sort jobs based on task id for consistency.
            jobs.sort(key=lambda j: j.task.id)
            for job in jobs:
                # Validate that the current time does not exceed the end of the frame.
                if time > k * self.frameSize:
                    print("Invalid Schedule")
                    return None  # type: ignore
                # Create an interval for the job and update time.
                interval: ScheduleInterval = ScheduleInterval()
                interval.initialize(time, job, False)
                self.schedule.addInterval(interval)
                time += job.remainingTime

            # If the frame is not fully utilized, add an idle interval.
            if time < k * self.frameSize:
                interval: ScheduleInterval = ScheduleInterval()
                interval.initialize(time, None, False)
                self.schedule.addInterval(interval)
                time = k * self.frameSize

        # Add a final idle interval until the specified end time.
        finalInterval: ScheduleInterval = ScheduleInterval()
        finalInterval.initialize(endTime, None, False)
        self.schedule.addInterval(finalInterval)

        # Post-process the schedule to finalize interval end times and mark job completions.
        latestDeadline: float = max([job.deadline for job in self.taskSet.jobs])
        adjustedEndTime: float = max(latestDeadline, float(endTime))
        self.schedule.postProcessIntervals(adjustedEndTime)

        return self.schedule


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
        file_path = "tasksets/ce_test2.json"

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
