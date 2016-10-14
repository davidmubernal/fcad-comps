# classes that creates objects to be 3D printed

import FreeCAD;
import Part;
import logging
import os
import Draft;
#import copy;
#import Mesh;

# can be taken away after debugging
# directory this file is
filepath = os.getcwd()
import sys
# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath)


import fcfun
import kcomp   # import material constants and other constants
import comps   # import my CAD components

from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, fillet_len
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL


logging.basicConfig(level=logging.DEBUG,
                    format='%(%(levelname)s - %(message)s')

# ---------- class EndShaftSlider ----------------------------------------
# Creates the slider that goes on a rod and supports the end of another
# rod. The slider runs on 2 linear bearings
# The slider is referenced on the slider axis
# Creates both sides, the upper part and the lower part, it also creates the
# linear bearings

#     slidrod_r : radius of the rod where the slider runs on
#     holdrod_r : radius of the rod that this slider holds
#     holdrod_sep : separation between the rods that are holded
#     holdrod_cen : 1: if the piece is centered on the perpendicular 
#     side        : 'left' or 'right' (slidding on axis Y)
#                 : 'bottom' or 'top' (slidding on axis X)
#
#          Y      axis= 'y'    side='left'
#          |
#          |                                  
#          |
#          |
#      ____|_________
#     |  |   |   ____|
#     |  |   |  |____|
#     |  |   |       |
#     |  |   |       |
#     |  |   |       |---------------- X: holdrod_cen = 1
#     |  |   |       |
#     |  |   |   ____|
#     |  |   |  |____|
#     |__|___|_______|________________ X: holdrod_cen = 0
#
#
#
#      ____|_________ __________________________________________ length
#     |  |   |   ____|
#     |  |   |  |____| ----------------------- holdrod_sep
#     |  |   |       |
#     |  |   |       |                        |
#     |  |   |       |
#     |  |   |       |                        |
#     |  |   |   ____|
#     |  |   |  |____|----- holdrod2end --------
#     |__|___|_______|__________________________________________ 
#
#          |    |
#          |----|----> slide2holdrod (+)
#


# --- Atributes:
# length : length of the slider, on the direction of the slidding axis
# width  : width of the slider, on the direction perpendicular to the slidding
#          axis. On the direction of the holding axis
# partheight : heigth of each part of the slider. So the total height will be
#              twice this height
# holdrod_sep : separation between the 2 rods that are holded and forms the 
#               perpendicular axis movement
# slide2holdrod : distance from the sliding rod (axis) to
#                 the beginning of the hold rod (axis). Positive
# slide2holdrod_sign : distance from the sliding rod (axis) to
#                 the beginning of the hold rod (axis). Positive
#                 or negative depending on the sign
# bearings : FreeCad object of the bearings
# top_slide : FreeCad object of the top part of the slider
# bot_slide : FreeCad object of the bottm part of the slider
# base_place: position of the 3 elements: All of them have the same base
#             position.
#             It is (0,0,0) when initialized, it has to be changed using the
#             function base_place

