import os
import json
import time
from taskset import *
from scheduleralgorithm import *
from CyclicSchedulerAlgorithm import *
from flow import *
from ilp import *


uStep = 0.05
tStep = 5
current_dir = os.path.dirname(os.path.abspath(__file__))
taskset_dir = os.path.join(current_dir, "tasksets")
output_dir = os.path.join(current_dir, "output")


def read_all_json_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            json_path = os.path.join(folder_path, filename)
            print(json_path)
            with open(json_path, "r") as json_file:
                data = json.load(json_file)
            yield data


def test_scheduler(scheduler: CyclicSchedulerAlgorithm):
    start_time = time.perf_counter()
    try:
        schedule = scheduler.buildSchedule(0, 72)
    except:
        schedule = None
    end_time = time.perf_counter()
    duration = end_time - start_time

    if schedule != None and schedule.validateDeadlines():
        return 1, duration

    return 0, 0


def consolidate_json_files():
    consolidated_data = []

    # Loop through all files in the output directory
    for filename in os.listdir(output_dir):
        # Process only files ending with .json
        if filename.endswith(".json"):
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "r") as json_file:
                data = json.load(json_file)
                consolidated_data.append(data)

    # Write the consolidated data to data.json with pretty-printing
    with open("data.json", "w") as outfile:
        json.dump(consolidated_data, outfile, indent=4)


def run_test(schedulers):
    curU = 0.1
    # outputs = {}
    # for scheduler in schedulers:
    #     name = scheduler.__name__
    #     outputs[name] = {
    #         "Scheduler": name,
    #         "nTaskSets": 400,
    #         "data": [],
    #     }

    while curU < 1:
        # for i in range(5):
        curU = round(curU, 3)
        nTasks = 60
        target_folder = os.path.join(taskset_dir, str(curU), str(nTasks))
        assert os.path.isdir(target_folder), f"Folder does not exist: {target_folder}"

        results = {
            cls.__name__: {
                "Scheduler": cls.__name__,
                "nTaskSets": 400,
                "successCount": 0,
                "utilization": curU,
                "nTasks": nTasks,
                "totalTime": 0,
            }
            for cls in schedulers
        }
        print(f"Processing U={curU} N={nTasks}...")
        for data in read_all_json_in_folder(target_folder):
            taskSet = TaskSet(data)

            for schedulerCls in schedulers:
                name = schedulerCls.__name__
                schedulerIns = schedulerCls(taskSet)

                success, duration = test_scheduler(schedulerIns)
                # print(f"success: {success}")
                # return None
                results[name]["successCount"] += success
                results[name]["totalTime"] += duration

        for name in results.keys():
            # target_dir = os.makedirs(
            #     os.path.join(output_dir, name), exist_ok=True
            # )
            file_path = f"{output_dir}/{name}_{curU}_{nTasks}_results.json"

            with open(file_path, "w") as json_file:
                json.dump(results[name], json_file)
        curU += uStep


if __name__ == "__main__":
    # run_test([NetworkFlowScheduler, IlpScheduler])

    consolidate_json_files()
