
import os
import time
import pickle
import random
from camera import Camera


class State:
    def __init__(self, camera) -> None:
        self.data = []

        resolution = 10
        mapped_x = int(camera.cX * resolution / camera.width)
        mapped_y = int(camera.cY * resolution / camera.height)

        self.data.append(mapped_x)

    def __str__(self) -> str:
        joined_string = ":".join(str(item) for item in self.data)
        return joined_string


class Action:
    def __init__(self, action):
        self.action = action

    def __str__(self) -> str:
        return str(self.action)


def my_hash(state: State, action: Action) -> str:
    return "{}.{}".format(str(state), str(action))


class QValueStore:
    def __init__(self, filePath: str) -> None:
        self.filePath = filePath
        self.storage: dict[str, float] = {}
        self.load(self.filePath)

    def get_q_value(self, state: State, action: Action) -> float:
        h = my_hash(state, action)
        return self.storage.get(h, -1.0)  # Default to -1 if not found

    def get_best_action(self, state: State, possibleActions: list[Action]) -> Action:
        return max(possibleActions, key=lambda action: self.get_q_value(state, action))

    def store_q_value(self, state: State, action: Action, value: float):
        h = my_hash(state, action)
        self.storage[h] = value

    def save(self):
        fw = open(self.filePath, "wb")
        pickle.dump(self.storage, fw)
        fw.close()
        print("saved: dictionary size", len(self.storage))

    # Loads a Q-table.
    def load(self, file: str):
        if os.path.exists(file):
            fr = open(file, "rb")
            self.storage = pickle.load(fr)
            print("Loading: dictionary size", len(self.storage))
            fr.close()
        else:
            self.save()


class ReinforcementProblem:
    def __init__(self) -> None:
        self.camera = Camera()
        self.camera.update()

        left = Action("LEFT")
        right = Action("RIGHT")
        forward = Action("FORWARD")
        stop = Action("STOP")
        self.ALL_ACTIONS = [left, right, forward, stop]

    def get_current_state(self) -> State:
        return State(self.camera)

    # Get the available actions for the given state.
    def get_available_actions(self, state: State) -> list[Action]:
        return self.ALL_ACTIONS

    # Take the given action and state, and return
    # a pair consisting of the reward and the new state.
    def take_action(self, state: State, action: Action) -> tuple[float, State]:
        reward = 0

        # todo: take the action
        self.camera.updateForSeconds(0.5)
        newState = self.get_current_state()

        return reward, newState

    # PARAMETERS:
    # Learning Rate
    # controls how much influence the current feedback value has over the stored Q-value.

    # Discount Rate
    # how much an action’s Q-value depends on the Q-value at the state (or states) it leads to.

    #  Randomness of Exploration
    # how often the algorithm will take a random action, rather than the best action it knows so far.


# Updates the store by investigating the problem.
def q_learning(
        problem: ReinforcementProblem,
        iterations,
        learningRate,
        discountRate,
        explorationRandomness
):
    # Get a starting state.
    # state = problem.getRandomState()
    save_iterations = 30
    # Repeat a number of times.
    total_change = 0  # Initialize total change
    num_changes = 0  # Initialize the number of changes
    state = problem.get_current_state()

    for i in range(iterations):
        # Get the list of available actions.
        actions = problem.get_available_actions(state)

        # Should we use a random action this time?
        if random.uniform(0, 1) < explorationRandomness:
            action = random.choice(actions)
            # print("adventure " + str(i))

        # Otherwise pick the best action if it has a known Q-value.
        else:
            best_action = store.get_best_action(state, actions)
            if store.get_q_value(state, best_action) == -1.0:  # No Q-value available
                action = random.choice(actions)  # Random exploration if unvisited
                # print("exploring unvisited " + str(i))
            else:
                action = best_action  # Use the best known action

        # Now get the current q from the store for the selected action.
        q = store.get_q_value(state, action)

        # Carry out the action and retrieve the reward and new state.
        reward, new_state = problem.take_action(state, action)

        # Get the q of the best action from the new state
        maxQ = store.get_q_value(
            new_state,
            store.get_best_action(new_state, problem.get_available_actions(new_state)),
        )

        # Perform the q learning.
        old_q = q
        q = (1 - learningRate) * q + learningRate * (reward + discountRate * maxQ)

        # Store the new Q-value.
        store.store_q_value(state, action, q)

        # And update the state.
        state = new_state

        # Update metrics
        change = abs(q - old_q)
        total_change += change
        num_changes += 1

        if i % save_iterations == 0:
            store.save()
            average_change = total_change / num_changes
            print(f"iteration {i}: average q-value change: {average_change:.02f} dictionary size: {len(store.storage)}")
            total_change = 0
            num_changes = 0


if __name__ == "__main__":
    store = QValueStore("training")
    problem = ReinforcementProblem()

    run = 0
    iterations = 100_00_000_000
    learning_rate = 0.1
    discount_rate = 0 # myopic (short-term focused) policy
    exploration_rate = 0.25 # on average every 4th action is random

    if run == 0:
        print("learning")
        q_learning(problem, iterations, learning_rate, discount_rate, exploration_rate)
    else:
        print("running")
        q_learning(problem, iterations, learning_rate, discount_rate, 0)
