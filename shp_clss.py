# ----------------------------------------------------------------------------
# -- TopoShp childran classes
# -- comps library
# -- Python functions for FreeCAD
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronic Technology. Rey Juan Carlos University (urjc.es)
# -- January-2018
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

import FreeCAD
import Part
import DraftVecUtils

import os
import sys
import math
import inspect
import logging

# directory this file is
filepath = os.getcwd()
import sys
# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath)

import fcfun
import fc_clss
import kcomp

from fcfun import V0, VX, VY, VZ, V0ROT
from fcfun import VXN, VYN, VZN

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ShpCyl (fc_clss.TopoShp):
    """
    Creates a shape of a cylinder
    Makes a cylinder in any position and direction, with optional extra
    heights and radius, and various locations in the cylinder

    Parameters:
    -----------
    r : float
        radius of the cylinder
    h : float
        height of the cylinder
    axis_h : FreeCAD.Vector
        vector along the cylinder height
    axis_d : FreeCAD.Vector
        vector along the cylinder radius, a direction perpendicular to axis_h
        only make sense if pos_d = 1.
        It can be None, but if None, axis_w has to be None
    axis_w : FreeCAD.Vector
        vector along the cylinder radius
        a direction perpendicular to axis_h and axis_d
        only make sense if pos_w = 1
        It can be None
    pos_h : int
        location of pos along axis_h (0, 1)
        0: the cylinder pos is centered along its height
        1: the cylinder pos is at its base (not considering xtr_h)
    pos_d : int
        location of pos along axis_d (0, 1)
        0: pos is at the circunference center
        1: pos is at the circunsference, on axis_d, at r from the circle center
           (not at r + xtr_r)
    pos_w : int
        location of pos along axis_w (0, 1)
        0: pos is at the circunference center
        1: pos is at the circunsference, on axis_w, at r from the circle center
           (not at r + xtr_r)
    xtr_top : float
        Extra height on top, it is not taken under consideration when
        calculating the cylinder center along the height
    xtr_bot : float
        Extra height at the bottom, it is not taken under consideration when
        calculating the cylinder center along the height or the position of
        the base
    xtr_r : float
        Extra length of the radius, it is not taken under consideration when
        calculating pos_d or pos_w
    pos : FreeCAD.Vector
        Position of the cylinder, taking into account where the center is


    Attributes:
    -----------
    pos_o : FreeCAD.Vector
        Position of the origin of the shape
    h_o : dictionary of FreeCAD.Vector
        vectors from the origin to the different points along axis_h
    d_o : dictionary of FreeCAD.Vector
        vectors from the origin to the different points along axis_d
    w_o : dictionary of FreeCAD.Vector
        vectors from the origin to the different points along axis_w

    
    pos_h = 1, pos_d = 0, pos_w = 0
    pos at 1:
            axis_w
              :
              :
             . .    
           .     .
         (    o    ) ---- axis_d       This o will be pos_o (origin)
           .     .
             . .    

           axis_h
              :
              :
          ...............
         :____:____:....: xtr_top
         |         |
         |         |
         |         |
         |         |
         |         |
         |         |
         |____1____|...............> axis_d
         :....o....:....: xtr_bot             This o will be pos_o


    pos_h = 0, pos_d = 1, pos_w = 0
    pos at x:

       axis_w
         :
         :
         :   . .    
         : .     .
         x         ) ----> axis_d
           .     .
             . .    

           axis_h
              :
              :
          ...............
         :____:____:....: xtr_top
         |         |
         |         |
         |         |
         x         |....>axis_d
         |         |
         |         |
         |_________|.....
         :....o....:....: xtr_bot        This o will be pos_o


    pos_h = 0, pos_d = 1, pos_w = 1
    pos at x:

       axis_w
         :
         :
         :   . .    
         : .     .
         (         )
           .     .
         x   . .     ....> axis_d

        axis_h
         :
         :
          ...............
         :____:____:....: xtr_top
        ||         |
        ||         |
        ||         |
        |x         |....>axis_d
        ||         |
        ||         |
        ||_________|.....
        ::....o....:....: xtr_bot
        :;
        xtr_r

    """
    def __init__(self, 
                 r, h, axis_h = VZ, 
                 axis_d = None, axis_w = None,
                 pos_h = 0, pos_d = 0, pos_w = 0,
                 xtr_top=0, xtr_bot=0, xtr_r=0, pos = V0):

        fc_clss.TopoShp.__init__(self, axis_d, axis_w, axis_h)

        # save the arguments as attributes:
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        for i in args:
            if not hasattr(self,i): # so we keep the attributes by CylHole
                setattr(self, i, values[i])

        # vectors from o (orig) along axis_h, to the pos_h points
        # h_o is a dictionary created in TopoShp.__init__
        self.h_o[0] =  self.vec_h(h/2. + xtr_bot)
        self.h_o[1] =  self.vec_h(xtr_bot)

        self.d_o[0] = V0
        if self.axis_d is not None:
            self.d_o[1] = self.vec_d(-r)
        elif pos_d == 1:
            logger.error('axis_d not defined while pos_d ==1')

        self.w_o[0] = V0
        if self.axis_w is not None:
            self.w_o[1] = self.vec_w(-r)
        elif pos_w == 1:
            logger.error('axis_w not defined while pos_w ==1')

        # calculates the position of the origin, and keeps it in attribute pos_o
        self.set_pos_o()

        shpcyl = fcfun.shp_cyl (r      = r + xtr_r,         # radius
                                h      = h+xtr_bot+xtr_top, # height
                                normal = self.axis_h,       # direction
                                pos    = self.pos_o)        # Position

        self.shp = shpcyl

