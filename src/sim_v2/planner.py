import pandas
from scipy.interpolate import interp1d, splprep
import csv

from utils import spline_trajectories

class Trajectory:
    def __init__(self, lat, lon, heading):
        self.lat=lat
        self.lon=lon
        self.heading=heading
        
    def __call__(self, u):
        return [self.lat(u), self.lon(u), self.heading(u)]
        

class Node:
    def __init__(self, row):
        self.lat = row['Latitude']
        self.lon = row['Longitude']
        self.head = row['Heading']
        if self.head > 180:
            self.head -= 360
        self.label = row['Label']
        self.desc = row['Desc']
        self.neighbors = eval(row['Neighbors'].replace(";", ","))
        
    def is_stop(self):
        return self.label in ["hold short", "takeoff"]
        
        
class GraphPlanner:
    def __init__(self, coordinate_converter, graphfile, interp='linear'):
        self.coordinate_converter = coordinate_converter
        df = pandas.read_csv(graphfile)
        self.graph = [Node(df.iloc[i]) for i in range(len(df))]
        self.interp = interp
        
    def __getitem__(self, index):
        return self.graph[index]
    
    def get_coord(self, n):
        return [self[n].lat, self[n].lon]
        
    def get_coords(self, rt):
        return [self.get_coord(n) for n in rt]
    
    # Copied from https://www.geeksforgeeks.org/building-an-undirected-graph-and-finding-shortest-path-using-dictionaries-in-python/
    def get_route(self, start, goal):
        explored = []
        queue = [[start]]
         
        if start == goal:
            raise Exception("Same Node")
         
        while queue:
            path = queue.pop(0)
            node = path[-1]
             
            if node not in explored:
                for neighbour in self[node].neighbors:
                    new_path = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)
                     
                    if neighbour == goal:
                        return new_path
                explored.append(node)
        raise Exception("No path between these nodes")

    def split_route(self, rt):
        rts = [[]]
        for n in rt:
            rts[-1].append(n)
            if self[n].is_stop() and n != rt[-1]:
                rts.append([n])
        return rts
    
    def write_coords_csv(self, coords, filename):
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Latitude','Longitude'])
            for c in coords:
                writer.writerow(c)
                
    def write_route_csv(self, route, filename):
        self.write_coords_csv(self.get_coords(route), filename)
        
    def get_node_by_desc(self, desc):
        for n in range(len(self.graph)):
            if self[n].desc == desc:
                return n
        raise Exception("No node with name " + name)
        
    def get_trajectory(self, route):
        lats = [self[n].lat for n in route]
        lons = [self[n].lon for n in route]
        if self.interp == "spline":
            return spline_trajectories.Trajectory(self.coordinate_converter, lats, lons)

        headings = [self[n].head for n in route]
        tck, u = splprep([lats, lons])
        
        lat_interp = interp1d(u, lats, kind=self.interp)
        lon_interp = interp1d(u, lons, kind=self.interp)
        heading_interp = interp1d(u, headings, kind=self.interp)
        
        return Trajectory(lat_interp, lon_interp, heading_interp)

# g = GraphPlanner("data/grant_co_map.csv")
# 
# coords = g.get_coords(range(len(g.graph)))
# g.write_route_csv(range(len(g.graph)), "data/all_pts.csv")
# 
# # g.graph[0].desc
# # 
# start = g.get_node_by_desc("Gate 3")
# to = g.get_node_by_desc("4 takeoff")
# to = g.get_node_by_desc("32L takeoff")
# to = g.get_node_by_desc("14L takeoff")
# 
# route = g.get_route(start, to)
# 
# g.write_route_csv(route, "data/14Lto.csv")
# 
# traj = g.get_trajectory(route)
# 
# g.write_coords_csv([traj(u)[:2] for u in np.linspace(0,1,300)], "data/dense_tr.csv")


class FixedWaypointPlanner:
    def __init__(self, filename):
        self.waypoints = pandas.read_csv(filename)
        
    def get_waypoints(self, map, belief, distance_to_holdline):
        return self.waypoints