class EndShaftSlider (object):

    # Separation from the end of the linear bearing to the end of the piece
    # on the Heigth dimension (Z)
    OUT_SEP_H = 3.0

    # Minimum separation between the bearings, on the slide direction
    MIN_BEAR_SEP = 3.0

    # Ratio between the the length rod (shaft) is inserted in the slider
    # and the diameter of the holded shaft
    HOLDROD_INS_RATIO = 2.0

    # Radius to chamfer the sides
    CHAMF_R = 2.0

    # Space for the sliding rod, to be added to its radius, and to be cut
    SLIDEROD_SPACE = 1.5

    # tolerance on their length for the bearings. Larger because the holes
    # usually are too tight and it doesn't matter how large is the hole
    #TOL_BEARING_L = 2.0 # printed in black and was too loose
    TOL_BEARING_L = 1.0 # reduced

    MTOL = TOL - 0.1 # reducing the tolrances, it was too tolerant :)
    MLTOL = TOL - 0.05 # reducing the tolrances, it was too tolerant :)

    # Bolts to hold the top and bottom parts:
    BOLT_R = 4
    BOLT_HEAD_R = kcomp.D912_HEAD_D[BOLT_R] / 2.0
    BOLT_HEAD_L = kcomp.D912_HEAD_L[BOLT_R] + MTOL
    BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
    BOLT_SHANK_R_TOL = BOLT_R / 2.0 + MTOL/2.0
    BOLT_NUT_R = kcomp.NUT_D934_D[BOLT_R] / 2.0
    BOLT_NUT_L = kcomp.NUT_D934_L[BOLT_R] + MTOL
    #  1.5 TOL because diameter values are minimum, so they may be larger
    BOLT_NUT_R_TOL = BOLT_NUT_R + 1.5*MTOL

    # Bolts for the pulleys
    BOLTPUL_R = 4
    BOLTPUL_SHANK_R_TOL = BOLTPUL_R / 2.0 + MTOL/2.0
    BOLTPUL_NUT_R = kcomp.NUT_D934_D[BOLTPUL_R] / 2.0
    BOLTPUL_NUT_L = kcomp.NUT_D934_L[BOLTPUL_R] + MTOL
    #  1.5 TOL because diameter values are minimum, so they may be larger
    BOLTPUL_NUT_R_TOL = BOLTPUL_NUT_R + 1.5*MTOL

    XTR_BOT_OUT = 1.0  

    def __init__ (self, slidrod_r, holdrod_r, holdrod_sep, 
                  name, holdrod_cen = 1, side = 'left'):

        doc = FreeCAD.ActiveDocument
        self.base_place = (0,0,0)
        self.slidrod_r = slidrod_r
        self.holdrod_r = holdrod_r
        self.holdrod_sep = holdrod_sep
        self.holdrod_cen = holdrod_cen
    
        self.name        = name
        #self.axis        = axis

        # Separation from the end of the linear bearing to the end of the piece
        # on the width dimension (perpendicular to the movement)
        if self.BOLT_R == 3:
            self.OUT_SEP_W = 8.0
            # on the length dimension (parallel to the movement)
            self.OUT_SEP_L = 10.0
        elif self.BOLT_R == 4:
            self.OUT_SEP_W = 10.0
            self.OUT_SEP_L = 14.0
        else:
            print "not defined"

        bearing_l     = kcomp.LMEUU_L[int(2*slidrod_r)] 
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = kcomp.LMEUU_D[int(2*slidrod_r)]
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL

        holdrod_r_tol =  holdrod_r + self.MLTOL/2.0

        holdrod_insert = self.HOLDROD_INS_RATIO * (2*slidrod_r) 

        self.slide2holdrod = bearing_r + self.MIN_BEAR_SEP 
        if side == 'right' or side == 'top':
            # the distance will be negative, either on the X axis (right)
            # or on the Y axis (top)
            self.slide2holdrod_sign = - self.slide2holdrod
        else:
            self.slide2holdrod_sign = self.slide2holdrod
    
        # calculation of the width
        # dimensions should not depend on tolerances
        slider_w = (  bearing_d     #bearing_d_tol
                    + self.OUT_SEP_W
                    + holdrod_insert
                    + self.MIN_BEAR_SEP )
        self.width = slider_w


        # calculation of the length
        # it can be determined by the holdrod_sep (separation of the hold rods)
        # or by the dimensions of the linear bearings. It will be the largest
        # of these two: 
        # tlen: total length ..
        tlen_holdrod = holdrod_sep + 2 * self.OUT_SEP_L + 2 * holdrod_r
        #tlen_holdrod = holdrod_sep + 2 * self.OUT_SEP_L + 2 * holdrod_r_tol
        #tlen_bearing = (  2 * bearing_l_tol
        tlen_bearing = (  2 * bearing_l
                        + 2* self.OUT_SEP_L
                        + self.MIN_BEAR_SEP)
        if tlen_holdrod > tlen_bearing:
            self.length = tlen_holdrod
            print "length comes from holdrod"
        else:
            self.length = tlen_bearing
            print "length comes from bearing: Check for errors"
       

        self.partheight = (  bearing_r
                           + self.OUT_SEP_H)

        
        # distance from the center of the hold rod to the end on the sliding
        # direction
        self.holdrod2end = (self.length - holdrod_sep)/2

