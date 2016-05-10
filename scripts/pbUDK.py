from pymel.util.common import path
import os
import json
import pymel.core as pm

# Patch for the broken getTransform in older pymel versions
pm.nt.Shape.getTransform = lambda x: x.getParent(generations=1)

title = 'Unreal Pipeline'
version = '1.07'


def UI():
    if pm.window('pbudk', exists=True):
        pm.deleteUI('pbudk')

    optspath = '%s/pbUDK.json' % pm.internalVar(usd=True)
    defaultdata = {'phyType': 1,
                   'maxVerts': 32,
                   'center': True,
                   'child': True,
                   'fbxPath': '%sdata/' % pm.workspace(q=True, rd=True),
                   'presetFile': '%s/UDKexport/UDK-FBX.fbxexportpreset' % pm.internalVar(usd=True),
                   'version': version,
                   'prefix': False,
                   'prefix_text': '',
                   'suffix': False,
                   'suffix_text': ''}

    with pm.window('pbudk', title="{0} - {1}".format(title, version), width=250, sizeable=True) as window:
        with pm.columnLayout():
            opts = JSONDict(optspath, defaultdata)
            PhyUI(opts)
            FbxUI(opts)
        window.show()


class PhyUI(object):
    def __init__(self, opts):
        self.opts = opts
        with pm.frameLayout('Physics', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Collision Type:')
                self.phyType = pm.radioButtonGrp(labelArray3=['Convex Hull', 'Box', 'Sphere'],
                                                 sl=self.opts['phyType'], nrb=3, cc=self.save,
                                                 cw3=[94, 64, 64], width=250)
                self.maxVerts = pm.intSliderGrp(field=True, l='Max Vertices:', v=self.opts['maxVerts'],
                                                cl3=['left', 'left', 'left'], cw3=[64, 48, 128], cc=self.save)
                pm.button(l='Add Hull', w=250, c=self._addHull)
        self.save()

    def _addHull(self, *args):
        if not pm.selected():
            return
        i = self.phyType.getSelect()
        if i == 1:
            self.convexHull()
        elif i == 2:
            self.boxHull()
        elif i == 3:
            self.sphereHull()

    def convexHull(self):
        sel = pm.selected()
        if not isinstance(sel[0], pm.nt.Transform):
            oldSel = sel
            sel = sel[0].node().getParent()
        else:
            oldSel = sel
            sel = sel[0]

        inputMesh = sel.getShape()
        hullNode = pm.createNode('DDConvexHull')
        outputNode = pm.createNode('mesh', n='UCX_{0}Shape_01'.format(sel))

        pm.connectAttr('%s.outMesh' % inputMesh, '%s.input[0].inputPolymesh' % hullNode)
        pm.connectAttr('%s.output' % hullNode, '%s.inMesh' % outputNode)

        hullNode.maxVertices.set(self.maxVerts.getValue())
        outputNode.getParent().setParent(sel)
        outputNode.getParent().translate.set(0, 0, 0)
        if not isinstance(oldSel[0], pm.nt.Transform):
            self.setComponents(oldSel, hullNode)

    def setComponents(self, sel, hullNode):
        coms = [str(i.name().split('.')[1]) for i in sel]
        hullNode.input[0].inputComponents.set(len(coms), *coms, type='componentList')

    @staticmethod
    def _get_bounds(sel):
        if sel > 1 and isinstance(sel[0], pm.Component):
            transform = sel[0].node().getTransform()
            t = pm.polyEvaluate(bc=True)
            bb = pm.dt.BoundingBox(pm.dt.Point(t[0][0], t[1][0], t[2][0]), pm.dt.Point(t[0][1], t[1][1], t[2][1]))
            verts = [i.getPosition() for i in pm.ls(pm.polyListComponentConversion(sel, tv=True), fl=True)]
            center = sum(verts) / len(verts)
        else:
            transform = sel[0]
            bb = sel[0].getBoundingBox()
            center = pm.objectCenter(sel[0])
        return bb, center, transform

    def boxHull(self):
        sel = pm.ls(sl=True, fl=True)
        bb, cnt, transform = self._get_bounds(sel)
        hull = pm.polyCube(w=bb.width(), h=bb.height(), d=bb.depth(), n='UCX_{0}_01'.format(transform))
        hull[0].setTranslation(cnt)
        sg = pm.PyNode('initialShadingGroup')
        sg.remove(hull[0].getShape())
        hull[0].setParent(transform)

    def sphereHull(self):
        sel = pm.ls(sl=True, fl=True)
        bb, cnt, transform = self._get_bounds(sel)
        hull = pm.polySphere(radius=max(bb.width(), bb.height(), bb.depth()) / 2, sx=8, sy=8,
                             n='UCX_{0}_01'.format(transform))
        hull[0].setTranslation(cnt)
        sg = pm.PyNode('initialShadingGroup')
        sg.remove(hull[0].getShape())
        hull[0].setParent(transform)

    def save(self, *args):
        self.opts['phyType'] = self.phyType.getSelect()
        self.opts['maxVerts'] = self.maxVerts.getValue()
        if self.phyType.getSelect() == 1:
            self.maxVerts.setEnable(True)
        else:
            self.maxVerts.setEnable(False)


class FbxUI(object):
    def __init__(self, opts):
        self.opts = opts
        with pm.frameLayout('Export Meshes (.FBX)', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Export List:')
                pm.separator(height=4)
                self.meshList = pm.textScrollList(height=250, width=250, ams=True, dkc=self._remove)
                with pm.rowColumnLayout(nc=3, cw=[(1, 82), (2, 82), (3, 82)]):
                    pm.button(l='Add', c=self._add)
                    pm.button(l='Remove', c=self._remove)
                    pm.button(l='Clear', c=self._clear)

                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2,124)]):
                    self.prefix = pm.checkBox(label='Prefix', value=self.opts['prefix'], cc=self.save)
                    self.suffix = pm.checkBox(label='Suffix', value=self.opts['suffix'], cc=self.save)
                    self.prefix_text = pm.textField(en=self.prefix.getValue(), text=self.opts['prefix_text'], cc=self.save)
                    self.suffix_text = pm.textField(en=self.suffix.getValue(), text=self.opts['suffix_text'], cc=self.save)

                pm.text(l='Export Path:')
                with pm.rowColumnLayout(nc=2, cw=[(1, 215), (2, 32)]):
                    self.fbxPath = pm.textField(text=self.opts['fbxPath'], cc=self._pathRefreash)
                    pm.button(l='...', c=self._path)

                with pm.rowColumnLayout(nc=3):
                    self.center = pm.checkBox(label='Move to Orgin', v=self.opts['center'], cc=self.save)
                    self.child = pm.checkBox(label='Export Childern', v=self.opts['child'], cc=self.save)
                    pm.button(l='FBXPreset', c=self._fbxPreset)

                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2, 124)]):
                    pm.button(l='Selected', c=self._selected)
                    pm.button(l='All', c=self._all)

        self._refresh()

    def _path(self, *args):
        exportPath = pm.fileDialog2(dir=path, fm=3, okc='Select Folder', cap='Select Export Folder')
        if exportPath:
            self.fbxPath.setText(exportPath[0])
            self.opts['fbxPath'] = exportPath[0]

    def _pathRefreash(self, text):
        self.opts['fbxPath'] = text

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
            if isinstance(i, pm.nt.Transform):
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

    def _clear(self, *args):
        sel = pm.ls()
        for i in sel:
            if hasattr(i, 'pbExport'):
                i.pbExport.delete()
        self._refresh()

    def _refresh(self):
        self.meshList.removeAll()
        sel = pm.ls(type=pm.nt.Transform)
        for i in sel:
            if hasattr(i, 'pbExport') and i.pbExport.get() is True:
                self.meshList.append(i)

    def export(self, dirpath, all=False, center=True, child=True):
        if os.path.isfile(self.opts['presetFile']):
            pm.mel.FBXLoadExportPresetFile(f=self.opts['presetFile'])
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
                exportPath = self._get_filename(dirpath, obj.name(), ext)
                if child:
                    children = obj.getChildren()
                    for i in children:
                        if isinstance(i, pm.nt.Transform):
                            pm.select(i, add=True)
                pm.mel.FBXExport(f=exportPath, s=True)
                if center:
                    obj.setTranslation([oldLoc[0], oldLoc[1], oldLoc[2]])

    def _get_filename(self, dir, name, ext):
        file_name = "{0}{1}{2}{3}".format(
            self.prefix_text.getText() if self.prefix.getValue() else "",
            name,
            self.suffix_text.getText() if self.suffix.getValue() else "",
            ext
        )
        return dir + os.sep + file_name;

    def centerPiv(self, obj):
        pm.select(obj)
        pm.makeIdentity(apply=True, t=True, r=True, s=True, n=False)
        pos = obj.getRotatePivot()
        obj.translate.set(-1 * pos.x, -1 * pos.y, -1 * pos.z)
        pm.makeIdentity(apply=True, t=True, r=True, s=True, n=False)

    def save(self, *args):
        self.prefix_text.setEnable(self.prefix.getValue())
        self.suffix_text.setEnable(self.suffix.getValue())

        self.opts['center'] = self.center.getValue()
        self.opts['child'] = self.child.getValue()
        self.opts['fbxPath'] = self.fbxPath.getText()
        self.opts['prefix'] = self.prefix.getValue()
        self.opts['prefix_text'] = self.prefix_text.getText()
        self.opts['suffix'] = self.suffix.getValue()
        self.opts['suffix_text'] = self.suffix_text.getText()


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
                if 'version' in data and data['version'] == version:
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

if __name__ == "__main__":
    UI()
