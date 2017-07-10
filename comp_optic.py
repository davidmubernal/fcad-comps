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


def f_cagecube (d_cagecube,
                axis_thru_rods = 'x',
                axis_thru_hole = 'y',
                name = 'cagecube'
               ):

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
                axis_thru_rods = axis_thru_rods,
                axis_thru_hole = axis_thru_hole,
                name = name)

    return cage


# ---------------------- CageCubeHalv -------------------------------

class CageCubeHalf (object):

    """ Creates a Half Cage Cube for optics, so you can put the lense
        at 45
        taps are only drawn with their max diameter, 
        setscrews and taps to secure the rods are not drawn
        Many other details are not drawn, neither the cover for the lense

        The right angle sides are identical, but there is a difference
        regarding to the tapped holes on the sides, the can have different
        sizes
    Args
        side_l: length of the side of the cube (then it will be halved)
        thread_d: 2 big threads, on the 2 perpendicular sides, centered
        thru_hole_d: internal hole after the thread
        thru_hole_depth: depth from which the thru hole starts
        lenshole_45_d: hole from the 45 angle side that will go to the center
        rod_d: 4 holes, on 2 sides, perpendicular sides. The rods will be 
               secured with screws, but those screws are not drawn
        rod_sep: separation of the rods
        rod_depth: how deep are the holes
        rod_thread_l: depth of the thread for the rods
        tap_d: diameter of the tap to connect accesories
        tap_l: depth of the taps to connect accesories
        tap_sep_l: separation of the tap to connect, large
        tap_sep_s: separation of the tap to connect, sort
        axis_1: direction of the first right side:
                'x', 'y', 'z', '-x', '-y', '-z'
        axis_2: direction big the other right side: 
                'x', 'y', 'z', '-x', '-y', '-z'
           Cannot be the same as axis_1, or its negated. Has to be perpendicular
           There are 24 posible orientations:
           6 posible axis_1 and 4 axis_2 for each axis_1
        name: name of the freecad object
    """

    def __init__ (self, side_l,
                        thread_d,
                        thru_hole_d,
                        thru_hole_depth,
                        lenshole_45_d,
                        rod_d,
                        rod_sep,
                        rod_depth,
                        tap12_d,
                        tap12_l,
                        tap21_d,
                        tap21_l,
                        tap_dist,
                        axis_1 = 'x',
                        axis_2 = 'y',
                        name = 'cagecube'):

        doc = FreeCAD.ActiveDocument

        self.base_place = (0,0,0)
        self.side_l  = side_l
        self.thread_d = thread_d
        self.thru_hole_d = thru_hole_d
        self.thru_hole_depth = thru_hole_depth
        self.lenshole_45_d = lenshole_45_d
        self.rod_d = rod_d
        self.rod_sep = rod_sep
        self.rod_depth = rod_depth
        self.axis_1 = axis_1
        self.axis_2 = axis_2
        # getting the freecad vector of the axis
        self.v_1 = fcfun.getfcvecofname(axis_1)
        self.v_2 = fcfun.getfcvecofname(axis_2)

        # cage
        shp_cage_box = fcfun.shp_boxcen(x=side_l,
                                        y=side_l,
                                        z=side_l, 
                                        cx=1, cy=1, cz=1,
                                        pos=V0)
        # taking the half away (it is less than the half)
        # the normal is on the opposite direction of the sum of axis_1 and
        # axis_2
        v_halfout = DraftVecUtils.neg(self.v_1 + self.v_2)
        v_halfout.normalize()
        # Making the cut with a cilinder, because it is easier, since the 
        # function is already availabe
        # radius is smaller: pythagoras, but to make it simpler
        # the position is not just the half, about a centimeter less, but
        # just thake the thru_hole_depth
        pos_halfout = DraftVecUtils.scaleTo(v_halfout, thru_hole_depth)
        shp_halfout = fcfun.shp_cyl(r= side_l, h=side_l, 
                                    normal = v_halfout,
                                    pos = pos_halfout)
      
        doc.recompute()
        #Part.show(shp_halfout)

        # hole on the 45 face, for the lense
        # on position (0,0,0) but the same direction as the previous
        # the heigth is hypotenuse, but to symplify and to cut over the total
        # length, we make it twice the cathetus
        shp_lensehole = fcfun.shp_cyl(r= lenshole_45_d/2.,
                                      h=2*thru_hole_depth, 
                                      normal = v_halfout,
                                      pos = V0)
        # make the cut know because freecad was having problems making the cut
        # all together, maybe because there 45 degrees cuts that 
        shp_45cut = shp_halfout.fuse(shp_lensehole)
        shp_cage_half = shp_cage_box.cut(shp_45cut)
        shp_cage_half = shp_cage_half.removeSplitter()
        doc.recompute()
        #Part.show(shp_cage_half)
   
        holes = []

        # threaded holes, centered:2
        pos_thread_1 = DraftVecUtils.scale(self.v_1, side_l/2.-thru_hole_depth)
        shp_thread_1 = fcfun.shp_cylcenxtr (r= thread_d/2.,
                                            h = thru_hole_depth,
                                            normal = self.v_1,
                                            ch=0, xtr_top=1., xtr_bot=0.,
                                            pos = pos_thread_1)

        # Not included in the list, because one element has to be out
        #holes.append(shp_thread_1)

        pos_thread_2 = DraftVecUtils.scale(self.v_2, side_l/2.-thru_hole_depth)
        shp_thread_2 = fcfun.shp_cylcenxtr (r= thread_d/2.,
                                            h = thru_hole_depth,
                                            normal = self.v_2,
                                            ch=0, xtr_top=1., xtr_bot=0.,
                                            pos = pos_thread_2)

        holes.append(shp_thread_2)


        # thru holes, centered:2, on the direction of right angles
        shp_thru_1 = fcfun.shp_cylcenxtr (r= thru_hole_d/2.,
                                            h = side_l,
                                            normal = self.v_1,
                                            ch=1, xtr_top=1., xtr_bot=1.,
                                            pos = V0)

        holes.append(shp_thru_1)

        shp_thru_2 = fcfun.shp_cylcenxtr (r= thru_hole_d/2.,
                                            h = side_l,
                                            normal = self.v_2,
                                            ch=1, xtr_top=1., xtr_bot=1.,
                                            pos = V0)

        holes.append(shp_thru_2)

        # holes to connect rods. 4 in 2 sides (perpendicular sides)
        # get the four directions, of the normals
        for vnormal in [self.v_1, self.v_2]:
            # for each normal, we take the other 4 perpendicular axis
            # for example, is vnormal is (1,0,0), the 4 perpendicular axis
            # will be (0,1,1), (0,-1,1), (0,-1,-1), (0,1,-1)
            fc_perp_coord_list = fcfun.get_fclist_4perp2_fcvec(vnormal)
            # position on the normal dimension (where the rod hole starts)
            vnormal_coord = DraftVecUtils.scale(vnormal,
                                                 (side_l/2. -rod_depth))
            for fc_perp_coord in fc_perp_coord_list:
                fc_perp_coord_scale = DraftVecUtils.scale(fc_perp_coord,
                                                          rod_sep/2.)
                fc_coord = fc_perp_coord_scale + vnormal_coord
                shp_rodhole = fcfun.shp_cylcenxtr (r= rod_d/2,
                                                   h = rod_depth,
                                                   normal = vnormal,
                                                   ch=0, xtr_top =1.,
                                                   xtr_bot=0,
                                                   pos = fc_coord)
                holes.append (shp_rodhole)

        # taps to mount to posts
        # get the direction axis_1 x axis_2
        vdir_12 = self.v_1.cross (self.v_2)
        vdir_21 = self.v_2.cross (self.v_1)
        axis1_coord = DraftVecUtils.scale(self.v_1, tap_dist)
        axis2_coord = DraftVecUtils.scale(self.v_2, tap_dist)
        axis12_coord = DraftVecUtils.scale(vdir_12, side_l/2. - tap12_l)
        axis21_coord = DraftVecUtils.scale(vdir_21, side_l/2. - tap21_l)
        fc_pos12 = axis1_coord + axis2_coord + axis12_coord
        fc_pos21 = axis1_coord + axis2_coord + axis21_coord
        shp_tap12 = fcfun.shp_cylcenxtr (r = tap12_d/2,
                                         h = tap12_l,
                                         normal = vdir_12,
                                         ch=0, xtr_top =1.,
                                         xtr_bot=0,
                                         pos = fc_pos12)
        shp_tap21 = fcfun.shp_cylcenxtr (r = tap21_d/2,
                                         h = tap21_l,
                                         normal = vdir_21,
                                         ch=0, xtr_top =1.,
                                         xtr_bot=0,
                                         pos = fc_pos21)
        holes.append (shp_tap12)
        holes.append (shp_tap21)

        shp_holes = shp_thread_1.multiFuse(holes)
        shp_holes = shp_holes.removeSplitter()
        doc.recompute()
        Part.show(shp_holes)

        shp_cage_holes = shp_cage_half.cut(shp_holes)


        doc.recompute()
        fco_cage = doc.addObject("Part::Feature", name )
        fco_cage.Shape = shp_cage_holes
        self.fco = fco_cage


    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        self.fco.Placement.Base = FreeCAD.Vector(position)