cyl = ShpCyl (r=2, h=2, axis_h = VZ, 
              axis_d = VX, axis_w = VY,
              pos_h = 1, pos_d = 1, pos_w = 0,
              xtr_top=0, xtr_bot=1, xtr_r=2,
              pos = V0)
              #pos = FreeCAD.Vector(1,2,0))
Part.show(cyl.shp)

"""


def shp_cylhole_gen (r_out, r_in, h,
                     axis_h = VZ, axis_ra = None, axis_rb = None,
                     pos_h = 0, pos_ra = 0, pos_rb = 0,
                     xtr_top=0, xtr_bot=0,
                     xtr_r_out=0, xtr_r_in=0,
                     pos = V0):
"""
"""
    This is a generalization of shp_cylholedir.
    Makes a hollow cylinder in any position and direction, with optional extra
    heights, and inner and outer radius, and various locations in the cylinder

    Returns: a TopoShape

    Parameters:
    -----------
    r_out : float
        radius of the outside cylinder
    r_in : float
        radius of the inner hole of the cylinder
    h : float
        height of the cylinder
    axis_h : FreeCAD.Vector
        vector along the cylinder height
    axis_ra : FreeCAD.Vector
        vector along the cylinder radius, a direction perpendicular to axis_h
        only make sense if pos_ra = 0.
        It can be None.
    axis_rb : FreeCAD.Vector
        vector along the cylinder radius,
        a direction perpendicular to axis_h and axis_ra
        only make sense if pos_rb = 0
        It can be None
    pos_h : int
        location of pos along axis_h (0, 1)
        0: the cylinder pos is centered along its height, not considering
           xtr_top, xtr_bot
        1: the cylinder pos is at its base (not considering xtr_h)
    pos_ra : int
        location of pos along axis_ra (0, 1)
        0: pos is at the circunference center
        1: pos is at the inner circunsference, on axis_ra, at r_in from the
           circle center (not at r_in + xtr_r_in)
        2: pos is at the outer circunsference, on axis_ra, at r_out from the
           circle center (not at r_out + xtr_r_out)
    pos_rb : int
        location of pos along axis_ra (0, 1)
        0: pos is at the circunference center
        1: pos is at the inner circunsference, on axis_ra, at r_in from the
           circle center (not at r_in + xtr_r_in)
        2: pos is at the outer circunsference, on axis_ra, at r_out from the
           circle center (not at r_out + xtr_r_out)
    xtr_top : float
        Extra height on top, it is not taken under consideration when
        calculating the cylinder center along the height
    xtr_bot : float
        Extra height at the bottom, it is not taken under consideration when
        calculating the cylinder center along the height or the position of
        the base
    xtr_r_in : float
        Extra length of the inner radius (hollow cylinder),
        it is not taken under consideration when calculating pos_ra or pos_rb.
        It can be negative, so this inner radius would be smaller
    xtr_r_out : float
        Extra length of the outer radius
        it is not taken under consideration when calculating pos_ra or pos_rb.
        It can be negative, so this outer radius would be smaller
    pos : FreeCAD.Vector
        Position of the cylinder, taking into account where the center is


    
    pos_h = 1, pos_ra = 0, pos_rb = 0
    pos at 1:
            axis_rb
              :
              :
             . .    
           . . . .
         ( (  0  ) ) ---- axis_ra
           . . . .
             . .    

           axis_h
              :
              :
          ...............
         :____:____:....: xtr_top
         | :     : |
         | :     : |
         | :     : |
         | :  0  : |     0: pos would be at 0, if pos_h == 0
         | :     : |
         | :     : |
         |_:__1__:_|....>axis_ra
         :.:..o..:.:....: xtr_bot        This o will be pos_o (orig)
         : :  :
         : :..:
         :  + :
         :r_in:
         :    :
         :....:
           +
          r_out
         

    Values for pos_ra  (similar to pos_rb along it axis)


           axis_h
              :
              :
          ...............
         :____:____:....: xtr_top
         | :     : |
         | :     : |
         | :     : |
         2 1  0  : |....>axis_ra    (if pos_h == 0)
         | :     : |
         | :     : |
         |_:_____:_|.....
         :.:..o..:.:....: xtr_bot        This o will be pos_o (orig)
         : :  :
         : :..:
         :  + :
         :r_in:
         :    :
         :....:
           +
          r_out

"""
"""
   

    # calculate pos_o, which is at the center of the circle and at the base
    # counting xtr_bot it is is > 0
    axis_h = DraftVecUtils.scaleTo(axis_h, 1)
    
    # vectors from o (orig) along axis_h, to the pos_h points
    # h_o is a dictionary created in 
    self.h_o[0] =  DraftVecUtils.scale(axis_h, h/2. + xtr_bot)
    h_o[1] =  DraftVecUtils.scale(axis_h, xtr_bot)

    # vectors from o (orig) along axis_ra, to the pos_ra points
    ra_o = {}
    ra_o[0] = V0
    if pos_ra != 0:
        if axis_ra is not None:
            axis_ra = DraftVecUtils.scaleTo(axis_ra, 1)
            ra_o[1] = DraftVecUtils.scale(axis_ra, - r_in)
            ra_o[2] = DraftVecUtils.scale(axis_ra, - r_out)
        else :
            logger.error('axis_ra not defined while pos_ra ==1')
    
    # vectors from o (orig) along axis_rb, to the pos_rb points
    rb_o = {}
    rb_o[0] = V0
    if pos_rb != 0:
        if axis_rb is not None:
            axis_rb = DraftVecUtils.scaleTo(axis_rb, 1)
            rb_o[1] = DraftVecUtils.scale(axis_rb, - r_in)
            rb_o[2] = DraftVecUtils.scale(axis_rb, - r_out)
        else :
            logger.error('axis_rb not defined while pos_rb ==1')

    pos_o = pos + (h_o[pos_h] + ra_o[pos_ra] + rb_o[pos_rb]).negative()

    shp_hollowcyl = shp_cylholedir (r_out = r_out + xtr_r_out,
                                    r_in  = r_in + xtr_r_in,
                                    h =  h+xtr_bot+xtr_top,
                                    normal = axis_h,
                                    pos = pos_o)

    return shp_hollowcyl
"""

#cyl = shp_cylhole_gen (r_in=2, r_out=5, h=4,
#                       #axis_h = FreeCAD.Vector(1,1,0), 
#                       axis_h = VZ,
#                       axis_ra = VX, axis_rb = VYN,
#                       pos_h = 0,  pos_ra = 1, pos_rb = 2,
#                       xtr_top=0, xtr_bot=1,
#                       xtr_r_in=0, xtr_r_out=-1,
#                       pos = V0)
#                       #pos = FreeCAD.Vector(1,2,3))
#Part.show(cyl)

