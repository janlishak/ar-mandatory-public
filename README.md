# Exam Project: Robot Tag

## Project Description

The robots have decided to play tag. Your task is to develop a seeker robot and an
avoider robot (it could be the same robot with different behaviors, or two separate
robots). In tag one robot is assigned to be the seeker and the others are avoiders.
The seeker starts in the center and the avoiders in the corners. In the center of the
arena a zone is marked with gray floor in which an avoider is safe. However, there
is only space for one avoider at a time! The winner of a round is the avoider that
stays alive the longest or all the avoiders still alive after 3 minutes.

### Technical requirements

You receive a Thymio II robot and you are welcome to use LEGO too. We will make
a rectangular arena where the floor is white, the safe zone is gray and the perimeter
is a black line. There will be no walls.
1. You are free to use any approach, sensor and robot (taught/used in the course)
2. It is expected that you employ some form of robot learning or evolutionary
robotics, but maybe this is not where you want to start.
3. A seeker robot has to turn its LEDs red and if in the safe zone orange.
4. An avoider robot has to turn its LEDs blue, but if it is safe green and if it is
tagged purple (due to embarrassment).
5. A seeker transmits “1” and if an avoider receives this it is tagged and has to
stand still.
6. An avoider transmits “2” and if an avoider in the safe zone receives this it has
to leave immediately and can first after 5 seconds begin to transmit “2”.
7. It is essential that you focus on how to make a robot that performs well also
in practice.

### Handin

Work on the project will start in full on the 19th of November. There will be no
mandatory teaching for the rest of the course, but some outings and talks may be
planned. We will have a tag-game on the 10th of December at 10:00 with prizes
for best performing robots. Handin of a group report documenting your project the
18th of December at 14:00


## Plan:

### Stage 1: Make it move.

- [x] Identify each sensor on the thymio bot w.r.t. actual position etc
- [x] Identify distance sensors detect other robots
- [x] Get baseline sensor readings from ground sensors.
	- black < 70
	- shiny > 800
	- base  > 400
- [x] Update obstacle avoidance code for this environment
- [x] Rewrite provided code to avoid using async

- [x] End of stage 1: A robot that can move around the environment, staying within the border.

### Stage 2: Make it aware.

- [x] Use camera to detect other robots
- [x] Camera to detect colour (-> status) of other robots
- [x] Seeker behaviour: search for untagged robots
- [x] Avoider behaviour: avoid collisions with other bots
- [x] Test signal emission/reception with another bot

- [x] End of stage 2: robot that can meet the task requirement in the most basic way

### Stage 3: Make it learn.

- [x] Use q-learning to optimise seeker behaviour

- [x] End of stage 3: robot ready to compete
