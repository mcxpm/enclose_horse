% enclose.horse solver: place at most B walls to enclose the horse in the
% highest-scoring area.
%
% Facts supplied by Python (see grid_to_facts in main.py):
%   cell(R,C)       every cell in the grid
%   walkable(R,C)   the horse can stand here (not water or a pre-placed wall)
%   grass(R,C)      a wall may be built here (plain '.' cells only)
%   boundary(R,C)   edge cell: if the horse reaches it, it escapes
%   horse(R,C)      the horse's starting cell
%   portal(R,C,P)   portal cell; cells with the same P are linked
%   bonus(R,C,V)    extra points if enclosed (cherry 3, apple 10, bees -5)
%   budget(B)       the most walls we may place

% Some grids have no portals or bonus items; tell clingo that's fine.
#defined portal/3.
#defined bonus/3.

dir(-1,0). dir(1,0). dir(0,-1). dir(0,1).

% Neighbours: up/down/left/right, plus every other cell of the same portal.
adj(R,C,R+DR,C+DC) :- cell(R,C), dir(DR,DC), cell(R+DR,C+DC).
adj(R1,C1,R2,C2)   :- portal(R1,C1,P), portal(R2,C2,P), (R1,C1) != (R2,C2).

% Choose up to B walls, only on grass.
{ wall(R,C) : grass(R,C) } B :- budget(B).

% z(R,C): the cells the horse can reach.
z(R,C)   :- horse(R,C).
z(R2,C2) :- z(R1,C1), adj(R1,C1,R2,C2), walkable(R2,C2), not wall(R2,C2).

% The horse must not reach the edge.
:- z(R,C), boundary(R,C).

% A wall that doesn't touch the enclosure changes nothing, so forbid it.
% This doesn't change the best score; it just saves the solver from trying
% every pointless spot for spare walls.
touches(R,C) :- wall(R,C), adj(R,C,R2,C2), z(R2,C2).
:- wall(R,C), not touches(R,C).

% Score: 1 per enclosed cell, plus each enclosed cell's bonus.
#maximize { 1,R,C,area : z(R,C) ; V,R,C,bonus : z(R,C), bonus(R,C,V) }.

#show wall/2.
