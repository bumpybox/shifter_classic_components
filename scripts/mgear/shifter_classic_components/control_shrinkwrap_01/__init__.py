"""Component Control Shrinkwrap 01 module"""

import pymel.core as pc

from mgear.shifter import component

from mgear.core import attribute, transform, primitive


#############################################
# COMPONENT
#############################################


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        if self.settings["neutralRotation"]:
            t = transform.getTransformFromPos(self.guide.pos["root"])
        else:
            t = self.guide.tra["root"]
            if self.settings["mirrorBehaviour"] and self.negate:
                scl = [1, 1, -1]
            else:
                scl = [1, 1, 1]
            t = transform.setMatrixScale(t, scl)

        self.ik_cns = primitive.addTransform(
            self.root, self.getName("ik_cns"), t)

        self.ctl = self.addCtl(self.ik_cns,
                               "ctl",
                               t,
                               self.color_ik,
                               self.settings["icon"],
                               w=self.settings["ctlSize"] * self.size,
                               h=self.settings["ctlSize"] * self.size,
                               d=self.settings["ctlSize"] * self.size,
                               tp=self.parentCtlTag)

        # we need to set the rotation order before lock any rotation axis
        if self.settings["k_ro"]:
            rotOderList = ["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"]
            attribute.setRotOrder(
                self.ctl, rotOderList[self.settings["default_rotorder"]])

        params = [s for s in
                  ["tx", "ty", "tz", "ro", "rx", "ry", "rz", "sx", "sy", "sz"]
                  if self.settings["k_" + s]]
        attribute.setKeyableAttributes(self.ctl, params)

        # Add plane for shrinkwrap.
        self.plane = pc.polyPlane(
            subdivisionsHeight=2,
            subdivisionsWidth=2,
            constructionHistory=False
        )[0]

        if self.settings["joint"]:
            self.jnt_pos.append([self.ctl, 0, None, self.settings["uniScale"]])

    def addAttributes(self):
        # Ref
        if self.settings["ikrefarray"]:
            ref_names = self.get_valid_alias_list(
                self.settings["ikrefarray"].split(","))
            if len(ref_names) > 1:
                self.ikref_att = self.addAnimEnumParam(
                    "ikref",
                    "Ik Ref",
                    0,
                    ref_names)

    def addOperators(self):
        self.plane.setMatrix(self.ctl.getMatrix(worldSpace=True))
        pc.rotate(self.plane, [90, 0, 0])
        pc.scale(
            self.plane,
            [
                self.settings["planeSize"] * self.size,
                self.settings["planeSize"] * self.size,
                self.settings["planeSize"] * self.size
            ]
        )
        pc.rename(self.plane, self.ctl.name().replace("_ctl", "_plane"))
        pc.parent(self.plane, self.root)
        pc.select("{}.vtx[4]".format(self.plane.name()), self.ik_cns)
        pc.runtime.PointOnPolyConstraint()
        self.plane.visibility.set(False)

        shrinkwrap_node = pc.deformer(self.plane, type="shrinkWrap")[0]
        mesh = pc.PyNode(self.settings["mesh"])
        mesh.worldMesh[0] >> shrinkwrap_node.targetGeom
        shrinkwrap_node.projection.set(3)
        shrinkwrap_node.bidirectional.set(True)
        shrinkwrap_node.envelope.set(0)

        # Connect attribute
        self.ctl.addAttr(
            "envelope",
            usedAsProxy=True,
            keyable=True,
            min=0,
            max=1
        )
        shrinkwrap_node.envelope.connect(self.ctl.envelope, force=True)

    # =====================================================
    # CONNECTOR
    # =====================================================
    def setRelation(self):
        """Set the relation beetween object from guide to rig"""
        self.relatives["root"] = self.ctl
        self.controlRelatives["root"] = self.ctl
        if self.settings["joint"]:
            self.jointRelatives["root"] = 0

        self.aliasRelatives["root"] = "ctl"

    def addConnection(self):
        """Add more connection definition to the set"""
        self.connections["standard"] = self.connect_standard
        self.connections["orientation"] = self.connect_orientation

    def connect_standard(self):
        """standard connection definition for the component"""
        self.connect_standardWithSimpleIkRef()

    def connect_orientation(self):
        """Orient connection definition for the component"""
        self.connect_orientCns()
