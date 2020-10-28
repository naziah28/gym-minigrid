from gym_minigrid.minigrid import *
from gym_minigrid.register import register
import networkx as nx
import random

import logging
import logging.config

# logging.config.fileConfig(fname='file.conf', disable_existing_loggers=False)

# Get the logger specified in the file
logger = logging.getLogger(__name__)

ACTIONS = {
    0: "left",
    1: "right",
    2: "forward",
    3: "pickup",
    4: "drop",
    5: "toggle",
    6: "done"
}

def get_graph(path_nodes):
    G = nx.Graph()

    # Add all nodes into graph
    for coord in path_nodes:
        G.add_node(coord)

    for node_a in path_nodes:
        for node_b in path_nodes:
            # make sure they not the same node
            if node_a != node_b:
                if (node_a[0] == node_b[0] and abs(node_a[1]-node_b[1]) == 1) or \
                        ((node_a[1] == node_b[1]) and (abs(node_a[0]-node_b[0]) == 1)):
                    G.add_edge(node_a, node_b)
    return G


class PutNearEnv(MiniGridEnv):
    """
    Environment in which the agent is instructed to place an object near
    another object through a natural language string.
    """

    def __init__(
        self,
        size=6,
        numObjs=2,
        walls=[],
        path=[],
        digblock_positions=[(1,4), (4,1)],
        goal_pos=(4,4)
    ):
        self.numObjs = numObjs
        self.grid_size = size
        self.walls = walls
        self.path = path
        self.digblock_positions = digblock_positions
        self.dropped_block = 0
        self.goal_pos=goal_pos

        if walls==[] and path==[]:
            for i in range(1, self.grid_size - 1):
                for j in range(1, self.grid_size - 1):
                    self.path.append((j,i))

        self.graph = get_graph(path)

        super().__init__(
            grid_size=size,
            max_steps=5*size,
            # Set this to True for maximum speed
            see_through_walls=True
        )

    def _gen_grid(self, width, height):
        self.grid = Grid(width, height)

        # Generate the surrounding walls
        self.grid.horz_wall(0, 0)
        self.grid.horz_wall(0, height-1)
        self.grid.vert_wall(0, 0)
        self.grid.vert_wall(width-1, 0)

        # add in maze walls
        if len(self.path) < 1:
            for wall in self.walls:
                self.grid.set(*wall, Wall())
        else:
            for i in range(1, self.grid_size - 1):
                for j in range(1, self.grid_size - 1):
                    if (j, i) not in self.path:
                        self.grid.set(j, i, Wall())

        # Types and colors of objects we can generate
        objs = []
        objPos = []

        def near_obj(env, p1):
            for p2 in objPos:
                dx = p1[0] - p2[0]
                dy = p1[1] - p2[1]
                if abs(dx) <= 1 and abs(dy) <= 1:
                    return True
            return False

        # Generate crusher
        obj = Box('red')
        self.put_obj(obj, *self.goal_pos)
        objs.append(('box', 'red'))
        objPos.append(self.goal_pos)

        # Generate single dig block
        self.selected_blocks = random.sample(self.digblock_positions, self.numObjs)
        for pos in self.selected_blocks:
            obj = Ball('blue')
            self.put_obj(obj, *pos)
            objs.append(('ball', 'blue'))
            objPos.append(pos)

        # Randomize the agent start position and orientation
        self.put_agent(1, 1)

        # Choose a random object to be moved
        objIdx = 0 #self._rand_int(0, len(objs))
        self.move_type, self.moveColor = 'ball', 'blue' #objs[objIdx]
        self.move_pos = objPos[objIdx]

        # Choose a target object (to put the first object next to)
        self.target_type, self.target_color = 'box', 'red' #objs[targetIdx]
        self.target_pos = self.goal_pos

        self.mission = 'put the %s %s near the %s %s' % (
            self.moveColor,
            self.move_type,
            self.target_color,
            self.target_type
        )

        self.currently_holding = False

    def step(self, action):

        preCarrying = self.carrying

        obs, reward, done, info, step_count = super().step(action) # todo: give state too

        u, v = self.dir_vec
        ox, oy = (self.agent_pos[0] + u, self.agent_pos[1] + v)
        tx, ty = self.target_pos

        # logger.info('{}: \ttaking action {} to {} \t{}'.format(step_count, ACTIONS[action],(ox,oy), reward))

        # If we picked up the wrong object, terminate the episode
        if action == self.actions.pickup and self.carrying:
            if self.carrying.type != self.move_type or self.carrying.color != self.moveColor:
                # todo: give a large penalty
                done = True
            elif self.currently_holding:
                reward -= 1
            else:
                # just match to block
                for (bx,by) in self.selected_blocks:
                    if abs(ox - bx) <= 1 and abs(oy - by) <= 1 and not self.currently_holding:
                        self.selected_blocks.remove((bx,by))
                        collected = (self.numObjs-len(self.selected_blocks))
                        reward += 2* collected
                        logger.info('{}: \tpicked up object {} {} {}'.format(step_count, collected, (bx, by), reward))
                        # reset to 0 until next drop is made
                        self.dropped_block = 0
                        self.currently_holding = True
                        break
                pass

        # if step_count > self.dropped_block and (self.dropped_block != 0):
            # logger.info('{}: \tpost drop action {} \t{}'.format(step_count, ACTIONS[action], reward))
                # agent_pos = self.agent_pos if type(self.agent_pos) is tuple else tuple(self.agent_pos)
                # reward += 0.1 * (13 - len(nx.shortest_path(self.graph, source=agent_pos, target=self.goal_pos)))

        # stop pickup at target
        if action == self.actions.pickup and abs(ox - tx) <= 1 and abs(oy - ty) <= 1:
            reward = -30
            logger.info('dumb move')

        # If successfully dropping an object near the target
        if action == self.actions.drop and preCarrying:
            if self.grid.get(ox, oy) is preCarrying:
                if abs(ox - tx) <= 0 and abs(oy - ty) <= 0:
                    reward += 20 * (self.numObjs-len(self.selected_blocks))# self._reward()
                    logger.info(f'{step_count}: dropped block! {len(self.selected_blocks)} remaining')
                    self.dropped_block = step_count
                    self.currently_holding = False

                    if len(self.selected_blocks) < 1:
                        logger.info('success!')
                        print('success!')
                        done = True
                else:
                    # dropped right item at wrong location
                    reward += -2
                    agent_pos = self.agent_pos if type(self.agent_pos) is tuple else tuple(self.agent_pos)
                    reward -= 0.05 * (len(nx.shortest_path(self.graph, source=agent_pos, target=self.goal_pos)))
                    logger.info('fail! {}'.format(reward))
                    done = True
            # todo: done if only all digblocks collected



        return obs, reward, done, info


