# -*- coding: utf-8 -*-
"""
Please see LICENSE for full license.
"""


import popupcad
import os
import sys
import api_examples

import qt.QtGui as qg

# file to load and work with
myfolder  = '/Users/nickgravish/popupCAD_files/designs/'
myfile    = 'robobee_interference_hinge.cad'

if __name__=='__main__':

    app = qg.QApplication(sys.argv)

    original = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, myfile))
    original.reprocessoperations(debugprint=True)

    new_geom = original.copy()
    # new_geom.reprocessoperations()

    # attempt to make a list of all vertices

    # loop through sketches, then geometries in sketches. Shift all by x = 1, y = 0.5
    shift_x = 3
    shift_y = 3

    # all_sketches = [sketch for id,sketch in d.sketches.items()]
    vertices = [opgeom.vertices() for id,sketch in new_geom.sketches.items() for opgeom in sketch.operationgeometry]

    # flatten the list
    vertices = [item for sub in vertices for item in sub]

    # apply the shift
    for v in vertices:
        pos = v.getpos()
        v.setpos((pos[0] + shift_x, pos[1] + shift_y))

    # re-process constructive operations
    new_geom.reprocessoperations()

    operations,layerdef,sketches,

    subdesign_mapping,sketch_mapping,op_mapping = api_examples.design_advanced_functions.merge_designs(original,new_geom,0)


    ################## show the new design

    editor = popupcad.guis.editor.Editor()
    editor.load_design(subdesign_mapping)
    editor.show()
    sys.exit(app.exec_())