#        if axis == 'x':
#            slid_x = self.length
#            slid_y = self.width
#            slid_z = self.partheight
#        else: # 'y': default
        slid_x = self.width
        slid_y = self.length
        slid_z = self.partheight

        if holdrod_cen == 1:
            # offset if it is centered on the y
            y_offs = - slid_y/2.0
        else:
            y_offs = 0


        slid_posx = - (bearing_r + self.OUT_SEP_W)


        bearing0_pos_y = self.OUT_SEP_L
        # Not bearing_l_tol, because the tol will be added on top and bottom
        # automatically
        bearing1_pos_y = self.length - (self.OUT_SEP_L + bearing_l)
         
        # adding the offset
        bearing0_pos_y = bearing0_pos_y + y_offs
        bearing1_pos_y = bearing1_pos_y + y_offs


        topslid_box = addBox(slid_x, slid_y, slid_z, "todslid_box")
        topslid_box.Placement.Base = FreeCAD.Vector(slid_posx, y_offs, 0)

        botslid_box = addBox(slid_x, slid_y, slid_z, "botslid_box")
        botslid_box.Placement.Base = FreeCAD.Vector(slid_posx, y_offs,
                                                    -self.partheight)

        topslid_chf = fillet_len (topslid_box, slid_z, 
                                  self.CHAMF_R, "topslid_chf")
        botslid_chf = fillet_len (botslid_box, slid_z,
                                  self.CHAMF_R, "botslid_chf")

        # list of elements that cut:
        cutlist = []

        sliderod = fcfun.addCyl_pos (r = slidrod_r + self.SLIDEROD_SPACE,
                               h = slid_y +2,
                               name = "sliderod",
                               axis = 'y',
                               h_disp = y_offs - 1)

        cutlist.append (sliderod)

        h_lmuu_0 = comps.LinBearing (
                         r_ext = bearing_r,
                         r_int = slidrod_r,
                         h     = bearing_l,
                         name  = "lm" + str(int(2*slidrod_r)) + "uu_0",
                         axis  = 'y',
                         h_disp = bearing0_pos_y,
                         r_tol  = self.MLTOL,
                         h_tol  = self.TOL_BEARING_L)

        cutlist.append (h_lmuu_0.bearing_cont)

        h_lmuu_1 = comps.LinBearingClone (
                                      h_lmuu_0,
                                      "lm" + str(int(2*slidrod_r)) + "uu_1",
                                      namadd = 0)
        h_lmuu_1.BasePlace ((0, bearing1_pos_y - bearing0_pos_y, 0))
        cutlist.append (h_lmuu_1.bearing_cont)


        # ------------ hold rods ----------------

        holdrod_0 = fcfun.addCyl_pos (
                                r = holdrod_r_tol,
                                h = holdrod_insert + 1,
                                name = "holdrod_0",
                                axis = 'x',
                                h_disp = bearing_r + self.MIN_BEAR_SEP )
                                #h_disp = bearing_r_tol + self.MIN_BEAR_SEP )

        holdrod_0.Placement.Base = FreeCAD.Vector(
                                     0,
                                     self.holdrod2end + y_offs,
                                     0)
        cutlist.append (holdrod_0)

        holdrod_1 = fcfun.addCyl_pos (
                                r = holdrod_r_tol,
                                h = holdrod_insert + 1,
                                name = "holdrod_1",
                                axis = 'x',
                                h_disp = bearing_r + self.MIN_BEAR_SEP )
                                #h_disp = bearing_r_tol + self.MIN_BEAR_SEP )

        holdrod_1.Placement.Base = FreeCAD.Vector(
                                       0,
                                       self.length - self.holdrod2end + y_offs,
                                       0)
        cutlist.append (holdrod_1)

        # -------------------- bolts and nuts
        bolt0 = addBoltNut_hole (
                            r_shank   = self.BOLT_SHANK_R_TOL,
                            l_bolt    = 2 * self.partheight,
                            r_head    = self.BOLT_HEAD_R_TOL,
                            l_head    = self.BOLT_HEAD_L,
                            r_nut     = self.BOLT_NUT_R_TOL,
                            l_nut     = self.BOLT_NUT_L,
                            hex_head  = 0, extra=1,
                            supp_head = 1, supp_nut=1,
                            headdown  = 0, name="bolt_hole")

        #bolt_left_pos_x =  -(  bearing_r_tol
        bolt_left_pos_x =  -(  bearing_r
                             + self.OUT_SEP_W
                             + sliderod.Base.Radius.Value) / 2.0

        #bolt_right_pos_x =   (  bearing_r_tol
        bolt_right_pos_x =   (  bearing_r
                              + self.MIN_BEAR_SEP
                              + 0.6 * holdrod_insert )

        bolt_low_pos_y =  self.OUT_SEP_L / 2.0 + y_offs
        bolt_high_pos_y =  self.length - self.OUT_SEP_L / 2.0 + y_offs

        bolt_lowmid_pos_y =  1.5 * self.OUT_SEP_L + 2 * holdrod_r + y_offs
        bolt_highmid_pos_y = (  self.length
                             - 1.5 * self.OUT_SEP_L
                             - 2 * holdrod_r  # no _tol
                             + y_offs)

        bolt_pull_pos_x =   (  bearing_r_tol
                              + self.MIN_BEAR_SEP
                              + 0.25 * holdrod_insert )
        #bolt_pullow_pos_y =  2.5 * self.OUT_SEP_L + 2 * holdrod_r_tol + y_offs
        bolt_pullow_pos_y =  2.5 * self.OUT_SEP_L + 2 * holdrod_r + y_offs
        bolt_pulhigh_pos_y = (  self.length
                             - 2.5 * self.OUT_SEP_L
                             - 2 * holdrod_r  # no _tol
                             + y_offs)

        bolt0.Placement.Base = FreeCAD.Vector (bolt_left_pos_x,
                                               self.length/2 + y_offs,
                                               -self.partheight)
        bolt0.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
        cutlist.append (bolt0)

