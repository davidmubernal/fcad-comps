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


# ---------------------- CageCubeHalf -------------------------------

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
        #Part.show(shp_holes)

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






#cage = f_cagecubehalf(kcomp_optic.CAGE_CUBE_HALF_60)

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
                           
def plate_thruhole_hole8 (side_l, 
           thick,
           thruhole_d,
           sym_hole_d,
           sym_hole_sep,
           cbore_hole_d,
           cbore_hole_head_d,
           cbore_hole_head_l,
           cbore_hole_sep_l,
           cbore_hole_sep_s,
           fc_axis_h,
           fc_axis_l,
           cl=1, cw=1, ch=1,
           pos = V0,
           name = 'plate'):

    """
    draws a square plate, with a thru-hole in the center.
    4 sets of holes in symetrical positions for screws
    4 sets of holes for cap-screws

                   fc_axis_l: axis on the large separation
                    |
                    |
            :-- sy_hole_sep -:
            :                :
            :cbore_hole_sep_s:
            :    :      :    :
          _______________________
         |       O      O       | -------------------
         |  0      ....      0  | ....               :
         |       /      \       |    :               :
         |      |        |      |    :               :
         |      |        |      |    +sym_hole_sep   + cbore_hole_sep_s
         |       \ .... /       |    :               :
         |  0                0  | ....               :
         |       O      O       | -------------------
         |______________________|


    Arguments:
        side_l: length of the plate (two sides)
        thick : thickness (height of the plate)
        thruhole_d: diamenter of the central hole
        sym_hole_d: diamenter of the symetrical holes
        sym_hole_sep: distance between the centers of the symetrical holes 
        cbore_hole_d: diameter of the shank of the counter bored hole
        cbore_hole_head_d: diameter of the cap of the counterbored screw
        cbore_hole_head_l: length of the cap (head) of the counterbored screw
        cbore_hole_sep_l: large separation of the counterbored holes
        cbore_hole_sep_s: small separation of the counterbored holes
        fc_axis_h: FreeCAD.Vector on the direction of the vertical (thickness)
        fc_axis_l: FreeCAD.Vector on the direction of the large distance of
                the counterbored asymetrical holes
        cl: 1: centered on the fc_axis_l direction
        cw: 1: centered on the axis_small direction (perpendicular to fc_axis_l
               and fc_axis_h)
        ch: 1: centered on the vertical direction (thickness)
        pos :  position of the center. FreeCAD.Vector
        name: name 

    """

    doc = FreeCAD.ActiveDocument

    # normalize de axis
    axis_h = DraftVecUtils.scaleTo(fc_axis_h,1)
    axis_l = DraftVecUtils.scaleTo(fc_axis_l,1)
    axis_s = fc_axis_l.cross(fc_axis_h)

    shp_box = fcfun.shp_box_dir(side_l, side_l, thick, axis_h, axis_l,
                                  cw = cl, cd = cw, ch = ch,
                                  pos = pos)

    # getting the offset of the center coordinates
    if cl == 1:
       l_0 = V0 # already centered
    else:
       l_0 = DraftVecUtils.scaleTo(axis_l, side_l/2.)
    if cw == 1:
       s_0 = V0
    else:
       s_0 = DraftVecUtils.scaleTo(axis_s, side_l/2.)
    if ch == 1: # for the height, we want the lower side
       h_0 = DraftVecUtils.scaleTo(axis_h, -thick/2.)
    else:
       h_0 = V0

    pos_center = pos + l_0 + s_0 + h_0

    shp_cenhole = fcfun.shp_cylcenxtr(r=thruhole_d/2., h=thick,
                                      normal=axis_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=1., 
                                      pos=pos_center)

    # symetrical holes
    holes = []
    for add_l in (DraftVecUtils.scaleTo(axis_l,  sym_hole_sep/2),
                  DraftVecUtils.scaleTo(axis_l, - sym_hole_sep/2)) :
        for add_s in (DraftVecUtils.scaleTo(axis_s,  sym_hole_sep/2),
                      DraftVecUtils.scaleTo(axis_s, - sym_hole_sep/2)) :
            pos_hole = pos_center + add_l + add_s
            shp_hole = fcfun.shp_cylcenxtr(r=sym_hole_d/2., h=thick,
                                      normal=axis_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=1., 
                                      pos=pos_hole)
            holes.append(shp_hole)

    # asymetrical hole
    for add_l in (DraftVecUtils.scaleTo(axis_l,  cbore_hole_sep_l/2),
                  DraftVecUtils.scaleTo(axis_l, - cbore_hole_sep_l/2)) :
        for add_s in (DraftVecUtils.scaleTo(axis_s,  cbore_hole_sep_s/2),
                      DraftVecUtils.scaleTo(axis_s, - cbore_hole_sep_s/2)) :
            pos_hole = pos_center + add_l + add_s
            shp_hole = fcfun.shp_cylcenxtr(r=cbore_hole_d/2., h=thick,
                                      normal=axis_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=1., 
                                      pos=pos_hole)
            pos_head = (  pos_hole
                      + DraftVecUtils.scaleTo(axis_h, thick-cbore_hole_head_l))
            shp_hole_head = fcfun.shp_cylcenxtr(r=cbore_hole_head_d/2.,
                                      h=cbore_hole_head_l,
                                      normal=axis_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=0, 
                                      pos=pos_head)
            shp_cbore_hole = shp_hole.fuse(shp_hole_head)

            holes.append(shp_cbore_hole)


    shp_holes = shp_cenhole.multiFuse(holes)

    shp_plate = shp_box.cut(shp_holes)
    doc.recompute()
    fco_plate = doc.addObject("Part::Feature", name )
    fco_plate.Shape = shp_plate

    return (fco_plate)



    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        self.fco.Placement.Base = FreeCAD.Vector(position)

    
                     

