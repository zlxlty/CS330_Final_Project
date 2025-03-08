#!/usr/bin/env python

"""
edf.py - Earliest Deadline First scheduler

EdfScheduler: scheduling algorithm that executes EDF (preemptive)
EdfPriorityQueue: priority queue that prioritizes by absolute deadline
"""

import json
import sys

from taskset import *
from scheduleralgorithm import *
from schedule import ScheduleInterval, Schedule
from display import SchedulingDisplay

#############################################################
# EdfScheduler class                                        #
#############################################################


class EdfScheduler(SchedulerAlgorithm):
    def __init__(self, taskSet):
        SchedulerAlgorithm.__init__(self, taskSet)

    def buildSchedule(self, startTime, endTime):
        self._buildPriorityQueue(EdfPriorityQueue)

        # TODO: build a scheduling using EDF, using _makeSchedulingDecision() to determine
        # the next decision to be made (think about how this differs from FIFO)
        time = startTime
        self.schedule.startTime = time

        previousJob = None
        didPreemptPrevious = False

        # Loop until the priority queue is empty, executing jobs non-preemptively in FIFO order
        while not self.priorityQueue.isEmpty():
            # Make a scheduling decision resulting in an interval
            interval, newJob = self._makeSchedulingDecision(time, previousJob)

            if interval.isIdle() and not self.priorityQueue.isEmpty():
                nextTime = min(j.releaseTime for j in self.priorityQueue.jobs)
            else:
                nextTime = interval.startTime

            didPreemptPrevious = interval.didPreemptPrevious  # should be False for FIFO

            if previousJob is not None:
                runDuration = nextTime - time
                previousJob.execute(runDuration)

                if didPreemptPrevious and (not previousJob.isCompleted()):
                    self.priorityQueue.addJob(previousJob)

            self.schedule.addInterval(interval)

            time = nextTime
            previousJob = newJob

        # If there is still a previous job, complete it and update the time
        if previousJob is not None:
            time += previousJob.remainingTime
            previousJob.executeToCompletion()

        # Add the final idle interval
        finalInterval = ScheduleInterval()
        finalInterval.initialize(time, None, False)
        self.schedule.addInterval(finalInterval)

        # Post-process the intervals to set the end time and whether the job completed
        latestDeadline = max([job.deadline for job in self.taskSet.jobs])
        endTime = max(time + 1.0, latestDeadline, float(endTime))
        self.schedule.postProcessIntervals(endTime)

        return self.schedule

    def _makeSchedulingDecision(self, t, previousJob):
        """
        Makes a scheduling decision after time t.  Assumes there is at least one job
        left in the priority queue.

        t: the beginning of the previous time interval, if one exists (or 0 otherwise)
        previousJob: the job that was previously executing, and will either complete or be preempted

        returns: (ScheduleInterval instance, Job instance of next job to execute)
        """
        # TODO: Make a scheduling decision at the next scheduling time point after time t.
        # Let's call this new time nextTime.
        #
        # If there was no previous job executing, the next job will come from the priority
        # queue at or after time t.
        # If there was a previous job executing, choose the highest-priority job from the
        # priority queue of those released at or before time nextTime.
        #
        # Note that if there was a previous job but when it finishes, no more jobs are ready
        # (released prior to that time), then there should be no job associated with the new
        # interval.  The ScheduleInterval.initialize method will handle this, you just have
        # to provide it with None rather than a job.
        #
        # Once you have the next job to execute (if any), build the interval (which starts at
        # nextTime) and return it and the next job.
        interval = ScheduleInterval()
        nextTime = t

        if previousJob is not None and not previousJob.isCompleted():
            nextTime += previousJob.remainingTime

            preemptor = self.priorityQueue.popPreemptingJob(t, previousJob)
            if preemptor is None:
                nextJob = self.priorityQueue.popFirst(nextTime)
                if not nextJob:
                    nextJob = None
                interval.initialize(nextTime, nextJob, False)
            else:
                nextTime = preemptor.releaseTime
                interval.initialize(nextTime, preemptor, True)
                nextJob = preemptor

        else:
            nextJob = self.priorityQueue.popFirst(nextTime)

            if not nextJob:
                nextJob = None

            interval.initialize(nextTime, nextJob, False)

        return interval, nextJob


#############################################################
# EdfPriorityQueue class                                    #
#############################################################


class EdfPriorityQueue(PriorityQueue):
    def __init__(self, jobReleaseDict):
        """
        Creates a priority queue of jobs ordered by absolute deadline.
        """
        PriorityQueue.__init__(self, jobReleaseDict)

    def _sortQueue(self):
        # EDF orders by absolute deadline
        self.jobs.sort(key=lambda x: (x.deadline, x.task.id, x.id))

    def _findFirst(self, t):
        """
        Returns the index of the highest-priority job released at or before t,
        or -1 if the queue is empty or if all remaining jobs are released after t.
        """
        if self.isEmpty():
            return -1

        currentJobs = [
            (i, job) for (i, job) in enumerate(self.jobs) if job.releaseTime <= t
        ]
        if len(currentJobs) == 0:
            return -1

        currentJobs.sort(key=lambda x: (x[1].deadline, x[1].task.id, x[1].id))
        return currentJobs[0][0]  # get the index from the tuple in the 0th position

    def popNextJob(self, t):
        """
        Removes and returns the highest-priority job of those released at or after t,
        or None if no jobs are released at or after t.
        """
        laterJobs = [
            (i, job) for (i, job) in enumerate(self.jobs) if job.releaseTime >= t
        ]

        if len(laterJobs) == 0:
            return None

        laterJobs.sort(key=lambda x: (x[1].releaseTime, x[1].deadline, x[1].task.id))
        return self.jobs.pop(
            laterJobs[0][0]
        )  # get the index from the tuple in the 0th position

    def popPreemptingJob(self, t, job):
        """
        Removes and returns the job that will preempt job 'job' after time 't', or None
        if no such preemption will occur (i.e., if no higher-priority jobs
        are released before job 'job' will finish executing).

        t: the time after which a preemption may occur
        job: the job that is executing at time 't', and which may be preempted
        """
        if job is None:
            return None

        hpJobs = [
            (i, j)
            for (i, j) in enumerate(self.jobs)
            if (
                (
                    j.deadline < job.deadline
                    or (j.deadline == job.deadline and j.task.id < job.task.id)
                )
                and j.releaseTime > t
                and j.releaseTime < t + job.remainingTime
            )
        ]

        if len(hpJobs) == 0:
            return None

        hpJobs.sort(key=lambda x: (x[1].releaseTime, x[1].deadline, x[1].task.id))
        return self.jobs.pop(
            hpJobs[0][0]
        )  # get the index from the tuple in the 0th position


#############################################################
# When this file is run, try it out with a given file       #
# (or with the default of p1_test1.json)                    #
#############################################################

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "tasksets/w1_prob3a.json"

    with open(file_path) as json_data:
        data = json.load(json_data)

    taskSet = TaskSet(data)

    taskSet.printTasks()
    taskSet.printJobs()

    edf = EdfScheduler(taskSet)
    schedule = edf.buildSchedule(0, 6)

    schedule.printIntervals(displayIdle=True)

    print("\n// Validating the schedule:")
    schedule.checkWcets()
    schedule.checkFeasibility()

    display = SchedulingDisplay(width=800, height=480, fps=33, scheduleData=schedule)
    display.run()
