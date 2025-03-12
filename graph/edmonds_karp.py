def edmondsKarp(capacity, neighbors, start, end):
    flow = 0
    length = len(capacity)
    flows = [[0 for i in range(length)] for j in range(length)]
    while True:
        max, parent = breadthFirstSearch(capacity, neighbors, flows, start, end)

        if max == 0:
            break
        flow = flow + max
        v = end
        while v != start:
            u = parent[v]
            flows[u][v] = flows[u][v] + max
            flows[v][u] = flows[v][u] - max
            v = u
    return (flow, flows)


def breadthFirstSearch(capacity, neighbors, flows, start, end):
    length = len(capacity)
    parents = [-1 for i in range(length)]  # parent table
    parents[start] = -2  # make sure source is not rediscovered
    M = [0 for i in range(length)]  # Capacity of path to vertex i
    M[start] = float("inf")

    queue = []
    queue.append(start)
    while queue:
        u = queue.pop(0)
        for v in neighbors[u]:
            # if there is available capacity and v is is not seen before in search
            if capacity[u][v] - flows[u][v] > 0 and parents[v] == -1:
                parents[v] = u
                # it will work because at the beginning M[u] is Infinity
                M[v] = min(M[u], capacity[u][v] - flows[u][v])  # try to get smallest
                if v != end:
                    queue.append(v)
                else:
                    return M[end], parents
    return 0, parents
