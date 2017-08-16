from collections import deque
from bluesky.examples import motor, det
from bluesky.spec_api import ct, a2scan, d2scan, mesh, inner_spec_decorator, partition

ct = fast_shutter_decorator()(ct)
scan = fast_shutter_decorator()(a2scan)
dscan = fast_shutter_decorator()(d2scan)
mesh = fast_shutter_decorator()(mesh)

gs.DETS = [det]



#def dscan(*args, time=None, md=None):
#    """
#    Scan over one multi-motor trajectory relative to current positions.
#
 #   Parameters
  #  ----------
   # *args
    #    patterned like (``motor1, start1, stop1,`` ...,
     #                   ``motorN, startN, stopN, intervals``)
     #   where 'intervals' in the number of strides (number of points - 1)
     #   Motors can be any 'setable' object (motor, temp controller, etc.)
   # time : float, optional
   #     applied to any detectors that have a `count_time` setting
   # md : dict, optional
    #    metadata
    #"""
#    if len(args) % 3 != 1:
#        raise ValueError("wrong number of positional arguments")
#    motors = []
#    for motor, start, stop, in partition(3, args[:-1]):
#        motors.append(motor)

#    intervals = list(args)[-1]
#    num = 1 + intervals

#    inner = inner_spec_decorator('d2scan', time, motors=motors)(
 #       bp.relative_inner_product_scan)
#
 #   return (yield from inner(gs.DETS, num, *(args[:-1]), md=md, 
  #                           per_step=one_nd_step_with_shutter))