def plate_lb2c (
           fc_axis_h,
           fc_axis_l,
           cl=1, cw=1, ch=0,
           pos = V0,
           name = 'lb2c_plate'):

    shp_plate = plate_thruhole_hole8 (
           side_l     = kcomp_optic.LB2C_PLATE['L'], # 76.2, 
           thick      = kcomp_optic.LB2C_PLATE['thick'],
           thruhole_d = kcomp_optic.LB2C_PLATE['thruhole_d'],
           sym_hole_d = kcomp_optic.LB2C_PLATE['sym_hole_d'],
           sym_hole_sep  = kcomp_optic.LB2C_PLATE['sym_hole_sep'],
           cbore_hole_d  = kcomp_optic.LB2C_PLATE['cbore_hole_d'],
           cbore_hole_head_d = kcomp_optic.LB2C_PLATE['cbore_hole_head_d'],
           cbore_hole_head_l = kcomp_optic.LB2C_PLATE['cbore_hole_head_l'],
           cbore_hole_sep_l = kcomp_optic.LB2C_PLATE['cbore_hole_sep_l'],
           cbore_hole_sep_s = kcomp_optic.LB2C_PLATE['cbore_hole_sep_s'],
           fc_axis_h = fc_axis_h,
           fc_axis_l = fc_axis_l,
           cl=cl, cw=cw, ch=ch,
           pos = pos,
           name = name)

    return shp_plate
                       



#doc = FreeCAD.newDocument()
#doc = FreeCAD.ActiveDocument


#plate_lb2c (fc_axis_h = VZ, fc_axis_l = VX, cl=1, cw=1, ch=0, pos=V0,
#            name = 'lb2c_plate')
 


# ---------------------- Sm1TubelensSm2 --------------------------

