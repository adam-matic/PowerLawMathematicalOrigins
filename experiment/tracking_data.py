import json
import numpy as np
from collections import namedtuple


class Trajectory:
    """Class to store and manage trajectory data (x, y coordinates over time)"""
    def __init__(self):
        self.xs = []
        self.ys = []
        self.ts = []
        self.data = []

    def add(self, x, y, t):
        """Add a new point to the trajectory"""
        self.xs.append(x)
        self.ys.append(y)
        self.ts.append(t)


class TrackingData:
    """Class to manage tracking data for the experiment"""
    def __init__(self):
        self.cursor = Trajectory()  # User cursor position
        self.target = Trajectory()  # Target position
        self.pen = Trajectory()     # Raw pen/mouse data

    def save_to_file(self, filename):
        """Save all tracking data to a JSON file"""
        data = {
            "cursor": {
                "xs": self.cursor.xs,
                "ys": self.cursor.ys,
                "ts": self.cursor.ts,
            },
            "target": {
                "xs": self.target.xs,
                "ys": self.target.ys,
                "ts": self.target.ts,
            },
            "pen": {
                "xs": self.pen.xs,
                "ys": self.pen.ys,
                "ts": self.pen.ts,
            },            
            "data": self.data            
        }

        try:
            with open(filename, "w") as f:
                json.dump(data, f)
            print(f"Successfully saved tracking data to {filename}")
        except Exception as e:
            print(f"Error saving tracking data: {e}")