# Naming convention for the bolts
#      ______________ 
#     |lu|   |   _ru_|       right up
#     |  |   |  |____|
#     |  |   |    rmu|       right middle up
#     |  |   | pu    |  pulley up
#     |0 |   | r     | right
#     |  |   | pd    |  pulley down
#     |  |   |   _rmd|       right middle down
#     |  |   |  |____|
#     |ld|___|____rd_|       right down
#       
        # Right
        boltr = Draft.clone(bolt0)
        boltr.Label = "bolt_hole_r"
        boltr.Placement.Base =  FreeCAD.Vector (-bolt_left_pos_x,
                                                self.length/2 + y_offs,
                                               -self.partheight)
        boltr.Placement.Rotation = FreeCAD.Rotation (VZ, 30)
        cutlist.append (boltr)


        # Left Up
        boltlu = Draft.clone(bolt0)
        boltlu.Label = "bolt_hole_lu"
        boltlu.Placement.Base =  FreeCAD.Vector (bolt_left_pos_x,
                                                bolt_low_pos_y,
                                               -self.partheight)
        boltlu.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltlu)
        
        # Left Down
        boltld = Draft.clone(bolt0)
        boltld.Label = "bolt_hole_ld"
        boltld.Placement.Base =  FreeCAD.Vector (bolt_left_pos_x,
                                                bolt_high_pos_y,
                                               -self.partheight)
        boltld.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltld)

        # Right Up 
        boltru = Draft.clone(bolt0)
        boltru.Label = "bolt_hole_ru"
        boltru.Placement.Base =  FreeCAD.Vector (bolt_right_pos_x,
                                                bolt_high_pos_y,
                                               -self.partheight)
        boltru.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltru)

        # Right Down
        boltrd = Draft.clone(bolt0)
        boltrd.Label = "bolt_hole_rd"
        boltrd.Placement.Base =  FreeCAD.Vector (bolt_right_pos_x,
                                                bolt_low_pos_y,
                                               -self.partheight)
        boltrd.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltrd)

        # Right Middle Up 
        boltrmu = Draft.clone(bolt0)
        boltrmu.Label = "bolt_hole_rmu"
        boltrmu.Placement.Base =  FreeCAD.Vector (bolt_right_pos_x,
                                                  bolt_highmid_pos_y,
                                                 -self.partheight)
        boltrmu.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltrmu)

        # Right Middle Down
        boltrmd = Draft.clone(bolt0)
        boltrmd.Label = "bolt_hole_rmd"
        boltrmd.Placement.Base =  FreeCAD.Vector (bolt_right_pos_x,
                                                bolt_lowmid_pos_y,
                                               -self.partheight)
        boltrmd.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltrmd)

        # Pulley bolt       
        boltpull0 = addBolt (
                            r_shank   = self.BOLTPUL_SHANK_R_TOL,
                            l_bolt    = 2 * self.partheight,
                            r_head    = self.BOLTPUL_NUT_R_TOL,
                            l_head    = self.BOLTPUL_NUT_L,
                            hex_head  = 1, extra=1,
                            support = 1, 
                            headdown  = 1, name="boltpul_hole")

        boltpull0.Placement.Base =  FreeCAD.Vector (bolt_pull_pos_x,
                                                    bolt_pulhigh_pos_y,
                                                   -self.partheight)
        boltpull0.Placement.Rotation = FreeCAD.Rotation (VZ, 30)
        cutlist.append (boltpull0)

        # Pulley Down
        boltpull1 = Draft.clone(boltpull0)
        boltpull1.Label = "boltpul_hole_1"
        boltpull1.Placement.Base =  FreeCAD.Vector (bolt_pull_pos_x,
                                                    bolt_pullow_pos_y,
                                                   -self.partheight)
        boltpull1.Placement.Rotation = FreeCAD.Rotation (VZ, 30)
        cutlist.append (boltpull1)

        # --- make a dent in the interior to save plastic
        # points: p dent

        pdent_ur = FreeCAD.Vector ( self.width + slid_posx + 1,
                                    bolt_highmid_pos_y - 1,
                                   -self.partheight - 1)
        pdent_ul = FreeCAD.Vector ( bolt_pull_pos_x + 1,
                                    bolt_pulhigh_pos_y - self.OUT_SEP_L ,
                                   -self.partheight - 1)
        pdent_dr = FreeCAD.Vector ( self.width + slid_posx + 1,
                                    bolt_lowmid_pos_y +1,
                                   -self.partheight - 1)
        pdent_dl = FreeCAD.Vector ( bolt_pull_pos_x + 1,
                                    bolt_pullow_pos_y + self.OUT_SEP_L ,
                                   -self.partheight - 1)

        pdent_list = [ pdent_ur, pdent_ul, pdent_dl, pdent_dr]

        dent_plane = doc.addObject("Part::Polygon", "dent_plane")
        dent_plane.Nodes = pdent_list
        dent_plane.Close = True
        dent_plane.ViewObject.Visibility = False
        dent = doc.addObject("Part::Extrusion", "dent")
        dent.Base = dent_plane
        dent.Dir = (0,0, 2*self.partheight +2)
        dent.Solid = True
        cutlist.append (dent)

        holes = doc.addObject("Part::MultiFuse", "holes")
        holes.Shapes = cutlist


        if side == 'right':
            holes.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
            topslid_chf.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
            botslid_chf.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
            # h_lmuu_0.bearing. bearings stay the same
            if holdrod_cen == False:
                holes.Placement.Base = FreeCAD.Vector (0, self.length,0)
                topslid_chf.Placement.Base = FreeCAD.Vector (0, self.length,0)
                botslid_chf.Placement.Base = FreeCAD.Vector (0, self.length,0)
        elif side == 'bottom':
            holes.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
            topslid_chf.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
            botslid_chf.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
            h_lmuu_0.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, 90)
            # lmuu_1 has relative position to lmuu_0, so if rotating it
            # to the other side and reseting its position will put it in its
            # place
            if holdrod_cen == True:
                h_lmuu_1.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, -90)
                h_lmuu_1.bearing.Placement.Base = FreeCAD.Vector (0,0,0)
            if holdrod_cen == False:
                holes.Placement.Base = FreeCAD.Vector (self.length,0,0)
                topslid_chf.Placement.Base = FreeCAD.Vector (self.length,0,0)
                botslid_chf.Placement.Base = FreeCAD.Vector (self.length,0,0)
                h_lmuu_0.bearing.Placement.Base = FreeCAD.Vector (
                                                          self.length,0,0)
                h_lmuu_1.bearing.Placement.Base = FreeCAD.Vector (
                            self.length - h_lmuu_1.bearing.Placement.Base.y ,0,0)
                h_lmuu_1.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, 90)
        elif side == 'top':
            holes.Placement.Rotation = FreeCAD.Rotation (VZ, -90)
            topslid_chf.Placement.Rotation = FreeCAD.Rotation (VZ, -90)
            botslid_chf.Placement.Rotation = FreeCAD.Rotation (VZ, -90)
            h_lmuu_0.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, -90)
            # lmuu_1 has relative position to lmuu_0, so if rotating it
            # to the other side and reseting its position will put it in its
            # place
            if holdrod_cen == True:
                h_lmuu_1.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, 90)
                h_lmuu_1.bearing.Placement.Base = FreeCAD.Vector (0,0,0)
            if holdrod_cen == False:
                #holes.Placement.Base = FreeCAD.Vector (self.length,0,0)
                #topslid_chf.Placement.Base = FreeCAD.Vector (self.length,0,0)
                #botslid_chf.Placement.Base = FreeCAD.Vector (self.length,0,0)
                #h_lmuu_0.bearing.Placement.Base = FreeCAD.Vector (
                                                          #self.length,0,0)
                h_lmuu_1.bearing.Placement.Base = FreeCAD.Vector (
                                         h_lmuu_1.bearing.Placement.Base.y ,0,0)
                h_lmuu_1.bearing.Placement.Rotation = FreeCAD.Rotation (VZ, -90)


        # elif side == 'left':
            # don't do anything, default condition

        bearings = doc.addObject("Part::Fuse", name + "_bear")
        bearings.Base = h_lmuu_0.bearing
        bearings.Tool = h_lmuu_1.bearing
        self.bearings = bearings

        top_slide = doc.addObject("Part::Cut", name + "_top")
        top_slide.Base = topslid_chf 
        top_slide.Tool = holes 
        self.top_slide = top_slide

        bot_slide = doc.addObject("Part::Cut", name + "_bot")
        bot_slide.Base = botslid_chf 
        bot_slide.Tool = holes 
        self.bot_slide = bot_slide

    # ---- end of __init__  EndShaftSlider

    # move both sliders (top & bottom) and the bearings
    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        self.bearings.Placement.Base = FreeCAD.Vector(position)
        self.top_slide.Placement.Base = FreeCAD.Vector(position)
        self.bot_slide.Placement.Base = FreeCAD.Vector(position)
        


"""

    # Move the bearing and its container
    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        self.bearing.Placement.Base = FreeCAD.Vector(position)
        self.bearing_cont.Placement.Base = FreeCAD.Vector(position)
"""




