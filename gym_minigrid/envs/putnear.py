from gym_minigrid.minigrid import *
from gym_minigrid.register import register
import random

class PutNearEnv(MiniGridEnv):
    """
    Environment in which the agent is instructed to place an object near
    another object through a natural language string.
    """

    def __init__(
        self,
        size=6,
        numObjs=6,
        walls=[],
        path=[],
        digblock_positions=[]
    ):
        self.numObjs = numObjs
        self.grid_size = size
        self.walls = walls
        self.path = path
        self.digblock_positions = digblock_positions

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

        print(self.width)

        # add in maze walls
        if len(self.path)<1:
            for wall in self.walls:
                self.grid.set(*wall, Wall())
        else:
            print(self.grid_size)
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
        goal_pos = (self.grid_size-2, self.grid_size-2)
        self.put_obj(obj, *goal_pos)
        objs.append(('box', 'red'))
        objPos.append(goal_pos)

        # Generate single dig block
        obj = Ball('blue')
        blocks = random.sample(self.digblock_positions, self.numObjs)
        for pos in blocks:
            self.put_obj(obj, *pos)
            objs.append(('ball', 'blue'))
            objPos.append(pos)

        # TODO: further down will need to be smart abt how we place these
        # Until we have generated all the objects
        # while len(objs) < self.numObjs:
            # Generate single dig block
            # obj = Ball('blue')
            # pos = self.place_obj(obj, reject_fn=near_obj)
            # objs.append(('ball', 'blue'))
            # objPos.append(pos)

        # Randomize the agent start position and orientation
        self.put_agent(1, 1)

        # Choose a random object to be moved
        objIdx = 0 #self._rand_int(0, len(objs))
        self.move_type, self.moveColor = 'ball', 'blue' #objs[objIdx]
        self.move_pos = objPos[objIdx]

        # Choose a target object (to put the first object next to)
        self.target_type, self.target_color = 'box', 'red' #objs[targetIdx]
        self.target_pos = goal_pos

        self.mission = 'put the %s %s near the %s %s' % (
            self.moveColor,
            self.move_type,
            self.target_color,
            self.target_type
        )

    def step(self, action):
        preCarrying = self.carrying

        obs, reward, done, info = super().step(action)

        u, v = self.dir_vec
        ox, oy = (self.agent_pos[0] + u, self.agent_pos[1] + v)
        tx, ty = self.target_pos

        # If we picked up the wrong object, terminate the episode
        if action == self.actions.pickup and self.carrying:
            reward += 0.01
            if self.carrying.type != self.move_type or self.carrying.color != self.moveColor:
                done = True
            else:
                pass
                # reward += 0.1

        # If successfully dropping an object near the target
        if action == self.actions.drop and preCarrying:
            if self.grid.get(ox, oy) is preCarrying:
                print('picked up object')
                if abs(ox - tx) <= 1 and abs(oy - ty) <= 1:
                    reward += self._reward()

                    print('success!')
            done = True

        return obs, reward, done, info


class PutNear7x7N4(PutNearEnv):
    def __init__(self):
        super().__init__(size=7, numObjs=3)


class PutNear8x8N3(PutNearEnv):
    def __init__(self):
        super().__init__(size=8, numObjs=3,
                         walls=[
                            # (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
                            (2, 2), (2, 2), (3, 2), (4, 2), (5, 2),
                            (5, 3),
                            (1, 4), (2, 4), (3, 4), (5, 4),
                            (1, 5), (2, 5), (3, 5), (5, 5)],
                         digblock_positions=[(2,3), (4,6), (6,3)]
                         )


class PutNear12x12N5(PutNearEnv):
    def __init__(self):
        super().__init__(size=12, numObjs=4,
                        path=[
                            (1, 1), (2, 1), (5, 1), (6, 1), (7, 1), (8, 1),(9,1), (10,1),
                            (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (10, 2),
                            (1, 3), (5, 3), (10, 3),
                            (1, 4), (5, 4), (10, 4),
                            (1, 5), (5, 5), (10, 5),
                            (1, 6), (5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6),
                            (1, 7), (7, 7), (10, 7),
                            (1, 8), (7, 8), (10, 8),
                            (1, 9), (2, 9), (3, 9), (4, 9), (5, 9), (6, 9), (7, 9), (10, 9),
                            (1, 10), (7, 10), (8, 10), (9, 10), (10, 10)],
                        digblock_positions=[(1, 2), (5, 1), (9, 6), (10, 1), (6, 9)])


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
