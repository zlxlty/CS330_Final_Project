#!/usr/bin/env python

"""
schedulerAlgorithm.py

SchedulerAlgorithm: base class for scheduling algorithms
PriorityQueue: base class for priority queues used to maintain the queue of jobs
"""

from schedule import Schedule
from taskset import TaskSet

#############################################################
# SchedulerAlgorithm class                                  #
#############################################################


class SchedulerAlgorithm(object):
    def __init__(self, taskSet: TaskSet):
        self.taskSet = taskSet

        self.schedule = Schedule(None, taskSet)
        self.time = 0

    def buildSchedule(self):
        raise NotImplementedError()

    def _makeSchedulingDecision(self, t):
        raise NotImplementedError()

    def _buildPriorityQueue(self, queueType):
        """
        Builds and returns the priority queue of jobs.

        queueType: the class name of the type of priority queue to create
        """
        jobReleases = {}

        for job in self.taskSet.jobs:
            r = job.releaseTime

            if r not in jobReleases:
                jobReleases[r] = [job]
            else:
                jobReleases[r].append(job)

        self.priorityQueue = queueType(jobReleases)


#############################################################
# PriorityQueue class                                       #
#############################################################


class PriorityQueue(object):
    def __init__(self, jobReleaseDict):
        """
        Builds the priority queue of all jobs.
        This will need to be sorted to match the scheduling algorithm.
        """
        self.jobs = []

        releaseTimes = sorted(jobReleaseDict.keys())
        for time in releaseTimes:
            for job in jobReleaseDict[time]:
                self.jobs.append(job)

        self._sortQueue()

    def isEmpty(self):
        """
        Returns a boolean indicating whether the priority queue is empty.
        """
        return len(self.jobs) == 0

    def addJob(self, job):
        """
        Adds a job to the priority queue.
        """
        self.jobs.append(job)
        self._sortQueue()

    def getFirst(self, t):
        """
        Returns the job with highest priority at time t, or None
        if no such jobs exist.
        """
        index = self._findFirst(t)
        if index >= 0:
            return self.jobs[index]
        else:
            return None

    def popFirst(self, t):
        """
        Removes and returns the job with the highest priority at time t,
        if one exists.
        """
        index = self._findFirst(t)
        if index >= 0:
            return self.jobs.pop(index)

    def _sortQueue(self):
        raise NotImplementedError

    def _findFirst(self, t):
        raise NotImplementedError

    def popNextJob(self, t):
        raise NotImplementedError

    def popPreemptingJob(self, t, job):
        raise NotImplementedError
