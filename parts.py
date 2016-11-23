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
            endstop_l =  kcomp.ENDSTOP['L']
            endstop_ht =  kcomp.ENDSTOP['HT']
            endstop_h =  kcomp.ENDSTOP['H']
            endstopdepth = endstop_ht + extra_endstop + extra_w
            depth = max (endstopdepth, depth)
            endstop_boltsep = kcomp.ENDSTOP['BOLT_SEP']
            endstop_bolt_h = kcomp.ENDSTOP['BOLT_H']
            endstop_bolt_d = kcomp.ENDSTOP['BOLT_D']
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
        base_h = .8 * profile_size # no need to go all the way down
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
        pulleybolt_h = 2 * extra_w + pulleynut_hole_h

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
            shp_shank_hbolt0 = fcfun.shp_cyl ( r = holdbolt_d/2 + TOL,
                                               h= bolt_shank + 2, normal = VY,
                                               pos = pos_shank_hbolt0)
            if depth > bolt_shank :
                pos_head_hbolt0 = FreeCAD.Vector(hbolt_p0x,
                                                 bolt_shank,
                                                 -profile_size/2.)
                shp_head_hbolt0 = fcfun.shp_cyl (
                                           r = holdbolthead_d/2 + TOL,
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

            
