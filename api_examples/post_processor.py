

Post processor should operate on generic laminate



import popupcad
from popupcad.filetypes.sketch import Sketch
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
from pprint import pprint

import qt.QtCore as qc
import qt.QtGui as qg
from popupcad_manufacturing_plugins.manufacturing.outersheet3 import OuterSheet3

# file to load and work with
myfolder  = '/Users/nickgravish/popupCAD_files/designs/'
myfile    = 'circle_test.cad'

d = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, myfile))
d.reprocessoperations(debugprint=True)

d.operations[-1].output[0]

# get list of all geometries that will be output to dxf
# out_geoms is a list of layer geometries
out_geoms = d.operations[-1].output[0].generic_laminate().all_geoms()

# get a list of interior points (since the circle is an interior point
interior_points = out_geoms[0].interiorpoints()

# only one geometry on the interioir
len(interior_points)

# compute step distance between adjacent pairs
steps = [np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2) for p1, p2 in
                                                            zip(interior_points[0][:-2], interior_points[0][1:-1])]
steps.append(np.sqrt((interior_points[0][-1][0] - interior_points[0][0][0])**2 +
                     (interior_points[0][-1][1] - interior_points[0][0][1])**2))

circular_difference = [step1 - step2 for step1, step2 in zip(steps[:-2], steps[1:-1])]
circular_difference.append(steps[-1] - steps[0])

# at this point, have list of steps in between points. Now need to find consecutive chunks of
# these points and then best fit an arc through them.























