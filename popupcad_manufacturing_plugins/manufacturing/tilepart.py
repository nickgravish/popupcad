# -*- coding: utf-8 -*-
"""
Contributed by Nick Gravish
Email: gravish<at>seas.harvard.edu.
Please see LICENSE for full license.
"""


# import os
# import sys
# import numpy as np
import math
import qt.QtGui as qg

# from popupcad.filetypes.operationoutput import OperationOutput
# import popupcad_manufacturing_plugins

import popupcad
from popupcad.filetypes.sketch import Sketch
from popupcad_manufacturing_plugins.manufacturing.autoweb4 import AutoWeb4
from popupcad.manufacturing.simplesketchoperation import SimpleSketchOp
from popupcad.filetypes.genericshapes import GenericLine
# from popupcad.manufacturing.transform_external import TransformExternal
from popupcad.manufacturing.transform_internal import TransformInternal
from popupcad.manufacturing.laminateoperation2 import LaminateOperation2
# from popupcad.manufacturing.sub_operation2 import SubOperation2
from popupcad.filetypes.operation2 import Operation2
# from popupcad.filetypes.material2 import default_material_types
from popupcad.manufacturing.multivalueoperation3 import MultiValueOperation3
from popupcad.widgets.dragndroptree import DraggableTreeWidget
from popupcad.widgets.listmanager import SketchListManager,SketchListViewer

class Dialog(qg.QDialog):
    # defaults = [20, 1., 0, 0, 0]

    def __init__(self,design,prioroperations):
        super(Dialog, self).__init__()

        self.prioroperations = prioroperations
        self.design = design

        #       operation/part | sketch to tile in | sheet to tile into
        #                  'Number of parts', 'Scale'
        #                       'x-gap', 'y-gap'
        #                       'Support offset'

        self.part = DraggableTreeWidget()
        self.part.linklist(prioroperations)
        self.part.setObjectName("Operation to tile")

        self.sketch_to_tile = SketchListManager(design,name = 'Sketch of tile area')

        self.sheet = DraggableTreeWidget()
        self.sheet.linklist(prioroperations)
        self.sheet.setObjectName("Sheet to tile into")

        #       operation/part | sketch to tile in | sheet to tile into
        layout_ops_sheet_sketch = qg.QHBoxLayout()
        layout_ops_sheet_sketch.addWidget(self.part)
        layout_ops_sheet_sketch.addWidget(self.sketch_to_tile)
        layout_ops_sheet_sketch.addWidget(self.sheet)

        #                  'Number of parts', 'Scale'
        number_of_parts_and_scale = qg.QHBoxLayout()

        number_of_parts_and_scale.addStretch()
        number_of_parts_and_scale.addWidget(qg.QLabel('Number of parts'))
        self.N = qg.QLineEdit()
        number_of_parts_and_scale.addWidget(self.N)

        number_of_parts_and_scale.addWidget(qg.QLabel('Scale'))
        self.scale = qg.QLineEdit()
        number_of_parts_and_scale.addWidget(self.scale)
        number_of_parts_and_scale.addStretch()

        #                       'x-gap', 'y-gap'
        xy_gap = qg.QHBoxLayout()
        xy_gap.addStretch()
        xy_gap.addWidget(qg.QLabel('X-gap'))
        self.x_gap = qg.QLineEdit()
        xy_gap.addWidget(self.x_gap)
        xy_gap.addWidget(qg.QLabel('Y-gap'))
        self.y_gap = qg.QLineEdit()
        xy_gap.addWidget(self.y_gap)
        xy_gap.addStretch()

        s_offset = qg.QHBoxLayout()
        s_offset.addStretch()
        s_offset.addWidget(qg.QLabel('Support offset'))
        self.support_offset = qg.QLineEdit()
        s_offset.addWidget(self.support_offset)
        s_offset.addWidget(self.support_offset)
        s_offset.addStretch()

        # Button 1 and 2
        buttons = qg.QHBoxLayout()
        button1 = qg.QPushButton('Ok')
        button1.clicked.connect(self.accept)
        buttons.addWidget(button1)

        button2 = qg.QPushButton('Cancel')
        button2.clicked.connect(self.reject)
        buttons.addWidget(button2)


        layout = qg.QVBoxLayout()
        layout.addLayout(layout_ops_sheet_sketch)
        layout.addLayout(number_of_parts_and_scale)
        layout.addLayout(xy_gap)
        layout.addLayout(s_offset)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def build_sketch_links(self):
        try:
            sketch_links = {}
            sketch_links['sketch_from']=[self.sketch_to_tile.itemlist.selectedItems()[0].value.id]
            return sketch_links
        except IndexError:
            return None

    def acceptdata(self):

        # get operation reference for part
        ii, jj = self.part.currentIndeces2()[0]
        opid = self.design.operations[ii].id
        part_opref = opid

        # get operation reference for sheet
        ii, jj = self.sheet.currentIndeces2()[0]
        opid = self.design.operations[ii].id
        sheet_opref = opid

        # get bounding box from the sketch
        sketch_id = self.sketch_to_tile.itemlist.selectedItems()[0].value.id
        sketch_bounding_box = self.design.sketches[sketch_id].output_csg()[0].bounds # may break if multiple sketches

        N = self.N.text()
        scale = float(self.scale.text())
        x_gap = float(self.x_gap.text())
        y_gap = float(self.y_gap.text())
        support_offset = float(self.support_offset.text())

        return part_opref, sheet_opref, sketch_bounding_box, N, scale, x_gap, y_gap, support_offset


