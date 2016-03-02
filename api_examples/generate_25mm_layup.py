# -*- coding: utf-8 -*-
"""
Please see LICENSE for full license.
"""

import popupcad
from popupcad.filetypes.sketch import Sketch
import numpy
import sys

import qt.QtCore as qc
import qt.QtGui as qg
from popupcad_manufacturing_plugins.manufacturing.outersheet3 import OuterSheet3
from popupcad.filetypes.material2 import default_material_types

if __name__=='__main__':

    app = qg.QApplication(sys.argv)

    sheet_width = 25        # mm
    hole_offset = 3
    hole_rad    = 0.79      # alignment pin geoms
    cross_len   = 1         # tick length
    cross_horiz = 10        # horizontal dimension from center crosshair
    dt          = 0.001     # small thickness for crosshair

    # initiate the file
    top_design = popupcad.filetypes.design.Design.new()

    # for a default sublaminate
    # top_design.define_layers(popupcad.filetypes.layerdef.LayerDef(*popupcad.filetypes.material2.default_sublaminate))

    # custom sublaminate
    custom_layer_list = ['rigid', 'adhesive', 'rigid', 'adhesive', 'flexible', 'adhesive', 'rigid', 'adhesive', 'rigid']
    custom_layers = [default_material_types[key].copy(identical=False) for key in custom_layer_list]

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

    ############# rectangle windows next


    # Add the sketches to the sketch list
    top_design.sketches[sheet.id] = sheet
    top_design.sketches[holes.id] = holes
    top_design.sketches[cross_hairs.id] = cross_hairs

    # get the layer links for making sketch ops
    layer_links = [layer.id for layer in top_design.return_layer_definition().layers]

    holes_sketch = popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [holes.id]},layer_links)
    holes_sketch .name = "Holes"

    sheet_sketch = popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [sheet.id]},layer_links)
    sheet_sketch.name = "sheet"

    cross_sketch = popupcad.manufacturing.simplesketchoperation.SimpleSketchOp({'sketch': [cross_hairs.id]},layer_links)
    cross_sketch.name = "Crosshairs"

    # laminate operation to combine cross hairs and holes
    sheet_with_holes = popupcad.manufacturing.laminateoperation2.LaminateOperation2({'unary': [(sheet_sketch.id,0)],
                                                                                     'binary': [(holes_sketch.id,0),
                                                                                                (cross_sketch.id,0)]},
                                                                                    'difference')

    # add the sketch ops to the design and generate the sketch op
    other_ops = [holes_sketch, sheet_sketch, cross_sketch, sheet_with_holes]
    [top_design.addoperation(item) for item in other_ops]
    [item.generate(top_design) for item in other_ops]

    # GUI
    editor = popupcad.guis.editor.Editor()
    editor.load_design(top_design)
    editor.show()
    sys.exit(app.exec_())


