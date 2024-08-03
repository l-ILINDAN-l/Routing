import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


from module.routing import Routing
from module.data_hosts_vlad import *

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
