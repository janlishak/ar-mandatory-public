import math
import os
import pickle
import random
import time
import sys
sys.path.append('../')

from robot.BehaviouralModule import behaviouralModule
from simulation.simulation import Simulation
from robot.image_processor import ImageProcessor
import threading

SEEKER = 0
AVOIDER = 1

class State:
    def __init__(self, image_processor = None, simulation = None, fromString = None) -> None:
        if fromString is not None:
            self.data = fromString.split(":")
            return

        self.data = []

        self.map_resolution = 15
        self.floatX = image_processor.cX / image_processor.width
        self.distFromMiddle = 1-abs(self.floatX-0.5)
        self.mapped_x = int(image_processor.cX * self.map_resolution / image_processor.width)
        self.mapped_y = int(image_processor.cY * self.map_resolution / image_processor.height)
        self.found = image_processor.found
        self.current_action = simulation.current_action

        self.data.append("X#" + str(self.mapped_x) + "#")
        self.data.append("F#" + str(self.found) + "#")
        # self.data.append(self.current_action)

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

    def print_best_actions(self):
        best_actions = {}

        # Collect all unique states from the stored state-action pairs
        unique_states = {key.split('.')[0] for key in self.storage.keys()}

        for state_str in unique_states:
            # Create a mock State object from the state_str if needed
            state = self.str_to_state(state_str)

            # Get all actions associated with this state in the storage
            possible_actions = [
                self.str_to_action(key.split('.')[1])
                for key in self.storage.keys() if key.startswith(state_str + ".")
            ]


            # Find the best action
            if possible_actions:
                best_action = self.get_best_action(state, possible_actions)
                best_actions[state] = best_action
                print(f"State: {state}, Best Action: {best_action}")
            else:
                print(f"No actions found for state: {state}")

    def str_to_state(self, state_str: str) -> State:
        return State(fromString=state_str)

    def str_to_action(self, action_str: str) -> Action:
        return Action(action_str)

    def print_all_values(self):
        # Sort the storage items by `state_str` (first part of the key)
        sorted_items = sorted(self.storage.items(), key=lambda item: item[0].split('.')[0])

        # Print each sorted state-action pair with its Q-value
        for key, q_value in sorted_items:
            state_str, action_str = key.split('.')
            print(f"State: {state_str}, Action: {action_str}, Q-Value: {q_value}")

    def print_best_action_per_state(self):
        # Dictionary to store the best action for each state
        best_actions = {}

        # Go through each item in the storage
        for key, q_value in self.storage.items():
            state_str, action_str = key.split('.')

            # If the state is not in best_actions, or if the current q_value is higher, update it
            if state_str not in best_actions or q_value > best_actions[state_str][1]:
                best_actions[state_str] = (action_str, q_value)

        # Sort states by state_str and print the best action for each state
        for state_str in sorted(best_actions.keys()):
            action_str, q_value = best_actions[state_str]
            print(f"State: {state_str}, Action: {action_str}, Q-Value: {q_value}")

    def print_all_values_sorted_by_action(self):
        # Sort the storage items by `action_str` (second part of the key)
        sorted_items = sorted(self.storage.items(), key=lambda item: item[0].split('.')[1])

        # Print each sorted state-action pair with its Q-value
        for key, q_value in sorted_items:
            state_str, action_str = key.split('.')
            print(f"State: {state_str}, Action: {action_str}, Q-Value: {q_value}")


class ReinforcementProblem:
    def __init__(self, is_simulation=False) -> None:
        self.image_processor = ImageProcessor()

        if is_simulation:
            self.simulation = Simulation()
            self.image_processor.set_trackbar_values([29, 78, 139, 255, 110, 255, 5, 30])
        else:
            from robot_metal import Metal
            self.simulation = Metal()
            self.image_processor.set_trackbar_values([41, 83, 97, 151, 110, 255, 5, 30])

        self.image_processor.set_frame_provider(self.simulation.capture_frame_to_numpy)

        self.simulation.update()
        self.image_processor.update()

        left = Action("LEFT")
        right = Action("RIGHT")
        # forward = Action("FORWARD")
        # stop = Action("STOP")
        # self.ALL_ACTIONS = [left, right, forward, stop]
        self.ALL_ACTIONS = [left, right]

    def get_current_state(self) -> State:
        return State(self.image_processor, self.simulation)

    # Get the available actions for the given state.
    def get_available_actions(self, state: State) -> list[Action]:
        return self.ALL_ACTIONS

    # Take the given action and state, and return
    # a pair consisting of the reward and the new state.
    def take_action(self, state: State, action: Action) -> tuple[float, State]:
        print(action)
        # todo: disabled here!
        self.simulation.perform_action(str(action))
        time.sleep(0.25)
        newState = self.get_current_state()

        reward = math.pow(2, newState.distFromMiddle*10)

        if newState.found:
            reward += 100

        # print(newState.found)
        # if not newState.found:
        #     if str(state.current_action) != str(newState.current_action):
        #         print("change")
        #         reward -= 10
        #     else:
        #         reward += 10

        # print(reward)
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
        learningRate,
        discountRate,
        explorationRandomness):
    i = 0
    save_iterations = 100
    total_change = 0
    num_changes = 0
    state = problem.get_current_state()
    # state = problem.getRandomState()

    def update():
        nonlocal problem, learningRate, discountRate, explorationRandomness
        nonlocal i, save_iterations, total_change, num_changes, state
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
        i += 1
    return update


if __name__ == "__main__":
    is_simulation = False
    store = QValueStore("training")
    # store.print_best_actions()
    store.print_best_action_per_state()
    problem = ReinforcementProblem(is_simulation)

    learning_rate = 0.1
    discount_rate = 0.75
    exploration_rate = 0.2  # on average every 5th action is random
    exploration_rate = 0.1  # to run

    q_learning_update = q_learning(problem, learning_rate, discount_rate, exploration_rate)

    def q_learn_loop():
        while True:
            q_learning_update()
    thread = threading.Thread(target=q_learn_loop, daemon=True)
    thread.start()

    # SIMULATION
    if is_simulation:
        def update():
            problem.simulation.update()
            problem.image_processor.update()
        problem.simulation.app.run()

    # REAL WORLD
    else:
        # Behavior Module
        b = behaviouralModule(problem.simulation.controller, debug=True, max_speed=100, robot_type=SEEKER)
        def behavior_loop():
            while True:
                b.update()
                time.sleep(0.2)


        thread = threading.Thread(target=behavior_loop, daemon=True)
        thread.start()
        # Image processing loop
        while True:
            problem.image_processor.update()