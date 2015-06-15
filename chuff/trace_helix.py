import math
import os
from matplotlib import pyplot as plt

R_TO_D = 180 / math.pi

def trace_helix(aligns, ori_psis, ori_xys, helical_twist = 167.1, helical_rise = 27.44, apix = 1.08714):

    '''
        trace a helix, correct the align parameters according to the helical parameter
        default to actin filament.
        return aligned parameters,
    '''

    # basic idea here is that the aligned parameters the distance of two particles are int times helical_rise,
    # the phi diff are int times of helical_twist
    # phi[i] = (phi[0] + i * dphi ) % 360 = (phi[i - 1] + dphi) % 360
    # y[i] = y[0] + i * dp = y[i - 1] + dp

    phis, thetas, psis, dxs, dys= zip(*aligns)[:5]
    N = len(dxs)
    angs = [0 for _ in range(N)]
    rs = [0 for _ in range(N)]
    phi_diffs = [0 for i in range(N)]
    for i in range(1, N):
        angs[i], rs[i] = get_curvature(phis[i], thetas[i], psis[i], phis[i-1], thetas[i-1], psis[i-1], helical_rise)
        phi_diffs[i] = phis[i] - phis[i-1]
    angs = window_smooth(angs, 5)
    new_xys = []
    for i in range(len(ori_xys)):
        new_xys.append([ori_xys[i][0] + dxs[i], ori_xys[i][1] + dys[i]])

    newx,newy = zip(*new_xys)
    from matplotlib import pyplot as plt
    plt.plot(newx, newy, 'x-')
    plt.show()
    dds = [0]
    for i in range(1, len(new_xys)):
        x1, y1 = new_xys[i]
        x0, y0 = new_xys[i-1]
        d2 = (x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0)
        dds.append(math.sqrt(d2))
    dxs, dys = zip(*[undo_shift(dxs[i], dys[i], ori_psis[i]) for i in range(len(dxs))])
    fit(dds, angs, phi_diffs, helical_twist, helical_rise / apix)


def smooth_xy(xys):

    from scipy.interpolate import UnivariateSpline

    xs, ys = zip(*xys)

    spl = UnivariateSpline(xs, ys)
    ys1 = spl(xs)

    spl = UnivariateSpline(ys1, xs)
    xs1 = spl(ys1)
    return zip(xs1, ys1)

def get_dist(xy1, xy2):
    '''
        get distance between two points
    '''
    dx = xy1[0] - xy2[0]
    dy = xy1[1] - xy2[1]
    return math.sqrt(dx * dx + dy * dy)

def even_xys(xys, angles = None):
    '''
        even xys takes an evened xys coordinate to even the distance between xys,
        and return the new xys
    '''
    dists = [0]
    for i in range(2, len(xys)):
        dists.append(get_dist(xys[i], xys[i - 1]))
        if angles is not None:
            ang = angles[i] * R_TO_D
            dists[i] = dists[i] / math.sin(2 * ang) / 2 * ang



def curvature_angles(thetas, psis):
    cs = [0. for _ in thetas]
    for i in range(1, len(thetas)):
        theta1, theta2 = thetas[i - 1: i + 1]
        psi1, psi2 = thetas[i - 1: i + 1]
        cs[i] = get_curve_angle(theta1, psi1, theta2, psi2)
    return cs


def get_curve_angle(theta1, psi1, theta2, psi2):
    from math import tan, acos, sqrt, pi
    pi1 = pi / 180
    theta1, psi1, theta2, psi2 = [ang * pi1 for ang in [theta1, psi1, theta2, psi2]]
    a1 = (tan(psi1), tan(theta1), 1)
    a2 = (tan(psi2), tan(theta2), 1)
    a12 = sum([aa * aa for aa in a1])
    a22 = sum([aa * aa for aa in a2])
    ca = (a1[0] * a2[0] + a1[1] * a2[1] + a1[2] * a2[2]) / sqrt(a12 * a22)
    ang = acos(ca) / pi1
    return ang

def smooth_angle(ang):
    '''
        smooth angles, so that the angle would be continuous change.
        This is not affected by gap between the data.
    '''

    from scipy.interpolate import UnivariateSpline

    spl = UnivariateSpline(range(len(ang)), ang)
    return spl(range(len(ang)))

def window_smooth(arr, window_size):
    import numpy as np

    weights = np.repeat(1.0, window_size) / window_size
    nma = np.convolve(arr, weights, 'same')
    return nma.tolist()

