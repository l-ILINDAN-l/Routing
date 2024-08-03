import numpy as np
import folium
import math
import module.loadSQL as loadSQL
import psycopg2
# from data_hosts_vlad import *
from module.data_hosts_vlad import *
import random


def dist_lat_long(point1_lat, point1_long, point2_lat, point2_long) -> float:
    return (6371 * math.acos(math.sin(math.radians(point1_lat)) * math.sin(math.radians(point2_lat))
                             + math.cos(math.radians(point1_lat)) * math.cos(math.radians(point2_lat)) *
                             math.cos(math.radians(point1_long - point2_long))))


class Routing:
    __table_point = None
    __table_road = None
    __table_stops = None

    __distanceMatrix = None
    __distDynamicMatrix = None

    __is_connect_itinerary: bool = False
    name_table_route: str = ''

    def __init__(self, host, port, dbname, user, password, connect_itinerary=False):
        dict_tables = loadSQL.get_tables_as_2d_arrays(host, port, dbname, user, password)
        self.__table_point = dict_tables["table_points"]
        self.__table_road = dict_tables["table_road"]
        self.__table_stops = dict_tables["table_stops"]

        self._create_dist_matr()
        self._create_dist_dyn_matr()

        if connect_itinerary:
            self.__is_connect_itinerary = True
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password
                )

                # Создание курсора
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM table_itinerary
                    """
                )

                rows = cursor.fetchall()
                a = len(rows)
                self.name_table_route = f'itinerary{a + 1}'
                cursor.execute(
                    f"""
                    INSERT INTO table_itinerary (itinerary_name)
                    VALUES ('itinerary{a + 1}');
                    CREATE TABLE itinerary{a + 1}(
                        number_in_itinerary SERIAL PRIMARY KEY,
                        point_id INTEGER
                    )
                    """
                )
                conn.commit()
            except Exception as e:
                print(f"__init__ Ошибка подключения к базе данных: {e}")
            finally:
                # Закрытие курсора и соединения
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

    def _create_dist_matr(self) -> None:
        count_point = len(self.__table_point)
        self.__distanceMatrix = [[float('inf') for _ in range(count_point)] for _ in range(count_point)]
        for road in self.__table_road:
            self.__distanceMatrix[road[2] - 1][road[3] - 1] = road[4]
            if not road[1]:
                self.__distanceMatrix[road[3] - 1][road[2] - 1] = road[4]
        for stop in self.__table_stops:
            point_id = stop[1]
            road_id = stop[5]
            start_id = self.__table_road[road_id - 1][2]
            end_id = self.__table_road[road_id - 1][3]
            self.__distanceMatrix[start_id - 1][point_id - 1] = dist_lat_long(
                self.__table_point[start_id - 1][1], self.__table_point[start_id - 1][2],
                self.__table_point[point_id - 1][1], self.__table_point[point_id - 1][2]
            )
            self.__distanceMatrix[point_id - 1][end_id - 1] = dist_lat_long(
                self.__table_point[point_id - 1][1], self.__table_point[point_id - 1][2],
                self.__table_point[end_id - 1][1], self.__table_point[end_id - 1][2]
            )
            if not self.__table_road[road_id - 1][1]:
                self.__distanceMatrix[point_id - 1][start_id - 1] = dist_lat_long(
                    self.__table_point[start_id - 1][1], self.__table_point[start_id - 1][2],
                    self.__table_point[point_id - 1][1], self.__table_point[point_id - 1][2]
                )
                self.__distanceMatrix[end_id - 1][point_id - 1] = dist_lat_long(
                    self.__table_point[point_id - 1][1], self.__table_point[point_id - 1][2],
                    self.__table_point[end_id - 1][1], self.__table_point[end_id - 1][2]
                )

    def _create_dist_dyn_matr(self) -> None:

        n = len(self.__distanceMatrix)

        self.__distDynamicMatrix = [[[float('inf'), []] for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    self.__distDynamicMatrix[i][j][0] = 0

                elif self.__distanceMatrix[i][j] != 0:
                    self.__distDynamicMatrix[i][j][0] = self.__distanceMatrix[i][j]
                    self.__distDynamicMatrix[i][j][1].append(j)

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if self.__distDynamicMatrix[i][j][0] > self.__distDynamicMatrix[i][k][0] + \
                            self.__distDynamicMatrix[k][j][0]:
                        self.__distDynamicMatrix[i][j][0] = self.__distDynamicMatrix[i][k][0] + \
                                                            self.__distDynamicMatrix[k][j][0]
                        self.__distDynamicMatrix[i][j][1] = self.__distDynamicMatrix[i][k][1] + \
                                                            self.__distDynamicMatrix[k][j][1]

    def simulated_annealing_route_build(self, start_id: int, end_id: int, points_id: list, initial_temp=1000,
                                        cooling_rate=0.995, num_iterations=10000) -> (float, list):
        def floyd_warshall(distance_matrix):
            n = len(distance_matrix)
            dist = [[distance_matrix[i][j] for j in range(n)] for i in range(n)]
            next_node = [[j if distance_matrix[i][j] != float('inf') else None for j in range(n)] for i in range(n)]

            for k in range(n):
                for i in range(n):
                    for j in range(n):
                        if dist[i][k] + dist[k][j] < dist[i][j]:
                            dist[i][j] = dist[i][k] + dist[k][j]
                            next_node[i][j] = next_node[i][k]
            return dist, next_node

        def reconstruct_path(next_node, u, v):
            if next_node[u][v] is None:
                return []
            path = [u]
            while u != v:
                u = next_node[u][v]
                path.append(u)
            return path

        def calculate_total_distance(route, shortest_paths):
            total_distance = 0
            for i in range(len(route) - 1):
                total_distance += shortest_paths[route[i]][route[i + 1]]
            return total_distance

        # Функция для генерации начального маршрута, включающего все обязательные узлы
        def initial_route(start_id, end_id, points_id):
            route = [start_id] + points_id + [end_id]
            return route

        def simulated_annealing(shortest_paths, start_id, end_id, points_id, initial_temp, cooling_rate,
                                num_iterations):
            current_route = initial_route(start_id, end_id, points_id)
            current_distance = calculate_total_distance(current_route, shortest_paths)

            best_route = current_route[:]
            best_distance = current_distance

            temperature = initial_temp

            for iteration in range(num_iterations):
                # Генерация соседнего состояния путем перестановки двух случайных узлов
                new_route = current_route[:]
                i, j = random.sample(range(1, len(new_route) - 1), 2)
                new_route[i], new_route[j] = new_route[j], new_route[i]

                new_distance = calculate_total_distance(new_route, shortest_paths)

                # Решение о принятии нового состояния
                if new_distance < current_distance or random.uniform(0, 1) < math.exp(
                        (current_distance - new_distance) / temperature):
                    current_route = new_route
                    current_distance = new_distance

                # Обновление лучшего найденного решения
                if current_distance < best_distance:
                    best_route = current_route
                    best_distance = current_distance

                # Уменьшение температуры
                temperature *= cooling_rate

            return best_route, best_distance

        shortest_paths, next_node = floyd_warshall(self.__distanceMatrix)
        best_route, best_distance = simulated_annealing(shortest_paths, start_id, end_id, points_id, initial_temp,
                                                        cooling_rate, num_iterations)

        # Восстановление полного маршрута, включая промежуточные узлы
        full_route = []
        for i in range(len(best_route) - 1):
            full_route.extend(reconstruct_path(next_node, best_route[i], best_route[i + 1])[:-1])
        full_route.append(best_route[-1])

        if self.__is_connect_itinerary:
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password
                )
                cursor = conn.cursor()
                for i in full_route:
                    cursor.execute(
                        f"""
                        INSERT INTO {self.name_table_route} (point_id)
                        VALUES ({i + 1})
                        """
                    )
                conn.commit()
            except Exception as e:
                print(f"Ошибка подключения к базе данных: {e}")
            finally:
                # Закрытие курсора и соединения
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        return best_distance, full_route

    def recursion_route_build(self, start: int, end: int, points: list) -> (float, list):
        best_path = []
        best_distance = float("inf")
        count_point_without_end = len(points) + 1
        points = [start] + points
        if self.__distDynamicMatrix is None:
            self._create_dist_dyn_matr()

        def _recursion_fun(mask, pos, distance, path):
            if mask == (1 << count_point_without_end) - 1:
                candidate_distance = distance + self.__distDynamicMatrix[points[pos]][end][0]
                nonlocal best_distance
                nonlocal best_path
                if best_distance > candidate_distance:
                    best_distance = candidate_distance
                    best_path = path + self.__distDynamicMatrix[points[pos]][end][1]
            else:
                for next_pos in range(1, count_point_without_end):
                    if mask & (1 << next_pos) == 0:
                        new_mask = mask | (1 << next_pos)
                        candidate_distance = distance + self.__distDynamicMatrix[points[pos]][points[next_pos]][0]
                        candidate_path = path + self.__distDynamicMatrix[points[pos]][points[next_pos]][1]
                        for index in range(count_point_without_end):
                            if points[index] in candidate_path:
                                new_mask = new_mask | (1 << index)
                        _recursion_fun(new_mask, next_pos, candidate_distance, candidate_path)

        _recursion_fun(1, 0, 0, [start])

        if self.__is_connect_itinerary:
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password
                )
                cursor = conn.cursor()
                for i in best_path:
                    cursor.execute(
                        f"""
                        INSERT INTO {self.name_table_route} (point_id)
                        VALUES ({i + 1})
                        """
                    )
                conn.commit()
            except Exception as e:
                print(f"Ошибка подключения к базе данных: {e}")
            finally:
                # Закрытие курсора и соединения
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        return (best_distance, best_path)

    def find_optimal_route_recursion(self, start_id, end_id, through_points) -> (float, list):
        if self.__distDynamicMatrix is None:
            self._create_dist_dyn_matr()
        return self.recursion_route_build(start_id, end_id, through_points)

    def print_rout(self, route) -> None:
        print(*map(lambda x: x + 1, route), end=" ")

    def create_map(self, path: list, name_file: str) -> None:
        points = []
        for point_id in path:
            points.append((self.__table_point[point_id][1], self.__table_point[point_id][2]))
        map_folium = folium.Map(location=points[0], zoom_start=14)
        folium.PolyLine(points, color='blue', weight=5, opacity=0.7).add_to(map_folium)
        index = 1
        for point in points:
            folium.Marker(location=point,
                          icon=folium.DivIcon(html=f"{index} {point[0]} {point[1]}", class_name="mapText")).add_to(
                map_folium)
            index += 1

        map_folium.get_root().html.add_child(folium.Element("""
            <style>
            .mapText {
                white-space: nowrap;
                font-size:large
            }
            </style>
            """
        ))
        map_folium.save(name_file + '.html')

    def create_all_map(self, name_file: str) -> None:
        map_folium = folium.Map(location=self.__table_point[0][1:], zoom_start=14)
        for point in self.__table_point:
            folium.Marker(location=list(point[1:]),
                          icon=folium.DivIcon(html=f"{point[0]} {point[1]} {point[2]}", class_name="mapText")).add_to(
                map_folium)
        for road in self.__table_road:
            point_start = road[2]
            point_end = road[3]
            points = [(self.__table_point[point_start - 1][1], self.__table_point[point_start - 1][2]),
                      (self.__table_point[point_end - 1][1], self.__table_point[point_end - 1][2])]
            if road[1]:
                folium.PolyLine(points, color='blue', weight=5, opacity=0.7).add_to(map_folium)
            else:
                folium.PolyLine(points, color='red', weight=5, opacity=0.7).add_to(map_folium)
        map_folium.get_root().html.add_child(folium.Element("""
        <style>
        .mapText {
            white-space: nowrap;
            font-size:large
        }
        </style>
        """))
        map_folium.save(name_file + '.html')

    def get_dist_din(self, from_id, to_id):
        return self.__distDynamicMatrix[from_id][to_id][0]

    def get_point_id_for_stop(self, stop_id: int):
        return self.__table_stops[stop_id - 1][1] - 1