class SM1TubelensSm2 (object):

    """ Creates a componente formed by joining:
        the lens tube SM1LXX + SM1A2 + SM2T2, so we have:
        - on one side a SM1 external thread
        - on the other side a SM2 external thread
        And inside we have a SM1 tube lens
        Since there are threads, they may be inserted differently, so 
        size may vary. Therefore, size are approximate, and also, details
        are not drawn, such as threads, or even the part that contains the
        thread is not drawn:
                                          .........................
                        lens tube     _HH ...........             :
                                     ||..|          :             :
        LED               SM1LXX     ||  |          :             :
        _____    ..... ______________||  |          :             :
           __|   :   _|..............||  |          :             :
          |      :  | :            : ||  |          :             :
          |  30.5+  | :    SM1     : ||  |          +55.9         + 57.2
          |      :  | :            : ||  |          :SM2_TLENS_D  :
          |__    :  |_:............:.||  |          :             :
        _____|   :....|______________||  |          :             :
                    : :              ||  |          :             :
                    :3:    Lext      ||..|          :             :
                                     ||__|..........:             :
         SM1_TLENS_D=30.5              HH ........................:
                                   0.7: 5.6


        So it will be:

                           
          lens tube     _HH 
                       ||..|
            SM1LXX     ||  |
         ______________||  |
        |..............||  |
        |              ||  |
        |    SM1       ||  |
        |              ||  |
        |..............||  |
        |______________||  |
                       ||  |
             Lext      ||..|
                       ||__|
                         HH 

        The 3mm thread on the left is not drawn

    Args
        sm1l_size: length of the side of the cube (then it will be halved)
        fc_axis: direction of the tube lens: FreeCAD.Vector
        axis_2: direction big the other right side: 
        pos : position of the object
        ref_sm1: 1: if the position is referred to the sm1 end
                 0: if the position is referred to the ring end
        name: name of the freecad object
    """

    def __init__ (self, sm1l_size,
                        fc_axis = VX,
                        ref_sm1 = 1,
                        pos = V0,
                        name = 'tubelens_sm1_sm2'):

        doc = FreeCAD.ActiveDocument

        # dictionary with the dimensions
        d_sm1l_sm2 = kcomp_optic.SM1L_2_SM2

        self.base_place = (0,0,0)
        self.sm1l_size  = sm1l_size
        self.sm_dict = d_sm1l_sm2
        self.sm1_d = d_sm1l_sm2['sm1_d']
        self.sm1_l = d_sm1l_sm2['sm1_l'][sm1l_size]
        self.sm2_d = d_sm1l_sm2['sm2_d']
        self.sm2_l = d_sm1l_sm2['sm2_l']
        self.ring_d = d_sm1l_sm2['ring_d']
        self.ring_l = d_sm1l_sm2['ring_l']
        self.thick = d_sm1l_sm2['thick']
        self.fc_axis = fc_axis
        self.ref_sm1 = ref_sm1
        self.pos = pos

        if ref_sm1 == 1:
            r1 = self.sm1_d/2.
            h1 = self.sm1_l
            r2 = self.sm2_d/2.
            h2 = self.sm2_l
        else:
            r1 = self.sm2_d/2.
            h1 = self.sm2_l
            r2 = self.sm1_d/2.
            h2 = self.sm1_l
        
        shp_sm1_tube_sm2 = fcfun.add3CylsHole (r1, h1, r2, h2, 
                                               rring = self.ring_d/2,
                                               hring = self.ring_l,
                                               thick = self.thick,
                                               normal = fc_axis,
                                               pos = pos)

        doc.recompute()
        fco_sm1_tube_sm2 = doc.addObject("Part::Feature", name )
        fco_sm1_tube_sm2.Shape = shp_sm1_tube_sm2
        self.fco = fco_sm1_tube_sm2

    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        self.fco.Placement.Base = FreeCAD.Vector(position)

 
        
                                               