class TilePart(Operation2):
    name = 'TiledPart'
    show = []

    def __init__(self, *args):
        super(TilePart, self).__init__()
        self.editdata(*args)
        self.id = id(self)

    def editdata(self,part_opref, sheet_opref, sketch_bounding_box, N, scale, x_gap, y_gap, support_offset):
        super(TilePart, self).editdata({},{},{})
        self.sheet_opref = sheet_opref
        self.part_opref = part_opref
        self.parts_bounding_box = sketch_bounding_box
        self.sc = scale
        self.N = N
        self.x_gap = x_gap
        self.y_gap = y_gap
        self.support_offset = support_offset

    # finally initialize sketch op in design
    def operate(self, design):

        part_to_insert = design.operations[design.operation_index(self.part_opref)]
        sheet_to_insert_into = design.operations[design.operation_index(self.sheet_opref)]

        print(part_to_insert.customname)
        print(sheet_to_insert_into.customname)
        print(len(design.operations))

        # insert_part_operation_number = self.design.operation_index(self.part_opref)
        # sheet = self.design.op_from_ref(self.sheet_opref)

        # insert_part_operation_number  = [cnt for cnt, op in enumerate(hinge.operations) if op.customname.find("FinalPart") != -1][0]
        # release_cut_operation_number  = [cnt for cnt, op in enumerate(hinge.operations) if op.customname.find("Release") != -1][0]

        # insert_part_operation_number = len(hinge.operations)-3
        # release_cut_operation_number = len(hinge.operations)-2

        # build the op_links, then auto make the operation
        op = part_to_insert
        op_ref = op.id
        op_links = {'parent': [(op_ref, op.getoutputref())]}

        new_web = AutoWeb4(op_links,[self.support_offset,0],MultiValueOperation3.keepout_types.laser_keepout)
        new_web.setcustomname(op.name)

        design.addoperation(new_web)
        new_web.generate(design)

        ######################## generate the same size construction line somewhere in the sheet file

        # get geom for line
        bounding_box = new_web.output[1].generic_laminate().getBoundingBox()

        # make the sketch
        construction_geom_hinge = Sketch.new()
        tmp_geom = [(bounding_box[0],bounding_box[1]), (bounding_box[0],bounding_box[3])]
        construction_line = GenericLine.gen_from_point_lists(tmp_geom,[],construction=False)
        construction_geom_hinge.addoperationgeometries([construction_line])

        # add sketch to sketch list
        design.sketches[construction_geom_hinge.id] = construction_geom_hinge

        # make the sketchop
        construction_geom_sketchop_hinge = SimpleSketchOp({'sketch': [construction_geom_hinge.id]},
                                            [layer.id for layer in design.return_layer_definition().layers])
        construction_geom_sketchop_hinge.name = "ConstructionLine"

        # finally initialize sketch op in design
        design.addoperation(construction_geom_sketchop_hinge)
        construction_geom_sketchop_hinge.generate(design)

        ######################## generate the external transform geometry in the sheet

        # center the bottom left to origin
        position_hinge = (-tmp_geom[0][0],-tmp_geom[0][1])
        tmp_geom = [(x + position_hinge[0], y + position_hinge[1]) for (x,y) in tmp_geom]

        # lets make 4x4
        width = (bounding_box[2] - bounding_box[0])*self.sc + self.x_gap
        height = (bounding_box[3] - bounding_box[1])*self.sc + self.y_gap


        # check if will all fit in one window, if not fill first and check if remainder will fit in second window
        max_num_cols = divmod(self.parts_bounding_box[0], width)[0]
        max_num_rows = divmod(self.parts_bounding_box[1], height)[0]

        arrayed_reference_lines = []

        # check if can fit in one
        # if N <= max_num_rows*max_num_cols:
        rows = math.ceil(self.N / max_num_cols)
        cols = math.ceil(self.N / rows)          # spread across the two windows
        n_count = 0

        new_center = (-self.parts_bounding_box[0]/2, 2)
        tmp_geom = [(x + new_center[0], y + new_center[1]) for (x,y) in tmp_geom]

        for row in range(rows):
            for col in range(cols):
                if n_count >= self.N or n_count >= max_num_rows*max_num_cols*2:
                    break

                if row < max_num_rows:
                    arrayed_reference_lines.append([(tmp_geom[0][0]+col*width, tmp_geom[0][1]*self.sc+
                                                     (max_num_rows-row - 1)*height),
                                                    (tmp_geom[1][0]+col*width, tmp_geom[1][1]*self.sc+
                                                     (max_num_rows-row - 1)*height)])

                else:
                    arrayed_reference_lines.append([(tmp_geom[0][0]+col*width,
                                                     tmp_geom[0][1]*self.sc+(max_num_rows-row - 1)*height -
                                                     2*new_center[1]),
                                                    (tmp_geom[1][0]+col*width,
                                                     tmp_geom[1][1]*self.sc+(max_num_rows-row - 1)*height -
                                                     2*new_center[1])])

        n_count = n_count + 1

        construction_geom_sheet = Sketch.new()
        construction_line = [GenericLine.gen_from_point_lists(line,[],construction=False) for
                     line in arrayed_reference_lines]
        construction_geom_sheet.addoperationgeometries(construction_line)

        # add sketch to sketch list
        design.sketches[construction_geom_sheet.id] = construction_geom_sheet

        # make the sketchop
        construction_geom_sketchop_sheet = SimpleSketchOp({'sketch': [construction_geom_sheet.id]},
                                            [layer.id for layer in design.return_layer_definition().layers])
        construction_geom_sketchop_sheet.name = "ConstructionLine"

        # finally initialize sketch op in design
        design.addoperation(construction_geom_sketchop_sheet)
        construction_geom_sketchop_sheet.generate(design)

        ######################## External transform the hinge onto the sheet construction line

        # # insert hinge into sheet as subdesign
        # sheet.subdesigns[hinge.id] = hinge

        # # make design links
        operation_links = {}
        operation_links['from'] = [(part_to_insert.id,0)]

        sketch_links = {}
        sketch_links['sketch_to'] = [construction_geom_sheet.id]
        sketch_links['sketch_from'] = [construction_geom_hinge.id]

        insert_part = TransformInternal(sketch_links, operation_links, 'scale', 'scale', 0, False, 1., 1.)
        insert_part.customname = 'Inserted part'

        design.addoperation(insert_part)
        insert_part.generate(design)
        insert_part_id = design.operations[-1].id # save for later

        ######################## External transform the web.sheet to the construction line

        # # make design links
        operation_links = {}
        operation_links['from'] = [(new_web.id,1)]

        sketch_links = {}
        sketch_links['sketch_to'] = [construction_geom_sheet.id]
        sketch_links['sketch_from'] = [construction_geom_hinge.id]

        insert_webs = TransformInternal(sketch_links, operation_links, 'scale', 'scale', 0, False, 1., 1.)
        insert_webs.customname = 'Inserted part webs'

        design.addoperation(insert_webs)
        insert_webs.generate(design)

        ######################## Remove web.sheet from sheet, union external transform + generateed sheet with hole + web
        # first the difference
        # link 1 is the sheet
        sheet_with_hole = LaminateOperation2({'unary': [(sheet_to_insert_into.id,0)], 'binary': [(insert_webs.id,0)]},'difference')
        sheet_with_hole.customname = 'Sheet with hole'
        design.addoperation(sheet_with_hole)
        sheet_with_hole.generate(design)

        sheet_with_part = LaminateOperation2({'unary': [(sheet_with_hole.id,0), (insert_part_id,0)],
                                      'binary':[]},'union')

        sheet_with_part.customname = 'First pass cuts'
        design.addoperation(sheet_with_part)
        sheet_with_part.generate(design)

        # ######################## Make release cut laminate operation
        #
        # # # make design links
        # # design_links = {}
        # # design_links['subdesign'] = [hinge.id]
        # operation_links = {}
        # operation_links['from'] = [(design.operations[release_cut_operation_number].id,0)]
        #
        # sketch_links = {}
        # sketch_links['sketch_to'] = [construction_geom_sheet.id]
        # sketch_links['sketch_from'] = [construction_geom_hinge.id]
        #
        # insert_release = TransformInternal(sketch_links, operation_links, 'scale', 'scale', 0, False, 1., 1.)
        #
        # insert_release.customname = 'Release'
        # design.addoperation(insert_release)
        # insert_release.generate(design)

    @classmethod
    def buildnewdialog(cls, design, currentop):
        dialog = Dialog(design, design.operations)
        return dialog

    def buildeditdialog(self, design):
        dialog = Dialog(design,design.prioroperations(self),self)
        return dialog