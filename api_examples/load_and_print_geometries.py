# -*- coding: utf-8 -*-
"""
Please see LICENSE for full license.
"""

import popupcad
import os
import sys
# import api_examples

import qt.QtGui as qg

from popupcad.filetypes.operationoutput import OperationOutput

# file to load and work with
myfolder  = '/Users/nickgravish/popupCAD_files/designs/'
myfile2    = 'robobee_interference_hinge.cad'
myfile    = '9layer_25x25.cad'


def shift_geom(original, shift_x = 0, shift_y = 0):
    new_geom = original.copy()

    # attempt to make a list of all vertices
    # loop through sketches, then geometries in sketches. Shift all by x = 1, y = 0.5

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
    return new_geom



if __name__=='__main__':

    app = qg.QApplication(sys.argv)

    sheet = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, myfile))
    sheet.reprocessoperations(debugprint=True)

    hinge = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, myfile2))
    hinge.reprocessoperations(debugprint=True)

    # Generate web
    names = [op.customname for op in hinge.operations]
    layer_loc = [i for i, c in enumerate(names) if 'final' in str.lower(c)]

    outer_buffer = 1        # footprint of the support sheet
    support_gap  = 0.25     # gap between part and sheet

    ls1 = hinge.operations[layer_loc[0]].output[0].csg
    sheet_out, outer_web, inner_elements, buffered_keepout = \
                            popupcad.algorithms.web.generate_web(ls1, popupcad.algorithms.keepout.laserkeepout(ls1),
                                             hinge.return_layer_definition(),
                                             (outer_buffer + support_gap)*popupcad.csg_processing_scaling,
                                             support_gap*popupcad.csg_processing_scaling)

    a = OperationOutput(outer_web, 'Web', hinge)
    b = OperationOutput(sheet_out, 'Sheet', hinge)
    c = OperationOutput(inner_elements, 'Inner Scrap', hinge)
    d = OperationOutput(buffered_keepout, 'Removed Material', hinge)


    # generate a construction line associated with the left line of the web of the part

    # generate the same size construction line somewhere in the sheet file

    # External transform the hinge onto the sheet construction line

    # remove the web.sheet from the sheet and make hole

    # Union the transform, the web, and the hole

    #
    # popupcad.manufacturing.transform_external()


    # sandbox creating new operations and sketches using new sketch id's
    #
    # # copy the operations
    # operations = [operation.copy_wrapper()
    #                   for operation in new_geom.operations]
    #
    # # copy the sketches to a new list, update the sketch name and ID.
    # sketches = {}
    # new_id_list = []
    # for key, value in new_geom.sketches.items():
    #     sketch_temp = value.copy(identical=True)
    #
    #     # make a new id and add the changed id to the list
    #     id_before = sketch_temp.id
    #     sketch_temp.regen_id()
    #     id_after  = sketch_temp.id
    #     sketch_temp.set_basename(str(id_after) + '.sketch')
    #
    #     sketches[sketch_temp.id] = sketch_temp
    #
    #     new_id_list.append((id_before, id_after))
    #
    # # sub designs for another time

    # subdesigns = {}
    # for key, value in new_geom.subdesigns.items():
    #     subdesigns[key] = value.copy(identical=True)

    # new = type(self)(operations,self.return_layer_definition().copy(),sketches,subdesigns)


    ################## show the new design

    editor = popupcad.guis.editor.Editor()
    editor.load_design(hinge)
    editor.show()
    sys.exit(app.exec_())
