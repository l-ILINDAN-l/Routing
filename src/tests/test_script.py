# from src.module.routing import Routing
#
# # test data
# matrix = [
#     [0, 10, float("inf"), 5],
#     [10, 0, float("inf"), 2],
#     [float("inf"), float("inf"), 0, 1],
#     [5, 2, 1, 0]
# ]
# start_id = 0
# through_points = [1, 2]
#
# routing = Routing(matrix)
# rout = routing.find_optimal_route(start_id, through_points)
# routing.print_rout(rout)

from src.module.routing import Routing
from src.tests.my_SQL import *

routing = Routing(host, port, dbname, user, password)

start_id = routing.get_point_id_for_stop(1)
end_id = routing.get_point_id_for_stop(10)
through_points = [routing.get_point_id_for_stop(i) for i in range(2, 10)]

dist_rec, path_rec = routing.find_optimal_route_recursion(start_id, end_id, through_points)

if dist_rec == float("inf"):
    print("Маршрут не найден")
else:
    print(dist_rec)
    routing.print_rout(path_rec)
    routing.create_map(path_rec, "route_rec")
    print()

dist_ann, path_ann = routing.simulated_annealing_route_build(start_id, end_id, through_points)
if dist_ann == float("inf"):
    print("Маршрут не найден")
else:
    print(dist_ann)
    routing.print_rout(path_ann)
    routing.create_map(path_ann, "route_ann")
    print()


routing.create_all_map("all_map")
