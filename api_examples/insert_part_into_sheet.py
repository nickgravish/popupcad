# -*- coding: utf-8 -*-
"""
Written by Nick Gravish
Harvard Microrobotics lab

Sample code to insert a part into an auto generated manufacturing sheet for laser machining

Please see LICENSE for full license.
"""

import popupcad
import os
import sys
# import api_examples

import qt.QtGui as qg

from popupcad.filetypes.operationoutput import OperationOutput
import popupcad_manufacturing_plugins

from popupcad.filetypes.sketch import Sketch
from popupcad_manufacturing_plugins.manufacturing.autoweb4 import AutoWeb4
from popupcad.manufacturing.simplesketchoperation import SimpleSketchOp
from popupcad.filetypes.genericshapes import GenericLine
from popupcad.manufacturing.transform_external import TransformExternal
from popupcad.manufacturing.laminateoperation2 import LaminateOperation2

# file to load and work with
myfolder  = '/Users/nickgravish/popupCAD_files/designs/'
myfile2    = 'robobee_interference_hinge_BAK.cad' #'test_geom.cad'
myfile    =  '9layer_25x25.cad' #'25mm_x_25mm_layup.cad'





def web_for_construction(op, outer_buffer = 1, support_gap = 0.25):
    """

    Parameters
    ----------
    op -> design file to create web from

    defaults for the web generation

    Returns
    -------
    sheet_out, outer_web, inner_elements, buffered_keepout
    laminates from the web generation function
    """


# generate a construction line associated with the left line of the web of the part
def add_construction(part, operation_ref = False):
    """
    This code takes in a design file and adds a construction line to the left vertical side of the bounding
    box of the laminate in the operation_ref operation. By default the operation_ref will grab the last operation
    assuming that this is final laminate operation that created the part
    Parameters
    ----------
    part -> a design file with
    operation_ref -> Reference to the operation that the construction geometry will be referencing

    Returns
    -------
    construction_line -> the geometry of the construction line for use with the transform op

    """

    # default to the last operation
    if not operation_ref:
        op = part.operations[-1]
    else:
        op = part.operations[operation_ref]



    construction_line = []
    return construction_line




# remove the web.sheet from the sheet and make hole

# Union the transform, the web, and the hole


