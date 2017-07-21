# ----------------------------------------------------------------------------
# -- Parts to print
# -- comps library
# -- Python FreeCAD functions and classes that groups components
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronics. Rey Juan Carlos University (urjc.es)
# -- November-2016
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

import FreeCAD;
import Part;
import Draft;
import DraftVecUtils
import logging

# ---------------------- can be taken away after debugging
import os
# directory this file is
filepath = os.getcwd()
import sys
# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath)
# ---------------------- can be taken away after debugging

import kcomp 
import fcfun
import comps
import kparts

from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, addCyl_pos, fillet_len
from fcfun import VXN, VYN, VZN
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL



logging.basicConfig(level=logging.DEBUG,
                    format='%(%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ----------- class IdlePulleyHolder ---------------------------
# Creates a holder for a IdlePulley. Usually made of bolts, washers and bearings
# It may include a space for a endstop
# It is centered at the idle pulley, but at the back, and at the profile height
#
#          hole for endstop
#         /   []: hole for the nut
#       ________  ___ 
#      ||__|    |    + above_h
#   ___|     [] |____:__________  Z=0
#      |        |      :         aluminum profile
#      | O    O |      :
#      |________|      + profile_size
#   __________________:________
#
#        O: holes for bolts to attach to the profile
#                 
#               Z 
#               :
#        _______:__ ...
#       /         /|   :
#      /________ / |   :
#      ||__|    |  |   + height
#      |     [] |  |   :
#      |        |  | ..:
#      | O    O | /    
#      |________|/.. + depth 
#      :        :
#      :........:
#          + width
#
#   attach_dir = '-y'  enstop_side= 1     TOP VIEW
#
#
#                Y
#                :                
#                :
#              __:_________
#             |  :   |__| |
#             | (:)       |
#          ...|__:________|..... X
#
# ----- Arguments:
# profile_size: size of the aluminum profile. 20mm, 30mm
# pulleybolt_d: diameter of the bolt used to hold the pulley
# holdbolt_d: diameter of the bolts used to attach this part to the aluminum
#   profile
# above_h: height of this piece above the aluminum profile
# mindepth: If there is a minimum depth. Sometimes needed for the endstop
#            to reach its target
# attach_dir: Normal vector to where the holder is attached:'x','-x','y','-y'
#             NOW ONLY -y IS SUPPORTED. YOU CAN ROTATE IT
# endstop_side: -1, 0, 1. Side where the enstop will be
#                if attach_dir= 'x', this will be referred to the y axis 
#                if 0, there will be no endstop
# endstop_h: height of the endstop. If 0 it will be just on top of the profile
# ----- Attributes:
# depth    : depth of the holder
# width    : depth of the holder
# height    : depth of the holder
# fco      : cad object of the compound

class IdlePulleyHolder (object):

    def __init__ (self, profile_size, pulleybolt_d, holdbolt_d, above_h,
                  mindepth = 0,
                  attach_dir = '-y', endstop_side = 0,
                  endstop_posh = 0,
                  name = "idlepulleyhold"):

        doc = FreeCAD.ActiveDocument

        self.profile_size = profile_size
        self.pulleybolt_d = pulleybolt_d
        self.holdbolt_d   = holdbolt_d
        self.above_h      = above_h

        
        # extra width on each side of the nut
        extra_w = 4.
        # ----------------- Depth calculation
        pulleynut_d = kcomp.NUT_D934_D[int(pulleybolt_d)]
        pulleynut_d_tol = pulleynut_d + 3*TOL
        pulleydepth = pulleynut_d + 2 * extra_w
        depth = max(pulleydepth, mindepth)
        if endstop_side != 0:
            extra_endstop = 3.
            endstop_l =  kcomp.ENDSTOP_B['L']
            endstop_ht =  kcomp.ENDSTOP_B['HT']
            endstop_h =  kcomp.ENDSTOP_B['H']
            endstopdepth = endstop_ht + extra_endstop + extra_w
            depth = max (endstopdepth, depth)
            endstop_boltsep = kcomp.ENDSTOP_B['BOLT_SEP']
            endstop_bolt_h = kcomp.ENDSTOP_B['BOLT_H']
            endstop_bolt_d = kcomp.ENDSTOP_B['BOLT_D']
            # distance of the bolt to the end
            endstop_bolt2lend = (endstop_l - endstop_boltsep)/2.
            # distance of the bolt to the topend
            endstop_bolt2hend = endstop_h - endstop_bolt_h
        self.depth = depth

        # ----------------- Width calculation
        holdbolthead_d = kcomp.D912_HEAD_D[int(holdbolt_d)]
        # the minimum width due to the holding bolts
        minwidth_holdbolt = 2 * holdbolthead_d + 4*extra_w
        # the minimum width due to the endstop
        if endstop_side == 0:
            endstop_l = 0
            endstop_ht = 0
            minwidth_endstop = 0
        else:
            minwidth_endstop = (  endstop_l
                                + 2*TOL
                                + pulleynut_d_tol
                                + 3*extra_w )
        width = max(minwidth_holdbolt, minwidth_endstop)
        self.width = width

        # ----------------- Height calculation
        base_h = .9 * profile_size # no need to go all the way down
        height = base_h + above_h
        self.height = height

#   attach_dir = '-y'  enstop_side= 1
#
#
#                Y
#                :                
#                :
#       p10    __:_________ p11
#             |  :   |__| |
#             | (:)       |        depth
#          ...|__:________|..... X
#           p00          p01 
#                 width
#                :
#      
#                      Y
#                      :
#       p11    ________:__ p01
#             | |__|   :  |
#             |       (:) |        depth
#          ...|________:__|..... X
#           p10          p00 
#                 width


        # Constants to dimensions
        # holding bolts that will be shank in the piece, the rest will be
        # for the head
        bolt_shank = 5.
        
        # holes for the holding bolts
        # separation from the center of the hole to the end
        hbolt_endsep =  extra_w + holdbolthead_d/2.
        # separation between the holding bolts
        hbolt_sep = width - 2 * ( extra_w + holdbolthead_d/2.)
        
        # Nut for the pulley bolt
        pulleynut_h = kcomp.NUT_D934_L[int(pulleybolt_d)]
        pulleynut_hole_h = kcomp.NUT_HOLE_MULT_H * pulleynut_h
        # height inside the piece of the pulley bolt
        # adding 1 to give enough space to the 25mm bolt, it was to tight
        pulleybolt_h = 2 * extra_w + pulleynut_hole_h +1

        if attach_dir == '-y':
            if endstop_side == 0:
                p0x = - width/2.
                p1x = + width/2.
                sg = 1 #sign
            else:
                sg = endstop_side # sign
                p0x = sg * (- pulleynut_d_tol/2. - extra_w)
                p1x =  p0x + sg * width
            p00 = FreeCAD.Vector ( p0x, 0, - base_h)
            p01 = FreeCAD.Vector ( p1x, 0, - base_h)
            p11 = FreeCAD.Vector ( p1x, depth, - base_h)
            p10 = FreeCAD.Vector ( p0x, depth, - base_h)


            shp_wire_base = Part.makePolygon([p00,p01, p11, p10, p00])
            shp_face_base = Part.Face(shp_wire_base)
            shp_box = shp_face_base.extrude(FreeCAD.Vector(0,0,height))



            hbolt_p0x = p0x + sg * hbolt_endsep
            #shank of holding bolt
            pos_shank_hbolt0 = FreeCAD.Vector(hbolt_p0x,
                                              -1,
                                             -profile_size/2.)
            shp_shank_hbolt0 = fcfun.shp_cyl ( r = holdbolt_d/2. + TOL,
                                               h= bolt_shank + 2, normal = VY,
                                               pos = pos_shank_hbolt0)
            if depth > bolt_shank :
                pos_head_hbolt0 = FreeCAD.Vector(hbolt_p0x,
                                                 bolt_shank,
                                                 -profile_size/2.)
                shp_head_hbolt0 = fcfun.shp_cyl (
                                           r = holdbolthead_d/2. + TOL,
                                           h = depth - bolt_shank + 1,
                                           normal = VY,
                                           pos = pos_head_hbolt0)
                shp_hbolt0 = shp_shank_hbolt0.fuse(shp_head_hbolt0)
            else: # no head
                shp_hbolt0 = shp_shank_hbolt0 
            shp_hbolt1 = shp_hbolt0.copy()
            # It is in zero
            shp_hbolt1.Placement.Base.x = sg * hbolt_sep

            # hole for the pulley bolt
            pulleybolt_pos = FreeCAD.Vector (0, depth - pulleydepth/2.,
                                             above_h - pulleybolt_h)
            shp_pulleybolt = fcfun.shp_cyl (r = pulleybolt_d/2. + 0.9*TOL/2,
                                            h = pulleybolt_h + 1,
                                            normal = VZ,
                                            pos = pulleybolt_pos)
                                            
            holes_list = [shp_hbolt0, shp_hbolt1]
            # hole for the nut:

            # hole for the endstop
            if endstop_side != 0:
                #endstopbox_l = endstop_l + 2*TOL
                #endstopbox_w = endstop_ht + extra_endstop + TOL
                endstopbox_l = endstop_l + 2*TOL + extra_w + 1
                endstopbox_w = depth + 2
                #endstop_posx = p1x + sg*(extra_w + endstopbox_l/2.)
                endstop_posx = p1x - sg*(endstopbox_l/2. -1)
                endstop_posy = (depth - endstopbox_w )
                #endstop_posy = (depth - endstopbox_w )
                endstop_posy = -1

                endstop_pos = FreeCAD.Vector(endstop_posx, endstop_posy,
                                             endstop_posh)
                shp_endstop = fcfun.shp_boxcen(x=endstopbox_l,
                                               y=endstopbox_w,
                                               z=above_h-endstop_posh +1,
                                               cx=1,
                                               pos=endstop_pos)
                holes_list.append(shp_endstop)

                # hole for the bolts of the endstop
                endstopbolt0_pos = FreeCAD.Vector(
                                  endstop_posx - endstop_boltsep/2.,
                                  depth - endstop_bolt2hend,
                                  endstop_posh + 1)
                shp_endstopbolt0 = fcfun.shp_cyl (
                                        r= endstop_bolt_d/2. + TOL/2.,
                                        h = extra_w + 1,
                                        normal = fcfun.VZN,
                                        pos=endstopbolt0_pos)
                holes_list.append(shp_endstopbolt0)
                shp_endstopbolt1 = shp_endstopbolt0.copy()
                shp_endstopbolt1.Placement.Base.x = endstop_boltsep
                holes_list.append(shp_endstopbolt1)

            shp_holes = shp_pulleybolt.multiFuse(holes_list)
            shp_pulleyhold = shp_box.cut(shp_holes)

            pulleyhold_aux = doc.addObject("Part::Feature", name + '_aux')
            pulleyhold_aux.Shape = shp_pulleyhold

            # fillet the top part if it has no endstop. So the belt doesnt
            # hit the corner
            if endstop_side == 0:
                fillet_r = (width - pulleynut_d_tol - 2 * extra_w) / 2.
                pulleyhold_aux = fcfun.filletchamfer(
                                       fco = pulleyhold_aux,
                                       e_len = depth,
                                       name = name + '_chmf',
                                       fillet = 1,
                                       radius = fillet_r,
                                       axis = 'y',
                                       zpos_chk = 1,
                                       zpos = above_h)
                                          


            h_nuthole = fcfun.NutHole (nut_r = pulleynut_d_tol/2.,
                                       nut_h = pulleynut_hole_h,
                                       hole_h = pulleydepth/2. + TOL,
                                       name = name + '_nuthole',
                                       extra = 1,
                                       nuthole_x = 0,
                                       cx = 1, cy = 0, holedown = 0)
            nuthole = h_nuthole.fco
            nuthole.Placement.Rotation = FreeCAD.Rotation(VX,-90)
            nuthole.Placement.Base.y = depth - pulleydepth/2. - TOL
            nuthole.Placement.Base.z = above_h - extra_w
            
            pulley_holder = doc.addObject("Part::Cut", name)
            pulley_holder.Base = pulleyhold_aux    
            pulley_holder.Tool = nuthole    

            self.fco = pulley_holder

        doc.recompute()
            
            
        
"""

doc = FreeCAD.newDocument()

idp = IdlePulleyHolder( profile_size=30.,
                        pulleybolt_d=3.,
                        holdbolt_d = 5,
                        above_h = 37.,
                        mindepth = 27.5,
                        attach_dir = '-y',
                        endstop_side = 0,
                        endstop_posh = 9.,
                        name = "idlepulleyhold")
"""




# Holder for the endstop to be attached to the rail of SEB15A_R
# Made fast and with hardcoded constants, no parametric


def endstopholder_rail ():

    in_w = kcomp.SEB15A_R['rw']
    add_w = 4.
    #out_w = in_w + 2 * add_w
    out_w = 36.

    ends_d = 6.  #endstop depth
    supp_d = 12.5 # support depth

    total_d = supp_d - ends_d + add_w

    bolt_h = 18.
    extra_h = 5.

    total_h = bolt_h + extra_h + add_w
    obox = fcfun.shp_boxcenfill(out_w, total_d, total_h, 1,
                                cx=1, cy=0, cz=0)


    ibox = fcfun.shp_boxcen(in_w + 1.5 * TOL, add_w + 1, total_h + 2,
                            cx=1, cy=0, cz=0, pos = FreeCAD.Vector(0, -1,-1))


    endsbolt2top = 7. # distance of the endstop bolt to the top
    endsboltsep = 9.6 # distance between endstop bolts
    endsbolt_depth = 5.5 # depth of the holes
    endsbolt_diam = 2.5 # diameter

    ends_bolt_pos0 = FreeCAD.Vector ( endsboltsep/2., total_d +1,
                                      total_h - endsbolt2top)
    ends_bolt0 = fcfun.shp_cyl (r=endsbolt_diam/2.+TOL/2.,
                                h = endsbolt_depth +1,
                                normal = VYN,
                                pos = ends_bolt_pos0) 
    ends_bolt_pos1 = FreeCAD.Vector ( -endsboltsep/2.,
                                       total_d +1,
                                       total_h - endsbolt2top)
    ends_bolt1 = fcfun.shp_cyl (r=endsbolt_diam/2.+TOL/2.,
                                h = endsbolt_depth +1,
                                normal = VYN,
                                pos = ends_bolt_pos1) 

    ends_bolt_pos00 = FreeCAD.Vector ( endsboltsep*1.5,
                                       total_d +1,
                                       total_h - endsbolt2top)
    ends_bolt00 = fcfun.shp_cyl (r=endsbolt_diam/2.+TOL/2.,
                                 h = endsbolt_depth +1,
                                 normal = VYN,
                                 pos = ends_bolt_pos00) 
    ends_bolt_pos11 = FreeCAD.Vector ( -endsboltsep*1.5,
                                        total_d +1,
                                        total_h - endsbolt2top)

    ends_bolt11 = fcfun.shp_cyl (r=endsbolt_diam/2.+TOL/2.,
                                 h = endsbolt_depth +1,
                                 normal = VYN,
                                 pos = ends_bolt_pos11) 



    railbolt_d = 3.

    railbolt = fcfun.shp_boxcenfill ( x=railbolt_d + 0.8*TOL,
                                      y= total_d + 2,
                                      z = railbolt_d + extra_h,
                                      fillrad = railbolt_d/2.,
                                      fx = 0, fy=1, fz=0,
                                      cx=1, cy=0, cz=0,
                                      pos = FreeCAD.Vector(0, -1, add_w))


    railbolthead_d = kcomp.D912_HEAD_D[int(railbolt_d)]

    railbolt_head_pos =  FreeCAD.Vector(
                                     0,
                                     add_w+3,
                                     add_w-railbolthead_d/2. + railbolt_d/2. )

    railbolt_head = fcfun.shp_boxcenfill (x=railbolthead_d + TOL,
                                          y= total_d + 2,
                                          z = railbolthead_d + extra_h,
                                          fillrad = railbolthead_d/2.,
                                          fx = 0, fy=1, fz=0,
                                          cx=1, cy=0, cz=0,
                                          pos = railbolt_head_pos)

    shp_fusecut = ibox.multiFuse([ends_bolt0, ends_bolt1,
                                  ends_bolt00, ends_bolt11,
                                  railbolt, railbolt_head])

    box = obox.cut(shp_fusecut)
    #Part.show (box)
    return (box)
            

# ----------- thin linear bearing housing with one rail to be attached

class ThinLinBearHouse (object):

    """

        Makes a housing for a linear bearing, but it is very thin
        and intented to be attached to one rail, instead of 2
        it has to parts, the lower and the upper part

         ________                           ______________
        | ::...::|                         | ::........:: |
        | ::   ::|    Upper part           |.::        ::.|
        |-::( )::|------                   |.::        ::.|  --> fc_slide_axis
        | ::...::|    Lower part           | ::........:: | 
        |_::___::|                   ______| ::        :: |______
        |_::|_|::|                  |__:_:___::________::__:_:__|
                                                   :
         _________                                 :
        |____O____|                                v
        |  0: :0  |                            fc_bot_axis
        | :     : |
        | :     : |
        | :     : |
        | :.....: |
        |__0:_:0__|
        |____O____|
        
         ________                           ______________
        | ::...::|                         | ::........:: |
        | ::   ::|    Upper part           |.::        ::.|
        |-::( )::|------                   |.::   *axis_center = 1
        | ::...::|    Lower part           | ::........:: | 
        |_::___::|                   ______| ::        :: |______
        |_::|_|::|                  |__:_:___::___*____::__:_:__|
             |                                   axis_center = 0
             |
             V
           always centered in this axis

                                            ______________
        1: axis_center=1                   | ::........:: |
           mid_center =1                   |.::        ::.|
        2: axis_center=0                4  |.::   1 --> fc_slide_axis
           mid_center =1                   | ::........:: | 
        3: axis_center=0             ______| ::        :: |______
           mid_center =0             |_:3:___::___2____::__:_:__|
        4: axis_center=1
           mid_center =0


    Arguments:
        d_lbear: dictionary with the dimensions of the linear bearing
        fc_slide_axis : FreeCAD.Vector with the direction of the slide
        fc_bot_axis: FreCAD.Vector with the direction of the bottom
        axis_center = See picture, indicates the reference point
        mid_center  = See picture, indicates the reference point
        pos = position of the reference point,

    Useful Attributes:
        n1_slide_axis: FreeCAD.Vector
        n1_bot_axis: FreeCAD.Vector
        n1_perp: FreeCAD.Vector
        slideaxisbot_dist: float
        boltcen_axis_dist: float
        boltcen_perp_dist: float
        + --- Dimensions:
        tot_h, tot_w, tot_l
        housing_l, base_h
        + --- FreeCAD objects
        fco_top = top part of the linear bearing housing
        fco_bot = bottom part of the linear bearing housing

           ________                           ______________
          | ::...::|                         | ::........:: |
          | ::   ::|                         |.::        ::.|
          |-::( )::|---:                     |.::        ::.|  --> n1_slide_axis
          | ::...::|   +slideaxisbot_dist    | ::........:: | 
          |_::___::|   :               ______| ::        :: |______
          |_::|_|::|...:              |__:_:___::________::__:_:__|
                                                     :
           _________                                 v
          |____O____|                              n1_bot_axis
          |  0: :0  |----              
          | :     : |   :
          | :     : |   + boltcen_axis_dist ..            --> n1_perp
          | :     : |   :                    :
          | :.....: |   :                    + centbolt_dist
          |__0:_:0__|----                    :
          |____O____|------------------------:
             :   :
             :   :
             :...:
               +boltcen_perp_dist
         
                                             ....housing_l..
                                             :              :
           ________....                      :______________:
          | ::...::|   :                     | ::........:: |
          | ::   ::|   :                     |.::        ::.|
          |-::( )::|   :                     |.::        ::.|  --> n1_slide_axis
          | ::...::|   +tot_h                | ::........:: | 
          |_::___::|   :           ... ______| ::        :: |______
          |_::|_|::|...:    base_h ...|__:_:___::________::__:_:__|
          :        :                  :                           :
          :........:                  :...........................:
              +                                      +
             tot_w                                 tot_l       

    """

    MIN_SEP_WALL = 3. # min separation of a wall
    MIN2_SEP_WALL = 2. # min separation of a wall
    OUT_SEP_H = kparts.OUT_SEP_H
    MTOL = kparts.MTOL
    MLTOL = kparts.MLTOL
    TOL_BEARING_L = kparts.TOL_BEARING_L
    # Radius to fillet the sides
    FILLT_R = kparts.FILLT_R

    def __init__(self, d_lbear,
                 fc_slide_axis = VX,
                 fc_bot_axis =VZN,
                 axis_center = 1,
                 mid_center  = 1,
                 pos = V0,
                 name = 'thinlinbearhouse'
                ):

        # normalize, just in case
        n1_slide_axis = DraftVecUtils.scaleTo(fc_slide_axis,1)
        n1_bot_axis = DraftVecUtils.scaleTo(fc_bot_axis,1)
        n1_bot_axis_neg = DraftVecUtils.neg(n1_bot_axis)
        # vector perpendicular to the others
        n1_perp = n1_slide_axis.cross(n1_bot_axis)


        self.rod_r = d_lbear['Di']/2.
        rod_r = self.rod_r
        self.bear_r = d_lbear['Di']
        if rod_r >= 6:
            BOLT_D = 4
        else:
            BOLT_D = 3  # M3 bolts

        doc = FreeCAD.ActiveDocument

        MIN_SEP_WALL = self.MIN_SEP_WALL
        MIN2_SEP_WALL = self.MIN2_SEP_WALL
        OUT_SEP_H = self.OUT_SEP_H
        # bolt dimensions:
        MTOL = self.MTOL
        MLTOL = self.MLTOL
        BOLT_HEAD_R = kcomp.D912_HEAD_D[BOLT_D] / 2.0
        BOLT_HEAD_L = kcomp.D912_HEAD_L[BOLT_D] + MTOL
        BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
        BOLT_SHANK_R_TOL = BOLT_D / 2.0 + MTOL/2.0
        BOLT_NUT_R = kcomp.NUT_D934_D[BOLT_D] / 2.0
        BOLT_NUT_L = kcomp.NUT_D934_L[BOLT_D] + MTOL
        #  1.5 TOL because diameter values are minimum, so they may be larger
        BOLT_NUT_R_TOL = BOLT_NUT_R + 1.5*MTOL

        # bearing dimensions:
        bearing_l     = kcomp.LMEUU_L[int(2*rod_r)] 
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = kcomp.LMEUU_D[int(2*rod_r)]
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL

        #There are two basic pieces: the base and the housing for the linear
        # bearing
        # dimensions of the housing:
        # length on the direction of the sliding rod
        bolt2wall = fcfun.get_bolt_end_sep(BOLT_D, hasnut=1) 
        #housing_l = bearing_l_tol + 2 * (2*BOLT_HEAD_R_TOL + 2* MIN_SEP_WALL)
        housing_l = bearing_l_tol + 2 * (2* bolt2wall)
        print "housing_l: %", housing_l
        # width of the housing (very tight)
        housing_w = max ((bearing_d_tol + 2* MIN_SEP_WALL), 
                         (d_lbear['Di'] + 4* MIN2_SEP_WALL + 2*BOLT_D))
        print "housing_w: %", housing_w

        # dimensions of the base:
        # length on the direction of the sliding rod
        base_l = housing_l +  4* MIN_SEP_WALL + 4 * BOLT_HEAD_R_TOL
        print "base_l: %", base_l
        # width of the base (very tight), the same as the housing
        base_w = housing_w
        print "base_w: %", base_w
        # height of the base (not tight). twice the mininum height
        base_h = 2 * OUT_SEP_H 
        print "base_h: %", base_h

        # height of the housing (not tight, can be large)
        housing_h = base_h +  2* BOLT_HEAD_L + bearing_d_tol
        print "housing_h: %", housing_h


        # distance on the slide_axis from midcenter=0 to midcenter 1.
        centbolt_dist = housing_l/2. + BOLT_HEAD_R_TOL + MIN_SEP_WALL
        # distance on the bot_axis from the rod to the bottom
        # the base and the housing are overlapped.
        # Not taking the tolerance
        #slideaxisbot_dist = bearing_d/2. + 2 * OUT_SEP_H + BOLT_HEAD_L
        slideaxisbot_dist = ( rod_r + kparts.ROD_SPACE_MIN + base_h
                             + 2 * BOLT_HEAD_L)

        #To make the boxes, we take the reference on midcenter=1 and 
        # axis_center = 0. Point 2 on the drawing

        if mid_center == 0:
            # get the vector to the center:
            fc_tomidcenter = DraftVecUtils.scale(n1_slide_axis,centbolt_dist)
        else:
            fc_tomidcenter = V0
        if axis_center == 1:
            fc_tobottom = DraftVecUtils.scale(n1_bot_axis,slideaxisbot_dist)
            fc_toaxis = V0
        else:
            fc_tobottom = V0
            fc_toaxis = DraftVecUtils.scale(n1_bot_axis,-slideaxisbot_dist)

        botcenter_pos = pos + fc_tomidcenter + fc_tobottom

        # point 1 on the drawing
        axiscenter_pos = pos + fc_tomidcenter + fc_toaxis

        shp_base = fcfun.shp_box_dir(box_w = base_w,
                                     box_d = base_l, #dir of n1_slide_axis
                                     box_h = base_h,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = botcenter_pos)

        # fillet the base:
        shp_base_fllt = fcfun.shp_filletchamfer_dir(shp_base,
                                                    fc_axis=fc_bot_axis,
                                                    radius=kparts.FILLT_R)


        shp_housing = fcfun.shp_box_dir(box_w = housing_w,
                                     box_d = housing_l, #dir of n1_slide_axis
                                     box_h = housing_h,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = botcenter_pos)
        #Part.show(shp_housing)

        shp_block = shp_base_fllt.fuse(shp_housing)

        # the rod hole
        shp_rod = fcfun.shp_cylcenxtr(r = rod_r + kparts.ROD_SPACE_MIN,
                                      h = base_l,
                                      normal = n1_slide_axis,
                                      ch = 1, xtr_top = 1, xtr_bot=1,
                                      pos = axiscenter_pos)
        # the linear bearing hole
        shp_lbear = fcfun.shp_cylcenxtr(r = bearing_r_tol,
                                        h = bearing_l_tol,
                                        normal = n1_slide_axis,
                                        ch = 1, xtr_top = 1, xtr_bot=1,
                                        pos = axiscenter_pos)
        shp_rodlbear = shp_rod.fuse(shp_lbear)
        shp_block_hole = shp_block.cut(shp_rodlbear)

        # bolts to atach to the support
        
        bolt1_atch_pos = (  botcenter_pos
                           + DraftVecUtils.scale(n1_slide_axis,centbolt_dist))
        bolt2_atch_pos = (  botcenter_pos
                           + DraftVecUtils.scale(n1_slide_axis,-centbolt_dist))

        shp_bolt1_atch = fcfun.shp_cylcenxtr(r=BOLT_SHANK_R_TOL,
                                             h = base_h,
                                             normal = n1_bot_axis_neg,
                                             ch = 0, xtr_top = 1, xtr_bot = 1,
                                             pos = bolt1_atch_pos)
        shp_bolt2_atch = fcfun.shp_cylcenxtr(r=BOLT_SHANK_R_TOL,
                                             h = base_h,
                                             normal = n1_bot_axis_neg,
                                             ch = 0, xtr_top = 1, xtr_bot = 1,
                                             pos = bolt2_atch_pos)
        bolt_holes = [shp_bolt2_atch]

        # 4 bolts to join the upper and lower parts
        # distance of the bolts to the center, on n1_slide_axis dir
        boltcen_axis_dist = housing_l/2. - bolt2wall
        # distance of the bolts to the center, on n1_perp dir
        boltcen_perp_dist = housing_w/2. - bolt2wall



        for vec_axis in [DraftVecUtils.scale(n1_slide_axis,boltcen_axis_dist),
                         DraftVecUtils.scale(n1_slide_axis,-boltcen_axis_dist)]:
            for vec_perp in [DraftVecUtils.scale(n1_perp,
                                                 boltcen_perp_dist),
                             DraftVecUtils.scale(n1_perp,
                                                 -boltcen_perp_dist)]:
                pos_i = botcenter_pos + vec_axis + vec_perp
                # the nut hole will be on the bottom side,
                
                shp_bolt = fcfun.shp_boltnut_dir_hole (
                                  r_shank = BOLT_SHANK_R_TOL,
                                  l_bolt  = housing_h,
                                  r_head  = BOLT_HEAD_R_TOL,
                                  l_head  = BOLT_HEAD_L,
                                  r_nut  = BOLT_NUT_R_TOL,
                                  # more space, because we want it well inside
                                  l_nut  = 1.5*BOLT_NUT_L,
                                  hex_head = 0,
                                  xtr_head=1,     xtr_nut=1,
                                  supp_head=1,    supp_nut=1,
                                  headstart=0,
                                  fc_normal = n1_bot_axis_neg,
                                  fc_verx1=V0,
                                  pos = pos_i)
                bolt_holes.append(shp_bolt)

        # ----------------- Attributes
        self.n1_slide_axis = n1_slide_axis
        self.n1_bot_axis = n1_bot_axis
        self.n1_perp = n1_perp
        self.slideaxisbot_dist = slideaxisbot_dist
        self.boltcen_axis_dist = boltcen_axis_dist
        self.boltcen_perp_dist = boltcen_perp_dist
        self.tot_h = housing_h
        self.tot_w = housing_w # == base_w
        self.tot_l = base_l
        self.housing_l  = housing_l
        self.base_h = base_h
        
        shp_bolt_holes = shp_bolt1_atch.multiFuse(bolt_holes)       
        shp_lbear_housing = shp_block_hole.cut(shp_bolt_holes)
        doc.recompute()
        # making 2 parts, intersection with 2 boxes:
        shp_box_top = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_l + 2, 
                                     box_h = housing_h /2. + 2,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_top = shp_lbear_housing.common(shp_box_top)
        shp_lbear_housing_top = shp_lbear_housing_top.removeSplitter() 
        fco_lbear_top = doc.addObject("Part::Feature", name + '_top') 
        fco_lbear_top.Shape = shp_lbear_housing_top


        shp_box_bot = fcfun.shp_box_dir(
                                     box_w = base_w + 2,
                                     box_d = base_l + 2,
                                     # larger, just in case
                                     box_h = housing_h/2. + base_h + 2,
                                     fc_axis_h = n1_bot_axis,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_bot = shp_lbear_housing.common(shp_box_bot)
        shp_lbear_housing_bot = shp_lbear_housing_bot.removeSplitter()
        fco_lbear_bot = doc.addObject("Part::Feature", name + '_bot') 
        fco_lbear_bot.Shape = shp_lbear_housing_bot

        self.fco_top = fco_lbear_top
        self.fco_bot = fco_lbear_bot




#doc = FreeCAD.newDocument()
#ThinLinBearHouse (kcomp.LMEUU[10])
#ThinLinBearHouse (kcomp.LMEUU[10], mid_center=0)
 

# ----------- Linear bearing housing 

class LinBearHouse (object):

    """
         Makes a housing for a linear bearing takes the dimensions
         from a dictionary, like the one defined in kcomp.py
         it has to parts, the lower and the upper part
 
          _____________                           ______________
         |::   ___   ::|                         |.::........::.|
         |:: /     \ ::|    Upper part           | ::        :: |
         |---|-----|---|------                   | ::        :: |
         |::  \___/  ::|    Lower part           |.::........::.| 
         |::_________::|                         |_::________::_|      
 
          _____________ 
         | 0 :     : 0 |
         |   :     :   |
         |   :     :   |
         |   :     :   |
         |   :     :   |
         |_0_:_____:_0_|
         



                                            ________________
        1: axis_center=1                   | : :........: : |
           mid_center =1                   |.: :        : :.|
        2: axis_center=0                   |.:4:   1 --------->: fc_slide_axis
           mid_center =1                   | : :........:.: | 
        3: axis_center=0                   | : :        : : |
           mid_center =0                   |_:3:___2____:_:_|
        4: axis_center=1
           mid_center =0

    """


    MTOL = kparts.MTOL
    MLTOL = kparts.MLTOL
    TOL_BEARING_L = kparts.TOL_BEARING_L
    # Radius to fillet the sides
    FILLT_R = kparts.FILLT_R


    def __init__(self, d_lbearhousing,
                 fc_slide_axis = VX,
                 fc_bot_axis =VZN,
                 axis_center = 1,
                 mid_center  = 1,
                 pos = V0,
                 name = 'linbearhouse'
                ):

        housing_l = d_lbearhousing['L']
        housing_w = d_lbearhousing['W']
        housing_h = d_lbearhousing['H']
        self.L = housing_l
        self.W = housing_w
        self.H = housing_h
        self.axis_h =  d_lbearhousing['axis_h']
        self.bolt_sep_l =  d_lbearhousing['bolt_sep_l']
        self.bolt_sep_w =  d_lbearhousing['bolt_sep_w']
        self.bolt_d =  d_lbearhousing['bolt_d']
        axis_h = self.axis_h


        # normalize, just in case they are not
        n1_slide_axis = DraftVecUtils.scaleTo(fc_slide_axis,1)
        n1_bot_axis = DraftVecUtils.scaleTo(fc_bot_axis,1)
        n1_bot_axis_neg = DraftVecUtils.neg(n1_bot_axis)
        # vector perpendicular to the others
        n1_perp = n1_slide_axis.cross(n1_bot_axis)

        # get the linear bearing dictionary
        d_lbear = d_lbearhousing['lbear']
        self.rod_r = d_lbear['Di']/2.
        rod_r = self.rod_r
        self.bear_r = d_lbear['Di']
        bolt_d = d_lbearhousing['bolt_d']

        doc = FreeCAD.ActiveDocument
        # bolt dimensions:
        MTOL = self.MTOL
        MLTOL = self.MLTOL
        BOLT_HEAD_R = kcomp.D912_HEAD_D[bolt_d] / 2.0
        BOLT_HEAD_L = kcomp.D912_HEAD_L[bolt_d] + MTOL
        BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
        BOLT_SHANK_R_TOL = bolt_d / 2.0 + MTOL/2.0

        # bearing dimensions:
        bearing_l     = d_lbear['L']
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = d_lbear['De']
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL

        cenbolt_dist_l = d_lbearhousing['bolt_sep_l']/2.
        cenbolt_dist_w = d_lbearhousing['bolt_sep_w']/2.

        #To make the boxes, we take the reference on midcenter=1 and 
        # axis_center = 0. Point 2 on the drawing

        if mid_center == 0:
            # get the vector to the center:
            fc_tomidcenter = DraftVecUtils.scale(n1_slide_axis,cenbolt_dist_l)
        else:
            fc_tomidcenter = V0
        if axis_center == 1:
            fc_tobottom = DraftVecUtils.scale(n1_bot_axis,axis_h)
            fc_toaxis = V0
        else:
            fc_tobottom = V0
            fc_toaxis = DraftVecUtils.scale(n1_bot_axis,-axis_h)

        # point 2 on the drawing
        botcenter_pos = pos + fc_tomidcenter + fc_tobottom

        # point 1 on the drawing
        axiscenter_pos = pos + fc_tomidcenter + fc_toaxis

        # center on top
        topcenter_pos = botcenter_pos + DraftVecUtils.scale(n1_bot_axis_neg,
                                                            housing_h)

        shp_housing = fcfun.shp_box_dir(box_w = housing_w,
                                     box_d = housing_l, #dir of n1_slide_axis
                                     box_h = housing_h,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = botcenter_pos)

        # fillet the base:
        shp_housing_fllt = fcfun.shp_filletchamfer_dir(shp_housing,
                                                    fc_axis=fc_bot_axis,
                                                    radius=2)

        # the rod hole
        shp_rod = fcfun.shp_cylcenxtr(r = rod_r + kparts.ROD_SPACE_MIN,
                                      h = housing_l,
                                      normal = n1_slide_axis,
                                      ch = 1, xtr_top = 1, xtr_bot=1,
                                      pos = axiscenter_pos)
        # the linear bearing hole
        shp_lbear = fcfun.shp_cylcenxtr(r = bearing_r_tol,
                                        h = bearing_l_tol,
                                        normal = n1_slide_axis,
                                        ch = 1, xtr_top = 1, xtr_bot=1,
                                        pos = axiscenter_pos)
        shp_rodlbear = shp_rod.fuse(shp_lbear)

        # 4 bolts to join the upper and lower parts
        # distance of the bolts to the center, on n1_slide_axis dir

        bolt_holes = []

        for vec_axis in [DraftVecUtils.scale(n1_slide_axis,cenbolt_dist_l),
                         DraftVecUtils.scale(n1_slide_axis,-cenbolt_dist_l)]:
            for vec_perp in [DraftVecUtils.scale(n1_perp,
                                                 cenbolt_dist_w),
                             DraftVecUtils.scale(n1_perp,
                                                 -cenbolt_dist_w)]:
                pos_i = topcenter_pos + vec_axis + vec_perp
                # the nut hole will be on the bottom side,
                
                shp_bolt = fcfun.shp_bolt_dir (
                                  r_shank = BOLT_SHANK_R_TOL,
                                  l_bolt  = housing_h,
                                  r_head  = BOLT_HEAD_R_TOL,
                                  l_head  = BOLT_HEAD_L,
                                  hex_head = 0,
                                  xtr_head=1,     xtr_shank=1,
                                  support=1,
                                  fc_normal = n1_bot_axis,
                                  fc_verx1=V0,
                                  pos = pos_i)
                bolt_holes.append(shp_bolt)

        shp_holes = shp_rodlbear.multiFuse(bolt_holes)       
        shp_lbear_housing = shp_housing_fllt.cut(shp_holes)
        Part.show(shp_lbear_housing)
        doc.recompute()
        # making 2 parts, intersection with 2 boxes:
        shp_box_top = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_l + 2, 
                                     box_h = housing_h - axis_h + 2,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_top = shp_lbear_housing.common(shp_box_top)
        shp_lbear_housing_top = shp_lbear_housing_top.removeSplitter() 
        fco_lbear_top = doc.addObject("Part::Feature", name + '_top') 
        fco_lbear_top.Shape = shp_lbear_housing_top

        shp_box_bot = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_l + 2,
                                     # larger, just in case
                                     box_h = axis_h + 2,
                                     fc_axis_h = n1_bot_axis,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_bot = shp_lbear_housing.common(shp_box_bot)
        shp_lbear_housing_bot = shp_lbear_housing_bot.removeSplitter()
        fco_lbear_bot = doc.addObject("Part::Feature", name + '_bot') 
        fco_lbear_bot.Shape = shp_lbear_housing_bot

        self.fco_top = fco_lbear_top
        self.fco_bot = fco_lbear_bot
        doc.recompute()

#LinBearHouse (kcomp.SCUU[10])
doc = FreeCAD.newDocument()
LinBearHouse (kcomp.SCUU_Pr[10])
