import numpy as np


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

    def tsp_without_return(self, start, points):
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

    def find_optimal_route(self, start_id, through_points):
        self._create_dist_dyn_matr()
        route = self.tsp_without_return(start_id, through_points)
        return route

    def print_rout(self, route):
        print(route[0], end=" ")
        for index in range(1, len(route)):
            print(*(self.__distDynamicMatrix[route[index - 1]][route[index]][1]), end=" ")
