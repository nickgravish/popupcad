# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 07:07:23 2016

@author: nickgravish
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 07:01:08 2016

@author: nickgravish
"""


#%%

#matplotlib.use('MacOSX')
%matplotlib osx

import popupcad
# from popupcad.filetypes.sketch import Sketch
import numpy as np
# import sys
import os

import matplotlib
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
myfile_complex = 'test_arc_geometry_complex.cad'

d = popupcad.filetypes.design.Design.load_yaml(os.path.join(myfolder, myfile_complex))
d.reprocessoperations(debugprint=True)

d.operations[-1].output[0]

# get list of all geometries that will be output to dxf
# out_geoms is a list of layer geometries
out_geoms = d.operations[-1].output[0].generic_laminate().all_geoms()

# get a list of interior points (since the circle is an interior point
interior_points = out_geoms[0].interiorpoints()
exterior_points = out_geoms[0].exteriorpoints()

#%%

# only one geometry on the interioir
len(interior_points)

# lets plot the list of points
x = [p1 for p1, p2 in interior_points[0]]
y = [p2 for p1, p2 in interior_points[0]]

plt.figure()
plt.plot(x,y, '-o')
plt.xlabel('x')
plt.ylabel('y')

x = [p1 for p1, p2 in exterior_points]
y = [p2 for p1, p2 in exterior_points]
plt.plot(x,y, '-o')
plt.axis([-6, 8, -5, 6])

#%% FInd the points along the circle

# compute step distance between adjacent pairs
steps = [np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2) for p1, p2 in
                                                            zip(interior_points[0][:-1], interior_points[0][1:])]
steps.append(np.sqrt((interior_points[0][-1][0] - interior_points[0][0][0])**2 +
                     (interior_points[0][-1][1] - interior_points[0][0][1])**2))

circular_difference = [np.abs(step1 - step2) for step1, step2 in zip(steps[:-1], steps[1:])]
circular_difference.append(np.abs(steps[-1] - steps[0]))

# at this point, have list of steps in between points. Now need to find consecutive chunks of
# these points and then best fit an arc through them.

# plot out the consecutive poitns and their differences
plt.figure()
plt.plot(circular_difference, 'o-')
plt.xlabel('Point along perimeter')
plt.ylabel('Difference between points')

plt.figure()
plt.hist(circular_difference)
plt.xlabel('Difference between points')
plt.ylabel('Count')

# 
#%% consolidate all points associated with the circular. Meaning lets circular rotate the xy points in the list so
#   that the arc is at the beginning.
 
def rotate(l,n):
    return l[n:] + l[:n]

# Need to find consecutive blocks of points with circ diff below a value
# use skiimage

from skimage import measure
thresh = 0.01

im = np.array(circular_difference) < thresh
all_labels = measure.label(im)

# now if a label is at the ends, merge them
if circular_difference[-1] < thresh :
    all_labels[all_labels==all_labels[-1]] = all_labels[0]

# list of all arc points
arc_labels = np.unique(all_labels[all_labels != 0])

#%% For arc fitting

from scipy import optimize
method_2 = "leastsq"

def calc_R(x, y, xc, yc):
    """ calculate the distance of each 2D points from the center (xc, yc) """
    print(x)
    print(xc)
    print(y)
    print(yc)
    
    return np.sqrt((x-xc)**2 + (y-yc)**2)

def f_2(input):
    """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """
    x = input[0]
    y = input[1]
    xc = input[2]
    yc = input[3]
    
    Ri = calc_R(x, y, xc, yc)
    return Ri - Ri.mean()

def best_fit_circle(x,y):
    xc, yc = np.mean(x), np.mean(y)
    print(center_estimate)

    input = []
    input.append(x)
    input.append(y)
    input.append(xc)
    input.append(yc)
    
    center_2, ier = optimize.leastsq(f_2, input)
    
    xc_2, yc_2 = center_2
    Ri_2       = calc_R(*center_2)
    R_2        = Ri_2.mean()
    residu_2   = sum((Ri_2 - R_2)**2)

    return xc_2, yc_2, Ri_2, R_2, residu_2


#%% Working
#  == METHOD 2 ==
from scipy      import optimize

method_2 = "leastsq"

def calc_R(xc, yc):
    """ calculate the distance of each 2D points from the center (xc, yc) """
#    print(x)
#    print(y)
    return np.sqrt((x-xc)**2 + (y-yc)**2)

def f_2(c):
    """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """
    Ri = calc_R(*c)
    return Ri - Ri.mean()

def best_fit_circle(x,y):
    center_estimate = np.mean(x), np.mean(y)
    center_2, ier = optimize.leastsq(f_2, center_estimate)
    
    xc_2, yc_2 = center_2
    Ri_2       = calc_R(*center_2)
    R_2        = Ri_2.mean()
    residu_2   = sum((Ri_2 - R_2)**2)
    return xc_2, yc_2, Ri_2, R_2, residu_2
    
    
#%% Locate the arc points and fit lines to them

x_all = np.array([p1 for p1, p2 in interior_points[0]])
y_all = np.array([p2 for p1, p2 in interior_points[0]])

x_centers = []
y_centers = []
R= []


plt.clf()
plt.plot(x_all, y_all)

for curr_label in arc_labels:
    print(curr_label)
    
    curr_indexes = np.where(all_labels == curr_label)
    
    x = x_all[curr_indexes]
    y = y_all[curr_indexes]

    xc_2, yc_2, Ri_2, R_2, residu_2 = best_fit_circle(x, y)

    plt.plot(x, y, 'o')
    plt.plot(xc_2, yc_2, 'o')    
    circle1 = plt.Circle((xc_2, yc_2), R_2, edgecolor='b', fill=None, 
                         linewidth=6, zorder = 10)
    plt.gcf().gca().add_artist(circle1)

    x_centers.append(xc_2)
    y_centers.append(yc_2)
    R.append(R_2)
    
    # find the beginning and end points of the arc
    consecutive = [np.abs(step1 - step2) for step1, step2 in zip(steps[:-1], steps[1:])]
    circular_difference.append(np.abs(steps[-1] - steps[0]))















