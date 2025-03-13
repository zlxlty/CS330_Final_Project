import json
import numpy as np
import matplotlib.pyplot as plt


def success_rate_v_utilization():
    # Load the JSON data
    with open("data.json", "r") as f:
        data = json.load(f)

    # Filter records for nTasks == 20
    data_filtered = [d for d in data if d["nTasks"] == 20]

    # Define utilization values from 0.1 to 0.95 (inclusive) in increments of 0.05
    util_values = [round(x, 2) for x in np.arange(0.1, 1.0, 0.05)]

    # Prepare lists to hold the average success rates for each scheduler
    rates_ilp = []
    rates_network = []

    for util in util_values:
        # Filter records matching the utilization and scheduler type (using rounding for float comparison)
        records_ilp = [
            d
            for d in data_filtered
            if round(d["utilization"], 2) == util and d["Scheduler"] == "IlpScheduler"
        ]
        records_net = [
            d
            for d in data_filtered
            if round(d["utilization"], 2) == util
            and d["Scheduler"] == "NetworkFlowScheduler"
        ]

        # Compute average success rate (if no record exists for a given util, set to 0)
        avg_ilp = (
            np.mean([d["successCount"] / d["nTaskSets"] for d in records_ilp])
            if records_ilp
            else 0
        )
        avg_net = (
            np.mean([d["successCount"] / d["nTaskSets"] for d in records_net])
            if records_net
            else 0
        )

        rates_ilp.append(avg_ilp)
        # Compute average execution times for each scheduler
        rates_network.append(avg_net)
    exec_times_ilp = []
    exec_times_network = []
    for util in util_values:
        records_ilp = [
            d
            for d in data_filtered
            if round(d["utilization"], 2) == util
            and d["Scheduler"] == "IlpScheduler"
            and d["successCount"] > 0
        ]
        records_net = [
            d
            for d in data_filtered
            if round(d["utilization"], 2) == util
            and d["Scheduler"] == "NetworkFlowScheduler"
            and d["successCount"] > 0
        ]
        avg_time_ilp = (
            np.mean([d["totalTime"] * 1000 / d["successCount"] for d in records_ilp])
            if records_ilp
            else 0
        )
        avg_time_net = (
            np.mean([d["totalTime"] * 1000 / d["successCount"] for d in records_net])
            if records_net
            else 0
        )
        exec_times_ilp.append(avg_time_ilp)
        exec_times_network.append(avg_time_net)

    # Set IEEE-like style parameters

    # Set IEEE-like style parameters
    plt.rc("font", family="Times New Roman", size=12)
    plt.rc("axes", grid=True)

    # Create grouped bar chart
    x = np.arange(len(util_values))  # positions for groups
    width = 0.35  # width of each bar

    fig, ax = plt.subplots(figsize=(10, 6))

    # Two bars per utilization: green for NetworkFlowScheduler and blue for IlpScheduler
    bar1 = ax.bar(
        x - width / 2, rates_network, width, color="green", label="NetworkFlowScheduler"
    )
    bar2 = ax.bar(x + width / 2, rates_ilp, width, color="blue", label="IlpScheduler")

    # Set x-axis labels and ticks
    ax.set_xticks(x)
    ax.set_xticklabels([f"{u:.2f}" for u in util_values])
    ax.set_xlabel("Utilization")
    ax.set_ylabel("Success Rate")
    ax.set_title("Success Rate and Execution Time vs. Utilization for nTasks=20")
    # Create a secondary y-axis for execution time
    ax2 = ax.twinx()

    # Plot execution time lines
    line_net = ax2.plot(
        x,
        exec_times_network,
        color="orange",
        marker="o",
        label="NetworkFlowScheduler",
    )
    line_ilp = ax2.plot(
        x, exec_times_ilp, color="red", marker="o", label="IlpScheduler"
    )

    ax2.set_ylabel("Execution Time (ms)")

    # Combine legends from both axes
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(handles1 + handles2, labels1 + labels2, loc="center left")

    # Enhance layout following IEEE guidelines (minimal grid and clean fonts)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)

    plt.tight_layout()
    plt.show()


