from pymel.util.common import path
import os
import json
import pymel.core as pm


title = 'Unreal Pipeline'
version = '1.02'


class UI(object):
    def __init__(self):
        if pm.window('pbudk', exists=True):
            pm.deleteUI('pbudk')

        optspath = '%s/pbUDK.json' % pm.internalVar(usd=True)
        defaultdata = {'phyType': 1,
                       'maxVerts': 32,
                       'center': True,
                       'child': True,
                       'fbxPath': '%sdata/' % pm.workspace(q=True, rd=True),
                       'presetFile': '%s/UDKexport/UDK-FBX.fbxexportpreset' % pm.internalVar(usd=True),
                       'version': version}

        with pm.window('pbudk', title="{0} - {1}".format(title, version), width=250, sizeable=False) as window:
            with pm.columnLayout() as self.wrapper:
                opts = JSONDict(optspath, defaultdata)
                PhyUI(opts)
                FbxUI(opts)

                window.show()


class JSONDict(dict):
    def __init__(self, filename, defaults, *args, **kwargs):
        super(JSONDict, self).__init__(**kwargs)
        self.filename = filename
        self.defaults = defaults
        self._load()
        self.update(*args, **kwargs)

    def _load(self):
        if os.path.isfile(self.filename) and os.path.getsize(self.filename) > 0:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                if 'version' in data and data['version'] == '1.02':
                    self.update(data)
                else:
                    self._dumpdefaults()
        else:
            self._dumpdefaults()

    def _dump(self):
        with open(self.filename, 'w') as f:
            json.dump(self, f, sort_keys=True, indent=4)

    def _dumpdefaults(self):
        with open(self.filename, 'w') as f:
            json.dump(self.defaults, f, sort_keys=True, indent=4)
        self._load()

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._dump()

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
        self._dump()


class PhyUI(object):
    def __init__(self, opts):
        self.opts = opts
        with pm.frameLayout('Physics', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Collision Type:')
                self.phyType = pm.radioButtonGrp(labelArray2=['Convex Hull', 'Box Collison'],
                                                 sl=self.opts['phyType'], nrb=2, cc=self.save)
                self.maxVerts = pm.intSliderGrp(field=True, l='Max Vertices:', v=self.opts['maxVerts'],
                                                cl3=['left', 'left', 'left'], cw3=[64, 48, 128], cc=self.save)
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

    def save(self, *args):
        self.opts['phyType'] = self.phyType.getSelect()
        self.opts['maxVerts'] = self.maxVerts.getValue()


class FbxUI(object):
    def __init__(self, opts):
        self.opts = opts
        with pm.frameLayout('Export Meshes (.FBX)', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Export List:')
                pm.separator(height=4)
                self.meshList = pm.textScrollList(height=120, width=250, ams=True, dkc=self._remove)
                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2, 124)]):
                    pm.button(l='Add', c=self._add)
                    pm.button(l='Remove', c=self._remove)

                pm.text(l='Export Path:')
                with pm.rowColumnLayout(nc=2, cw=[(1, 215), (2, 32)]):
                    self.fbxPath = pm.textField(text=self.opts['fbxPath'])
                    pm.button(l='...', c=self._path)

                with pm.rowColumnLayout(nc=3):
                    self.center = pm.checkBox(label='Move to Orgin', v=self.opts['center'])
                    self.child = pm.checkBox(label='Export Childern', v=self.opts['child'])
                    pm.button(l='FBXPreset', c=self._fbxPreset)

                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2, 124)]):
                    pm.button(l='Selected', c=self._selected)
                    pm.button(l='All', c=self._all)

        self._refresh()

    def _path(self, *args):
        exportPath = path(pm.fileDialog2(dir=path, fm=3, okc='Select Folder', cap='Select Export Folder')[0])
        try:
            self.fbxPath.setText(exportPath)
        except TypeError:
            pass

    def _selected(self, *args):
        self.export(self.fbxPath.getText(), all=False, center=self.center.getValue(), child=self.child.getValue())

    def _all(self, *args):
        self.export(self.fbxPath.getText(), all=True, center=self.center.getValue(), child=self.child.getValue())

    def _fbxPreset(self, *args):
        tempData = pm.fileDialog2(dir=path(self.opts['presetFile']).parent, fm=1, okc='Select Preset File',
                                  cap='Sselect FPXExportPreset File', ff='FBX Export Presets (*.fbxexportpreset)')
        if tempData:
            self.opts['presetFile'] = tempData[0]

    def _add(self, *args):
        sel = pm.selected()
        for i in sel:
            try:
                i.pbExport.set(True)
            except:
                i.addAttr('pbExport', at='bool')
                i.pbExport.set(True)
        self._refresh()

    def _remove(self, *args):
        sel = self.meshList.getSelectItem()
        for i in sel:
            i = pm.PyNode(i)
            i.pbExport.delete()
        self._refresh()

    def _refresh(self):
        self.meshList.removeAll()
        sel = pm.ls(type=pm.nt.Mesh)
        for i in sel:
            if hasattr(i.getParent(), 'pbExport') and i.getParent().pbExport.get() is True:
                self.meshList.append(i.getParent())

    def export(self, path, all=False, center=True, child=True):
        # Load the fbx Preset
        pm.mel.FBXLoadExportPresetFile(f=self.opts.data['presetFile'])
        ext = '.fbx'

        if all:
            pm.select(self.meshList.getAllItems())
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
                exportPath = path + os.sep + obj.name() + ext
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

    def save(self, *args):
        self.opts['center'] = self.center.getValue()
        self.opts['child'] = self.child.getValue()
        self.opts['fbxPath'] = self.fbxPath.getText()
