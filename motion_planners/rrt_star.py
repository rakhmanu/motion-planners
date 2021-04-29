from __future__ import print_function

from random import random
from time import time

from .utils import INF, argmin, elapsed_time, BLUE, RED, apply_alpha

EPSILON = 1e-6
PRINT_FREQUENCY = 100

class OptimalNode(object):

    def __init__(self, config, parent=None, d=0, path=[], iteration=None):
        self.config = config
        self.parent = parent
        self.children = set()
        self.d = d
        self.path = path
        if parent is not None:
            self.cost = parent.cost + d
            self.parent.children.add(self)
        else:
            self.cost = d
        self.solution = False
        self.creation = iteration
        self.last_rewire = iteration

    def set_solution(self, solution):
        if self.solution is solution:
            return
        self.solution = solution
        if self.parent is not None:
            self.parent.set_solution(solution)

    def retrace(self):
        if self.parent is None:
            return self.path + [self.config]
        return self.parent.retrace() + self.path + [self.config]

    def rewire(self, parent, d, path, iteration=None):
        if self.solution:
            self.parent.set_solution(False)
        self.parent.children.remove(self)
        self.parent = parent
        self.parent.children.add(self)
        if self.solution:
            self.parent.set_solution(True)
        self.d = d
        self.path = path
        self.update()
        self.last_rewire = iteration

    def update(self):
        self.cost = self.parent.cost + self.d
        for n in self.children:
            n.update()

    def clear(self):
        self.node_handle = None
        self.edge_handle = None

    def draw(self, env):
        # https://github.mit.edu/caelan/lis-openrave
        from manipulation.primitives.display import draw_node, draw_edge
        color = apply_alpha(BLUE if self.solution else RED, alpha=0.5)
        self.node_handle = draw_node(env, self.config, color=color)
        if self.parent is not None:
            self.edge_handle = draw_edge(
                env, self.config, self.parent.config, color=color)

    def __str__(self):
        return self.__class__.__name__ + '(' + str(self.config) + ')'
    __repr__ = __str__


def safe_path(sequence, collision):
    path = []
    for q in sequence:
        if collision(q):
            break
        path.append(q)
    return path

##################################################

def rrt_star(start, goal, distance, sample, extend, collision, radius,
             max_time=INF, max_iterations=INF, goal_probability=.2, informed=True):
    if collision(start) or collision(goal):
        return None
    nodes = [OptimalNode(start)]
    goal_n = None
    start_time = time()
    iteration = 0
    while (elapsed_time(start_time) < max_time) and (iteration < max_iterations):
        do_goal = goal_n is None and (iteration == 0 or random() < goal_probability)
        s = goal if do_goal else sample()
        # Informed RRT*
        if informed and (goal_n is not None) and (distance(start, s) + distance(s, goal) >= goal_n.cost):
            continue
        if iteration % PRINT_FREQUENCY == 0:
            success = goal_n is not None
            cost = goal_n.cost if success else INF
            print('Iteration: {} | Time: {:.3f} | Success: {} | {} | Cost: {:.3f}'.format(
                iteration, elapsed_time(start_time), success, do_goal, cost))
        iteration += 1

        nearest = argmin(lambda n: distance(n.config, s), nodes)
        path = safe_path(extend(nearest.config, s), collision)
        if len(path) == 0:
            continue
        new = OptimalNode(path[-1], parent=nearest, d=distance(
            nearest.config, path[-1]), path=path[:-1], iteration=iteration)
        # if safe and do_goal:
        if do_goal and (distance(new.config, goal) < EPSILON):
            goal_n = new
            goal_n.set_solution(True)
        # TODO - k-nearest neighbor version
        neighbors = filter(lambda n: distance(n.config, new.config) < radius, nodes)
        nodes.append(new)

        # TODO: smooth solution once found to improve the cost bound
        for n in neighbors:
            d = distance(n.config, new.config)
            if (n.cost + d) < new.cost:
                path = safe_path(extend(n.config, new.config), collision)
                if (len(path) != 0) and (distance(new.config, path[-1]) < EPSILON):
                    new.rewire(n, d, path[:-1], iteration=iteration)
        for n in neighbors:  # TODO - avoid repeating work
            d = distance(new.config, n.config)
            if (new.cost + d) < n.cost:
                path = safe_path(extend(new.config, n.config), collision)
                if (len(path) != 0) and (distance(n.config, path[-1]) < EPSILON):
                    n.rewire(new, d, path[:-1], iteration=iteration)
    if goal_n is None:
        return None
    return goal_n.retrace()

def informed_rrt_star(start, goal, distance, sample, extend, collision, radius, **kwargs):
    return rrt_star(start, goal, distance, sample, extend, collision, radius, informed=True, **kwargs)
