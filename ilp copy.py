from gurobipy import Model, GRB

# Create model
model = Model("CyclicExecutive")

# Parameters for tasks
tasks = {
    1: {"T": 4, "C": 1, "J": 5},  # Task 1 has 3 jobs
    2: {"T": 5, "C": 2, "J": 4},  # Task 2 has 2 jobs
    3: {"T": 20, "C": 1, "J": 1},  # Task 2 has 2 jobs
    4: {"T": 20, "C": 2, "J": 1},  # Task 2 has 2 jobs
}
f = 2
P = 20
F = P // f

# Pre-calculate valid frame sets V(i,j)
V = {}
for i, data in tasks.items():
    T_i = data["T"]
    J_i = data["J"]
    for j in range(1, J_i + 1):
        V[(i, j)] = []
        for k in range(1, F + 1):
            if (k - 1) * f >= (j - 1) * T_i and k * f <= j * T_i:
                V[(i, j)].append(k)

# Create decision variables x[i,j,k] for valid (i,j,k)
x = {}
for i, data in tasks.items():
    J_i = data["J"]
    for j in range(1, J_i + 1):
        for k in V[(i, j)]:
            x[(i, j, k)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}_{k}")

model.update()

# Add job assignment constraints
for i, data in tasks.items():
    J_i = data["J"]
    for j in range(1, J_i + 1):
        model.addConstr(
            sum(x[(i, j, k)] for k in V[(i, j)]) == 1, name=f"jobAssign_{i}_{j}"
        )

# Add frame capacity constraints for each frame k
for k in range(1, F + 1):
    expr = 0
    for i, data in tasks.items():
        C_i = data["C"]
        J_i = data["J"]
        for j in range(1, J_i + 1):
            if k in V[(i, j)]:
                expr += C_i * x[(i, j, k)]
    model.addConstr(expr <= f, name=f"frameCap_{k}")

# Set objective (dummy, since we only need feasibility)
model.setObjective(0, GRB.MINIMIZE)

# Solve the model
model.optimize()

# Print solution if feasible
if model.status == GRB.OPTIMAL:
    for var in model.getVars():
        if var.x > 0.5:
            print(f"{var.varName} = {var.x}")
