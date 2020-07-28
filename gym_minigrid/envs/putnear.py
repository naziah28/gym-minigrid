from gym_minigrid.minigrid import *
from gym_minigrid.register import register


class PutNearEnv(MiniGridEnv):
    """
    Environment in which the agent is instructed to place an object near
    another object through a natural language string.
    """

    def __init__(
        self,
        size=6,
        numObjs=6
    ):
        self.numObjs = numObjs

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
        walls = [
            (2, 1), (3, 1), (4, 1), (5, 1),
            (1, 4), (2, 4), (3, 4),
            (1, 5), (2, 5), (3, 5),
        ]

        for wall in walls:
            self.grid.set(*wall, Wall())


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
        goal_pos = (6, 6)
        self.put_obj(obj, *goal_pos)
        objs.append(('box', 'red'))
        objPos.append(goal_pos)

        # Generate single dig block
        obj = Ball('blue')
        pos = (2,3)
        self.put_obj(obj, *pos)
        objs.append(('ball', 'blue'))
        objPos.append(pos)

        # TODO: further down will need to be smart abt how we place these
        # # Until we have generated all the objects
        # while len(objs) < self.numObjs:
        #
        #     # Generate single dig block
        #     obj = Ball('blue')
        #     pos = self.place_obj(obj, reject_fn=near_obj)
        #     objs.append(('ball', 'blue'))
        #     objPos.append(pos)

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
        super().__init__(size=8, numObjs=3)


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
