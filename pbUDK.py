import pymel.core as pm


class UI(object):
    def __init__(self):
        with pm.window(title='pbUDK2', width=250, sizeable=False, mb=True, mbv=True, mnb=True, mxb=True) as window:
            with pm.columnLayout() as self.wrapper:

                # UI Sections
                self._phyUI()
                self._fbxUI()
                self._refUI()
                self._t3dUI()

                # Render Window
                window.show()

    # Build UI
    def _phyUI(self):
        with pm.frameLayout('Physics', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Collision Type:')
                self.phyType = pm.radioButtonGrp(labelArray2=['Convex Hull(ucx)', 'Box Collison(ucb)'], sl=0, nrb=2)
                pm.button(l='Add Hull', w=250, c=self._addHull)

    def _fbxUI(self):
        with pm.frameLayout('Export Meshes (.FBX)', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Export Path:')
                with pm.rowColumnLayout(nc=2, cw=[(1, 215), (2, 32)]):
                    self.fbxPath = pm.textField()
                    pm.button(l='...', c=self._fbxPath)

                self.center = pm.checkBox(label='Move to Orgin', v=True)

                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2, 124)]):
                    pm.button(l='Selected', c=self._selected)
                    pm.button(l='All', c=self._all)

        # Path Set
        self.fbxPath.setText(pm.workspace(q=True, rd=True) + 'data/')

    def _refUI(self):
        with pm.frameLayout('UDK Reference', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Reference Name:')
                self.refName = pm.textField(w=250)
                with pm.rowColumnLayout(nc=2, cw=[(1, 124), (2, 124)]):
                    pm.button(l='Add/Set Reference', c=self._addRef)
                    pm.button(l='Remove Reference', c=self._removeRef)

    def _t3dUI(self):
        with pm.frameLayout('Export Transformations (.T3D)', collapsable=True, cl=False, bs='out'):
            with pm.columnLayout(width=250):
                pm.text(l='Export Path:')
                with pm.rowColumnLayout(nc=2, cw=[(1, 215), (2, 32)]):
                    self.t3dPath = pm.textField()
                    pm.button(l='...', c=self._t3dPath)
                pm.text(l='Map Name:')
                self.mapName = pm.textField(w=250)
                pm.button(l='Export Level', w=250, c=self._exportLvl)

        # Path Set
        self.t3dPath.setText(pm.workspace(q=True, rd=True) + 'data/UDKexport.t3d')

    # Buttons
    def _addHull(self, *args):
        if self.center == 1:
            phy().addHull()
        if self.center == 2:
            phy().addHull()

    def _selected(self, *args):
        exportFBX(self.fbxPath.getText(), all=False, center=self.center.getValue())

    def _all(self, *args):
        exportFBX(self.fbxPath.getText(), all=True, center=self.center.getValue())

    def _fbxPath(self, *args):
        path = self.fbxPath.getText()
        path = pm.fileDialog2(dir=path, fm=3, okc="Select Folder", cap="Select Export Folder")
        self.fbxPath.setText(path[0])

    def _addRef(self, *args):
        t3dExport().ref = self.refName.getText()

    def _removeRef(self, *args):
        del t3dExport().ref

    def _exportLvl(self, *args):
        t3dExport().export(self.t3dPath, self.mapName)

    def _t3dPath(self, *args):
        path = self.t3dPath.getText()
        filters = "Unreal Text (*.t3d)"
        path = pm.fileDialog2(dir=path, fm=0, ff=filters, cap='Set T3D Location')
        self.t3dPath.setText(path[0])


# Physics
class phy(object):
    def __init__(self):
        pass

    def addHull(self):
        prefix = 'ucx_'
        sel = pm.selected()

        for s in sel:
            name = prefix + s.name()
            print name


# FBX Export
def exportFBX(path, all=False, center=True):
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
                centerPiv(obj)
            exportPath = path + obj.name() + ext
            pm.mel.FBXExport(f=exportPath, s=True)
            if center:
                obj.translateBy([oldLoc[0], oldLoc[1], oldLoc[2]])


def centerPiv(obj):
    pm.select(obj)
    pm.makeIdentity(apply=True, t=True, r=True, s=True, n=False)
    pos = obj.getRotatePivot()
    obj.translate.set(-1 * pos.x, -1 * pos.y, -1 * pos.z)


# T3D Export
class t3dExport(object):
    def __init__(self):
        pass

    @property
    def ref(self):
        sel = pm.selected()
        return sel[0].T3DTag.get()

    @ref.setter  # NOQA
    def ref(self, refName):
        sel = pm.selected()
        if len(sel) != 0:
            for item in sel:
                if item.hasAttr('T3DTag'):
                    item.T3DTag.set(refName)
                else:
                    item.addAttr('T3DTag', dt='string')
                    item.T3DTag.set(refName)
        else:
            pm.warning('Select at least one polygon object!')

    @ref.deleter  # NOQA
    def ref(self):
        sel = pm.selected()
        if len(sel) != 0:
            for item in sel:
                if item.hasAttr('T3DTag'):
                    item.T3DTag.delete()
                else:
                    msg = 'No Tag to delete!'
                    pm.warning(msg)
        else:
            pm.warning('Select at least one polygon object!')

    def export(self, path, mapName):
        pass
