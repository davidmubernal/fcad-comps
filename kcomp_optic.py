# ----------------------------------------------------------------------------
# -- Component Constants
# -- comps library
# -- Constants about different optical components
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronic Technology. Rey Juan Carlos University (urjc.es)
# -- July-2017
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

import kcomp 



INCH = 25.4  # how many mm are one inch

CAGE_CUBE_60 = {
           'L'             :  76.2 ,  # Length of each side (3 inch)
           'thru_hole_d'   :  63.5 ,  # both sides, thru, not threaded
                                      # Thru, 4 sides
           'thru_thread_d' :  2.035*INCH ,  # SM2 (2.035"-40): d=51.689 mm
           'thru_rod_d'    :  6. ,    # 4 places, 2 sides, thru, on SM2 side
           'thru_rod_sep'  :  60. ,   # Separation between the rods
           # thread of the rods that can be tapped on the sides other than
           # the rod thru-holes: 
           'rod_thread_d'  :  kcomp.UNC_D['4'] ,  #4-40
           'rod_thread_l'  :  1.5 ,  # depth of the thread for the rods
           # aditional taps to connect accesories
           'tap_d'  :  kcomp.UNC_D['8'] ,  #8-32
           'tap_l'  :  3.0 ,  # depth of the #8-32 tap (I don't know)
           'tap_sep_l': 66.,   # separation of the #8_32 tap, large
           'tap_sep_s': 35.8   # separation of the #8_32 tap, short
                 }


CAGE_CUBE_HALF_60 = {
           # 76.2 Length of each side (3 inch)
           'L'              : CAGE_CUBE_60['L'],
           # Thru, 2 sides
           # 2.035*INCH ,  # SM2 (2.035"-40): d=51.689 mm
           'thread_d'   : CAGE_CUBE_60['thru_thread_d'],
           # internal hole after the SM2 thread
           'thru_hole_d'     : 41.9,
           # distance from the edge that the internal hole starts after
           # the SM2 thread
           'thru_hole_depth' : 8.9,
           # Hole for the lens at 45 degrees
           # to the center, for 2inch optics (50.8mm)
           'lenshole_45_d'   :  49.3,  
           'rod_d'    :  6. ,    # 4 places, 2 sides,  perpendicular sides
           'rod_sep'  :  60. ,   # Separation between the rods
           'rod_depth':  6.4 ,   # how deep are the holes
           # taps to mount to posts, on the to triangular sides
           # to diferenciate the sides, the perpendicular sides are named
           # axis_1 and axis_2, so 12 will be the cross product of
           # axis_1 x axis_2, and the other 21 will be axis_2 x axis_1
           'tap12_d' :  4. ,  #M4x0.7 diameter
           'tap12_l' :  6.4 ,  # length: depth of the M4x0.7 tap
           'tap21_d' :  6. ,  #M6x1 diameter
           'tap21_l' :  8.9 , # length: depth of the M6x1.0 tap
           # the distance to the center in direction to the right angle
           # see picture below
           'tap_dist':  10.2  # The dis
                 }

#
#                 /|
#               /  |
#             /    |
#           /      |
#         /   0    |---
#       /     :    |  + 27.9 
#     /____________|...
#     :       :    :
#     :       :----:
#     :         27.9
#     :.. 76.2 ....:  -> 76.2/2 = 38.3
#           :      :
#           :.38.3.:  -> the center
#           : :
#           : : -------> 10.2: distance to the center: 48.3-27.9 


# metric bread board constant dimensions:

BREAD_BOARD_M = {
                  'thick'  : 12.7, #thickness of the board
                  'hole_d' : 6., # tapped M6 holes
                  'hole_sep' : 25., # separation between holes
                  'hole_sep_edge' : 12.5, #separation from 1st hole to edge
                  'cbored_hole_d' : 6., # M6 counterbored holes on the corners
                  'cbored_hole_sep' : 25., # distance counterbored holes to edge
                  'cbore_head_d' : 10., # head diameter M6
                  'cbore_head_l' : 10., # head diameter M6
                  'minw_cencbore': 450. # minimum width to have a counter
                                #bored hole at the center
                  }
                

