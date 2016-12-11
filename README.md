# c4d_python_octree_plugin
Octree visualized with a Cinema 4D Python Plugin

This is a test I did for myself to visualize octree code.


Included scene file: python_octree.c4d

BP Py Octree Object
Parameters:
Scripts:
    Null Count: Number of search objects added to scene when "Add Nulls" is pressed
    Radius: Radius of the random placement of nulls
    Seed: Seed for random generator
    Add Null: Adds nulls that will be searched
    Remove Nulls: Removes all children of the Octree object

Octree:
    Max Depth: Maximum depth of the octree
    Max Elements Per Node: Maximum number of elements a node will contain before it divides
    Radius: Radius of the root null

Query:
    Query Object Link: A link for an object that will set the position of the octree query
    Radius: Radius of the bounding box that will be used for the query

Display:
    Draw Octree Nodes: Un-check to hide the bounding boxes drawn for the nodes
    Octree Node Color: Base color for the nodes
    Query Set Octree Node Color: Color of nodes that are part of the query
    Element Color: Base color of the spheres that represent elements that will be tested for distance
    Query Set Element Color: Color of elements that were selected in the query
    Closest Element Color: After the octree does the query, the closest object is calculated.
    Query Box Color: Color of the bounding box used for query
    Element Radius: Base radius for elements
    Query Set Element Radius: Radius of elements of object selected in the query
    Closes Element Radius: Radius of the closest element

