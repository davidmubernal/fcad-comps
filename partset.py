# ----------------------------------------------------------------------------
# -- Components
# -- parts_set library
# -- Python classes that creates useful sets of parts for FreeCAD
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronic Technology. Rey Juan Carlos University (urjc.es)
# -- July-2018
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------


import FreeCAD
import Part
import logging
import os
import inspect
import Draft
import DraftGeomUtils
import DraftVecUtils
import math
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

import kcomp # before, it was called mat_cte
import fcfun
import comps
import shp_clss
import fc_clss
import parts

from fcfun import V0, VX, VY, VZ
from fcfun import VXN, VYN, VZN


logging.basicConfig(level=logging.DEBUG,
                    format='%(%(levelname)s - %(message)s')

logger = logging.getLogger(__name__)



class BearWashSet (fc_clss.PartsSet):
    """ A set of bearings and washers, usually to make idle pulleys

    Parameters:
    -----------
    metric : int
        Metric (diameter) of the bolt that holds the set
    axis_h : FreeCAD.Vector
        vector along the cylinder height
    pos_h : int
        location of pos along axis_h (0,1,2,3)
        0: pos is centered along its height
        1: pos is at the base of the bearing
        2: pos is at the base of the regular washer
        3: pos is at the base of the large washer (this is the bottom)
    axis_d : FreeCAD.Vector
        vector perpendicular to the axis_h, along the radius
    pos_d : int
        location of pos along axis_d (0,1,2,3)
        0: pos is centered at the cylinder axis
        1: pos is at the bearing internal radius (defined by netric)
        2: pos is at the bearing external radius
        3: pos is at the large washer external radius
    axis_w : FreeCAD.Vector
        vector perpendicular to the axis_h and axis_d, along the radius
    pos_w : int
        location of pos along axis_w (0,1,2,3)
        0: pos is centered at the cylinder axis
        1: pos is at the bearing internal radius (defined by netric)
        2: pos is at the bearing external radius
        3: pos is at the large washer external radius
        
    group : int
        1: make a group
        0: leave as individual componentes
        
    pos : FreeCAD.Vector
        Position of the cylinder, taking into account where the center is

    Attributes:
    -----------
    metric : int or float (in case of M2.5) or even str for inches ?
        Metric of the washer

    pos_o : FreeCAD.Vector
        Position of the origin of the shape
    h_o : dictionary of FreeCAD.Vector
        vectors from the origin to the different points along axis_h
    d_o : dictionary of FreeCAD.Vector
        vectors from the origin to the different points along axis_d
    w_o : dictionary of FreeCAD.Vector
        vectors from the origin to the different points along axis_w
    h0_cen : int
    d0_cen : int
    w0_cen : int
        indicates if pos_h = 0 (pos_d, pos_w) is at the center along
        axis_h, axis_d, axis_w, or if it is at the end.
        1 : at the center (symmetrical, or almost symmetrical)
        0 : at the end

    tot_h : float
        Total height of the set: idler pulley
    r_in : float
        inner radius, the radius of the bearing
    r_ext : float
        external radius, the radius of the large washer


    idler pulley without the washer for the bolt because it is between a holder,
    The holder is in dots, not in the group
    pos_o is at the center of symmetry: see o in the drawing

                 axis_h
                   :            pos_h
                ...:...
                :     :                  bolt head
      ..........:.....:........
                               :         Holder for the pulley group
      ....._________________...:
          |_________________|     3      large washer
              |_________|         2      regular washer
              |         |         1
              |    o    |         0      bearing
              |_________|        -1
           ___|_________|___     -2      regular washer
      ....|_________________|..  -3      large washer
                               :
      .........................:         Holder for the pulley group
                :.....:                  nut
                  :.:                    bolt shank
 
                   01   2   3   pos_d, pos_w
    """

    # large washer (din9021) metric
    lwash_m_dict = { 3: 4, 4: 6}
    # regular washer (din125) has the same metric as the pulley
    # bearing tipe
    bear_m_dict = { 3: 603, 4: 624}

    def __init__(self, metric,
                 axis_h, pos_h,
                 axis_d = None, pos_d = 0,
                 axis_w = None, pos_w = 0,
                 pos = V0,
                 group = 1,
                 name = ''):

        default_name = 'bearing_idlpulley_m' + str(metric)
        self.set_name (name, default_name, change = 0)

        fc_clss.PartsSet.__init__(self,
                          axis_d = axis_d, axis_w = axis_w, axis_h = axis_h)

        # save the arguments as attributes:
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        for i in args:
            if not hasattr(self,i): # so we keep the attributes by CylHole
                setattr(self, i, values[i])

        try:
            # lwash_m is the size (metric) of the large washer
            self.lwash_m = self.lwash_m_dict[metric]
            # bear_type is the type of bearing, such as 603, 624,...
            self.bear_type = self.bear_m_dict[metric]
            # lwash_dict is the dictionary with the dimensions of large washer
            self.lwash_dict = kcomp.D9021[self.lwash_m]
            # rwash_dict is the dictionary with the dimensions of regular washer
            self.rwash_dict = kcomp.D125[metric]
            # bear is the dictionary with the dimensions of the bearing
            self.bear_dict = kcomp.BEARING[self.bear_type]
        except KeyError:
            logger.error('Bearing/washer key not found: ' + str(metric))
        else:
            # dimensions of each element
            # height, along axis_h
            self.lwash_h     = self.lwash_dict['t'] # height (thickness)
            self.lwash_r_out = self.lwash_dict['do']/2.
            self.rwash_h     = self.rwash_dict['t'] # height (thickness)
            self.rwash_r_out = self.rwash_dict['do']/2.
            self.bear_h      = self.bear_dict['t'] # height (thickness)
            self.bear_r_out  = self.bear_dict['do']/2.
            # total height:
            self.tot_h = 2 * (self.lwash_h + self.rwash_h) + self.bear_h
            #  inner radius of the pulley, the radius of the bearing
            self.r_in = self.bear_r_out
            # external radius, the radius of the large washer
            self.r_ext = self.lwash_r_out

            # pos_h/d/w = 0 are at the center
            self.h0_cen = 1
            self.d0_cen = 1
            self.w0_cen = 1

            # the origin (pos_o) is at the center of symmetry
            # vectors from o (orig) along axis_h, to the pos_h points
            # h_o is a dictionary created in Obj3D.__init__
            self.h_o[0] = V0
            self.h_o[1] = self.vec_h(-self.bear_h/2.)
            self.h_o[2] = self.vec_h(-self.bear_h/2. - self.rwash_h)
            self.h_o[3] = self.vec_h(- self.bear_h/2.
                                     - self.rwash_h
                                     - self.lwash_h)

            self.d_o[0] = V0
            if self.axis_d is not None:
                self.d_o[1] = self.vec_d(-metric/2.)
                self.d_o[2] = self.vec_d(-self.bear_r_out)
                self.d_o[3] = self.vec_d(-self.lwash_r_out)
            elif pos_d != 0:
                logger.error('axis_d not defined while pos_d != 0')

            self.w_o[0] = V0
            if self.axis_d is not None:
                self.w_o[1] = self.vec_w(-self.metric/2.)
                self.w_o[2] = self.vec_w(-self.bear_r_out)
                self.w_o[3] = self.vec_w(-self.lwash_r_out)
            elif pos_w != 0:
                logger.error('axis_w not defined while pos_w != 0')

            # calculates the position of the origin, and keeps it in attribute
            # pos_o
            self.set_pos_o()

            # creation of the bearing
            bearing = fc_clss.BearingOutl(bearing_nb = self.bear_type,
                                  axis_h = self.axis_h,
                                  pos_h = 0,
                                  axis_d = self.axis_d,
                                  axis_w = self.axis_w,
                                  pos = self.pos_o,
                                  #pos = rwash_b.get_pos_h(1),
                                  name = 'idlpull_bearing')
            self.append_part(bearing)
            # creation of the bottom regular washer
            rwash_b = fc_clss.Din125Washer(metric= metric,
                                   axis_h = self.axis_h,
                                   pos_h = 1,
                                   pos = bearing.get_pos_h(-1),
                                   name = 'idlpull_rwash_bt')
            self.append_part(rwash_b)
            # creation of the bottom large washer
            lwash_b = fc_clss.Din9021Washer(metric= self.lwash_m,
                                    axis_h = self.axis_h,
                                    pos_h = 1,
                                    pos = rwash_b.get_pos_h(-1),
                                    name = 'idlpull_lwash_bt')
            self.append_part(lwash_b)
            # creation of the top regular washer
            rwash_t = fc_clss.Din125Washer(metric= metric,
                                   axis_h = self.axis_h,
                                   pos_h = -1,
                                   pos = bearing.get_pos_h(1),
                                   name = 'idlpull_rwash_tp')
            self.append_part(rwash_t)
            # creation of the top large washer
            lwash_t = fc_clss.Din9021Washer(metric= self.lwash_m,
                                    axis_h = self.axis_h,
                                    pos_h = -1,
                                    pos = rwash_t.get_pos_h(1),
                                    name = 'idlpull_lwash_tp')
            self.append_part(lwash_t)


            if group == 1:
                self.make_group ()




