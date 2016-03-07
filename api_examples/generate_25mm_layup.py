# -*- coding: utf-8 -*-
"""
Please see LICENSE for full license.
"""

import popupcad
from popupcad.filetypes.sketch import Sketch
import numpy as np
import sys

import qt.QtGui as qg
from popupcad.filetypes.material2 import default_material_types

if __name__=='__main__':

    app = qg.QApplication(sys.argv)

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

    # initiate the file
    top_design = popupcad.filetypes.design.Design.new()

    # custom sublaminate
    custom_layer_list = ['rigid', 'adhesive', 'rigid', 'adhesive', 'flexible', 'adhesive', 'rigid', 'adhesive', 'rigid']
    custom_layers = [default_material_types[key].copy(identical=False) for key in custom_layer_list]

    # for a default sublaminate
    # custom_layers = *popupcad.filetypes.material2.default_sublaminate)

    top_design.define_layers(popupcad.filetypes.layerdef.LayerDef(*custom_layers))

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
    top_design.sketches[sheet.id] = sheet
    top_design.sketches[holes.id] = holes
    top_design.sketches[cross_hairs.id] = cross_hairs
    top_design.sketches[left_tri.id] = left_tri

    # get the layer links for making sketch ops
    layer_links = [layer.id for layer in top_design.return_layer_definition().layers]

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
    windows = [Sketch.new() for _ in top_design.return_layer_definition().layers]
    windows_sketchop = []
    # make windows, center on middle of sheet at bottom
    window_width = wind_w(len(windows))
    window_coords = np.array([round(kk*(1 + space_x)*window_width,4) for kk in range(len(windows))])
    window_coords = list(window_coords - np.mean(window_coords)) # center is 0

    for kk, (layer, window, x_coord) in enumerate(zip(top_design.return_layer_definition().layers,
                                                      windows,
                                                      window_coords)):

        window.name = layer.name + '_window'

        tmp_geom = [(x_coord, -sheet_width/2. + buff_y),
                    (x_coord,  -sheet_width/2. + buff_y + wind_h),
                    (x_coord + window_width, -sheet_width/2. + buff_y + wind_h),
                    (x_coord + window_width, -sheet_width/2. + buff_y)]
        sheet_poly = popupcad.filetypes.genericshapes.GenericPoly.gen_from_point_lists(tmp_geom,[])
        window.addoperationgeometries([sheet_poly])
        top_design.sketches[window.id] = window

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
    [top_design.addoperation(item) for item in other_ops]
    [item.generate(top_design) for item in other_ops]

    # GUI
    editor = popupcad.guis.editor.Editor()
    editor.load_design(top_design)
    editor.show()
    sys.exit(app.exec_())

