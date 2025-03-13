import json
import numpy as np
import matplotlib.pyplot as plt


def success_rate_v_utilization(nTasks=30):
    with open("data.json", "r") as f:
        data = json.load(f)

    data_filtered = [d for d in data if d["nTasks"] == nTasks]

    util_values = [round(x, 2) for x in np.arange(0.1, 1.0, 0.05)]

    rates_ilp = []
    rates_network = []

    for util in util_values:
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

    plt.rc("font", family="Times New Roman", size=12)
    plt.rc("axes", grid=True)

    x = np.arange(len(util_values))
    width = 0.35

    _, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        x - width / 2, rates_network, width, color="green", label="NetworkFlowScheduler"
    )
    ax.bar(x + width / 2, rates_ilp, width, color="blue", label="IlpScheduler")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{u:.2f}" for u in util_values])
    ax.set_xlabel("Utilization")
    ax.set_ylabel("Success Rate")
    ax.set_title(f"Success Rate and Execution Time vs. Utilization for nTasks={nTasks}")
    ax2 = ax.twinx()

    # Plot execution time lines
    ax2.plot(
        x,
        exec_times_network,
        color="orange",
        marker="o",
        label="NetworkFlowScheduler",
    )
    ax2.plot(x, exec_times_ilp, color="red", marker="o", label="IlpScheduler")

    ax2.set_ylabel("Execution Time (ms)")

    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(handles1 + handles2, labels1 + labels2, loc="center left")

    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)

    plt.tight_layout()
    plt.show()


def success_rate_v_task_size(utilization=0.85, nTasks_values=range(5, 26, 5)):

    # Load the JSON data
    with open("data.json", "r") as f:
        data = json.load(f)

    data_filtered = [d for d in data if round(d["utilization"], 2) == utilization]

    rates_ilp = []
    rates_network = []

    for tasks in nTasks_values:
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

    plt.rc("font", family="Times New Roman", size=12)
    plt.rc("axes", grid=True)

    x = np.arange(len(nTasks_values))
    width = 0.35

    _, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        x - width / 2, rates_network, width, color="green", label="NetworkFlowScheduler"
    )
    ax.bar(x + width / 2, rates_ilp, width, color="blue", label="IlpScheduler")

    ax.set_xticks(x)
    ax.set_xticklabels([str(n) for n in nTasks_values])
    ax.set_xlabel("nTasks")
    ax.set_ylabel("Success Rate")
    ax.set_title(
        f"Success Rate and Execution Time vs. nTasks for utilization={utilization}"
    )

    ax2 = ax.twinx()

    ax2.plot(
        x,
        exec_times_network,
        color="orange",
        marker="o",
        label="NetworkFlowScheduler",
    )
    ax2.plot(
        x,
        exec_times_ilp,
        color="red",
        marker="o",
        label="IlpScheduler",
    )

    ax2.set_ylabel("Execution Time (ms)")

    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(handles1 + handles2, labels1 + labels2, loc="center left")

    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
    plt.tight_layout()
    plt.show()


# success_rate_v_utilization(nTasks=60)
success_rate_v_task_size(utilization=0.5, nTasks_values=range(20, 61, 10))