#doc = FreeCAD.newDocument()
#idle_pulley = BearWashSet( metric=3,
#                 axis_h = VZ, pos_h = 0,
#                 axis_d = None, pos_d = 0,
#                 axis_w = None, pos_w = 0,
#                 pos = V0,
#                 name = '')



class NemaMotorPulleySet (fc_clss.PartsSet):
    """ Set composed of a Nema Motor and a pulley

    Number positions of the pulley will be after the positions of the motor


            axis_h
                :
                :
         _______:_______ .....11 <-> 5
        |______:_:______|.....10 <-> 4
            |  : :  |
            |  : :  |........9 <-> 3
            |  : :  |
         ___|__:_:__|___ .....8 <-> 2
        |______:_:______|.....7 <-> 1
         |     : :     | 
         |     : :     | 
         |     : :     | 
         |_____:o:_____|......6 <-> 0 (for the pulley)
         :      :   :
         :      :   :
                0...56789.......axis_d, axis_w
                    |
                01  23456 (for the pulley)

              axis_h
                  :
                  :
                  2 ............................
                 | |                           :
                 | |                           + shaft_l
              ___|1|___.............           :
        _____|____0____|_____......:..circle_h.:
       | ::       3       :: |     :  
       |                     |     :
       |                     |     :
       |                     |     + base_l
       |                     |     :
       |                     |     :
       |                     |     :
       |__________4__________|.....:
                 : :               :
                 : :               :
                 : :               :+ rear_shaft_l (optional)
                 :5:               :
                  01...2..3..4.....:...........axis_d (same as axis_w)
                   |   |  |  |
                   |   |  |  v
                   |   |  | end of the motor
                   |   |  v
                   |   | bolt holes
                   |   V
                   |  radius of the circle (cylinder)
                   v
                   radius of the shaft



                axis_w
                  :
                  :
        __________:__________.....
       /                     \....: chmf_r
       |  O               O  |
       |          _          |
       |        .   .        |
       |      (  ( )  )      |........axis_d
       |        .   .        |
       |          -          |
       |  O               O  |
       \_____________________/
       :                     :
       :.....................:
                  +
               motor_w (same as d): Nema size in inches /10

    pos_o (origin) is at pos_d=0, pos_w=0, pos_h=1

    Parameters:
    -----------

    pulley_pos_h : float
        position in mm of the pulley along the shaft
        0:  it is at the base of the shaft
        -1: the top of the pulley will be aligned with the end of the shaft

    pos_d: int
        location of pos along the axis_d  see drawing
           Locations coinciding with the motor
        0: at the axis of the shaft
        1: at the radius of the shaft
        2: at the end of the circle(cylinder) at the base of the shaft
        3: at the bolts
        4: at the end of the piece
           Locations of the pulley
        5: at the inner radius
        7: at the external radius
        7: at the pitch radius (outside the toothed part)
        8: at the end of the base (not the toothed part)
        9: at the end of the flange (V0 is no flange)

    pos_h : int
        location of pos along the axis_h, see drawing
        0: at the base of the shaft (not including the circle at the base
           of the shaft)
        1: at the end of the circle at the base of the shaft
        2: at the end of the shaft
        3: at the end of the bolt holes
        4: at the bottom base
        5: at the end of the rear shaft, if no rear shaft, it will be
           the same as pos_h = 4
        6: at the base of the pulley
        7: at the base of the bottom flange of the pulley
        8: at the base of the toothed part of the pulley
        9: at the center of the toothed part of the pulley
        10: at the end (top) of the toothed part of the pulley
        11: at the end (top) of the pulley of the pulley

       
    """

    def __init__ (self,
                  # motor parameters
                  nema_size = 17,
                  base_l = 32.,
                  shaft_l = 24.,
                  shaft_r = 0,
                  circle_r = 11.,
                  circle_h = 2.,
                  chmf_r = 1, 
                  rear_shaft_l=0,
                  bolt_depth = 3.,
                  # pulley parameters
                  pulley_pitch = 2.,
                  pulley_n_teeth = 20,
                  pulley_toothed_h = 7.5,
                  pulley_top_flange_h = 1.,
                  pulley_bot_flange_h = 0,
                  pulley_tot_h = 16.,
                  pulley_flange_d = 15.,
                  pulley_base_d = 15.,
                  pulley_tol = 0,
                  pulley_pos_h = -1,
                  # general parameters
                  axis_d = VX,
                  axis_w = None,
                  axis_h = VZ,
                  pos_d = 0,
                  pos_w = 0,
                  pos_h = 1,
                  pos = V0,
                  group = 1,
                  name = ''):

        default_name = 'nema' + str(nema_size) + '_pulley_set'
        self.set_name (name, default_name, change=0)

        if (axis_w is None) or (axis_w == V0):
            axis_w = axis_h.cross(axis_d)

        fc_clss.PartsSet.__init__(self, axis_d = axis_d,
                                  axis_w = axis_w, axis_h = axis_h)

        # save the arguments as attributes:
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        for i in args:
            if not hasattr(self,i):
                setattr(self, i, values[i])

        # pos_w = 0 and pos_d are at the center, pos_h
        self.d0_cen = 1 #symmetric
        self.w0_cen = 1 #symmetric
        self.h0_cen = 0

        # creation of the motor, we don't know all the relative positions
        # so we create it at pos_d=pos_w = 0, pos_h = 1

        nema_motor = comps.PartNemaMotor (
                              nema_size = nema_size,
                              base_l = base_l,
                              shaft_l = shaft_l,
                              shaft_r = shaft_r,
                              circle_r = circle_r,
                              circle_h = circle_h,
                              chmf_r = chmf_r, 
                              rear_shaft_l= rear_shaft_l,
                              bolt_depth = bolt_depth,
                              bolt_out  = 0,
                              cut_extra = 0,
                              axis_d = self.axis_d,
                              axis_w = self.axis_w,
                              axis_h = self.axis_h,
                              pos_d = 0,
                              pos_w = 0,
                              pos_h = 0,
                              pos = pos)

        self.append_part(nema_motor)
        nema_motor.parent = self

        self.shaft_r = nema_motor.shaft_r
        self.circle_r = nema_motor.circle_r
        self.circle_h = nema_motor.circle_h

        # creation of the pulley. Locate it at pos_d,w,h = 0
        gt_pulley = comps.PartGtPulley (
                              pitch = pulley_pitch,
                              n_teeth = pulley_n_teeth,
                              toothed_h = pulley_toothed_h,
                              top_flange_h = pulley_top_flange_h,
                              bot_flange_h = pulley_bot_flange_h,
                              tot_h = pulley_tot_h,
                              flange_d = pulley_flange_d,
                              base_d = pulley_base_d,
                              shaft_d = 2 * self.shaft_r,
                              tol = 0,
                              axis_d = self.axis_d,
                              axis_w = self.axis_w,
                              axis_h = self.axis_h,
                              pos_d = 0,
                              pos_w = 0,
                              pos_h = 0,
                              pos = pos,
                              model_type = 1) # dimensional model

        if pulley_pos_h < 0: #top of the pulley aligned with top of the shaft
            # shaft_l includes the length of the circle
            pulley_pos_h = shaft_l - gt_pulley.tot_h
            if pulley_pos_h < 0:
                pulley_pos_h = 0
            self.pulley_pos_h = pulley_pos_h
        elif pulley_pos_h + gt_pulley.base_h > shaft_l:
            logger.warning("pulley seems to be out of the shaft")

        self.append_part(gt_pulley)
        gt_pulley.parent = self

        # conversions of the relative points from the parts to the total set
        self.d_o[0] = nema_motor.d_o[0] # V0
        self.d_o[1] = nema_motor.d_o[1]
        self.d_o[2] = nema_motor.d_o[2]
        self.d_o[3] = nema_motor.d_o[3]
        self.d_o[4] = nema_motor.d_o[4]
        self.d_o[5] = gt_pulley.d_o[2]
        self.d_o[6] = gt_pulley.d_o[3]
        self.d_o[7] = gt_pulley.d_o[4]
        self.d_o[8] = gt_pulley.d_o[5]
        self.d_o[9] = gt_pulley.d_o[6]

        self.w_o[0] = nema_motor.w_o[0] # V0
        self.w_o[1] = nema_motor.w_o[1]
        self.w_o[2] = nema_motor.w_o[2]
        self.w_o[3] = nema_motor.w_o[3]
        self.w_o[4] = nema_motor.w_o[4]
        self.w_o[5] = gt_pulley.w_o[2]
        self.w_o[6] = gt_pulley.w_o[3]
        self.w_o[7] = gt_pulley.w_o[4]
        self.w_o[8] = gt_pulley.w_o[5]
        self.w_o[9] = gt_pulley.w_o[6]

        self.h_o[0] = nema_motor.h_o[0] # V0 (origin) base of the shaft
        self.h_o[1] = nema_motor.h_o[1] # end of the circle
        self.h_o[2] = nema_motor.h_o[2] # end of the shaft
        self.h_o[3] = nema_motor.h_o[3] # bottom end of the bolt holes
        self.h_o[4] = nema_motor.h_o[4] # bottom of the base 
        self.h_o[5] = nema_motor.h_o[5] # rear shaft
        # position of the base of the shaft (including the circle)
        # + nema_motor.h_o[0] = V0 (not needed)
        # relative position of the base of the pulley: V0 (not needed)
        # + gt_pulley.h_o[0] = V0 -> base of the pulley
        # distance from the base of the shaft (circle included) to the base
        # of the pulley:
        # + self.vec_h(self.pulley_pos_h):
        #self.h_o[6]  = (   nema_motor.h_o[0] + gt_pulley.h_o[0]
        #                 + self.vec_h(self.pulley_pos_h))
        self.h_o[6]  = self.vec_h(self.pulley_pos_h)
        self.h_o[7]  = self.h_o[6] + gt_pulley.h_o[1]
        self.h_o[8]  = self.h_o[6] + gt_pulley.h_o[2]
        self.h_o[9]  = self.h_o[6] + gt_pulley.h_o[3]
        self.h_o[10] = self.h_o[6] + gt_pulley.h_o[4]
        self.h_o[11] = self.h_o[6] + gt_pulley.h_o[5]

        # check if the pulley is on top of the shaft or not:
        if self.h_o[11].Length > self.h_o[5].Length:
            self.tot_h = self.h_o[11].Length + self.h_o[0].Length
        else:
            self.tot_h = self.h_o[5].Length + self.h_o[0].Length

        self.set_pos_o(adjust = 1)
        self.set_part_place(nema_motor)
        self.set_part_place(gt_pulley, self.get_o_to_h(6))

        self.place_fcos()
        if group == 1:
            self.make_group()

    def get_nema_motor(self):
        """ gets the nema motor"""
        part_list = self.get_parts()
        for part_i in part_list:
            if isinstance(part_i, PartNemaMotor):
                return part_i

    def get_gt_pulley(self):
        """ gets the gt2 pulley"""
        part_list = self.get_parts()
        for part_i in part_list:
            if isinstance(part_i, PartGtPulley):
                return part_i


 

