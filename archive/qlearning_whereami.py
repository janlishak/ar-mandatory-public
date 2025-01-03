
import os
import time
import pickle
import random
from robot import ThymioController

class State:
    def __init__(self, surface, status) -> None:
        self.surface = surface
        self.status = status

    def __str__(self) -> str:
        
        return f'{self.surface}.{self.status}'


class Action:
    def __init__(self, direction, speed):
        self.action = f'{direction}.{speed}'

    def __str__(self) -> str:
        return self.action


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

        self.robot = ThymioController(role="avoider")

        directions = ["LEFT", "RIGHT", "FORWARD", "STOP", "BACKWARDS"]
        speeds = ["SLOW", "FAST"]

        self.ALL_ACTIONS = [(Action(direction, speed)) for direction in directions for speed in speeds] 


    def get_current_state(self) -> State:

        # surface = self.robot.detect_surface() # get surface from robot

        # status = self.robot.set_status() # current status, ie safe, normal, embarrassed
        
        
        surface = random.choice(["open-ground", "black-tape", "black-tape-left", "black-tape-right", "safe-zone", "safe-zone-left", "safe-zone-right"])
        status = ["embarrassed" if surface == "black-tape" else "safe" if surface == "safe_zone" else "normal"][0]
        print(f'simulating state: {surface}.{status}')
        return State(surface, status)

    # Get the available actions for the given state.
    def get_available_actions(self, state: State) -> list[Action]:
        return self.ALL_ACTIONS

    # Take the given action and state, and return
    # a pair consisting of the reward and the new state.
    def take_action(self, state: State, action: Action) -> tuple[float, State]:
        reward = 0

        # todo: take the action
        robot.perform_action(action.direction, action.speed)
        new_status = robot.get_status()
        ## make some reward function base on the new status
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
            print("adventure " + str(i))

        # Otherwise pick the best action if it has a known Q-value.
        else:
            best_action = store.get_best_action(state, actions)
            if store.get_q_value(state, best_action) == -1.0:  # No Q-value available
                action = random.choice(actions)  # Random exploration if unvisited
                print("exploring unvisited " + str(i))
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
    store = QValueStore("training_whereami")
    problem = ReinforcementProblem()

    run = 0
    iterations = 100_000
    learning_rate = 0.1
    discount_rate = 0 # myopic (short-term focused) policy
    exploration_rate = 0.2 # on average every 4th action is random

    if run == 0:
        print("learning")
        q_learning(problem, iterations, learning_rate, discount_rate, exploration_rate)
    else:
        print("running")
        q_learning(problem, iterations, learning_rate, discount_rate, 0)
