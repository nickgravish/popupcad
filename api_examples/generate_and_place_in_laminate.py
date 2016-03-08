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
import numpy as np
import math

import qt.QtGui as qg

from popupcad.filetypes.operationoutput import OperationOutput
import popupcad_manufacturing_plugins

from popupcad.filetypes.sketch import Sketch
from popupcad_manufacturing_plugins.manufacturing.autoweb4 import AutoWeb4
from popupcad.manufacturing.simplesketchoperation import SimpleSketchOp
from popupcad.filetypes.genericshapes import GenericLine
from popupcad.manufacturing.transform_external import TransformExternal
from popupcad.manufacturing.transform_internal import TransformInternal
from popupcad.manufacturing.laminateoperation2 import LaminateOperation2
from popupcad.manufacturing.sub_operation2 import SubOperation2
from popupcad.manufacturing.multivalueoperation3 import MultiValueOperation3
from popupcad.filetypes.material2 import default_material_types

plugins = []
import popupcad_manufacturing_plugins
plugins.append(popupcad_manufacturing_plugins)


# file to load and work with
myfolder  = '/Users/nickgravish/popupCAD_files/designs/'
hinge_file    = 'robobee_interference_hinge_BAK.cad'

def generate_laminate(design):
    """
    Take in a design file and generate a support laminate for this part

    """

    sheet_width = 25        # mm
    hole_offset = 3         # location of hole in from corner
    hole_rad    = 0.79      # alignment pin geoms
    cross_len   = 1         # tick length
    cross_horiz = 10        # horizontal dimension from center crosshair
    dt          = 0.001     # small thickness for crosshair

    buff_x      = 5         # for window sizes
    buff_y      = 1
    wind_h      = 1
    space_x     = 1.3

    # window width, maximum of 1 mm
    wind_w      = lambda N: min((sheet_width - 2*buff_x)/(N + 1.3*N - 1.3), 1)

    # the laminate design
    layup = popupcad.filetypes.design.Design.new()
    layup.updatefilename("layup")
    layer_list = hinge.return_layer_definition().layers
    layup.define_layers(popupcad.filetypes.layerdef.LayerDef(*layer_list))


    # initiate the sketches
    ############# sheet first
    sheet = Sketch.new()
    tmp_geom = [(-sheet_width/2., -sheet_width/2.), (-sheet_width/2.,  sheet_width/2.),
                ( sheet_width/2.,  sheet_width/2.), ( sheet_width/2., -sheet_width/2.)]
    sheet_poly = popupcad.filetypes.genericshapes.GenericPoly.gen_from_point_lists(tmp_geom,[])
    sheet.addoperationgeometries([sheet_poly])

    ############# holes second
    holes = Sketch.new()
    tmp_geom = [(-sheet_width/2. + hole_offset, -sheet_width/2. + hole_offset),
                (-sheet_width/2. + hole_offset,  sheet_width/2. - hole_offset),
                ( sheet_width/2. - hole_offset,  sheet_width/2. - hole_offset),
                ( sheet_width/2. - hole_offset, -sheet_width/2. + hole_offset)]
    # make list of hole geometry
    holes_poly = [popupcad.filetypes.genericshapes.GenericCircle.gen_from_point_lists([pt, (pt[0]+hole_rad, pt[1])],[])
                                        for pt in tmp_geom]
    holes.addoperationgeometries(holes_poly)

    ############# upper triangle
    left_tri = Sketch.new()
    tmp_geom = [(-sheet_width/2. + hole_offset/4, sheet_width/2. - hole_offset*(2/3)),
                (-sheet_width/2. + hole_offset/4 + hole_rad,  sheet_width/2. - hole_offset*(2/3)),
                (-sheet_width/2. + hole_offset/4 + 0.5*hole_rad,  sheet_width/2. - hole_offset*(2/3) + 1.2*hole_rad*.75)]
    # make list of hole geometry
    sheet_poly = popupcad.filetypes.genericshapes.GenericPoly.gen_from_point_lists(tmp_geom,[])
    left_tri.addoperationgeometries([sheet_poly])

    ############# crosshairs
    cross_hairs = Sketch.new()
    tmp_geom_horiz = [(0,-cross_len), (0,cross_len)]
    tmp_geom_vert  = [(-cross_len,0), (cross_len,0)]
    shift = [-cross_horiz, 0, cross_horiz]

    cross_poly_horiz = [popupcad.filetypes.genericshapes.GenericPoly.gen_from_point_lists([(tmp_geom_horiz[0][0] + c - dt/2.,
                                                                                            tmp_geom_horiz[0][1] - dt/2.),
                                                                                           (tmp_geom_horiz[1][0] + c - dt/2.,
                                                                                            tmp_geom_horiz[1][1] - dt/2.),
                                                                                           (tmp_geom_horiz[1][0] + c + dt/2.,
                                                                                            tmp_geom_horiz[1][1] + dt/2.),
                                                                                           (tmp_geom_horiz[0][0] + c + dt/2.,
                                                                                            tmp_geom_horiz[0][1] - dt/2.)],
                                                                                           [])
                                                                                    for c in shift]

    cross_poly_vert  = [popupcad.filetypes.genericshapes.GenericPoly.gen_from_point_lists([(tmp_geom_vert[0][0] + c - dt/2.,
                                                                                            tmp_geom_vert[0][1] - dt/2.),
                                                                                           (tmp_geom_vert[1][0] + c - dt/2.,
                                                                                            tmp_geom_vert[1][1] + dt/2.),
                                                                                           (tmp_geom_vert[1][0] + c + dt/2.,
                                                                                            tmp_geom_vert[1][1] + dt/2.),
                                                                                           (tmp_geom_vert[0][0] + c + dt/2.,
                                                                                            tmp_geom_vert[0][1] - dt/2.)],
                                                                                           [])
                                                                                    for c in shift]

    cross_hairs.addoperationgeometries(cross_poly_horiz + cross_poly_vert)

    # Build the sheet with holes
    # Add the sketches to the sketch list
    layup.sketches[sheet.id] = sheet
    layup.sketches[holes.id] = holes
    layup.sketches[cross_hairs.id] = cross_hairs
    layup.sketches[left_tri.id] = left_tri

    # get the layer links for making sketch ops
    layer_links = [layer.id for layer in layer_list]

    holes_sketch = popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [holes.id]},layer_links)
    holes_sketch .name = "Holes"

    trian_sketch = popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [left_tri.id]},layer_links)
    trian_sketch .name = "Left triangle"

    sheet_sketch = popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [sheet.id]},layer_links)
    sheet_sketch.name = "sheet"

    cross_sketch = popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [cross_hairs.id]},layer_links)
    cross_sketch.name = "Crosshairs"

    # laminate operation to combine cross hairs and holes
    sheet_with_holes = popupcad.manufacturing.laminateoperation2.LaminateOperation2({'unary': [(sheet_sketch.id,0)],
                                                                                     'binary': [(holes_sketch.id,0),
                                                                                                (cross_sketch.id,0),
                                                                                                (trian_sketch.id,0)]},
                                                                                    'difference')
    sheet_with_holes.name = "Sheet with holes"

    ############# rectangle windows
    windows = [Sketch.new() for _ in layer_list]
    windows_sketchop = []
    # make windows, center on middle of sheet at bottom
    window_width = wind_w(len(windows))
    window_coords = np.array([round(kk*(1 + space_x)*window_width,4) for kk in range(len(windows))])
    window_coords = list(window_coords - np.mean(window_coords)) # center is 0

    for kk, (layer, window, x_coord) in enumerate(zip(layer_list,
                                                      windows,
                                                      window_coords)):

        window.name = layer.name + '_window'

        tmp_geom = [(x_coord, -sheet_width/2. + buff_y),
                    (x_coord,  -sheet_width/2. + buff_y + wind_h),
                    (x_coord + window_width, -sheet_width/2. + buff_y + wind_h),
                    (x_coord + window_width, -sheet_width/2. + buff_y)]
        sheet_poly = popupcad.filetypes.genericshapes.GenericPoly.gen_from_point_lists(tmp_geom,[])
        window.addoperationgeometries([sheet_poly])
        layup.sketches[window.id] = window

        # make a sketch op on all layers above the current layer, this will be removed with a difference from the sheet
        windows_sketchop.append(popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [window.id]},
                                                                                   layer_links[kk+1:]))
        windows_sketchop[-1].name = "Window_" + layer.name


    # laminate operation to remove windows from sheet with holes
    sheet_with_windows = popupcad.manufacturing.laminateoperation2.LaminateOperation2({'unary': [(sheet_with_holes.id,0)],
                                                                                     'binary': [(sktch.id,0) for sktch
                                                                                                in windows_sketchop]},
                                                                                     'difference')
    sheet_with_windows.name = "Final sheet"

    # add the sketch ops to the design and generate the sketch op
    other_ops = windows_sketchop + [trian_sketch, holes_sketch, sheet_sketch, cross_sketch, sheet_with_holes, sheet_with_windows]
    [layup.addoperation(item) for item in other_ops]
    [item.generate(layup) for item in other_ops]

    design.subdesigns[layup.id] = layup

    subop = SubOperation2({'source': [layup.id]}, [], [],
                          [popupcad.manufacturing.sub_operation2.OutputData((layup.operations[-1].id,0),0)])
    subop.setcustomname("Support layup")
    subop.generate(design)
    design.addoperation(subop)

    return layup, subop

