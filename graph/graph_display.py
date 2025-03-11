import networkx as nx
import matplotlib.pyplot as plt


class NetworkDisplay(object):
    def __init__(self, width, height, flowScheduler):
        self.G = nx.DiGraph()
        self.width = width
        self.height = height
        self.interval = 0.5
        self.flowScheduler = flowScheduler

        self.defaultColor = "lightgrey"
        self.frameColor = "lightblue"
        self.jobColor = "lightgreen"
        self.jobWarningColor = "yellow"
        self.jobErrorColor = "red"

        self._buildGraph()

    def _buildGraph(self):
        self.G.add_node((-2, 0), color=self.defaultColor)
        self.G.add_node((-2, 1), color=self.defaultColor)

        self.pos = {(-2, 0): (0, 0), (-2, 1): (3, 0)}

        curY = -1 * self.height / 2
        interval = self.height / (self.flowScheduler.numFrames - 1)
        for k in range(1, self.flowScheduler.numFrames + 1):
            self.G.add_node((-1, k), color=self.frameColor)
            self.pos[(-1, k)] = (1, curY)
            curY += interval

        curY = -1 * self.height / 2
        interval = self.height / (len(self.flowScheduler.taskSet.jobs) - 1)
        for job in self.flowScheduler.taskSet.jobs:
            self.G.add_node((job.task.id, job.id), color=self.jobColor)
            self.pos[(job.task.id, job.id)] = (2, curY)
            curY += interval

        capacityMap = self.flowScheduler.capacityMap
        flowMap = self.flowScheduler.flowMap

        jobToFrame = {}
        for i in range(len(capacityMap)):
            for j in range(len(capacityMap[i])):
                if capacityMap[i][j] == 0:
                    continue

                nodeIdU = self.flowScheduler.indexToNodeId[i]
                nodeIdV = self.flowScheduler.indexToNodeId[j]
                self.G.add_edge(
                    nodeIdU, nodeIdV, flow=flowMap[i][j], capacity=capacityMap[i][j]
                )

                # Mark jobs that are assigned to more than one frame.
                if nodeIdV[0] > 0 and flowMap[i][j] > 0:
                    if not nodeIdV in jobToFrame:
                        jobToFrame[nodeIdV] = nodeIdU[1]
                    else:
                        node = self.G.nodes.get(nodeIdV)
                        node["color"] = self.jobWarningColor

                # Mark jobs that are not completed.
                if nodeIdV == (-2, 1) and flowMap[i][j] < capacityMap[i][j]:
                    node = self.G.nodes.get(nodeIdU)
                    node["color"] = self.jobErrorColor

        # Create an edge label dictionary in the format "f/c"
        self.edge_labels = {
            (u, v): (
                f"{data['flow']}/{data['capacity']}"
                if u[0] != -1
                else f"{data['flow']}"
            )
            for u, v, data in self.G.edges(data=True)
        }

    def run(self):
        node_colors = [self.G.nodes.get(nodeId)["color"] for nodeId in self.G.nodes]

        # Draw the graph
        plt.figure(figsize=(self.width, self.height))
        nx.draw_networkx(
            self.G,
            self.pos,
            with_labels=True,
            node_color=node_colors,
            node_size=1500,
            arrows=True,
            arrowstyle="->",
            arrowsize=20,
        )
        nx.draw_networkx_edge_labels(
            self.G, self.pos, edge_labels=self.edge_labels, label_pos=0.25
        )

        plt.title("Network Flow Schedule")
        plt.axis("off")
        plt.show()
