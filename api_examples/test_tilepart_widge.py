
import qt.QtGui as qg
import popupcad
from popupcad_manufacturing_plugins.manufacturing.tilepart import TilePart
import os
import sys

# file to load and work with
myfolder  = '/Users/nickgravish/popupCAD_files/designs'
design_file    = 'Transmissions.cad'

if __name__=='__main__':

    app = qg.QApplication(sys.argv)

    design = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, design_file))

    #part_opref, sheet_opref, sketch_bounding_box, N, scale, x_gap, y_gap, support_offset

    part_opref = design.operations[-2].id
    sheet_opref = design.operations[-1].id
    sketch_id = 4646817552

    scaling = popupcad.csg_processing_scaling
    sketch_bounding_box = design.sketches[sketch_id].output_csg()[0].bounds # may break if multiple sketches
    sketch_bounding_box = [geom/scaling for geom in sketch_bounding_box]

    N = 10
    scale = 1
    x_gap = 0
    y_gap = 0
    support_offset = 0

    new = TilePart(part_opref, sheet_opref, sketch_bounding_box, N, scale, x_gap, y_gap, support_offset)
    new.operate(design)

    ################## show the new design

    editor = popupcad.guis.editor.Editor()
    editor.load_design(design)
    editor.show()
    sys.exit(app.exec_())