def array_part_into_layup(hinge, sheet, support_offset = 0.0, N = 12, sc = 1, x_gap = 0, y_gap = 0):

    # original_sheet_id = sheet.operations[-1].id

    # get hinge op id
    insert_part_operation_number  = [cnt for cnt, op in enumerate(hinge.operations) if op.customname.find("FinalPart") != -1][0]
    release_cut_operation_number  = [cnt for cnt, op in enumerate(hinge.operations) if op.customname.find("Release") != -1][0]

    # insert_part_operation_number = len(hinge.operations)-3
    # release_cut_operation_number = len(hinge.operations)-2

    # build the op_links, then auto make the operation
    op = hinge.operations[insert_part_operation_number]
    op_ref = op.id
    op_links = {'parent': [(op_ref, op.getoutputref())]}

    new_web = AutoWeb4(op_links,[support_offset,0],MultiValueOperation3.keepout_types.laser_keepout)
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

    # two locations to place parts, upper and lower "windows"
    parts_bounding_box = (15, 9.5) # width, height

    # lets make 4x4
    width = (bounding_box[2] - bounding_box[0])/sc + x_gap
    height = (bounding_box[3] - bounding_box[1])/sc + y_gap


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

    for row in range(rows):
        for col in range(cols):
            if n_count > N or n_count > max_num_rows*max_num_cols*2:
                break

            if row < max_num_rows:
                arrayed_reference_lines.append([(tmp_geom[0][0]+col*width, tmp_geom[0][1]/sc+(max_num_rows-row - 1)*height),
                                                (tmp_geom[1][0]+col*width, tmp_geom[1][1]/sc+(max_num_rows-row - 1)*height)])

            else:
                arrayed_reference_lines.append([(tmp_geom[0][0]+col*width,
                                                 tmp_geom[0][1]/sc+(max_num_rows-row - 1)*height - 2*new_center[1]),
                                                (tmp_geom[1][0]+col*width,
                                                 tmp_geom[1][1]/sc+(max_num_rows-row - 1)*height - 2*new_center[1])])

            n_count = n_count + 1

    construction_geom_sheet = Sketch.new()
    construction_line = [GenericLine.gen_from_point_lists(line,[],construction=False) for
                         line in arrayed_reference_lines]
    construction_geom_sheet.addoperationgeometries(construction_line)

    # add sketch to sketch list
    hinge.sketches[construction_geom_sheet.id] = construction_geom_sheet

    # make the sketchop
    construction_geom_sketchop_sheet = SimpleSketchOp({'sketch': [construction_geom_sheet.id]},
                                                [layer.id for layer in hinge.return_layer_definition().layers])
    construction_geom_sketchop_sheet.name = "ConstructionLine"

    # finally initialize sketch op in design
    hinge.addoperation(construction_geom_sketchop_sheet)
    construction_geom_sketchop_sheet.generate(hinge)

    ######################## External transform the hinge onto the sheet construction line

    # # insert hinge into sheet as subdesign
    # sheet.subdesigns[hinge.id] = hinge

    # # make design links
    operation_links = {}
    operation_links['from'] = [(hinge.operations[insert_part_operation_number].id,0)]

    sketch_links = {}
    sketch_links['sketch_to'] = [construction_geom_sheet.id]
    sketch_links['sketch_from'] = [construction_geom_hinge.id]

    insert_part = TransformInternal(sketch_links, operation_links, 'scale', 'scale', 0, False, 1., 1.)
    insert_part.customname = 'Inserted part'

    hinge.addoperation(insert_part)
    insert_part.generate(hinge)
    insert_part_id = hinge.operations[-1].id # save for later

    ######################## External transform the web.sheet to the construction line

    # # make design links
    operation_links = {}
    operation_links['from'] = [(new_web.id,1)]

    sketch_links = {}
    sketch_links['sketch_to'] = [construction_geom_sheet.id]
    sketch_links['sketch_from'] = [construction_geom_hinge.id]

    insert_webs = TransformInternal(sketch_links, operation_links, 'scale', 'scale', 0, False, 1., 1.)
    insert_webs.customname = 'Inserted part webs'

    hinge.addoperation(insert_webs)
    insert_webs.generate(hinge)


    # ######################## Make web of subdesign in sheet
    #
    # # build the op_links, then auto make the operation
    # op = hinge.operations[-1]
    # op_ref = op.id # last operation is the one we want
    # op_links = {'parent': [(op_ref, op.getoutputref())]}
    #
    # # note second value has to be 0
    # new_web = AutoWeb4(op_links,[support_offset,0],popupcad.manufacturing.multivalueoperation3.MultiValueOperation3.keepout_types.laser_keepout)
    # new_web.setcustomname(op.name)
    #
    # hinge.addoperation(new_web)
    # new_web.generate(hinge)
    # web_id = hinge.operations[-1].id

    ######################## Remove web.sheet from sheet, union external transform + generateed sheet with hole + web
    # first the difference
    # link 1 is the sheet
    sheet_with_hole = LaminateOperation2({'unary': [(sheet.id,0)], 'binary': [(insert_webs.id,0)]},'difference')
    sheet_with_hole.customname = 'Sheet with hole'
    hinge.addoperation(sheet_with_hole)
    sheet_with_hole.generate(hinge)

    sheet_with_part = LaminateOperation2({'unary': [(sheet_with_hole.id,0), (insert_part_id,0)],
                                          'binary':[]},'union')

    sheet_with_part.customname = 'First pass cuts'
    hinge.addoperation(sheet_with_part)
    sheet_with_part.generate(hinge)

    ######################## Make release cut laminate operation

    # # make design links
    # design_links = {}
    # design_links['subdesign'] = [hinge.id]
    operation_links = {}
    operation_links['from'] = [(hinge.operations[release_cut_operation_number].id,0)]

    sketch_links = {}
    sketch_links['sketch_to'] = [construction_geom_sheet.id]
    sketch_links['sketch_from'] = [construction_geom_hinge.id]

    insert_release = TransformInternal(sketch_links, operation_links, 'scale', 'scale', 0, False, 1., 1.)

    insert_release.customname = 'Release'
    hinge.addoperation(insert_release)
    insert_release.generate(hinge)


if __name__=='__main__':

    app = qg.QApplication(sys.argv)

    hinge = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, hinge_file))
    hinge.reprocessoperations(debugprint=True)

    # generate laminate based on the layers in the design
    layup, subop = generate_laminate(hinge)



    # place op the laminate
    array_part_into_layup(hinge, subop, N = 24, x_gap = 0.1, y_gap = 0.1)

    ################## show the new design
    editor = popupcad.guis.editor.Editor()
    editor.load_design(hinge)
    editor.show()
    sys.exit(app.exec_())




