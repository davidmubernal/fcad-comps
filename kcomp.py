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

