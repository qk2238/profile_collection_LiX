import time
import pylab as plt

last_scan_uid = None
last_scan_id = None

def fetch_scan(**kwargs):
    if len(kwargs) == 0:  # Retrieve last dataset
        header = db[-1]
        return header, header.table(fill=True)
    else:
        headers = db(**kwargs)
        return headers, db.get_table(headers, fill=True)

def list_scans(**kwargs):
    headers = list(db(**kwargs))
    uids = []
    for h in headers:
        s = "%8s%10s%10s" % (h.start['proposal_id'], h.start['run_id'], h.start['plan_name'])
        try:
            s = "%s%8d" % (s, h.start['num_points'])
        except:
            s = "%s%8s" % (s,"")
        t = time.asctime(time.localtime(h.start['time'])).split()
        s = s + (" %s-%s-%s %s " % (t[4], t[1], t[2], t[3])) 
        try:
            s = "%s %s" % (s, h.start['sample_name'])
        except:
            pass
        print(s, h.start['uid'])
        uids.append(h.start['uid'])

    return(uids)

# map xv vlaue from range xm1=[min, max] to range xm2
def x_conv(xm1, xm2, xv):
    a = (xm2[-1]-xm2[0])/(xm1[-1]-xm1[0])
    return xm2[0]+a*(xv-xm1[0])

# example: plot_data(data, "cam04_stats1_total", "hfm_x1", "hfm_x2")
def plot_data(data, ys, xs1, xs2=None, thresh=0.8, take_diff=False, no_plot=False):
    yv = data[ys]
    xv1 = np.asarray(data[xs1])
    if take_diff:
        yv = np.fabs(np.diff(yv))
        xv1 = (xv1[1:]+xv1[:-1])/2

    idx = yv>thresh*yv.max()
    xp = np.average(xv1[idx], weights=yv[idx])
    xx = xv1[yv==yv.max()]
    pk_ret = {xs1: xp, ys: np.average(yv[idx])}
    xm1 = [xv1[0], xv1[len(xv1)-1]]
    
    if not no_plot:
        fig = plt.figure(figsize=(8,6))
        ax1 = fig.add_subplot(111)
        ax1.plot(xv1, yv)
        ax1.plot(xv1[idx],yv[idx],"o")
        ax1.plot([xp,xp],[yv.min(), yv.max()])
        ax1.set_xlabel(xs1)
        ax1.set_ylabel(ys)
        ax1.set_xlim(xm1)

    if xs2!=None:
        xv2 = np.asarray(data[xs2])
        if take_diff:
            xv2 = (xv2[1:]+xv2[:-1])/2
        xm2 = [xv2[0], xv2[len(xv2)-1]]
        if not no_plot:
            ax2 = ax1.twiny()
            ax2.set_xlabel(xs2)
            #xlim1 = ax1.get_xlim()
            ax2.set_xlim(xm2)
        print("y max at %s=%f, %s=%f" % (xs1, xx, xs2, x_conv(xm1, xm2, xx)))
        print("y center at %s=%f, %s=%f" % (xs1, xp, xs2, x_conv(xm1, xm2, xp)))
        pk_ret[xs2] = x_conv(xm1, xm2, xp)
    else:
        print("y max at %s=%f" % (xs1, xx))
        print("y center at %s=%f" % (xs1, xp))

    if no_plot:
        return pk_ret