class PutNear7x7N4(PutNearEnv):
    def __init__(self):
        super().__init__(size=7, numObjs=2, goal_pos=(5,5), digblock_positions=[(1,5), (5,1)])


class PutNear8x8N3(PutNearEnv):
    def __init__(self):
        super().__init__(size=8, numObjs=3,
                         walls=[
                            (3, 2), (4, 2), (5, 2),
                            (5, 3),
                            (1, 4), (2, 4), (3, 4), (5, 4),
                            (1, 5), (2, 5), (3, 5), (5, 5)],
                         goal_pos=(6,6),
                         digblock_positions=[(2,2), (3,6), (6,1)]
                         )


class PutNear12x12N5(PutNearEnv):
    def __init__(self):
        super().__init__(size=12, numObjs=4,
                        path=[
                            # (1, 1), (2, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9,1), (10,1),
                            # (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6,2), (10, 2),
                            # (1, 3), (5, 3), (10, 3),
                            # (1, 4), (5, 4), (10, 4),
                            # (1, 5), (5, 5), (10, 5),
                            # (1, 6), (5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6),
                            # (1, 7), (7, 7), (10, 7),
                            # (1, 8), (7, 8), (10, 8),
                            # (1, 9), (2, 9), (3, 9), (4, 9), (5, 9), (6, 9), (7, 9), (10, 9),
                            # (1, 10), (7, 10), (8, 10), (9, 10), (10, 10)
                        ],
                         goal_pos=(6,6),
                        digblock_positions=[(6, 2), (9, 7), (9, 2), (6, 10)])

class PutNear50x50N6(PutNearEnv):
    def __init__(self):
        super().__init__(size=50, numObjs=4, goal_pos=(48, 48),
                        digblock_positions=[(10, 10), (45, 35), (45, 10), (30, 40)])


register(
    id='MiniGrid-PutNear-6x6-N2-v0',
    entry_point='gym_minigrid.envs:PutNearEnv'
)

register(
    id='MiniGrid-PutNear-7x7-N4-v0',
    entry_point='gym_minigrid.envs:PutNear7x7N4'
)

register(
    id='MiniGrid-PutNear-8x8-N3-v0',
    entry_point='gym_minigrid.envs:PutNear8x8N3'
)

register(
    id='MiniGrid-PutNear-12x12-N5-v0',
    entry_point='gym_minigrid.envs:PutNear12x12N5'
)

register(
    id='MiniGrid-PutNear-50x50-N6-v0',
    entry_point='gym_minigrid.envs:PutNear50x50N6'
)