motor_pulley = NemaMotorPulleySet(pulley_pos_h = 10,
                                  rear_shaft_l = 10,
                                  axis_d = VZ,
                                  axis_w = None,
                                  axis_h = VX,
                                  pos_d = 2,
                                  pos_w = 0,
                                  pos_h = 4,
                                  pos = V0,
                                  )



class NemaMotorPulleyHolderSet (fc_clss.PartsSet):
    """ Set composed of a Nema Motor with a pulley and the holder of the motor

    Number positions of the pulley will be after the positions of the motor


            axis_h
                :
                :
         _______:_______ .....13 <-> 5
        |______:_:______|.....12 <-> 4
            |  : :  |
            |  : :  |........11 <-> 3
            |  : :  |
         ___|__:_:__|___ .....10 <-> 2
        |______:_:______|.....  <-> 1 (not used)
         |     : :     | 
         |     : :     | 
         |     : :     | 
         |_____:o:_____|......9 <-> 0 (for the pulley)
         :      :   :
         :      :   :
                0...567.......axis_d, axis_w (pos_d for motor_pulley)
                    |
                    234   (correspondence with the pulley)
                    2: inner radius
                    3: external radius
                    4: pitch radius
                    5, 6: base and flange not defined here

              axis_h
                  :
                  :
                  6 ............................
                 | |                           :
                 | |                           + shaft_l
              ___|5|___.............           :
        _____|____1____|_____......:..circle_h.: (same as 3 in the holder)
       | ::               :: |     :  
       |                     |     :
       |                     |     :
       |                     |     + base_l
       |                     |     :
       |                     |     :
       |                     |     :
       |__________7__________|.....:
                 : :               :
                 : :               :
                 : :               :+ rear_shaft_l (optional)
                 : :               :
                 :8:...............:...........axis_d (same as axis_w)



                axis_w
                  :
                  :
        __________:__________.....
       /                     \....: chmf_r
       |  O               O  |
       |          _          |
       |        .   .        |
       |      (  ( )  )      |........axis_d
       |        .   .        |
       |          -          |
       |  O               O  |
       \_____________________/
       :                     :
       :.....................:
                  +
               motor_w (same as d): Nema size in inches /10


              axis_d
                 :
         ________5_________  9: belt pitch radius
        ||                || 8: belt outer radius
        || O     4_     O || 7: belt inner radius
        ||    /      \    || 6: shaft_radius
        ||   |   3    |   ||
        ||    \      /    || 10: shaft radius 
        || O     2_     O || 11: belt inner radius, 12:belt outer r; 13: pitch r
        ||_______1________|| .....
        ||_______o____::__|| ..... wall_thick.....> axis_w
                 0    1 2  3 (axis_w)
                  4567
                  ||||
                  |||7: belt pitch radius
                  |||
                  ||6 : belt outer radius
                  ||
                  |5  : belt inner radius
                  |
                  4: shaft radius
                  (along axis_w is symmetrical: negative number will get
                   the other side)


               axis_h (for the holder is pointing to the opposite direction)
                 :
                 :
                 :
         ________0_________ ....................................> axis_w
        |  ::  :    :  ::  |                                  :
        |__::__:_1__:__::__|....................              :
        ||                ||....+ motor_min_h  :              :
        ||  ||   2    ||  ||                   :              +tot_h
        ||  ||        ||  ||                   + motor_max_h  :
        ||  ||        ||  ||                   :              :
        ||  ||   3    ||  ||...................:              :
        ||_______4________||..................................:
        :   :          :   :
        :   :          :   :
        :   :          :   :
        :   :          :   :
        :   :..........:   :
        :   bolt_wall_sep  :
        :                  :
        :                  :
        :.....tot_w........:

    pos_h: int
        location along axis_h
        0 : top of the holder
        1 : top inner wall: top of motor body
        2 : top end of the rail
        3 : bottom end of the rail
        4 : bottom end of the rail
        5 : end of the motor circle (cylinder)
        6 : end of the shaft
        7 : base of motor body
        8 : rear shaft
        9 : base of pulley
        10: bottom of pulley toothed part
        11: middle of pulley toothed part
        12: top of pulley toothed part
        13: end of pulley


    """


    def __init__ (self,
                  # motor parameters
                  nema_size = 17,
                  motor_base_l = 32.,
                  motor_shaft_l = 24.,
                  motor_shaft_r = 0,
                  motor_circle_r = 11.,
                  motor_circle_h = 2.,
                  motor_chmf_r = 1, 
                  motor_rear_shaft_l=0,
                  motor_bolt_depth = 3.,
                  # pulley parameters
                  pulley_pitch = 2.,
                  pulley_n_teeth = 20,
                  pulley_toothed_h = 7.5,
                  pulley_top_flange_h = 1.,
                  pulley_bot_flange_h = 0,
                  pulley_tot_h = 16.,
                  pulley_flange_d = 15.,
                  pulley_base_d = 15.,
                  pulley_tol = 0,
                  pulley_pos_h = -1,
                  # holder parameters
                  hold_wall_thick = 4.,
                  hold_motorside_thick = 4.,
                  hold_reinf_thick = 4.,
                  hold_rail_min_h =10.,
                  hold_rail_max_h =20.,
                  hold_rail = 1, # if there is a rail or not at the profile side
                  hold_motor_xtr_space = 2., # counting on one side
                  hold_bolt_wall_d = 4., # Metric of the wall bolts
                  hold_bolt_wall_sep = 0, # optional
                  hold_chmf_r = 1.,
                  # general parameters
                  axis_d = VX,
                  axis_w = None,
                  axis_h = VZ,
                  pos_d = 0,
                  pos_w = 0,
                  pos_h = 1,
                  pos = V0,
                  group = 0,
                  name = ''):


        default_name = 'nema_' + str(nema_size) + 'holer_motor_pulley_set'
        self.set_name (name, default_name, change=0)

        if (axis_w is None) or (axis_w == V0):
            axis_w = axis_h.cross(axis_d)

        fc_clss.PartsSet.__init__(self, axis_d = axis_d,
                                  axis_w = axis_w, axis_h = axis_h)


        # save the arguments as attributes:
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        for i in args:
            if not hasattr(self,i):
                setattr(self, i, values[i])

        # pos_w = 0 is at the center
        self.d0_cen = 0
        self.w0_cen = 1 #symmetric
        self.h0_cen = 0

        # creation of the motor with pulley
        nema_motor_pulley = NemaMotorPulleySet (
                  # motor parameters
                  nema_size = nema_size,
                  base_l = motor_base_l,
                  shaft_l = motor_shaft_l,
                  shaft_r = motor_shaft_r,
                  circle_r = motor_circle_r,
                  circle_h = motor_circle_h,
                  chmf_r = motor_chmf_r, 
                  rear_shaft_l = motor_rear_shaft_l,
                  bolt_depth = motor_bolt_depth,
                  # pulley parameters
                  pulley_pitch = pulley_pitch,
                  pulley_n_teeth = pulley_n_teeth,
                  pulley_toothed_h = pulley_toothed_h,
                  pulley_top_flange_h = pulley_top_flange_h,
                  pulley_bot_flange_h = pulley_bot_flange_h,
                  pulley_tot_h = pulley_tot_h,
                  pulley_flange_d = pulley_flange_d,
                  pulley_base_d = pulley_base_d,
                  pulley_tol = pulley_tol,
                  pulley_pos_h = pulley_pos_h,
                  # general parameters
                  axis_d = axis_d,
                  axis_w = axis_w,
                  axis_h = axis_h,
                  pos_d = 0,
                  pos_w = 0,
                  pos_h = 0,
                  pos = pos)

        self.append_part(nema_motor_pulley)
        nema_motor_pulley.parent = self

        nema_holder = parts.PartNemaMotorHolder(
                  nema_size = nema_size,
                  wall_thick = hold_wall_thick,
                  motorside_thick = hold_motorside_thick,
                  reinf_thick = hold_reinf_thick,
                  motor_min_h = hold_rail_min_h,
                  motor_max_h = hold_rail_max_h,
                  rail = hold_rail, 
                  motor_xtr_space = hold_motor_xtr_space,
                  bolt_wall_d = hold_bolt_wall_d,
                  bolt_wall_sep = hold_bolt_wall_sep,
                  chmf_r = hold_chmf_r,
                  axis_h = axis_h.negative(), #pointing down
                  axis_d = axis_d,
                  axis_w = axis_w,
                  #pos_h = 0, # at the point of union with the motor
                  pos_h = 0, # at the point of union with the motor
                  pos_d = 0,
                  pos_w = 0,
                  pos = pos)

        self.append_part(nema_holder)
        nema_holder.parent = self

        self.d_o[0] = nema_holder.d_o[0] # end that is attatched to the profile
        self.d_o[1] = nema_holder.d_o[1] # inside the wall that is attached
        self.d_o[2] = nema_holder.d_o[2] # bolt holes closed to the wall
        self.d_o[3] = nema_holder.d_o[3] # at the motor axis
        self.d_o[4] = nema_holder.d_o[4] # bolt holes away from the wall
        self.d_o[5] = nema_holder.d_o[5] # the other end, opposite to the wall
        # not sure which order to take
        # taking first away from the wall
        #             axis -v                 shaft radius
        self.d_o[6] = nema_holder.d_o[3] + nema_motor_pulley.d_o[1]
        #             axis -v                 belt inner radius
        self.d_o[7] = nema_holder.d_o[3] + nema_motor_pulley.d_o[5]
        #             axis -v                 belt external radius
        self.d_o[8] = nema_holder.d_o[3] + nema_motor_pulley.d_o[6]
        #             axis -v                 belt pitch radius
        self.d_o[9] = nema_holder.d_o[3] + nema_motor_pulley.d_o[7]

        # then, taking those closer to the the wall
        #             axis -v                 shaft radius
        self.d_o[10] = nema_holder.d_o[3] + nema_motor_pulley.d_o[1].negative()
        #             axis -v                 belt inner radius
        self.d_o[11] = nema_holder.d_o[3] + nema_motor_pulley.d_o[5].negative()
        #             axis -v                 belt external radius
        self.d_o[12] = nema_holder.d_o[3] + nema_motor_pulley.d_o[6].negative()
        #             axis -v                 belt pitch radius
        self.d_o[13] = nema_holder.d_o[3] + nema_motor_pulley.d_o[7].negative()

        # symmetric
        self.w_o[0] = nema_holder.w_o[0] # motor axis
        self.w_o[1] = nema_holder.w_o[1] # rail (or wall bolt holes)
        self.w_o[2] = nema_holder.w_o[2] # bolt holes for the motor
        self.w_o[3] = nema_holder.w_o[3] # end of the piece
        self.w_o[4] = nema_motor_pulley.w_o[4] # shaft radius
        self.w_o[5] = nema_motor_pulley.w_o[5] # belt inner radius
        self.w_o[6] = nema_motor_pulley.w_o[6] # belt outer radius
        self.w_o[7] = nema_motor_pulley.w_o[7] # belt pitch radius

        self.h_o[0] = nema_holder.h_o[0] # top of the holder
        self.h_o[1] = nema_holder.h_o[1] # top inner wall: top of motor body
        self.h_o[2] = nema_holder.h_o[2] # top end of the rail
        self.h_o[3] = nema_holder.h_o[3] # bottom end of the rail
        self.h_o[4] = nema_holder.h_o[4] # bottom end of the rail
        # end of the motor circle (cylinder):
        self.h_o[5] = self.h_o[1] + nema_motor_pulley.h_o[1]
        self.h_o[6] = self.h_o[1] + nema_motor_pulley.h_o[2] #end of the shaft
        self.h_o[7] = self.h_o[1] + nema_motor_pulley.h_o[4] #base of motor body
        self.h_o[8] = self.h_o[1] + nema_motor_pulley.h_o[5] #rear shaft
        self.h_o[9] = self.h_o[1] + nema_motor_pulley.h_o[5] #base of pulley
        # bottom of pulley toothed part
        self.h_o[10] = self.h_o[1] + nema_motor_pulley.h_o[8]
        # middle of pulley toothed part
        self.h_o[11] = self.h_o[1] + nema_motor_pulley.h_o[9]
        # top of pulley toothed part
        self.h_o[12] = self.h_o[1] + nema_motor_pulley.h_o[10]
        # end of pulley
        self.h_o[13] = self.h_o[1] + nema_motor_pulley.h_o[11]

        self.set_pos_o(adjust = 1)
        self.set_part_place(nema_holder)
        self.set_part_place(nema_motor_pulley, self.get_o_to_h(1)
                                              +self.get_o_to_d(3))

        self.place_fcos()
        if group == 1:
            self.make_group()

        def get_nema_holder(self):
            """ gets the nema holder"""
            part_list = self.get_parts()
            for part_i in part_list:
                if isinstance(part_i, PartNemaMotorHolder):
                    return part_i

        def get_nema_motor_pulley(self):
            """ gets the nema motor pulley set"""
            part_list = self.get_parts()
            for part_i in part_list:
                if isinstance(part_i, PartNemaMotorPulleySet):
                    return part_i



#doc = FreeCAD.newDocument()
#nemamotorpullhold = NemaMotorPulleyHolderSet(
#                                      axis_d = VX,
#                                      axis_w = VY,
#                                      axis_h = VZ,
#                                      pos_d = 1,
#                                      pos_w = 3,
#                                      pos_h = 1,
#                                      pos = V0
#                                        )
        