class BreadBoard (object):


    def __init__ (self, length,
                        width,
                        thick,
                        hole_d,
                        hole_sep,
                        hole_sep_edge,
                        cbored_hole_d,
                        cbored_hole_sep,
                        cbored_head_d,
                        cbored_head_l,
                        central_cbore = 0,
                        cl= 1,
                        cw = 1,
                        ch = 0,
                        fc_dir_h = VZ,
                        fc_dir_w = VY,
                        pos = V0,
                        name = 'breadboard'):

        doc = FreeCAD.ActiveDocument

        shp_box = fcfun.shp_box_dir(box_w = length,
                                    box_d = width,
                                    box_h = thick,
                                    fc_axis_h = fc_dir_h,
                                    fc_axis_d = fc_dir_w,
                                    cw=cl, cd=cw, ch=ch,
                                    pos = pos)
        # normalize the axis, just in case:
        axis_h = DraftVecUtils.scaleTo(fc_dir_h,1)
        axis_w = DraftVecUtils.scaleTo(fc_dir_w,1)
        axis_l = axis_w.cross(axis_h)

        # getting the corner coordinates
        if cl == 1:
           l_0 = DraftVecUtils.scaleTo(axis_l, -length/2.)
        else:
           l_0 = V0
        if cw == 1:
           w_0 = DraftVecUtils.scaleTo(axis_w, -width/2.)
        else:
           w_0 = V0
        if ch == 1:
           h_0 = DraftVecUtils.scaleTo(axis_h, -thick/2.)
        else:
           h_0 = V0

        # the point on the edge
        pos_corner = pos + l_0 + w_0 + h_0


        #Counterbored holes
        pos_1cbored = (  pos_corner 
                       + DraftVecUtils.scaleTo(axis_l, cbored_hole_sep)
                       + DraftVecUtils.scaleTo(axis_w, cbored_hole_sep))
        pos_2cbored = (  pos_corner
                       + DraftVecUtils.scaleTo(axis_l, length - cbored_hole_sep)
                       + DraftVecUtils.scaleTo(axis_w, cbored_hole_sep))
        pos_3cbored = (  pos_corner
                       + DraftVecUtils.scaleTo(axis_l, length - cbored_hole_sep)
                       + DraftVecUtils.scaleTo(axis_w, width - cbored_hole_sep))
        pos_4cbored = (  pos_corner
                       + DraftVecUtils.scaleTo(axis_l, cbored_hole_sep)
                       + DraftVecUtils.scaleTo(axis_w, width - cbored_hole_sep))

        extra_headcbore = DraftVecUtils.scaleTo(axis_h, thick-cbored_head_l)

        cbshank1 = fcfun.shp_cylcenxtr(r=cbored_hole_d/2., h=thick,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=1., 
                                      pos=pos_1cbored)
        cbholehead1 = fcfun.shp_cylcenxtr(r=cbored_head_d/2.,
                                      h=cbored_head_l,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=0., 
                                      pos=pos_1cbored +extra_headcbore)
        cbore1 = cbshank1.fuse(cbholehead1)

        cbshank2 = fcfun.shp_cylcenxtr(r=cbored_hole_d/2., h=thick,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=1., 
                                      pos=pos_2cbored)
        cbholehead2 = fcfun.shp_cylcenxtr(r=cbored_head_d/2.,
                                      h=cbored_head_l,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=0., 
                                      pos=pos_2cbored +extra_headcbore)
        cbore2 = cbshank2.fuse(cbholehead2)

        cbshank3 = fcfun.shp_cylcenxtr(r=cbored_hole_d/2., h=thick,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=1., 
                                      pos=pos_3cbored)
        cbholehead3 = fcfun.shp_cylcenxtr(r=cbored_head_d/2.,
                                      h=cbored_head_l,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=0., 
                                      pos=pos_3cbored +extra_headcbore)
        cbore3 = cbshank3.fuse(cbholehead3)

        cbshank4 = fcfun.shp_cylcenxtr(r=cbored_hole_d/2., h=thick,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=1., 
                                      pos=pos_4cbored)
        cbholehead4 = fcfun.shp_cylcenxtr(r=cbored_head_d/2.,
                                      h=cbored_head_l,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=0., 
                                      pos=pos_4cbored +extra_headcbore)
        cbore4 = cbshank4.fuse(cbholehead4)

        cboreholes_list = [cbore2, cbore3, cbore4]
        if central_cbore == 1:
            poscentral = (  pos_corner
                          + DraftVecUtils.scaleTo(axis_l, length/2.)
                          + DraftVecUtils.scaleTo(axis_w, width/2.))
            cbshankcentral = fcfun.shp_cylcenxtr(r=cbored_hole_d/2., h=thick,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=1., 
                                      pos=poscentral)
            cbholeheadcentral = fcfun.shp_cylcenxtr(r=cbored_head_d/2.,
                                      h=cbored_head_l,
                                      normal=fc_dir_h,
                                      ch = 0,
                                      xtr_top=1., xtr_bot=0., 
                                      pos=poscentral +extra_headcbore)
            cbholecentral = cbshankcentral.fuse(cbholeheadcentral)
            cboreholes_list.append(cbholecentral)

        cboresholes = cbore1.multiFuse(cboreholes_list)

        pos_1st_tap = (   pos_corner
                        + DraftVecUtils.scaleTo(axis_l, hole_sep_edge)
                        + DraftVecUtils.scaleTo(axis_w, hole_sep_edge)
                      )

        tapholes = []
        for li in range (int(length)//int(hole_sep)):
            for wi in range (int(width)//int(hole_sep)):
                # if 50/25 -> range 0,1, will make on 12,5 and 37,5
                pos_tap = (   pos_1st_tap
                           +  DraftVecUtils.scaleTo(axis_l, li * hole_sep)
                           +  DraftVecUtils.scaleTo(axis_w, wi * hole_sep))
                hole = fcfun.shp_cylcenxtr(r=hole_d/2., h=thick,
                                           normal=fc_dir_h,
                                           ch = 0,
                                           xtr_top=1., xtr_bot=1., 
                                           pos=pos_tap)
                tapholes.append(hole)

        allholes = cboresholes.multiFuse(tapholes)
        shp_breadboard = shp_box.cut(allholes)
        doc.recompute()
        fco_breadboard = doc.addObject("Part::Feature", name )
        fco_breadboard.Shape = shp_breadboard
        self.fco = fco_breadboard




def f_breadboard (d_breadboard,
                  length,
                  width,
                  cl = 1,
                  cw = 1,
                  ch = 1,
                  fc_dir_h = VZ,
                  fc_dir_w = VY,
                  pos = V0,
                  name = 'breadboard'
                   ):



    if max(length,width) >= d_breadboard['minw_cencbore']:
        central_cbore = 1
    else:
        central_cbore = 0

    breadboard = BreadBoard(
                        length = length,
                        width  = width,
                        thick  = d_breadboard['thick'],
                        hole_d  = d_breadboard['hole_d'],
                        hole_sep  = d_breadboard['hole_sep'],
                        hole_sep_edge  = d_breadboard['hole_sep_edge'],
                        cbored_hole_d  = d_breadboard['cbored_hole_d'],
                        cbored_hole_sep  = d_breadboard['cbored_hole_sep'],
                        cbored_head_d  = d_breadboard['cbore_head_d'],
                        cbored_head_l  = d_breadboard['cbore_head_l'],
                        central_cbore = central_cbore,
                        cl= cl,
                        cw = cw,
                        ch = ch,
                        fc_dir_h = fc_dir_h,
                        fc_dir_w = fc_dir_w,
                        pos = pos,
                        name = 'breadboard')


    return breadboard


#doc = FreeCAD.newDocument()
#doc = FreeCAD.ActiveDocument


#f_breadboard (kcomp_optic.BREAD_BOARD_M, 
#              length = 200.,
#              width = 500.,
#              cl = 1,
#              cw = 1,
#              ch = 1,
#              fc_dir_h = VZ,
#              fc_dir_w = VY,
#              pos = V0,
#              name = 'breadboard'
#              )
