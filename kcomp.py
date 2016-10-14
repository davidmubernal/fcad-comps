# file with constants about diferent components, materials and pieces 
# this is the old mat_cte.py. But mat seemed to be mathematical
# and some other general constants for the printer


# ---------------------- Tolerance in mm
TOL = 0.4
STOL = TOL / 2.0       # smaller tolerance

# height of the layer to print. To make some supports, ie: bolt's head
LAYER3D_H = 0.3  

# ---------------------- Bearings
LMEUU_L = { 10: 29.0, 12: 32.0 }; #the length of the bearing
LMEUU_D = { 10: 19.0, 12: 22.0 }; #diamenter of the bearing 



# E3D V6 extrusor dimensions
"""
    ___________
   |           |   outup
    -----------
      |     |
      |     |      in
    ___________
   |           |   outbot
    -----------
"""

E3DV6_IN_DIAM = 12.0
E3DV6_IN_H = 6.0
E3DV6_OUT_DIAM = 16.0
E3DV6_OUTUP_H = 3.7
E3DV6_OUTBOT_H = 3.0

# separation of the extruders.
# with the fan, the extruder are about 30mm wide. So 15mm from the center.
# giving 10mm separation, results in 40mm separation
# and total length of 70mm
extrud_sep = 40.0

# DIN-912 bolt dimmensions
# head: the index is the M, i.e: M3, M4, ..., the value is the diameter of the head of the bolt
D912_HEAD_D = {3: 5.5, 4: 7.0, 5: 8.5, 6:10.0, 8:13.0, 10:18.0} 
# length: the index is the M, i.e: M3, M4, ..., the value is the length of the head of the bolt
# well, it is the same as the M, never mind...
D912_HEAD_L =  {3: 3.0,4: 4.0, 5: 5.0,  6:6.0, 8:8.0,  10:10.0} 

# Nut DIN934 dimensions
"""
       ___     _
      /   \    |   s_max: double the apothem
      \___/    |_

   r is the circumradius,  usually called e_min
"""

# the circumdiameter, min value
NUT_D934_D = {3: 6.01, 4: 7.66, 5: 8.79}
# double the apotheme, max value
NUT_D934_2A = {3: 5.5, 4: 7.0,  5: 8.0}
# the heigth, max value
NUT_D934_L  = {3: 2.4, 4: 3.2,  5: 4.0}

# tightening bolt with added tolerances:
# Bolt's head radius
#tbolt_head_r = (tol * d912_head_d[sk_12['tbolt']])/2 
# Bolt's head lenght
#tbolt_head_l = tol * d912_head_l[sk_12['tbolt']] 
# Mounting bolt radius with added tolerance
#mbolt_r = tol * sk_12['mbolt']/2

# ----------------------------- shaft holder SK dimensions --------

SK12 = { 'd':12.0, 'H':37.5, 'W':42.0, 'L':14.0, 'B':32.0, 'S':5.5,
         'h':23.0, 'A':21.0, 'b': 5.0, 'g':6.0,  'I':20.0,
         'mbolt': 5, 'tbolt': 4} 

# ------------------------- T8 Nut for leadscrew ---------------------
#   
#  1.5|3.5| 10  | 
#      __  _____________________________ d_ext: 22
#     |__|
#     |__|   screw_d: 0.35  --- d_screw_pos: 16
#    _|  |______     ________ d_shaft_ext: 10.2
#   |___________|    --- d_T8 (threaded) 
#   |___________|    ---   
#   |_    ______|    ________
#     |__|
#     |__|  -------------------
#     |__|  ____________________________
#
#   
#      10  |3.5| 1.5
#           __  _____________________________ d_flan: 22
#          |__|
#          |__|   screw_d: 0.35  --- d_screw_pos: 16
#    ______|  |_    ________ d_shaft_ext: 10.2
#   |___________|    ___ d_T8 (threaded) 
#   |___________|    ___   
#   |_______   _|    ________
#          |__|
#          |__|  -------------------
#          |__|  ____________________________
#
#          |  |
#           nut_flan_l: 3.5
#   |  nut_l:15  |
#
#              | |
#               T8NUT_SHAFT_OUT: 1.5

T8N_SCREW_D     = 0.35
T8N_D_FLAN      = 22.0
T8N_D_SCREW_POS = 16.0
T8N_D_SHAFT_EXT = 10.2
T8N_D_T8        = 8.0
T8N_L           = 15.0
T8N_FLAN_L      = 3.5
T8N_SHAFT_OUT   = 1.5

# ------------------------- T8 Nut Housing ---------------------

# Box dimensions:
T8NH_L = 30.0
T8NH_W = 34.0
T8NH_H = 28.0

# separation between the screws that attach to the moving part
T8NH_ScrLSep  = 18.0
T8NH_ScrWSep =  24.0

# separation between the screws to the end
T8NH_ScrL2end = (T8NH_L - T8NH_ScrLSep)/2.0
T8NH_ScrW2end = (T8NH_W - T8NH_ScrWSep)/2.0

# Screw dimensions, that attach to the moving part: M4 x 7
T8NH_ScrD = 4.0
T8NH_ScrR = T8NH_ScrD / 2.0
T8NH_ScrL = 7.0

# Screw dimensions, that attach to the Nut Flange: M3 x 10
T8NH_FlanScrD = 3.0
T8NH_FlanScrL = 10.0




