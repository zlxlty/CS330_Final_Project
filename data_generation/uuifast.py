import random


# Citation: @inproceedings{cheramy2014, Author = {Ch\'eramy, Maxime and Hladik, Pierre-Emmanuel and D\'eplanche, Anne-Marie}, Booktitle = {Proc. of the 5th International Workshop on Analysis Tools and Methodologies for Embedded and Real-time Systems}, Series = {WATERS}, Title = {SimSo: A Simulation Tool to Evaluate Real-Time Multiprocessor Scheduling Algorithms}, Year = {2014}}
def UUniFastDiscard(n, u, nsets, frameSize, choosePeriodFunc):
    sets = []
    while len(sets) < nsets:
        # Classic UUniFast algorithm:
        util_periods = []
        sumU = u
        for i in range(1, n):
            nextSumU = sumU * random.random() ** (1.0 / (n - i))
            util_periods.append((sumU - nextSumU, choosePeriodFunc()))
            sumU = nextSumU
        util_periods.append((sumU, choosePeriodFunc()))

        # If no task utilization exceeds 1:
        if all(ut <= 1 and pd * ut < frameSize for ut, pd in util_periods):
            sets.append(util_periods)

    return sets
