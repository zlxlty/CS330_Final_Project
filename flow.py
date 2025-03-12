#!/usr/bin/env python

"""
flow.py - Network Flow scheduler.
This module uses an Network Flow formulation with the Edmonds-Karp Algorithm
to schedule tasks by assigning jobs to valid frames within a hyperperiod.
"""

import json
import sys
from typing import Dict, Tuple, List, Optional, Any

from taskset import *
from scheduleralgorithm import *
from CyclicSchedulerAlgorithm import *
from schedule import ScheduleInterval, Schedule
from display import SchedulingDisplay
from graph import edmondsKarp, NetworkDisplay

from gurobipy import Model, GRB
from math import lcm, gcd
from collections import defaultdict


#############################################################
# IlpScheduler class                                        #
#############################################################
class NetworkFlowScheduler(CyclicSchedulerAlgorithm):
    """
    An Network-Flow-based scheduler that maps task jobs to valid time frames
    in order to construct a feasible schedule.
    """

    def __init__(self, taskSet: TaskSet) -> None:
        """
        Initialize the network flow scheduler.
        """
        super().__init__(taskSet)

        """
        NodeId is a tuple of integers (i, j)
        - For job nodes, i is the task id and j is the job id.
        - For frame nodes, i is -1 and j is the frame number.
        - For source and sink nodes, i is -2 and j is 0 for source and 1 for sink.
        """
        self.numNodes = (
            len(self.taskSet.jobs) + self.numFrames + 2
        )  # magic number 2 for source and sink nodes.
        self.indexToNodeId: Dict[int, Tuple[int, int]] = self._makeIndexToNodeIdMap()
        self.nodeIdToIndex: Dict[Tuple[int, int], int] = {
            v: k for k, v in self.indexToNodeId.items()
        }

    def _makeIndexToNodeIdMap(self) -> Dict[int, Tuple[int, int]]:
        indexToNodeId: Dict[int, Tuple[int, int]] = {0: (-2, 0), 1: (-2, 1)}

        i = 2
        for job in self.taskSet.jobs:
            indexToNodeId[i] = (job.task.id, job.id)
            i += 1

        for k in range(1, self.numFrames + 1):
            indexToNodeId[i] = (-1, k)
            i += 1
        return indexToNodeId

    def runFlowAlgorithm(self):
        self.capacityMap = [
            [0 for i in range(self.numNodes)] for j in range(self.numNodes)
        ]
        self.neighbors = defaultdict(list)
        sourceIndex = self.nodeIdToIndex[(-2, 0)]
        sinkIndex = self.nodeIdToIndex[(-2, 1)]

        for k in range(1, self.numFrames + 1):
            frameIndex = self.nodeIdToIndex[(-1, k)]
            self.capacityMap[sourceIndex][frameIndex] = self.frameSize
            self.neighbors[sourceIndex].append(frameIndex)
            self.neighbors[frameIndex].append(sourceIndex)

        for job in self.taskSet.jobs:
            jobIndex = self.nodeIdToIndex[(job.task.id, job.id)]
            self.capacityMap[jobIndex][sinkIndex] = int(job.task.wcet)
            self.neighbors[jobIndex].append(sinkIndex)
            self.neighbors[sinkIndex].append(jobIndex)

        for (i, j), validFrames in self.validFrameMap.items():
            for k in validFrames:
                frameIndex = self.nodeIdToIndex[(-1, k)]
                jobIndex = self.nodeIdToIndex[(i, j)]
                self.capacityMap[frameIndex][jobIndex] = self.frameSize
                self.neighbors[frameIndex].append(jobIndex)
                self.neighbors[jobIndex].append(frameIndex)

        self.maxFlow, self.flowMap = edmondsKarp(self.capacityMap, self.neighbors, 0, 1)

        totalWorkNeeded = sum([job.task.wcet for job in self.taskSet.jobs])

        assert (
            self.maxFlow == totalWorkNeeded
        ), "Network Flow Failed to find a preemptive schedule."

    def runBestFitDescentApproximation(self):
        assert (
            self.flowMap
        ), "flowMap not initiated, please call runFlowAlgorithm first."

        preemptedJobToFrames = {}
        for job in self.taskSet.jobs:
            jobIndex = self.nodeIdToIndex[(job.task.id, job.id)]
            assignedFrameIndices = [
                i for i in range(len(self.flowMap)) if self.flowMap[i][jobIndex] > 0
            ]
            if len(assignedFrameIndices) > 1:
                preemptedJobToFrames[jobIndex] = assignedFrameIndices

        for jobIndex, frameIndices in preemptedJobToFrames.items():
            for frameIndex in frameIndices:
                curFlow = self.flowMap[frameIndex][jobIndex]
                self.flowMap[frameIndex][jobIndex] = 0
                self.flowMap[self.nodeIdToIndex[(-2, 0)]][frameIndex] -= curFlow
                self.flowMap[jobIndex][self.nodeIdToIndex[(-2, 1)]] -= curFlow
        # REVIEW - Remove for final version
        display = NetworkDisplay(12, 10, self)
        display.run(filename=f"./output/flow_reduced.png")
        # sort all preempted jobs by ascending order of their periods
        jobIds = [
            self.indexToNodeId[i]
            for i in sorted(
                list(preemptedJobToFrames.keys()),
                key=lambda i: self.taskSet.getTaskById(self.indexToNodeId[i][0]).period,
            )
        ]

        sourceIndex = self.nodeIdToIndex[(-2, 0)]
        sinkIndex = self.nodeIdToIndex[(-2, 1)]

        for jobId in jobIds:
            jobIndex = self.nodeIdToIndex[jobId]

            validFrames = self.validFrameMap[jobId]
            frameIndices = [self.nodeIdToIndex[(-1, frame)] for frame in validFrames]

            wcet = self.taskSet.getTaskById(jobId[0]).wcet

            if wcet.is_integer():
                wcet = int(wcet)

            frameIndices = sorted(
                [
                    i
                    for i in frameIndices
                    if self.capacityMap[sourceIndex][i] - self.flowMap[sourceIndex][i]
                    >= wcet
                ],
                key=lambda i: self.capacityMap[sourceIndex][i]
                - self.flowMap[sourceIndex][i],
            )

            assert (
                len(frameIndices) > 0
            ), f"BestFitDescent Failed to match job {jobId} to a frame."

            assignedFrameIndex = frameIndices[0]

            self.flowMap[sourceIndex][assignedFrameIndex] += wcet
            self.flowMap[assignedFrameIndex][jobIndex] += wcet
            self.flowMap[jobIndex][sinkIndex] += wcet

    def _makeAssignmentDecision(self) -> Optional[Dict[int, List[Job]]]:
        """
        Formulate and solve the Network Flow model for job-to-frame assignment.
        :return: A mapping from frame index k to the list of jobs assigned to that frame,
                 or None if no feasible solution is found.
        """
        try:
            self.runFlowAlgorithm()
            display = NetworkDisplay(12, 10, self)
            display.run(filename=f"./output/flow_1.png")

            self.runBestFitDescentApproximation()
            display = NetworkDisplay(12, 10, self)
            display.run(filename=f"./output/flow_2.png")
        except AssertionError as e:
            print(e)
            return None

        intervalToJobs: Dict[int, List[Job]] = defaultdict(list)
        for k in range(1, self.numFrames + 1):
            frameIndex = self.nodeIdToIndex[(-1, k)]
            row = self.flowMap[frameIndex]
            jobIds = [self.indexToNodeId[i] for i in range(len(row)) if row[i] > 0]
            for i, j in jobIds:
                intervalToJobs[k].append(self.taskSet.getTaskById(i).getJobById(j))
        return intervalToJobs


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
        file_path = "tasksets/ce_test1.json"

    # Load the task set data from the specified file.
    with open(file_path) as json_data:
        data = json.load(json_data)

    # Initialize the task set.
    taskSet = TaskSet(data)

    # Print tasks and jobs for verification.
    taskSet.printTasks()
    taskSet.printJobs()

    # Create an instance of the ILP scheduler.
    flow = NetworkFlowScheduler(taskSet)
    print(f"ilp.hyperPeriod: {flow.hyperPeriod}")
    print(f"ilp.frameSize: {flow.frameSize}")
    print(f"ilp.validFrame Set: {flow.validFrameMap}")
    print(f"ilp.indexToNodeId Set: {flow.indexToNodeId}")
    print(f"ilp.nodeIdToIndex Set: {flow.nodeIdToIndex}")

    schedule = flow.buildSchedule(0, 100)
    # # Build the complete schedule from time 0 to 20.
    # schedule = ilp.buildSchedule(0, 20)

    # Print the schedule intervals (including idle intervals).
    schedule.printIntervals(displayIdle=True)

    # Validate the schedule by checking worst-case execution times and overall feasibility.
    print("\n// Validating the schedule:")
    schedule.checkWcets()
    schedule.checkFeasibility()

    # Display the schedule graphically.
    display = SchedulingDisplay(width=800, height=480, fps=33, scheduleData=schedule)
    display.run()
