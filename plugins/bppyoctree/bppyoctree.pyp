# bppyoctree.pyp
# Octree test visualized in Cinema 4D
# R18
# Joe Buck
# 12/10/2016

import os
import random
import c4d
from c4d import plugins, bitmaps

PLUGIN_ID = 1038479


class AABB(object):
    def __init__(self, pos, rad):
        self.pos = pos
        self.rad = rad
        self.top = self.pos.y + c4d.Vector(0.0, self.rad, 0.0).y
        self.bottom = self.pos.y - c4d.Vector(0.0, self.rad, 0.0).y
        self.right = self.pos.x + c4d.Vector(self.rad, 0.0, 0.0).x
        self.left = self.pos.x - c4d.Vector(self.rad, 0.0, 0.0).x
        self.back = self.pos.z + c4d.Vector(0.0, 0.0, self.rad).z
        self.front = self.pos.z - c4d.Vector(0.0, 0.0, self.rad).z

    def IntersectAABB(self, other):
        if (self.bottom > other.top or
                    self.top < other.bottom or
                    self.right < other.left or
                    self.left > other.right or
                    self.back < other.front or
                    self.front > other.back):
            return False
        else:
            return True

    def IntersectPoint(self, v):
        if (v.x < self.right and
                    v.x > self.left and
                    v.y > self.bottom and
                    v.y < self.top and
                    v.z < self.back and
                    v.z > self.front):
            return True
        else:
            return False

    def __str__(self):
        return "AABB pos:%f, %f, %f rad:%f" % (self.pos.x, self.pos.y, self.pos.z, self.rad)


class OctreeElement(object):
    def __init__(self, pos, obj):
        self.pos = pos
        self.obj = obj
        self.in_query_set = False
        self.distance = 0.0


class OctreeNode(object):
    def __init__(self, pos, rad, max_elements, max_depth, depth):
        self.aabb = AABB(pos, rad)
        self.max_elements = max_elements
        self.max_depth = max_depth
        self.depth = depth
        self.nodes = list()
        self.elements = list()
        self.in_query_set = False

    def Insert(self, element):
        if self.aabb.IntersectPoint(element.pos):
            if self.nodes:
                for node in self.nodes:
                    if node.Insert(element):
                        break
            else:
                if len(self.elements) < self.max_elements:
                    self.elements.append(element)
                else:
                    if self.depth >= self.max_depth:
                        self.elements.append(element)
                    else:
                        self.Divide()
                        self.elements.append(element)
                        for e in self.elements:
                            for node in self.nodes:
                                if node.Insert(e):
                                    break
                        del self.elements[:]
            return True
        else:
            return False

    def Divide(self):
        vectors = list()
        rad = self.aabb.rad / 2.0
        x = self.aabb.pos.x
        y = self.aabb.pos.y
        z = self.aabb.pos.z

        # top left back
        vectors.append(c4d.Vector(x - rad, y + rad, z + rad))
        # top right back
        vectors.append(c4d.Vector(x + rad, y + rad, z + rad))
        # top left front
        vectors.append(c4d.Vector(x - rad, y + rad, z - rad))
        # top right front
        vectors.append(c4d.Vector(x + rad, y + rad, z - rad))
        # bottom left back
        vectors.append(c4d.Vector(x - rad, y - rad, z + rad))
        # bottom right back
        vectors.append(c4d.Vector(x + rad, y - rad, z + rad))
        # bottom left front
        vectors.append(c4d.Vector(x - rad, y - rad, z - rad))
        # bottom right front
        vectors.append(c4d.Vector(x + rad, y - rad, z - rad))

        for pos in vectors:
            self.nodes.append(OctreeNode(pos,
                                         rad,
                                         self.max_elements,
                                         self.max_depth,
                                         self.depth + 1))

    def Generator(self):
        yield self
        for node in self.nodes:
            for n in node.Generator():
                yield n

    def Query(self, aabb, list):
        if self.aabb.IntersectAABB(aabb):
            self.in_query_set = True
            if self.nodes:
                for node in self.nodes:
                    node.Query(aabb, list)
            else:
                for element in self.elements:
                    element.in_query_set = True
                    element.distance = (aabb.pos - element.pos).GetLengthSquared()
                    list.append(element)