if __name__=='__main__':

    app = qg.QApplication(sys.argv)

    sheet = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, myfile))
    sheet.reprocessoperations(debugprint=True)

    # assume sheet is the last laminate, save for later
    original_sheet_id = sheet.operations[-1].id

    hinge = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, myfile2))
    hinge.reprocessoperations(debugprint=True)

    # get hinge op id
    insert_part_operation_number = len(hinge.operations)-1
    release_cut_operation_number = len(hinge.operations)-2

    support_offset = 0.1

    ######################## make a web with default sizes

    # build the op_links, then auto make the operation
    op = hinge.operations[insert_part_operation_number]
    op_ref = op.id
    op_links = {'parent': [(op_ref, op.getoutputref())]}

    new_web = AutoWeb4(op_links,[support_offset,0],popupcad.manufacturing.multivalueoperation3.MultiValueOperation3.keepout_types.laser_keepout)
    new_web.setcustomname(op.name)

    hinge.addoperation(new_web)
    new_web.generate(hinge)

    ######################## generate the same size construction line somewhere in the sheet file

    # get geom for line
    bounding_box = new_web.output[1].generic_laminate().getBoundingBox()

    # make the sketch
    construction_geom_hinge = Sketch.new()
    tmp_geom = [(bounding_box[0],bounding_box[1]), (bounding_box[0],bounding_box[3])]
    construction_line = GenericLine.gen_from_point_lists(tmp_geom,[],construction=False)
    construction_geom_hinge.addoperationgeometries([construction_line])

    # add sketch to sketch list
    hinge.sketches[construction_geom_hinge.id] = construction_geom_hinge

    # make the sketchop
    construction_geom_sketchop_hinge = SimpleSketchOp({'sketch': [construction_geom_hinge.id]},
                                                [layer.id for layer in hinge.return_layer_definition().layers])
    construction_geom_sketchop_hinge.name = "ConstructionLine"

    # finally initialize sketch op in design
    hinge.addoperation(construction_geom_sketchop_hinge)
    construction_geom_sketchop_hinge.generate(hinge)

    ######################## generate the external transform geometry in the sheet

    # center the bottom left to origin
    position_hinge = (-tmp_geom[0][0],-tmp_geom[0][1])
    tmp_geom = [(x + position_hinge[0], y + position_hinge[1]) for (x,y) in tmp_geom]

    construction_geom_sheet = Sketch.new()
    construction_line = GenericLine.gen_from_point_lists(tmp_geom,[],construction=False)
    construction_geom_sheet.addoperationgeometries([construction_line])

    # add sketch to sketch list
    sheet.sketches[construction_geom_sheet.id] = construction_geom_sheet

    # make the sketchop
    construction_geom_sketchop_sheet = SimpleSketchOp({'sketch': [construction_geom_sheet.id]},
                                                [layer.id for layer in sheet.return_layer_definition().layers])
    construction_geom_sketchop_sheet.name = "ConstructionLine"

    # finally initialize sketch op in design
    sheet.addoperation(construction_geom_sketchop_sheet)
    construction_geom_sketchop_sheet.generate(sheet)

    ######################## External transform the hinge onto the sheet construction line

    # insert hinge into sheet as subdesign
    sheet.subdesigns[hinge.id] = hinge

    # # make design links
    design_links = {}
    design_links['subdesign'] = [hinge.id]

    sketch_links = {}
    sketch_links['sketch_to'] = [construction_geom_sheet.id]

    sub_sketch_id = construction_geom_hinge.id

    subopref = (hinge.operations[-3].id,0)

    insert_part = TransformExternal(sketch_links, design_links, subopref, sub_sketch_id, 'scale', 'scale', 0, False, 1., 1.)
    insert_part.customname = 'Inserted part'

    sheet.addoperation(insert_part)
    insert_part.generate(sheet)
    insert_part_id = sheet.operations[-1].id # save for later

    ######################## Make web of subdesign in sheet

    # build the op_links, then auto make the operation
    op = sheet.operations[-1]
    op_ref = op.id # last operation is the one we want
    op_links = {'parent': [(op_ref, op.getoutputref())]}

    # note second value has to be 0
    new_web = AutoWeb4(op_links,[support_offset,0],popupcad.manufacturing.multivalueoperation3.MultiValueOperation3.keepout_types.laser_keepout)
    new_web.setcustomname(op.name)

    sheet.addoperation(new_web)
    new_web.generate(sheet)
    web_id = sheet.operations[-1].id

    ######################## Remove web.sheet from sheet, union external transform + generateed sheet with hole + web
    # first the difference
    # link 1 is the sheet
    sheet_with_hole = LaminateOperation2({'unary': [(original_sheet_id,0)], 'binary': [(web_id,1)]},'difference')
    sheet_with_hole.customname = 'Sheet with hole'
    sheet.addoperation(sheet_with_hole)
    sheet_with_hole.generate(sheet)

    sheet_with_part = LaminateOperation2({'unary': [(sheet_with_hole.id,0), (web_id,0), (insert_part_id,0)],
                                          'binary':[]},'union')

    sheet_with_part.customname = 'First pass cuts'
    sheet.addoperation(sheet_with_part)
    sheet_with_part.generate(sheet)

    ######################## Make release cut laminate operation
    # release cut is second to last layer

    # # make design links
    design_links = {}
    design_links['subdesign'] = [hinge.id]

    sketch_links = {}
    sketch_links['sketch_to'] = [construction_geom_sheet.id]

    sub_sketch_id = construction_geom_hinge.id

    subopref = (hinge.operations[release_cut_operation_number].id,0)

    insert_release = TransformExternal(sketch_links, design_links, subopref, sub_sketch_id, 'scale', 'scale', 0, False, 1., 1.)
    insert_release.customname = 'Release'
    sheet.addoperation(insert_release)
    insert_release.generate(sheet)


    ################## show the new design

    editor = popupcad.guis.editor.Editor()
    editor.load_design(sheet)
    editor.show()
    sys.exit(app.exec_())
