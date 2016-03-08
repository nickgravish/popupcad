# -*- coding: utf-8 -*-
"""
Written by Nick Gravish
Harvard Microrobotics lab

Sample code to insert a part into an auto generated manufacturing sheet for laser machining

Please see LICENSE for full license.
"""
from networkx.algorithms.operators.binary import union

import popupcad
import math
import os
import sys
from pprint import pprint
import numpy as np

# for plotting
# import matplotlib.pyplot as plt
# import seaborn as sns

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
hinge_file    = 'robobee_interference_hinge_BAK.cad'
myfile        =  '9layer_25x25.cad' #'25mm_x_25mm_layup.cad'

if __name__=='__main__':

    app = qg.QApplication(sys.argv)

    sheet = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, myfile))
    sheet.reprocessoperations(debugprint=True)

    # assume sheet is the last laminate, save for later
    original_sheet_id = sheet.operations[-1].id

    hinge = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, hinge_file))
    hinge.reprocessoperations(debugprint=True)

    # get hinge op id
    insert_part_operation_number = len(hinge.operations)-1
    release_cut_operation_number = len(hinge.operations)-2

    support_offset = 0.1


    # going to make 12 hinges (in microns)
    offsets = [298.793538 ,265.6681327, 239.9011416, 219, 201.4618598, 186.3226217,
               172.9311793, 160.8275347, 149.6727555, 139.206462, 129.2196409, 119.5362643]

    offsets = [of/1000 for of in offsets]


    ############################ make an array of new hinge designs with adjusted hinge length

    # specific to this file
    topteeth_key = 4748049616
    bottomteeth_key = 4707609552

    print(hinge.sketches[topteeth_key])
    constraint_names = [c.name for c in hinge.sketches[topteeth_key].constraintsystem.constraints]
    idx = [i for i, c in enumerate(constraint_names) if c == 'Y Distance']
    idx_top = idx[0] # just worry about one for now
    print('constraint number ' + str(idx_top))

    print(hinge.sketches[bottomteeth_key])
    constraint_names = [c.name for c in hinge.sketches[bottomteeth_key].constraintsystem.constraints]
    idx = [i for i, c in enumerate(constraint_names) if c == 'Y Distance']
    idx_bot = idx[0] # just worry about one for now
    print('constraint number ' + str(idx_bot))


    #################### update the length
    def update_y_length(des, new_length, key, idx):
        """
        Example function to update the length of a specific geometric constraint in sketch.
        Note that constraint in this case takes abs val of number
        """
        # make a copy, this is just for the demo
        adjusted_constraint = des.sketches[key]

        # update the constraint value
        adjusted_constraint.constraintsystem.constraints[idx].value = new_length

        # define the vertex return function
        def get_v():
            return [vertex for geom in adjusted_constraint.operationgeometry
                    for vertex in geom.vertices()]

        # go through the steps of updating geometry
        adjusted_constraint.constraintsystem.get_vertices = get_v
        adjusted_constraint.constraintsystem.cleanup()
        adjusted_constraint.constraintsystem.generator
        adjusted_constraint.constraintsystem.update()

        # return
        return adjusted_constraint


    hinges = []
    insert_part_operation_number_list = []

    for kk, offset in enumerate(offsets):

        # generate new interference hinge
        tmp = hinge.copy()
        update_y_length(tmp, offset, topteeth_key, idx_top)
        update_y_length(tmp, offset, bottomteeth_key, idx_bot)

        holes = Sketch.new()
        diam = 0.02
        loc = (-2.705,0.02)
        tmp.reprocessoperations()

        # make list of squares
        holes_poly = [popupcad.filetypes.genericshapes.GenericPoly.gen_from_point_lists([(loc[0]+diam*3*(k+1),loc[1]),
                                                                                         (loc[0]+diam*3*(k+1),loc[1] + diam),
                                                                                         (loc[0]+diam*3*(k+1) + diam,loc[1] + diam),
                                                                                         (loc[0]+diam*3*(k+1) + diam,loc[1])],
                                                                                          []) for k in range(kk+1)]
        holes.addoperationgeometries(holes_poly)

        tmp.sketches[holes.id] = holes

        layer_links = [layer.id for layer in tmp.return_layer_definition().layers] # just the top layer
        holes_sketch = popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [holes.id]},[layer_links[-1]])

        tmp.addoperation(holes_sketch)
        holes_sketch.generate(tmp)

        cut_holes = popupcad.manufacturing.laminateoperation2.LaminateOperation2({'unary': [(tmp.operations[insert_part_operation_number].id,0)],
                                                                                     'binary': [(holes_sketch.id,0)]},
                                                                                    'difference')
        tmp.addoperation(cut_holes)
        cut_holes.generate(tmp)

        tmp.reprocessoperations()
        insert_part_operation_number_list.append(cut_holes.id)
        # Change the constraint value
        hinges.append(tmp)

    ############################ Tile these hinges into the sheet

    ######################## make a web with default sizes

    construction_geom_hinge = []

    for hng in hinges:
        # build the op_links, then auto make the operation
        op = hng.operations[insert_part_operation_number]
        op_ref = op.id
        op_links = {'parent': [(op_ref, op.getoutputref())]}

        new_web = AutoWeb4(op_links,[support_offset,0],popupcad.manufacturing.multivalueoperation3.MultiValueOperation3.keepout_types.laser_keepout)
        new_web.setcustomname(op.name)

        hng.addoperation(new_web)
        new_web.generate(hng)

        ######################## generate the same size construction line somewhere in the sheet file

        # get geom for line
        bounding_box = new_web.output[1].generic_laminate().getBoundingBox()

        # make the sketch
        construction_geom_hinge.append(Sketch.new())
        tmp_geom = [(bounding_box[0],bounding_box[1]), (bounding_box[0],bounding_box[3])]
        construction_line = GenericLine.gen_from_point_lists(tmp_geom,[],construction=False)
        construction_geom_hinge[-1].addoperationgeometries([construction_line])

        # add sketch to sketch list
        hng.sketches[construction_geom_hinge[-1].id] = construction_geom_hinge[-1]

        # make the sketchop
        construction_geom_sketchop_hinge = SimpleSketchOp({'sketch': [construction_geom_hinge[-1].id]},
                                                    [layer.id for layer in hinge.return_layer_definition().layers])
        construction_geom_sketchop_hinge.name = "ConstructionLine"

        # finally initialize sketch op in design
        hng.addoperation(construction_geom_sketchop_hinge)
        construction_geom_sketchop_hinge.generate(hng)

    ######################## generate the external transform geometry in the sheet

    # center the bottom left to origin
    position_hinge = (-tmp_geom[0][0],-tmp_geom[0][1])
    tmp_geom = [(x + position_hinge[0], y + position_hinge[1]) for (x,y) in tmp_geom]

    # two locations to place parts, upper and lower "windows"
    parts_bounding_box = (15, 8.5) # width, height

    # lets make 4x4
    sc = 1
    x_gap = 0
    y_gap = 0
    width = (bounding_box[2] - bounding_box[0])/sc + x_gap
    height = (bounding_box[3] - bounding_box[1])/sc + y_gap

    # number of parts
    N = 12

    # check if will all fit in one window, if not fill first and check if remainder will fit in second window
    max_num_cols = divmod(parts_bounding_box[0], width)[0]
    max_num_rows = divmod(parts_bounding_box[1], height)[0]

    arrayed_reference_lines = []

    # check if can fit in one
    # if N <= max_num_rows*max_num_cols:
    rows = math.ceil(N / max_num_cols)
    cols = math.ceil(N / rows)          # spread across the two windows
    n_count = 0

    new_center = (-parts_bounding_box[0]/2, 2)
    tmp_geom = [(x + new_center[0], y + new_center[1]) for (x,y) in tmp_geom]

    arrayed_reference_lines_top = []
    arrayed_reference_lines_bot = []

    for row in range(rows):
        for col in range(cols):
            if n_count > N or n_count > max_num_rows*max_num_cols*2:
                break


            arrayed_reference_lines_top.append([(tmp_geom[0][0]+col*width, tmp_geom[0][1]/sc+(max_num_rows-row - 1)*height),
                                            (tmp_geom[1][0]+col*width, tmp_geom[1][1]/sc+(max_num_rows-row - 1)*height)])


            arrayed_reference_lines_bot.append([(tmp_geom[0][0]+col*width,
                                             tmp_geom[0][1]/sc+(max_num_rows-row - 1)*height - 11),
                                            (tmp_geom[1][0]+col*width,
                                             tmp_geom[1][1]/sc+(max_num_rows-row - 1)*height - 11)])

            n_count = n_count + 1



    construction_geom_sheet_top = []
    construction_geom_sheet_bot = []

    construction_geom_sketchop_sheet = []

    for ref_top, ref_bot in zip(arrayed_reference_lines_top, arrayed_reference_lines_bot):

        # top
        construction_geom_sheet_top.append(Sketch.new())

        construction_line = [GenericLine.gen_from_point_lists(ref_top,[],construction=False)]
        construction_geom_sheet_top[-1].addoperationgeometries(construction_line)

        # add sketch to sketch list
        sheet.sketches[construction_geom_sheet_top[-1].id] = construction_geom_sheet_top[-1]

        # make the sketchop
        construction_geom_sketchop_sheet.append(SimpleSketchOp({'sketch': [construction_geom_sheet_top[-1].id]},
                                                    [layer.id for layer in sheet.return_layer_definition().layers]))
        construction_geom_sketchop_sheet[-1].name = "ConstructionLine"

        # finally initialize sketch op in design
        sheet.addoperation(construction_geom_sketchop_sheet[-1])
        construction_geom_sketchop_sheet[-1].generate(sheet)

        # bot
        construction_geom_sheet_bot.append(Sketch.new())

        construction_line = [GenericLine.gen_from_point_lists(ref_bot,[],construction=False)]
        construction_geom_sheet_bot[-1].addoperationgeometries(construction_line)

        # add sketch to sketch list
        sheet.sketches[construction_geom_sheet_bot[-1].id] = construction_geom_sheet_bot[-1]

        # make the sketchop
        construction_geom_sketchop_sheet.append(SimpleSketchOp({'sketch': [construction_geom_sheet_bot[-1].id]},
                                                    [layer.id for layer in sheet.return_layer_definition().layers]))
        construction_geom_sketchop_sheet[-1].name = "ConstructionLine"

        # finally initialize sketch op in design
        sheet.addoperation(construction_geom_sketchop_sheet[-1])
        construction_geom_sketchop_sheet[-1].generate(sheet)



    ######################## External transform the hinge onto the sheet construction line


    # make design links
    design_links = {}
    design_links['subdesign'] = [hinge.id]

    insert_part_id =[]
    release_id = []
    web_id = []

    for construction_geom_sht_top, construction_geom_sht_bot, construction_geom_hng, hng, idd in zip(construction_geom_sheet_top,
                                                                      construction_geom_sheet_bot,
                                                                      construction_geom_hinge,
                                                                      hinges,
                                                                      insert_part_operation_number_list):

        ########### upper
        # insert hinge into sheet as subdesign
        sheet.subdesigns[hng.id] = hng

        sketch_links = {}
        sketch_links['sketch_to'] = [construction_geom_sht_top.id]

        sub_sketch_id = construction_geom_hng.id

        subopref = (idd,0)

        insert_part = TransformExternal(sketch_links, design_links, subopref, sub_sketch_id, 'scale', 'scale', 0, False, 1., 1.)
        insert_part.customname = 'Inserted part'

        sheet.addoperation(insert_part)
        insert_part.generate(sheet)
        insert_part_id.append(sheet.operations[-1].id) # save for later

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
        web_id.append(sheet.operations[-1].id)


        ######################## Make release cut laminate operation

        # # make design links
        design_links = {}
        design_links['subdesign'] = [hinge.id]

        sketch_links = {}
        sketch_links['sketch_to'] = [construction_geom_sht_top.id]

        sub_sketch_id = construction_geom_hng.id

        subopref = (hinge.operations[release_cut_operation_number].id,0)

        insert_release = TransformExternal(sketch_links, design_links, subopref, sub_sketch_id, 'scale', 'scale', 0, False, 1., 1.)
        insert_release.customname = 'Release'
        sheet.addoperation(insert_release)
        insert_release.generate(sheet)
        release_id.append(sheet.operations[-1].id)

        ########### bottom
        # insert hinge into sheet as subdesign
        sheet.subdesigns[hng.id] = hng

        sketch_links = {}
        sketch_links['sketch_to'] = [construction_geom_sht_bot.id]

        sub_sketch_id = construction_geom_hng.id

        subopref = (idd,0)

        insert_part = TransformExternal(sketch_links, design_links, subopref, sub_sketch_id, 'scale', 'scale', 0, False, 1., 1.)
        insert_part.customname = 'Inserted part'

        sheet.addoperation(insert_part)
        insert_part.generate(sheet)
        insert_part_id.append(sheet.operations[-1].id) # save for later

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
        web_id.append(sheet.operations[-1].id)


        ######################## Make release cut laminate operation

        # # make design links
        design_links = {}
        design_links['subdesign'] = [hinge.id]

        sketch_links = {}
        sketch_links['sketch_to'] = [construction_geom_sht_bot.id]

        sub_sketch_id = construction_geom_hng.id

        subopref = (hinge.operations[release_cut_operation_number].id,0)

        insert_release = TransformExternal(sketch_links, design_links, subopref, sub_sketch_id, 'scale', 'scale', 0, False, 1., 1.)
        insert_release.customname = 'Release'
        sheet.addoperation(insert_release)
        insert_release.generate(sheet)
        release_id.append(sheet.operations[-1].id)

    #
    #
    # ######################## Remove web.sheet from sheet, union external transform + generateed sheet with hole + web
    # first the difference
    # link 1 is the sheet
    diff_ops = [(tmp_web_id,1) for tmp_web_id in web_id]
    sheet_with_hole = LaminateOperation2({'unary': [(original_sheet_id,0)], 'binary': diff_ops},'difference')
    sheet_with_hole.customname = 'Sheet with hole'
    sheet.addoperation(sheet_with_hole)
    sheet_with_hole.generate(sheet)

    # ############################## Finally union the sheet with holes, the webs, and the parts

    union_ops = [(tmp_web_id,0) for tmp_web_id in web_id] + \
                [(tmp_insert_part_id, 0) for tmp_insert_part_id in insert_part_id]

    sheet_with_part = LaminateOperation2({'unary': [(sheet_with_hole.id,0)] + union_ops, 'binary':[]},'union')

    sheet_with_part.customname = 'First pass cuts'
    sheet.addoperation(sheet_with_part)
    sheet_with_part.generate(sheet)

    ## union the release
    union_ops = [(tmp_release_id,0) for tmp_release_id in release_id]

    release_part = LaminateOperation2({'unary': union_ops, 'binary':[]},'union')

    release_part.customname = 'Release'
    sheet.addoperation(release_part)
    release_part.generate(sheet)
    #
    # ## final cleanup
    # sheet_with_part_cleanup = popupcad.manufacturing.cleanup2.Cleanup2(sheet_with_part, 0,
    #                                                                    popupcad.manufacturing.multivalueoperation3.MultiValueOperation3.keepout_types.laser_keepout)
    # sheet_with_part_cleanup.customname = 'Cleanup final'
    # sheet.addoperation(sheet_with_part_cleanup)
    # sheet_with_part_cleanup.generate(sheet)


    ################## show the new design



    editor = popupcad.guis.editor.Editor()
    editor.load_design(sheet)
    editor.show()
    sys.exit(app.exec_())