def f_cagecubehalf (d_cagecubehalf,
                    axis_1 = 'x',
                    axis_2 = 'y',
                    name = 'cagecubehalf'
                   ):

    """ creates a half cage cube: 2 perpendicular sides, and a 45 degree angle
        side,
        it creates from a dictionary

    Args
        d_cagecubehalf: dictionary with the dimensions of the cage cube,
                    defined in kcomp_optic.py
        axis_1: direction of the first right side:
                'x', 'y', 'z', '-x', '-y', '-z'
        axis_2: direction big the other right side: 
                'x', 'y', 'z', '-x', '-y', '-z'
           Cannot be the same as axis_1, or its negated. Has to be perpendicular
           There are 24 posible orientations:
           6 posible axis_1 and 4 axis_2 for each axis_1
        name: name of the freecad object

    """

    cage = CageCubeHalf(
                side_l = d_cagecubehalf['L'],
                thread_d = d_cagecubehalf['thread_d'],
                thru_hole_d = d_cagecubehalf['thru_hole_d'],
                thru_hole_depth = d_cagecubehalf['thru_hole_depth'],
                lenshole_45_d = d_cagecubehalf['lenshole_45_d'],
                rod_d     = d_cagecubehalf['rod_d'],
                rod_sep   = d_cagecubehalf['rod_sep'],
                rod_depth = d_cagecubehalf['rod_depth'],
                tap12_d   = d_cagecubehalf['tap12_d'],
                tap12_l   = d_cagecubehalf['tap12_l'],
                tap21_d   = d_cagecubehalf['tap21_d'],
                tap21_l   = d_cagecubehalf['tap21_l'],
                tap_dist  = d_cagecubehalf['tap_dist'],
                axis_1 = axis_1,
                axis_2 = axis_2,
                name   = name)

    return cage



doc = FreeCAD.newDocument()
doc = FreeCAD.ActiveDocument



cage = f_cagecubehalf(kcomp_optic.CAGE_CUBE_HALF_60)

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
                           

