from uuifast import UUniFastDiscard
import random
import os
import json
import math

PERIODS = [6, 12, 18, 24]
choosePeriodFunc = lambda: random.choice(PERIODS)


def generate_data(folderPath, nSets=400, nTasks=15, uStep=0.05):
    assert (
        uStep > 0 and uStep < 1
    ), "Please input a utilization step size in between 0 and 1."

    curU = uStep
    while curU < 1:
        sets = UUniFastDiscard(nTasks, curU, nSets, 6, choosePeriodFunc)
        curFolderPath = "/".join([folderPath, str(round(curU, 3))])
        os.makedirs(curFolderPath, exist_ok=True)
        curFolderPath = "/".join([curFolderPath, str(nTasks)])
        os.makedirs(curFolderPath, exist_ok=True)

        for fileIndex, utilizations in enumerate(sets):
            jsonDict = {"startTime": 0, "endTime": math.lcm(*PERIODS), "taskset": []}
            for i, (u, period) in enumerate(utilizations):
                wcet = period * u
                jsonDict["taskset"].append(
                    {
                        "taskId": i + 1,
                        "period": period,
                        "wcet": wcet,
                        "deadline": period,
                        "offset": 0,
                    }
                )

            file_path = f"{curFolderPath}/ce_test_{fileIndex}.json"

            with open(file_path, "w") as json_file:
                json.dump(jsonDict, json_file)

        curU += uStep


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    generate_data(os.path.join(parent_dir, "tasksets"), nTasks=18)
