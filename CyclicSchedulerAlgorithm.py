import json
import sys

from taskset import *
from scheduleralgorithm import *
from schedule import ScheduleInterval, Schedule
from display import SchedulingDisplay

from gurobipy import Model, GRB
from typing import Dict, Tuple, List
from functools import reduce
from math import lcm, gcd
from collections import defaultdict


class CyclicSchedulerAlgorithm(SchedulerAlgorithm):
    def __init__(self, taskSet: TaskSet):
        SchedulerAlgorithm.__init__(self, taskSet)
        self.hyperPeriod = self._getHyperPeriod()
        self.frameSize = self._getValidFrameSize()
        # Define valid frame set V for each job (i,j).
        # It is a list of frames k where the job can be scheduled,
        # where the entire frame lies within [ (j-1)*T_i, j*T_i ].
        self.validFrameMap: Dict[Tuple[int, int], List[int]] = (
            self._buildValidFrameSet()
        )

    def _getHyperPeriod(self):
        return lcm(*[int(t.period) for t in self.taskSet.tasks.values()])

    def _buildValidFrameSet(self):
        # valid_frame: Map<<task_id, job_id>, frame_id>
        valid_frame = {}
        numFrames = self.hyperPeriod // self.frameSize

        for job in taskSet.jobs:
            i = job.task.id
            j = job.id
            valid_frame[(i, j)] = []
            for k in range(1, numFrames + 1):
                p = job.task.period
                # Assuming job id always increment by 1
                if (k - 1) * self.frameSize >= (
                    j - 1
                ) * p and k * self.frameSize <= j * p:
                    valid_frame[(i, j)].append(k)

        return valid_frame

    def _isValidFrameSize(self, frameSize):
        if self.hyperPeriod % frameSize != 0:
            return False

        for task in self.taskSet.tasks.values():
            if frameSize < task.wcet:
                return False

            if (
                2 * frameSize - gcd(int(task.period), int(frameSize))
                > task.relativeDeadline
            ):
                return False

        return True

    def _getValidFrameSize(self):
        for i in range(self.hyperPeriod, 1, -1):
            if self._isValidFrameSize(i):
                return i

    def _makeAssignmentDecision(self):
        model = Model("CyclicExecutive")
        # Create decision variables x[i,j,k] for valid (i,j,k)
        x = {}
        for (i, j), validFrame in self.validFrameMap.items():
            for k in validFrame:
                x[(i, j, k)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}_{k}")

        model.update()

        # Add job assignment constraints
        for job in self.taskSet.jobs:
            i = job.task.id
            j = job.id
            model.addConstr(
                sum(x[(i, j, k)] for k in self.validFrameMap[(i, j)]) == 1,
                name=f"jobAssign_{i}_{j}",
            )

        # Add frame capacity constraints for each frame k
        numFrames = self.hyperPeriod // self.frameSize
        for k in range(1, numFrames + 1):
            totalWork = 0
            for job in self.taskSet.jobs:
                i = job.task.id
                j = job.id
                if k in self.validFrameMap[(i, j)]:
                    totalWork += job.task.wcet * x[(i, j, k)]

            model.addConstr(totalWork <= self.frameSize, name=f"frameCap_{k}")

        # Set objective (dummy, since we only need feasibility)
        model.setObjective(0, GRB.MINIMIZE)
        model.optimize()

        # Print solution if feasible
        if model.status == GRB.OPTIMAL:
            assignedVars = [var.varName for var in model.getVars() if var.x > 0.5]
            intervalToJobs = defaultdict(list)

            for varName in assignedVars:
                _, i, j, k = varName.split("_")
                i, j, k = int(i), int(j), int(k)
                intervalToJobs[k].append(self.taskSet.getTaskById(i).getJobById(j))
            return intervalToJobs
        else:
            return None

    def buildSchedule(self, startTime, endTime):

        intervalToJobs = self._makeAssignmentDecision()

        time = startTime
        self.schedule.startTime = time
        numFrames = self.hyperPeriod // self.frameSize
        for k in range(1, numFrames + 1):
            jobs = intervalToJobs[k]
            jobs.sort(key=lambda j: j.task.id)
            for job in jobs:
                # assert time <= k * self.frameSize
                if time > k * self.frameSize:
                    print("Invalid Schedule")
                    return None
                interval = ScheduleInterval()
                interval.initialize(time, job, False)
                self.schedule.addInterval(interval)
                time += job.remainingTime

            # Add an idle interval in the end if the frame is not fully used.
            if time < k * self.frameSize:
                interval = ScheduleInterval()
                interval.initialize(time, None, False)
                self.schedule.addInterval(interval)
                time = k * self.frameSize

        # Add the final idle interval
        finalInterval = ScheduleInterval()
        finalInterval.initialize(endTime, None, False)
        self.schedule.addInterval(finalInterval)

        # Post-process the intervals to set the end time and whether the job completed
        latestDeadline = max([job.deadline for job in self.taskSet.jobs])
        endTime = max(latestDeadline, float(endTime))
        self.schedule.postProcessIntervals(endTime)

        return self.schedule
