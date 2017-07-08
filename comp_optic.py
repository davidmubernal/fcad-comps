# ----------------------------------------------------------------------------
# -- Components
# -- comps library
# -- Python classes that creates optical components
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronic Techonology. Rey Juan Carlos University (urjc.es)
# -- July-2017
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------


import FreeCAD;
import Part;
import logging
import os
import Draft;
import DraftGeomUtils;
import DraftVecUtils;
import math;
#import copy;
#import Mesh;

# ---------------------- can be taken away after debugging
# directory this file is
filepath = os.getcwd()
import sys
# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath)
# ---------------------- can be taken away after debugging

import kcomp 
import kcomp_optic
import fcfun

from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, addCyl_pos, fillet_len
from fcfun import VXN, VYN, VZN
from fcfun import addBolt, addBoltNut_hole, NutHole


logging.basicConfig(level=logging.DEBUG,
                    format='%(%(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# ---------------------- CageCube -------------------------------
# Creates Cage Cube for optics
# Arguments:
# side_l: length of the side of the cube
# thru_hole_d: big thru-hole on 2 sides, not threaded, centered
# thru_thread_d: 2 big thru-hole threaded, on 4 sides, centered
# thru_rod_d: 4 thru holes, on 2 sides
# thru_rod_sep: separation of the rods
# rod_thread_d: on the sides other than the thru_rods, there are threads to
#             insert a rod
# rod_thread_l: depth of the thread for the rods
# tap_d: diameter of the 
# axis_thru_rods: direction of rods: 'x', 'y', 'z'
# axis_thru_hol: direction big thru_hole: 'x', 'y', 'z'. Cannot be the same 
#                as axis_thru_rods
# 6 posible orientations:
# Thru-rods can be on X, Y or Z axis
# thru-hole can be on X, Y, or Z axis, but not in the same as thru-rods


class CageCube (object):

    """ Creates Cage Cube for optics
        taps are only drawn with their max diameter, 
        setscrews and taps to secure the rods are not drawn
    Args
        side_l: length of the side of the cube
        thru_hole_d: big thru-hole on 2 sides, not threaded, centered
        thru_thread_d: 2 big thru-hole threaded, on 4 sides, centered
        thru_rod_d: 4 thru holes, on 2 sides
        thru_rod_sep: separation of the rods
        rod_thread_d: on the sides other than the thru_rods, there are threads
            to insert a rod
        rod_thread_l: depth of the thread for the rods
        tap_d: diameter of the tap to connect accesories
        tap_l: depth of the taps to connect accesories
        tap_sep_l: separation of the tap to connect, large
        tap_sep_s: separation of the tap to connect, sort
        axis_thru_rods: direction of rods: 'x', 'y', 'z'
        axis_thru_hole: direction big thru_hole: 'x', 'y', 'z'.
           Cannot be the same as axis_thru_rods
           There are 6 posible orientations:
           Thru-rods can be on X, Y or Z axis
           thru-hole can be on X, Y, or Z axis, but not in the same as thru-rods
    """


    def __init__ (self, side_l,
                        thru_hole_d,
                        thru_thread_d,
                        thru_rod_d,
                        thru_rod_sep,
                        rod_thread_d,
                        rod_thread_l,
                        tap_d,
                        tap_l,
                        tap_sep_l,
                        tap_sep_s,
                        axis_thru_rods = 'x',
                        axis_thru_hole = 'y',
                        name = 'cagecube'):

        doc = FreeCAD.ActiveDocument

        self.base_place = (0,0,0)
        self.side_l  = side_l
        self.thru_hole_d = thru_hole_d
        self.thru_thread_d = thru_thread_d
        self.thru_rod_d = thru_rod_d
        self.axis_thru_rods = axis_thru_rods
        self.axis_thru_hole = axis_thru_hole
        # getting the freecad vector of the axis
        self.v_thru_rods = fcfun.getfcvecofname(axis_thru_rods)
        self.v_thru_hole = fcfun.getfcvecofname(axis_thru_hole)

        # cage
        shp_cage_box = fcfun.shp_boxcen(x=side_l,
                                        y=side_l,
                                        z=side_l, 
                                        cx=1, cy=1, cz=1,
                                        pos=V0)

        # centered Thru hole: 1
        shp_thru_hole_cen0 = fcfun.shp_cylcenxtr (r= thru_hole_d/2.,
                                             h = side_l,
                                             normal = self.v_thru_hole,
                                             ch=1, xtr_top=1., xtr_bot=1.,
                                             pos = V0)
        holes = []
        #holes.append(shp_thru_hole_cen0)

        # threaded thru-holes, centered:2
        # getting the perpendicular directions of v_thru_hole
        # if (1,0,0) -> (0,1,0)
        v_thru_hole_perp1 = FreeCAD.Vector(self.v_thru_hole.y,
                                           self.v_thru_hole.z,
                                           self.v_thru_hole.x);
        shp_thru_hole_cen1 = fcfun.shp_cylcenxtr (r= thru_thread_d/2.,
                                             h = side_l,
                                             normal = v_thru_hole_perp1,
                                             ch=1, xtr_top=1., xtr_bot=1.,
                                             pos = V0)

        holes.append(shp_thru_hole_cen1)
        v_thru_hole_perp2 = FreeCAD.Vector(self.v_thru_hole.z,
                                           self.v_thru_hole.x,
                                           self.v_thru_hole.y);
        shp_thru_hole_cen2 = fcfun.shp_cylcenxtr (r= thru_thread_d/2.,
                                             h = side_l,
                                             normal = v_thru_hole_perp2,
                                             ch=1, xtr_top=1., xtr_bot=1.,
                                             pos = V0)
        holes.append(shp_thru_hole_cen2)

        # thru-holes for the rods:
        # dimensions are added to the axis other than the normal
        fc_list = fcfun.get_fclist_4perp2_vecname(axis_thru_rods)
        for fcvec in fc_list: 
          fc_dist = DraftVecUtils.scale(fcvec, thru_rod_sep/2.)
          shp_thru_hole_rod = fcfun.shp_cylcenxtr (r= thru_rod_d/2.,
                                             h = side_l,
                                             normal = self.v_thru_rods,
                                             ch=1, xtr_top=1., xtr_bot=1.,
                                             pos = fc_dist)
          holes.append(shp_thru_hole_rod)

        # taps to connect rods. 4 in 4 sides (not on the side of the thru-holes
        # for the rods
        # get the four directions, of the normals
        fc_rodtap_list = fcfun.get_fclist_4perp_vecname(axis_thru_rods)
        for vnormal in fc_rodtap_list:
            # for each normal, we take the other 4 perpendicular axis
            # for example, is vnormal is (1,0,0), the 4 perpendicular axis
            # will be (0,1,1), (0,-1,1), (0,-1,-1), (0,1,-1)
            fc_perp_coord_list = fcfun.get_fclist_4perp2_fcvec(vnormal)
            vnormal_coord = DraftVecUtils.scale(vnormal,
                                                 (side_l/2. -rod_thread_l))
            for fc_perp_coord in fc_perp_coord_list:
                fc_perp_coord_scale = DraftVecUtils.scale(fc_perp_coord,
                                                     thru_rod_sep/2.)
                fc_coord = fc_perp_coord_scale + vnormal_coord
                shp_rodtap = fcfun.shp_cylcenxtr (r= rod_thread_d/2,
                                                  h = rod_thread_l,
                                                  normal = vnormal,
                                                  ch=0, xtr_top =1.,
                                                  xtr_bot=0,
                                                  pos = fc_coord)
                holes.append (shp_rodtap)



        # taps for mounting a cover, on the 2 sides of the centered thru-hole
        # direction: self.v_thru_hole and negated
        for vnormal in [self.v_thru_hole, DraftVecUtils.neg(self.v_thru_hole)]:
            vnormal_coord = DraftVecUtils.scale(vnormal,
                                               (side_l/2. -tap_l))
            # the large separation is the same as the thru rods
            for vdir_large in [self.v_thru_rods,
                                DraftVecUtils.neg(self.v_thru_rods)]:
                #scale this direction to the length of the separation (half)
                fc_coord_large =  DraftVecUtils.scale(vdir_large, tap_sep_l/2.)
                # the sort separation: cross product
                vdir_short = vnormal.cross (vdir_large)
                vdir_short.normalize()
                for vdir_short_i in [vdir_short, DraftVecUtils.neg(vdir_short)]:
                    fc_coord_short = DraftVecUtils.scale(vdir_short_i,
                                                         tap_sep_s/2.)
                    fc_coord = vnormal_coord + fc_coord_large + fc_coord_short
                    shp_tap = fcfun.shp_cylcenxtr (r= tap_d/2,
                                                  h = tap_l,
                                                  normal = vnormal,
                                                  ch=0, xtr_top =1.,
                                                  xtr_bot=0,
                                                  pos = fc_coord)
                    holes.append (shp_tap)
  
       


        shp_holes = shp_thru_hole_cen0.multiFuse(holes)
        shp_holes = shp_holes.removeSplitter()

        shp_cage = shp_cage_box.cut(shp_holes)


        doc.recompute()
        fco_cage = doc.addObject("Part::Feature", name )
        fco_cage.Shape = shp_cage
        self.fco = fco_cage


    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        self.fco.Placement.Base = FreeCAD.Vector(position)


def f_cagecube (d_cagecube):

    """ creates a cage cube, it creates from a dictionary

    Args
        d_cagecube: dictionary with the dimensions of the cage cube,
                    defined in kcomp_optic.py
        axis_thru_rods: direction of rods: 'x', 'y', 'z'
        axis_thru_hole: direction big thru_hole: 'x', 'y', 'z'.
           Cannot be the same as axis_thru_rods
           There are 6 posible orientations:
           Thru-rods can be on X, Y or Z axis
           thru-hole can be on X, Y, or Z axis, but not in the same as thru-rods
    """

    cage = CageCube(side_l = d_cagecube['L'],
                thru_hole_d = d_cagecube['thru_hole_d'],
                thru_thread_d = d_cagecube['thru_thread_d'],
                thru_rod_d = d_cagecube['thru_rod_d'],
                thru_rod_sep = d_cagecube['thru_rod_sep'],
                rod_thread_d = d_cagecube['rod_thread_d'],
                rod_thread_l = d_cagecube['rod_thread_l'],
                tap_d = d_cagecube['tap_d'],
                tap_l = d_cagecube['tap_l'],
                tap_sep_l = d_cagecube['tap_sep_l'],
                tap_sep_s = d_cagecube['tap_sep_s'],
                axis_thru_rods = 'x',
                axis_thru_hole = 'y',
                name = 'cagecube')

    return cage


doc = FreeCAD.newDocument()
doc = FreeCAD.ActiveDocument



cage = f_cagecube(kcomp_optic.CAGE_CUBE_60)

#cage = CageCube(side_l = kcomp_optic.CAGE_CUBE_60['L'],
#                thru_hole_d = kcomp_optic.CAGE_CUBE_60['thru_hole_d'],
#                thru_thread_d = kcomp_optic.CAGE_CUBE_60['thru_thread_d'],
#                thru_rod_d = kcomp_optic.CAGE_CUBE_60['thru_rod_d'],
#                thru_rod_sep = kcomp_optic.CAGE_CUBE_60['thru_rod_sep'],
#                rod_thread_d,
#                rod_thread_l,
#                tap_d,
#                tap_l,
#                tap_sep_l,
#                tap_sep_s,
#                axis_thru_rods = 'x',
#                axis_thru_hole = 'y',
#                name = 'cagecube')
                           

