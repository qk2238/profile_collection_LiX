print("loading configuration for microscope-EM ...")

from bluesky.plan_stubs import sleep as sleeplan

ss = PositioningStackMicroscope()
#xps_trj = XPStraj('xf16idc-mc-xps-rl4.nsls2.bnl.local', 
#                  'scan', 'test', devices={'scan.Y': ss.y, 'scan.X': ss.x})  # 'scan.rY': ss.ry,
xps = XPSController("xf16idc-mc-xps-rl4.nsls2.bnl.local", "XPS-RL4")
ss.x = xps.def_motor("scan.X", "ss_x", direction=-1)
ss.y = xps.def_motor("scan.Y", "ss_y")
#ss.ry = xps.def_motor("rot.rY", "ss_ry")
xps.init_traj("scan")

try:
    camES1       = setup_cam("camES1")
    camScope     = setup_cam("camScope")
except Exception as e:
    print(f"at least one of the cameras is not avaiable: {e}")

#def raster(detectors, exp_time, fast_axis, f_start, f_end, Nfast, 
def raster(exp_time, fast_axis, f_start, f_end, Nfast,
           slow_axis=None, s_start=0, s_end=0, Nslow=1, md=None, return_pos=True):
    """ raster scan in fly mode using detectors with exposure time of exp_time
        detectors must be a member of pilatus_detectors_ext
        fly on the fast_axis, step on the slow_axis, both specified as Ophyd motors
        the fast_axis must be one of member of xps_trj.motors, for now this is hard-coded
        the specified positions are relative to the current position
        for the fast_axis are the average positions during detector exposure 
        
        use it within the run engine: RE(raster(...))
        update 2020aug: always use the re-defined pilatus detector group 
    """
    #if not set(detectors).issubset(pilatus_detectors_ext):
    #    raise Exception("only pilatus_detectors_ext can be used in this raster scan.")
    pil.set_trigger_mode(PilatusTriggerMode.ext_multi)
    detectors = [pil]

    step_size = (f_end-f_start)/(Nfast-1)
    dt = exp_time + 0.005    # exposure_period is 5ms longer than exposure_time, as defined in Pilatus
    xps.traj.define_traj(fast_axis, Nfast-1, step_size, dt, motor2=slow_axis)
    p0_fast = fast_axis.position

    ready_pos = {}
    # the user motor position may be defined in opposite sign compared to the dial position (XPS)
    running_forward = (fast_axis.user_offset_dir()==0)
    motor_pos_sign = (1 if running_forward else -1)
    ready_pos[running_forward] = (p0_fast+f_start-xps.traj.traj_par['rampup_distance'])*motor_pos_sign-step_size/2
    ready_pos[not running_forward] = (p0_fast+f_end+xps.traj.traj_par['rampup_distance'])*motor_pos_sign+step_size/2
    xps.traj.traj_par['ready_pos'] = [ready_pos[True], ready_pos[False]]
    
    xps.traj.clear_readback()
    
    if slow_axis is not None:
        p0_slow = slow_axis.position
        pos_s = p0_slow+np.linspace(s_start, s_end, Nslow)
        motor_names = [slow_axis.name, fast_axis.name]
    else:
        if Nslow != 1:
            raise Exception(f"invlaid input, did not pass slow_axis, but passed Nslow != 1 ({Nslow})")
        p0_slow = None
        pos_s = [0]   # needed for the loop in inner()
        motor_names = [fast_axis.name]

    print(pos_s)
    print(motor_names)
    xps.traj.detectors = detectors
    
    pil.exp_time(exp_time)
    pil.number_reset(True)  # set file numbers to 0
    #pil.number_reset(False) # but we want to auto increment
    pil.set_num_images(Nfast*Nslow)
    print('setting up to collect %d exposures of %.2f sec ...' % (Nfast*Nslow, exp_time))
    
    scan_shape = [Nslow, Nfast]
    _md = {'shape': tuple(scan_shape),
           'plan_args': {'detectors': list(map(repr, detectors))},
           'plan_name': 'raster',
           'plan_pattern': 'outer_product',
           'motors': tuple(motor_names),
           'hints': {},
           }
    _md.update(md or {})
    _md['hints'].setdefault('dimensions', [(('time',), 'primary')])        
   
    def line():
        print("in line()")
        yield from bps.kickoff(xps.traj, wait=True)
        yield from bps.complete(xps.traj, wait=True)
        print("leaving line()")

    @bpp.stage_decorator(detectors)
    @bpp.stage_decorator([xps.traj])
    @bpp.run_decorator(md=_md)
    @fast_shutter_decorator()
    def inner(detectors, fast_axis, slow_axis, Nslow, pos_s):
        running_forward = True
        
        print("in inner()")
        for sp in pos_s:
            print("start of the loop")
            if slow_axis is not None:
                print(f"moving {slow_axis.name} to {sp}")
                yield from mv(slow_axis, sp)

            print("starting trajectory ...")
            xps.traj.select_forward_traj(running_forward)
            yield from line()
            print("Done")
            running_forward = not running_forward

        yield from bps.collect(xps.traj)
        print("leaving inner()")

    yield from inner(detectors, fast_axis, slow_axis, Nslow, pos_s)
    yield from sleeplan(1.0)  # give time for the current em timeseries to finish
         
    if return_pos:
        if slow_axis is not None:
            yield from mov(fast_axis, p0_fast, slow_axis, p0_slow)
        else:
            yield from mov(fast_axis, p0_fast)

