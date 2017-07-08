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
