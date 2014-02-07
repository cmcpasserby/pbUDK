from pymel.util.common import path
import pickle
import pymel.core as pm


class UI(object):
    def __init__(self):
        if pm.window('pbudk', exists=True):
            pm.deleteUI('pbudk')

        with pm.window('pbudk', title='pbUDK', width=250, sizeable=False) as window:
            with pm.columnLayout() as self.wrapper:

                # UI Sections
                opts = Options()
                opts = opts.load()
                PhyUI(opts)
                FbxUI(opts)

                # Render Window
                window.show()


class Options(object):
    def __init__(self):
        self.optionsVersion = 1.0
        self.dumpPath = path('%s/pbUDK.conf' % pm.internalVar(usd=True))
        # Physics options
        self.phyType = 1
        self.maxVerts = 32

        # FBX options
        self.presetFile = path('%s/UDKexport/UDK-FBX.fbxexportpreset' % pm.internalVar(usd=True))
        self.fbxPath = path('%sdata/' % pm.workspace(q=True, rd=True))
        self.center = True
        self.child = True

    def dump(self):
        try:
            with open(self.dumpPath, 'wb') as dumpFile:
                pickle.dump(self, dumpFile)
        except:
            pass

    def load(self):
        try:
            if self.dumpPath.exists():
                with open(self.dumpPath, 'rb') as dumpFile:
                    return pickle.load(dumpFile)
            else:
                self.dump()
                return self
        except:
            pass


class PhyUI(object):
    def __init__(self, opts):
        self.opts = opts
        with pm.frameLayout('Physics', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Collision Type:')
                self.phyType = pm.radioButtonGrp(labelArray2=['Convex Hull', 'Box Collison'],
                                                 sl=self.opts.phyType, nrb=2, cc=self.saveOptions)
                self.maxVerts = pm.intSliderGrp(field=True, l='Max Vertices:', v=self.opts.maxVerts,
                                                cl3=['left', 'left', 'left'], cw3=[64, 48, 128],
                                                cc=self.saveOptions)
                pm.button(l='Add Hull', w=250, c=self._addHull)

    def _addHull(self, *args):
        if self.phyType.getSelect() == 1:
            self.convexHull()
        elif self.phyType.getSelect() == 2:
            self.boxHull()

    def convexHull(self):
        sel = pm.selected()
        print sel
        if not isinstance(sel[0], pm.nt.Transform):
            oldSel = sel
            sel = sel[0].node().getParent()
            print sel
        else:
            oldSel = sel
            sel = sel[0]

        inputMesh = sel.getShape()

        hullNode = pm.createNode('DDConvexHull')
        outputNode = pm.createNode('mesh', n='UCX_%sShape' % sel)

        pm.connectAttr('%s.outMesh' % inputMesh, '%s.input[0].inputPolymesh' % hullNode)
        pm.connectAttr('%s.output' % hullNode, '%s.inMesh' % outputNode)

        hullNode.maxVertices.set(self.maxVerts.getValue())
        outputNode.getParent().setParent(sel)
        outputNode.getParent().translate.set(0, 0, 0)

        if not isinstance(oldSel[0], pm.nt.Transform):
            self.setComponents(oldSel, hullNode)

    def comStr(self, sel):
        comStr = []
        for i in sel:
            comStr.append(str(i.name().split('.')[1]))
        return comStr

    def setComponents(self, sel, hullNode):
        coms = self.comStr(sel)
        hullNode.input[0].inputComponents.set(len(coms), *coms, type='componentList')

    def boxHull(self):
        sel = pm.selected()
        bb = sel[0].getBoundingBox()
        hull = pm.polyCube(w=bb.width(), h=bb.height(), d=bb.depth(), n='UCX_%s' % sel[0])
        cnt = pm.objectCenter(sel[0])
        hull[0].setTranslation(cnt)

        sg = pm.PyNode('initialShadingGroup')
        sg.remove(hull[0].getShape())
        hull[0].setParent(sel[0])

    def saveOptions(self, *args):
        self.opts.phyType = self.phyType.getSelect()
        self.opts.maxVerts = self.maxVerts.getValue()
        self.opts.dump()


class FbxUI(object):
    def __init__(self, opts):
        self.opts = opts
        with pm.frameLayout('Export Meshes (.FBX)', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Export Path:')
                with pm.rowColumnLayout(nc=2, cw=[(1, 215), (2, 32)]):
                    self.fbxPath = pm.textField(text=self.opts.fbxPath)
                    pm.button(l='...', c=self._path)

                with pm.rowColumnLayout(nc=2):
                    self.center = pm.checkBox(label='Move to Orgin', v=self.opts.center, cc=self.saveOptions)
                    self.child = pm.checkBox(label='Export Childern', v=self.opts.child, cc=self.saveOptions)

                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2, 124)]):
                    pm.button(l='Selected', c=self._selected)
                    pm.button(l='All', c=self._all)

    def _path(self, *args):
        path = self.fbxPath.getText()
        path = pm.fileDialog2(dir=path, fm=3, okc='Select Folder', cap='Select Export Folder')
        try:
            self.fbxPath.setText(path[0])
        except TypeError:
            pass
        self.saveOptions()

    def _selected(self, *args):
        self.export(self.fbxPath.getText(), all=False, center=self.center.getValue(), child=self.child.getValue())

    def _all(self, *args):
        self.export(self.fbxPath.getText(), all=True, center=self.center.getValue(), child=self.child.getValue())

    def export(self, path, all=False, center=True, child=True):
        # Load the fbx Preset
        presetPath = '%s/UDKexport/UDK-FBX.fbxexportpreset' % pm.internalVar(usd=True)
        pm.mel.FBXLoadExportPresetFile(f=presetPath)
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

    def saveOptions(self, *args):
        self.opts.center = self.center.getValue()
        self.opts.child = self.child.getValue()
        self.opts.fbxPath = self.fbxPath.getText()
        self.opts.dump()