def success_rate_v_task_size():

    # Load the JSON data
    with open("data.json", "r") as f:
        data = json.load(f)

    # Filter records for utilization == 0.85
    data_filtered = [d for d in data if round(d["utilization"], 2) == 0.85]

    # Define nTasks values from 20 to 60 in increments of 10
    nTasks_values = list(range(20, 61, 10))

    # Prepare lists to hold the average success rates for each scheduler
    rates_ilp = []
    rates_network = []

    for tasks in nTasks_values:
        # Filter records matching the nTasks value and scheduler type
        records_ilp = [
            d
            for d in data_filtered
            if d["nTasks"] == tasks and d["Scheduler"] == "IlpScheduler"
        ]
        records_net = [
            d
            for d in data_filtered
            if d["nTasks"] == tasks and d["Scheduler"] == "NetworkFlowScheduler"
        ]

        # Compute average success rate
        avg_ilp = (
            np.mean([d["successCount"] / d["nTaskSets"] for d in records_ilp])
            if records_ilp
            else 0
        )
        avg_net = (
            np.mean([d["successCount"] / d["nTaskSets"] for d in records_net])
            if records_net
            else 0
        )

        rates_ilp.append(avg_ilp)
        rates_network.append(avg_net)

    # Compute average execution times (in ms) for each scheduler
    exec_times_ilp = []
    exec_times_network = []
    for tasks in nTasks_values:
        records_ilp = [
            d
            for d in data_filtered
            if d["nTasks"] == tasks
            and d["Scheduler"] == "IlpScheduler"
            and d["successCount"] > 0
        ]
        records_net = [
            d
            for d in data_filtered
            if d["nTasks"] == tasks
            and d["Scheduler"] == "NetworkFlowScheduler"
            and d["successCount"] > 0
        ]

        # Multiply totalTime (in seconds) by 1000 to convert to ms
        avg_time_ilp = (
            np.mean([d["totalTime"] * 1000 / d["successCount"] for d in records_ilp])
            if records_ilp
            else 0
        )
        avg_time_net = (
            np.mean([d["totalTime"] * 1000 / d["successCount"] for d in records_net])
            if records_net
            else 0
        )

        exec_times_ilp.append(avg_time_ilp)
        exec_times_network.append(avg_time_net)

    # Set IEEE-like style parameters
    plt.rc("font", family="Times New Roman", size=12)
    plt.rc("axes", grid=True)

    # Create grouped bar chart
    x = np.arange(len(nTasks_values))  # positions for groups
    width = 0.35  # width of each bar

    fig, ax = plt.subplots(figsize=(10, 6))

    # Two bars per nTasks value: green for NetworkFlowScheduler and blue for IlpScheduler
    bar1 = ax.bar(
        x - width / 2, rates_network, width, color="green", label="NetworkFlowScheduler"
    )
    bar2 = ax.bar(x + width / 2, rates_ilp, width, color="blue", label="IlpScheduler")

    ax.set_xticks(x)
    ax.set_xticklabels([str(n) for n in nTasks_values])
    ax.set_xlabel("nTasks")
    ax.set_ylabel("Success Rate")
    ax.set_title("Success Rate and Execution Time vs. nTasks for utilization=0.85")

    # Create a secondary y-axis for execution time
    ax2 = ax.twinx()

    # Plot execution time lines
    line_net = ax2.plot(
        x,
        exec_times_network,
        color="orange",
        marker="o",
        label="NetworkFlowScheduler",
    )
    line_ilp = ax2.plot(
        x,
        exec_times_ilp,
        color="red",
        marker="o",
        label="IlpScheduler",
    )

    ax2.set_ylabel("Execution Time (ms)")

    # Combine legends from both axes and place in bottom left
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(handles1 + handles2, labels1 + labels2, loc="center left")

    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
    plt.tight_layout()
    plt.show()


success_rate_v_task_size()
