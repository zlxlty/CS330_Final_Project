from taskset import *
from scheduleralgorithm import *
from schedule import Schedule, ScheduleInterval
from typing import Dict, Tuple, List, Optional, Any

from math import lcm, gcd


class CyclicSchedulerAlgorithm(SchedulerAlgorithm):
    def __init__(self, taskSet: TaskSet) -> None:
        """
        - Computes the hyperperiod as the least common multiple of all task periods.
        - Determines a valid frame size that divides the hyperperiod.
        - Builds a mapping (validFrameMap) of each job (identified by task id and job id)
          to the set of frames in which it can be scheduled.
        """
        super().__init__(taskSet)
        self.hyperPeriod: int = self._getHyperPeriod()
        self.frameSize: int = self._getValidFrameSize()
        self.numFrames: int = self.hyperPeriod // self.frameSize
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

        for job in self.taskSet.jobs:
            i: int = job.task.id
            j: int = job.id
            valid_frame[(i, j)] = []
            for k in range(1, self.numFrames + 1):
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
        - Decision variables x[i,j,k] indicate whether job j of task i is assigned to frame k.
        - Each job must be assigned exactly one valid frame.
        - The sum of the execution times of jobs assigned in a frame must not exceed the frame size.
        :return: A mapping from frame index k to the list of jobs assigned to that frame,
                 or None if no feasible solution is found.
        """
        raise NotImplementedError()

    def buildSchedule(self, startTime: float, endTime: float) -> Schedule:
        """
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

        # Process each frame in the hyperperiod.
        for k in range(1, self.numFrames + 1):
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
