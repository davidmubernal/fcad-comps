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
            