class BPPyOctreeData(plugins.ObjectData):
    def __init__(self):
        self.octree = None
        self.nearest_object = None

    def Message(self, node, type, data):
        if type == c4d.MSG_DESCRIPTION_COMMAND:
            if data['id'][0].id == c4d.ADD_NULLS_BUTTON:
                c4d.StopAllThreads()
                data = node.GetDataInstance()
                count = data.GetLong(c4d.ADD_NULLS_COUNT)
                seed = data.GetLong(c4d.ADD_NULLS_SEED)
                rad = data.GetReal(c4d.ADD_NULLS_RADIUS)
                random.seed(seed)
                doc = node.GetDocument()
                doc.StartUndo()
                for i in xrange(count):
                    null = c4d.BaseObject(c4d.Onull)
                    # null[c4d.NULLOBJECT_DISPLAY] = c4d.NULLOBJECT_DISPLAY_NONE
                    x = random.uniform(-rad, rad)
                    y = random.uniform(-rad, rad)
                    z = random.uniform(-rad, rad)
                    null.InsertUnderLast(node)
                    null.SetName(str(i))
                    doc.AddUndo(c4d.UNDOTYPE_NEW, null)
                    null.SetAbsPos(c4d.Vector(x, y, z))
                doc.EndUndo()
                c4d.EventAdd()
            elif data['id'][0].id == c4d.REMOVE_NULLS_BUTTON:
                c4d.StopAllThreads()
                children = node.GetChildren()
                doc = node.GetDocument()
                doc.StartUndo()
                for child in children:
                    doc.AddUndo(c4d.UNDOTYPE_DELETE, child)
                    child.Remove()
                doc.EndUndo()
                c4d.EventAdd()
        return True

    def Init(self, node):
        data = node.GetDataInstance()
        data.SetLong(c4d.ADD_NULLS_COUNT, 100)
        data.SetReal(c4d.ADD_NULLS_RADIUS, 100.0)
        data.SetLong(c4d.ADD_NULLS_SEED, 0)
        data.SetLong(c4d.OCTREE_MAX_DEPTH, 5)
        data.SetLong(c4d.OCTREE_MAX_NODE_ELEMENTS, 2)
        data.SetReal(c4d.OCTREE_RAD, 100.0)
        data.SetReal(c4d.QUERY_RAD, 10.0)
        data.SetBool(c4d.DISPLAY_DRAW_NODES, True)
        data.SetVector(c4d.DISPLAY_NODE_COLOR, c4d.Vector(0.277, 0.366, 0.59))
        data.SetVector(c4d.DISPLAY_SELECTED_NODE_COLOR, c4d.Vector(0.164, 0.74, 0.133))
        data.SetVector(c4d.DISPLAY_ELEMENT_COLOR, c4d.Vector(0.087000, 0.230816, 0.870000))
        data.SetVector(c4d.DISPLAY_SELECTED_ELEMENT_COLOR, c4d.Vector(0.110920, 0.940000, 0.065800))
        data.SetVector(c4d.DISPLAY_CLOSEST_ELEMENT_COLOR, c4d.Vector(0.83, 0.733, 0))
        data.SetVector(c4d.DISPLAY_QUERY_BOX_COLOR, c4d.Vector(0.778, 0.118, 0.91))
        data.SetReal(c4d.DISPLAY_ELEMENT_RADIUS, 3.0)
        data.SetReal(c4d.DISPLAY_SELECTED_ELEMENT_RADIUS, 5.0)
        data.SetReal(c4d.DISPLAY_CLOSEST_ELEMENT_RADIUS, 8.0)
        return True

    def AddToExecution(self, op, list):
        list.Add(op, c4d.EXECUTIONPRIORITY_EXPRESSION, 0)
        return True

    def Execute(self, op, doc, bt, priority, flags):
        self.octree = OctreeNode(c4d.Vector(0.0),
                                 op.GetParameter(c4d.OCTREE_RAD, c4d.DESCFLAGS_GET_0),
                                 op.GetParameter(c4d.OCTREE_MAX_NODE_ELEMENTS, c4d.DESCFLAGS_GET_0),
                                 op.GetParameter(c4d.OCTREE_MAX_DEPTH, c4d.DESCFLAGS_GET_0),
                                 0)

        objects = op.GetChildren()
        # print "objects count %i" % (len(objects),)
        for obj in objects:
            self.octree.Insert(OctreeElement(obj.GetAbsPos(), obj))
        query_object = op.GetParameter(c4d.QUERY_OBJECT_LINK, c4d.DESCFLAGS_GET_0)
        if query_object is not None:
            query_rad = op.GetParameter(c4d.QUERY_RAD, c4d.DESCFLAGS_GET_0)
            query_pos = ~op.GetMg() * query_object.GetMg().off
            query_list = list()
            self.octree.Query(AABB(query_pos, query_rad), query_list)
            if query_list:
                query_list.sort(key=lambda x: x.distance)
                self.nearest_object = query_list[0].obj
            else:
                self.nearest_object = None
        return c4d.EXECUTIONRESULT_OK

    def Draw(self, op, drawpass, bd, bh):
        if drawpass != c4d.DRAWPASS_OBJECT:
            return c4d.DRAWRESULT_SKIP
        cam = bd.GetSceneCamera(bh.GetDocument())
        if cam is not None:
            data = op.GetDataInstance()
            bd.SetMatrix_Matrix(op, op.GetMg())
            query_object = op.GetParameter(c4d.QUERY_OBJECT_LINK, c4d.DESCFLAGS_GET_0)
            if query_object is not None:
                m = c4d.Matrix()
                m.off = ~op.GetMg() * query_object.GetMg().off
                bd.DrawBox(m, data.GetReal(c4d.QUERY_RAD), data.GetVector(c4d.DISPLAY_QUERY_BOX_COLOR), True)
            for node in self.octree.Generator():
                if op.GetParameter(c4d.DISPLAY_DRAW_NODES, c4d.DESCFLAGS_GET_0):
                    m = c4d.Matrix()
                    m.off = node.aabb.pos
                    line_z_offset = 4 if node.in_query_set else 2
                    bd.LineZOffset(line_z_offset)
                    color = c4d.DISPLAY_SELECTED_NODE_COLOR if node.in_query_set else c4d.DISPLAY_NODE_COLOR
                    bd.DrawBox(m,
                               node.aabb.rad,
                               data.GetVector(color),
                               True)
                for element in node.elements:
                    selected_element_color = op.GetParameter(c4d.DISPLAY_SELECTED_ELEMENT_COLOR, c4d.DESCFLAGS_GET_0)
                    element_color = op.GetParameter(c4d.DISPLAY_ELEMENT_COLOR, c4d.DESCFLAGS_GET_0)
                    color = selected_element_color if node.in_query_set else element_color
                    element_size = op.GetParameter(c4d.DISPLAY_ELEMENT_RADIUS, c4d.DESCFLAGS_GET_0)
                    selected_element_size = op.GetParameter(c4d.DISPLAY_SELECTED_ELEMENT_RADIUS, c4d.DESCFLAGS_GET_0)
                    size = selected_element_size if node.in_query_set else element_size
                    bd.DrawSphere(element.pos, c4d.Vector(size, size, size), color, c4d.NOCLIP_Z)
                if self.nearest_object:
                    color = op.GetParameter(c4d.DISPLAY_CLOSEST_ELEMENT_COLOR, c4d.DESCFLAGS_GET_0)
                    size = op.GetParameter(c4d.DISPLAY_CLOSEST_ELEMENT_RADIUS, c4d.DESCFLAGS_GET_0)
                    bd.DrawSphere(self.nearest_object.GetAbsPos(), c4d.Vector(size, size, size), color, c4d.NOCLIP_Z)
        return c4d.DRAWRESULT_OK

    def GetVirtualObjects(self, op, hh):
        # print "GetVirtualObjects"
        return_null = c4d.BaseObject(c4d.Onull)
        if not return_null:
            return
        return return_null


if __name__ == "__main__":
    path, file = os.path.split(__file__)
    bmp = bitmaps.BaseBitmap()
    bmp.InitWith(os.path.join(path, "res", "obppyoctree.tif"))
    plugins.RegisterObjectPlugin(id=PLUGIN_ID,
                                 str="BP Py Octree",
                                 g=BPPyOctreeData,
                                 description="Obppyoctree",
                                 icon=bmp,
                                 info=c4d.OBJECT_GENERATOR | c4d.OBJECT_INPUT | c4d.OBJECT_CALL_ADDEXECUTION)
