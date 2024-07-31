import numpy as np
import folium
import math


def dist_lat_long(point1_lat, point1_long, point2_lat, point2_long) -> float:
    return 111.2 * math.acos(math.sin(math.radians(point1_lat)) * math.sin(math.radians(point2_lat))
                             + math.cos(math.radians(point1_lat)) * math.cos(math.radians(point2_lat)) * math.cos(
        math.radians(point1_long - point2_long)))


class Routing:
    __table_stops = None
    __table_point = None
    __table_road = None
    __distanceMatrix = None  # [array[int]]
    __distDynamicMatrix = None  # [array[int, array[int]]]

    def __init__(self, distanceMatrix):
        self.__distanceMatrix = distanceMatrix

    def __init__(self, table_stops, table_point, table_road):
        self.__table_stops = table_stops
        self.__table_point = table_point
        self.__table_road = table_road

    def _create_dist_matr(self) -> None:
        pass

        for road in self.__table_road:
            pass

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

    def tsp_without_return(self, start: int, points: list) -> list:
        points = [start] + points
        n = len(points)

        memo = {}

        def _dp(mask, pos):
            if (mask, pos) in memo:
                return memo[(mask, pos)]

            if mask == (1 << n) - 1:
                return (0, [points[pos]])

            ans = float('inf')
            best_path = []
            for next_pos in range(n):
                if mask & (1 << next_pos) == 0:
                    new_mask = mask | (1 << next_pos)
                    candidate_dist, candidate_path = _dp(new_mask, next_pos)
                    candidate_dist += self.__distDynamicMatrix[points[pos]][points[next_pos]][0]
                    if candidate_dist < ans:
                        ans = candidate_dist
                        best_path = candidate_path

            memo[(mask, pos)] = (ans, [points[pos]] + best_path)
            return memo[(mask, pos)]

        optimal_distance, path = _dp(1, 0)
        return path

    def tsp_without_return(self, start: int, end: int, points: list) -> list:
        points = [start] + points + [end]
        n = len(points)

        memo = {}

        def _dp(mask, pos):
            if (mask, pos) in memo:
                return memo[(mask, pos)]
            if mask == (1 << (n - 1)) - 1:
                return (self.__distDynamicMatrix[points[pos]][end][0], [points[pos], pos])
            ans = float('inf')
            best_path = []
            for next_pos in range(1, n - 1):
                if mask & (1 << next_pos) == 0:
                    new_mask = mask | (1 << next_pos)
                    candidate_dist, candidate_path = _dp(new_mask, next_pos)
                    candidate_path += self.__distDynamicMatrix[points[pos]][points[next_pos]]
                    if candidate_dist < ans:
                        ans = candidate_dist
                        best_path = candidate_path
            memo[(mask, pos)] = (ans, [points[pos]] + best_path)
            return memo[(mask, pos)]

        optimal_distance, path = _dp(1, 0)
        return path

    def find_optimal_route(self, start_id, through_points):
        if self.__distDynamicMatrix is None:
            self._create_dist_dyn_matr()
        return self.tsp_without_return(start_id, through_points)

    def find_optimal_route(self, start_id, end_id, through_points):
        if self.__distDynamicMatrix is None:
            self._create_dist_dyn_matr()
        return self.tsp_without_return(start_id, end_id, through_points)

    def print_rout(self, route) -> None:
        print(route[0], end=" ")
        for index in range(1, len(route)):
            print(*(self.__distDynamicMatrix[route[index - 1]][route[index]][1]), end=" ")

    def create_map(self, path: list, name_file: str) -> None:
        points = []
        for point_id in path:
            points.append((self.__table_point[point_id][1], self.__table_point[point_id][2]))
        map_folium = folium.Map(location=points[0], zoom_start=14)
        folium.PolyLine(points, color='blue', weight=5, opacity=0.7).add_to(map_folium)
        for point in points:
            folium.Marker(location=point).add_to(map_folium)
        map_folium.save(name_file + '.html')