def fit(dds, angs, phi_diffs, helical_twist, helical_rise):
    from math import pi, sin

    dds1  = dds[:]
    for i in range(1, len(dds1)):
        ang = angs[i] * pi / 180.
        if ang == 0 or ang == 180 or ang == 360:
            pass
        else:
            dds1[i] = dds1[i] / sin(ang) * ang
    dds1 = dds[:]
    for i in range(1, len(dds1)):
        dds1[i] = dds1[i - 1] + dds[i]
    ints, slope, c = fit_integer(dds1, helical_rise)

    p_ys = ints * slope + c

    # update dds, phi_diffs
    for i in range(1, len(dds)):
        dds[i] = p_ys[i] - p_ys[i - 1]
        #update phi_diffs
        n = ints[i] - ints[i - 1]
        p_ddphi = n * helical_twist
        while p_ddphi > 360: p_ddphi -= 360
        phi_diffs[i] = p_ddphi

def fit_integer(dds, dp):
    import numpy as np
    A0 = np.arange(len(dds))
    B = np.array(dds[:])
    oldA0 = A0
    slope, c = 0, 0
    plt.clf()
    for i in range(20):
        A = np.vstack([A0, np.ones(len(dds))]).T
        slope, c = np.linalg.lstsq(A, B)[0]
        oslope = slope
#        slope = slope - (slope - dp)  / 2
        print slope,dp
        A0 = ( B - c) / slope
        A0 = np.rint(A0)
        diff = A0 - oldA0
        if len(np.unique(diff)) == 1:
            break
        oldA0 = A0
#        plt.plot(A0, dds,'o-')
    diffs = B - ( A0 * slope + c)
    diff_grad = np.gradient(diffs)
    plt.plot(np.arange(len(diff_grad)), diff_grad)
    mean, stdv = diff_grad.mean(), diff_grad.std()
    offset = 0
    for i in range(1,len(diff_grad)):
        if diff_grad[i] - diff_grad[i - 1] > stdv:
            offset += 1
            print offset
        A0[i] -= offset
    A = np.vstack([A0, np.ones(len(A0))]).T
    slope, c = np.linalg.lstsq(A, B)[0]
    print slope, c
    print A0
#    plt.plot([0,max(A0)], [c, c + max(A0) * slope])
    plt.plot(A0, B - A0 * slope - c, 'o')
    plt.savefig('test.png')

    import Image
    Image.open('test.png').save('test.jpg')
    return A0, slope, c

def undo_shift(dx, dy, psi):
    '''
        psi in counterclockwise, from original to dx,dy
    '''
    from math import pi, cos,sin
    psi = psi * pi / 180
    dx1 = dx * cos(psi) - dy * sin(psi)
    dy1 = dx * sin(psi) + cos(psi)
    return dx1,dy1

def get_curvature(phi1, theta1, psi1, phi2, theta2, psi2, dp):
    '''
        we do not need phi in this calculation. The helix is along the z axis and
        phi is the first rotation of the volume,
        which does not affect the curvature calculation

    '''
    from math import tan, acos, sqrt, pi
    pi1 = pi / 180
    phi1, theta1, psi1, phi2, theta2, psi2 = [ang * pi1 for ang in [phi1, theta1, psi1, phi2, theta2, psi2]]
    a1 = (tan(psi1), tan(theta1), 1)
    a2 = (tan(psi2), tan(theta2), 1)
    a12 = sum([aa * aa for aa in a1])
    a22 = sum([aa * aa for aa in a2])
    ca = (a1[0] * a2[0] + a1[1] * a2[1] + a1[2] * a2[2]) / sqrt(a12 * a22)
    ang = acos(ca) / pi1
    if ang == 0:
        r = float('inf')
    else:
        r = dp / (2 * ang)
    return ang, r

if __name__ == "__main__":
    import numpy as np
    import random
    #def trace_helix(aligns, ori_psis, ori_xys, helical_twist = 167.1, helical_rise = 27.44):

    import sys
    if len(sys.argv) > 2:
        align_param = sys.argv[1]
        box_file = sys.argv[2]
    else:
        align_param = "sxihrsr_bin4_gold2/output1_graphs/%04d_MT1_1.txt" % int(sys.argv[1])
        box_file = "scans/%04d_MT1_1_doc.spi" % int(sys.argv[1])
    aligns = open(align_param).read().strip().split("\n")
    aligns = [[float(m) for m in align.split()[:5]] for align in aligns]
    boxes = open(box_file).read().strip().split("\n")
    boxes = [[float(m) for m in box.split()[2:6]] for box in boxes if box.strip() and not box.strip().startswith(";")]
    ori_xys = [box[:2] for box in boxes]
    smooth_xy(ori_xys, even_dist=1)
    exit()
    xs,ys = zip(*ori_xys)
    from matplotlib import pyplot as plt
    #plt.plot(xs, ys, 'x')

    A = np.vstack([xs, np.ones(len(xs))]).T
    B = np.array(ys)
    r = np.linalg.lstsq(A, B)
    slope, c = r[0]
    print r[1], r[2], r[3]
    print slope, c
    #plt.plot([xs[0], xs[-1]], [ xs[0] * slope + c, xs[-1] * slope + c])
    #plt.show()
    ori_psis = [box[3]  for box in boxes]
    trace_helix(aligns, ori_psis, ori_xys)
