
# Post processor should operate on generic laminate

# for appropriate plotting in pycharm
import matplotlib
matplotlib.use('qt4agg')

import popupcad
# from popupcad.filetypes.sketch import Sketch
import numpy as np
# import sys
import os

import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('dark')
sns.set_context('talk')
plt.show(block=False)

# from pprint import pprint
#
# import qt.QtCore as qc
# import qt.QtGui as qg
# from popupcad_manufacturing_plugins.manufacturing.outersheet3 import OuterSheet3

# file to load and work with
myfolder  = '/Users/nickgravish/popupCAD/api_examples/'
myfile    = 'test_arc_geometry.cad'

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

# lets plot the list of points
x = [p1 for p1, p2 in interior_points[0]]
y = [p2 for p1, p2 in interior_points[0]]

plt.figure()
plt.plot(x,y, '-o')
plt.xlabel('x')
plt.ylabel('y')
plt.show(block=False)


# compute step distance between adjacent pairs
steps = [np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2) for p1, p2 in
                                                            zip(interior_points[0][:-2], interior_points[0][1:-1])]
steps.append(np.sqrt((interior_points[0][-1][0] - interior_points[0][0][0])**2 +
                     (interior_points[0][-1][1] - interior_points[0][0][1])**2))

circular_difference = [step1 - step2 for step1, step2 in zip(steps[:-2], steps[1:-1])]
circular_difference.append(steps[-1] - steps[0])

# at this point, have list of steps in between points. Now need to find consecutive chunks of
# these points and then best fit an arc through them.

# plot out the consecutive poitns and their differences
plt.figure()
plt.plot(circular_difference, 'o-')
plt.xlabel('Point along perimeter')
plt.ylabel('Difference between points')

# consolidate all points associated with the circular. Meaning lets circular rotate the xy points in the list so
# that the arc is at the beginning.






















