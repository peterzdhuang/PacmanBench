# PacmanBench


speed needs to a factor when frightened 
decrease it to 1 block every 2 seconds?
they cannot reverse unless changing modes?

ghosts have 2 rules when calculating a target tile 
they cant reverse
they cant go into a wall 

So when a target tile is found, 
it will take the euclidian distance of its legal neighbours 
to find out which is the closest 

if there is a tie  right and top will always take precedence 

the formula for euclidian distance is 
L2=(xneighbor​−xtarget​)^2+(yneighbor​−ytarget​)^2



Blinky (Red): Top-right

Pinky (Pink): Top-left

Inky (Cyan): Bottom-right

Clyde (Orange): Bottom-left