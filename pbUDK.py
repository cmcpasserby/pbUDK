import pymel.core as pm


class UI(object):
    def __init__(self):
        if pm.window('pbudk', exists=True):
            pm.deleteUI('pbudk')

        with pm.window('pbudk', title='pbUDK2', width=250, sizeable=False, mb=True, mbv=True, mnb=True, mxb=True) as window:
            with pm.columnLayout() as self.wrapper:

                # UI Sections
                PhyUI()
                FbxUI()
                T3dUI()

                # Render Window
                window.show()


class PhyUI(object):
    def __init__(self):
        with pm.frameLayout('Physics', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Collision Type:')
                self.phyType = pm.radioButtonGrp(labelArray2=['Convex Hull(UCX)', 'Box Collison(UCX)'],
                                                 sl=0, nrb=2, cc=self._enableMaxVerts)
                self.maxVerts = pm.intSliderGrp(field=True, l='Max Vertices:', v=32)
                pm.button(l='Add Hull', w=250, c=self._addHull)

    def _addHull(self, *args):
        if self.phyType.getSelect() == 1:
            self.convexHull()
        elif self.phyType.getSelect() == 2:
            self.boxHull()
        else:
            self.sphereHull()

    def convexHull(self):
        sel = pm.selected()
        inputMesh = sel[0].getShape()
        hullNode = pm.createNode('DDConvexHull')
        outputNode = pm.createNode('mesh', n='UCX_%sShape' % sel[0])

        pm.connectAttr('%s.outMesh' % inputMesh, '%s.input[0].inputPolymesh' % hullNode)
        pm.connectAttr('%s.output' % hullNode, '%s.inMesh' % outputNode)

        hullNode.maxVertices.set(self.maxVerts.getValue())
        outputNode.getParent().setParent(sel[0])

        # Move collsion to 0, 0, 0 due to it being parented
        outputNode.getParent().translate.set(0, 0, 0)

    def boxHull(self):
        sel = pm.selected()
        bb = sel[0].getBoundingBox()
        hull = pm.polyCube(w=bb.width(), h=bb.height(), d=bb.depth(), n='UCX_%s' % sel[0])
        cnt = pm.objectCenter(sel[0])
        hull[0].setTranslation(cnt)

        sg = pm.PyNode('initialShadingGroup')
        sg.remove(hull[0].getShape())
        hull[0].setParent(sel[0])

    def _enableMaxVerts(self, *args):
        if self.phyType.getSelect() == 1:
            self.maxVerts.setEnable(True)
        else:
            self.maxVerts.setEnable(False)


class FbxUI(object):
    def __init__(self):
        with pm.frameLayout('Export Meshes (.FBX)', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Export Path:')
                with pm.rowColumnLayout(nc=2, cw=[(1, 215), (2, 32)]):
                    self.fbxPath = pm.textField()
                    pm.button(l='...', c=self._path)

                with pm.rowColumnLayout(nc=2):
                    self.center = pm.checkBox(label='Move to Orgin', v=True)
                    self.child = pm.checkBox(label='Export Childern', v=True)

                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2, 124)]):
                    pm.button(l='Selected', c=self._selected)
                    pm.button(l='All', c=self._all)

        # Path Set
        self.fbxPath.setText(pm.workspace(q=True, rd=True) + 'data/')

    def _path(self, *args):
        path = self.fbxPath.getText()
        path = pm.fileDialog2(dir=path, fm=3, okc='Select Folder', cap='Select Export Folder')
        try:
            self.fbxPath.setText(path[0])
        except TypeError:
            pass

    def _selected(self, *args):
        self.export(self.fbxPath.getText(), all=False, center=self.center.getValue(), child=self.child.getValue())

    def _all(self, *args):
        self.export(self.fbxPath.getText(), all=True, center=self.center.getValue(), child=self.child.getValue())

    def export(self, path, all=False, center=True, child=True):
        # Load the fbx Preset
        pm.mel.FBXLoadExportPresetFile(f="C:/Users/User/Documents/maya/2012-x64/scripts/UDKexport/UDK-FBX.fbxexportpreset")
        ext = '.fbx'

        if all:
            pm.select(ado=True)
            sel = pm.selected()
        else:
            sel = pm.selected()

        if len(sel) == 0:
            pm.warning('Nothing is selected!')
        else:
            for obj in sel:
                pm.select(obj)
                if center:
                    oldLoc = obj.getRotatePivot()
                    self.centerPiv(obj)
                exportPath = path + obj.name() + ext
                if child:
                    children = obj.getChildren()
                    for i in children:
                        if isinstance(i, pm.nt.Transform):
                            pm.select(i, add=True)
                pm.mel.FBXExport(f=exportPath, s=True)
                if center:
                    obj.translateBy([oldLoc[0], oldLoc[1], oldLoc[2]])

    def centerPiv(self, obj):
        pm.select(obj)
        pm.makeIdentity(apply=True, t=True, r=True, s=True, n=False)
        pos = obj.getRotatePivot()
        obj.translate.set(-1 * pos.x, -1 * pos.y, -1 * pos.z)


class RefUI(object):
    def __init__(self):
        with pm.frameLayout('UDK Reference', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Reference Name:')
                self.refName = pm.textField(w=250)
                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2, 124)]):
                    pm.button(l='Add/Set Reference', c=self._addRef)
                    pm.button(l='Remove Reference', c=self._removeRef)

    def _addRef(self, *args):
        sel = pm.selected()
        if len(sel) != 0:
            for item in sel:
                try:
                    item.T3DTag.set(self.refName.getText())
                except:
                    item.addAttr('T3DTag', dt='string')
                    item.T3DTag.set(self.refName.getText())
        else:
            pm.warning('Select at least one polygon object')

    def _removeRef(self, *args):
        sel = pm.selected()
        if len(sel) != 0:
            for item in sel:
                try:
                    item.T3DTag.delete()
                except:
                    pm.warning('No Tag to delete!')
        else:
            pm.warning('Select at least one polygon object!')


class T3dUI(object):
    def __init__(self):
        with pm.frameLayout('Export Transformations (.T3D)', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Export Path:')
                with pm.rowColumnLayout(nc=2, cw=[(1, 215), (2, 32)]):
                    self.t3dPath = pm.textField()
                    pm.button(l='...', c=self._path)
                pm.text(l='Map Name:')
                self.mapName = pm.textField(w=250)
                pm.button(l='Export Level', w=250, c=self._export)

        # Path Set
        self.t3dPath.setText(pm.workspace(q=True, rd=True) + 'data/UDKexport.t3d')

    def _path(self, *args):
        path = self.t3dPath.getText()
        filters = "Unreal Text (*.t3d)"
        path = pm.fileDialog2(dir=path, fm=0, ff=filters, cap='Set T3D Location')
        try:
            self.t3dPath.setText(path[0])
        except TypeError:
            pass

    def _export(self, *args):
        pass
