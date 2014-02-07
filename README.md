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

Usage
-----

### Physics
Once you got the UI running you can add adjust the amount of verts in the collision hull and add hulls with the add hull button.  If using the convex hull mode instead of box collision you can update the amount of verts in real time on a selected object with a hull attached, up to the point where you  delete history.

### Export Meshes
Export path just sets a directory to dump all export fbx files into, the file name it’s self id set from the name of the objects transform in the maya scene.
Move to origin, moves objects to 0 0 0 XYZ in the scene, before export and places them back to their old locations after export. Export children exports any meshes parented to the selected mesh I put this option in here so it will auto export collision hulls made with this tool. 
The tool comes with a default FBX export preset file that has good settings for UDK, but this can be set to use one made by the user with the FBXPreset button.


Credits
-------
The convex hull [DDConvexHull]( https://github.com/digitaldestructo/DDConvexHull) generation plug-in was written by [Jonathan Tilden]( https://github.com/digitaldestructo), who created a Maya Node that uses the StanHull method to create a convex hull in real-time.  The open source code StanHull code in the plugin was written by Stan Melax and John Ratcliff.
