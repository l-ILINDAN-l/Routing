from src.module.routing import Routing

# test data
matrix = [
    [0, 10, float("inf"), 5],
    [10, 0, float("inf"), 2],
    [float("inf"), float("inf"), 0, 1],
    [5, 2, 1, 0]
]
start_id = 0
through_points = [1, 2]

routing = Routing(matrix)
rout = routing.find_optimal_route(start_id, through_points)
routing.print_rout(rout)