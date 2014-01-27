pbUDK
=====

pbUDK is a toolset for working with and exporting content from Maya to UDK, Includes one click export tools, and collision hull generation tools with future plans for exporting transformations via unrealText to udk.

Installation
------------
Clone or extract contents to the parent of your Maya scripts folder.  Than enable the DDConvexHull plug-in for your version of Maya in the Maya plugin manager

Once this is done simply just open a python console and run these commands. 
```
import pbUDK
pbUDK.UI()
```
Optionally you could create a shelf button containing the same python code as above.

Credits
-------
The convex hull [DDConvexHull]( https://github.com/digitaldestructo/DDConvexHull) generation plug-in was written by [Jonathan Tilden]( https://github.com/digitaldestructo), who created a Maya Node that uses the StanHull method to create a convex hull in real-time.  The open source code StanHull code in the plugin was written by Stan Melax and John Ratcliff.
