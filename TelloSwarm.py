from djitellopy import Tello
import time
import cv2
import numpy as np
import threading
import sys
import os
import math
from queue import Queue
from threading import Thread, Barrier
from typing import List, Callable, Optional
from .enforce_types import enforce_types
import logging

import asyncio


# TelloSwarm class
# I stole enforce_types from https://github.com/Linaom1214/tello-swarm/blob/main/djitellopy/swarm.py
@enforce_types
class TelloSwarm:
    """
    A Class to control multiple tello drones at once
    """

    drones: List[Tello]
    swarm_size: int
    barrier: Barrier
    funcBarrier: Barrier
    funcQueues: List[Queue]
    threads: List[Thread]
    curDrone: int
    known_landmarks: List[np.ndarray]

    @staticmethod
    def fromIPString(ip_string: str):
        """
        Create a TelloSwarm object from a string of IP addresses separated by double spaces.
        """
        return TelloSwarm([Tello(host=ip) for ip in ip_string.split("  ")])

    def fromListStrings(ip_list: List[str]):
        """
        Create a TelloSwarm object from a list of IP addresses (strings).
        """
        return TelloSwarm([Tello(host=ip) for ip in ip_list])

    def __init__(self, drones: List[Tello]):
        """
        Initialize a TelloSwarm object with a list of Tello objects.
        """
        self.drones = drones
        self.swarm_size = len(drones)
        self.barrier = Barrier(self.swarm_size)
        self.funcBarrier = Barrier(len(drones) + 1)
        self.funcQueues = [Queue() for _ in range(self.swarm_size)]
        self.threads = []
        self.curDrone = 0
        self.initThreads()

    def initThreads(self):
        """
        Initialize the threads for the drones in the swarm.

        An internal function that creates a thread for each drone in the swarm.
        """

        def worker(i):
            queue = self.funcQueues[i]
            drone = self.drones[i]
            while True:
                func = queue.get()
                self.funcBarrier.wait()
                try:
                    func(i, drone)
                except Exception as e:
                    logging.error(f"Error executing function on drone {i}: {e}")
                self.funcBarrier.wait()

        self.threads = []
        for i in range(self.swarm_size):
            thread = Thread(target=worker, args=(i,))
            thread.start()
            self.threads.append(thread)

    def load_known_landmarks(self, descriptor_paths):
        landmarks = []
        for path in descriptor_paths:
            descriptors = np.load(path)
            landmarks.append(descriptors)
        self.known_landmarks = landmarks

    def detect_landmarks(self, frame):
        # Detect keypoints and descriptors in the current frame
        keypoints, descriptors = self.orb.detectAndCompute(frame, None)
        matches = []
        for landmark in self.known_landmarks:
            matches.extend(self.bf.match(descriptors, landmark))
        matches = sorted(matches, key=lambda x: x.distance)
        return matches

    def localize(self, drone_index):
        frame = self.drones[drone_index].get_frame_read().frame
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        matches = self.detect_landmarks(gray_frame)
        if matches:
            positions = [self.compute_position_from_match(match) for match in matches]
            avg_position = np.mean(positions, axis=0)
            return avg_position
        return None

    def compute_position_from_match(self, match):
        return np.array([match.pt[0], match.pt[1], 0])

    def fly_in_formation(
        self, leader_index: int, distance: float = 100.0, a: float = 2.5
    ):
        def formation_func(x):
            return (x**a) / (x**a + (1 - x) ** a)

        def move_to_position(i, drone):
            if i == leader_index:
                drone.move_up(int(distance))
            else:
                leader_position = self.localize(leader_index)
                if leader_position is None:
                    print(f"Error getting position for drone {leader_index}")
                    return
                position = formation_func(i / (self.num_drones - 1))
                angle = position * np.pi * 2
                dx = distance * np.cos(angle)
                dy = distance * np.sin(angle)
                target_position = leader_position + np.array([dx, dy, 0])
                drone.go_xyz_speed(
                    int(target_position[0]),
                    int(target_position[1]),
                    int(target_position[2]),
                    30,
                )

        self.callAllDrones(move_to_position)

    def addDrone(self, drone: Tello):
        """
        Add a drone to the swarm.
        """
        self.drones.append(drone)
        self.swarm_size += 1
        self.barrier = Barrier(self.swarm_size)
        self.funcBarrier = Barrier(self.swarm_size + 1)
        self.funcQueues.append(Queue())
        thread = Thread(target=self.init_worker, args=(self.swarm_size - 1,))
        thread.start()
        self.threads.append(thread)

    def remove_drone(self, index: int):
        if 0 <= index < self.swarm_size:
            self.drones.pop(index)
            self.swarm_size -= 1
            self.barrier = Barrier(self.swarm_size)
            self.funcBarrier = Barrier(self.swarm_size + 1)
            self.funcQueues.pop(index)
            self.threads.pop(index).join()

    async def async_call_all_drones(self, func: Callable[[int, Tello], None]):
        tasks = [
            asyncio.to_thread(func, i, drone) for i, drone in enumerate(self.drones)
        ]
        await asyncio.gather(*tasks)

    def callAllDrones(self, func: Callable[[int, Tello], None]):
        """
        Call a function on all drones in the swarm.
        """
        for queue in self.funcQueues:
            queue.put(func)
        self.funcBarrier.wait()

    def health_check(self):
        statuses = []
        for i, drone in enumerate(self.drones):
            try:
                battery = drone.get_battery()
                status = f"Drone {i}: Battery at {battery}%"
                statuses.append(status)
            except Exception as e:
                statuses.append(f"Drone {i}: Error - {e}")
        return statuses

    def callDrone(self, func: Callable[[int, Tello], None], drone: int):
        """
        Call a function on a specific drone in the swarm.
        """
        self.funcQueues[drone].put(func)
        self.funcBarrier.wait()

    def callNextDrone(self, func: Callable[[int, Tello], None]):
        """
        Call a function on the next drone in the swarm.
        """
        self.callDrone(func, self.curDrone)
        self.curDrone = (self.curDrone + 1) % self.swarm_size

    def wait(self):
        """
        Wait for all drones in the swarm to finish their current function.
        """
        self.funcBarrier.wait()

    def syncDrones(self, timeout: float = None):
        """Sync parallel tello threads. The code continues when all threads
        have called `swarm.sync`.

        ```python
        def doStuff(i, tello):
            tello.move_up(50 + i * 10)
            swarm.sync()

            if i == 2:
                tello.flip_back()
            # make all other drones wait for one to complete its flip
            swarm.sync()

        swarm.parallel(doStuff)
        """
        return self.Barrier.wait(timeout)

    def __del__(self):
        """
        End the connection to all drones in the swarm.
        """
        for drone in self.drones:
            try:
                drone.end()
            except Exception as e:
                logging.error(f"Error ending drone connection: {e}")

    def __getattr__(self, attrName):
        """
        Call a function on all drones in the swarm.
        E.X:
            swarm.takeoff()
            swarm.flip("r")
            swarm.land()
        """

        def wrapper(*args, **kwargs):
            self.callAllDrones(
                lambda i, drone: getattr(drone, attrName)(*args, **kwargs)
            )

        return wrapper

    def __iter__(self):
        """
        Return an iterator for the drones in the swarm.
        """
        return iter(self.drones)

    def __len__(self):
        """
        Return the number of drones in the swarm.
        """
        return self.swarm_size
