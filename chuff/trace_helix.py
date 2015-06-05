import math

def trace_helix(aligns, ori_psis, ori_xys, helical_twist = 167.1, helical_rise = 27.44):
    '''
        trace a helix, correct the align parameters according to the helical parameter
        default to actin filament.
        return aligned parameters,
    '''

    # basic idea here is that the aligned parameters the distance of two particles are int times helical_rise,
    # the phi diff are int times of helical_twist
    # phi[i] = (phi[0] + i * dphi ) % 360 = (phi[i - 1] + dphi) % 360
    # y[i] = y[0] + i * dp = y[i - 1] + dp

    dxs, dys, phis, thetas, psis = zip(aligns)[:5]
    N = len(dxs)
    angs = [0 for _ in range(N)]
    rs = [0 for _ in range(N)]
    phi_diffs = [0 for i in range(N)]
    for i in range(1, N):
        angs[i], rs[i] = get_curvature(phis[i], thetas[i], psis[i], phis[i-1], thetas[i-1], psis[i-1], helical_rise)
        phi_diffs[i] = phis[i] - phis[i-1]
    angs = window_smooth(angs, 5)
    dxs, dys = zip([undo_shift(dxs[i], dys[i], ori_psis[i]) for i in range(len(dxs))])
    new_xys = []
    for i in range(len(ori_xys)):
        new_xys.append([ori_xys[i][0] + dxs[i], ori_xys[i][1] + dys[i]])

    dds = [0]
    for i in range(1, len(new_xys)):
        x1, y1 = new_xys[i]
        x0, y0 = new_xys[i-1]
        d2 = (x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0)
        dds.append(math.sqrt(d2))
    fit(dds, angs, phi_diffs, helical_twist, helical_rise)

def window_smooth(arr, window_size):
    import numpy as np

    weights = np.repeat(1.0, window_size) / window_size
    nma = np.convolve(arr, weights, 'valid')
    return nma.tolist()

def fit(dds, angs, phi_diffs, helical_twist, helical_rise):
    from math import pi, sin

    dds1  = dds[:]
    for i in range(1, len(dds1)):
        ang = angs[i] * pi / 180.
        dds1[i] = dds1[i] / sin(ang) * ang
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
    for i in range(10):
        A = np.vstack([A0, np.ones(len(dds1))]).T
        slope, c = np.linalg.lstsq(A, B)[0]
        slope = (slope + dp) / 2
        A0 = ( B - c) / slope
        A0 = np.rint(A0)
        diff = A0 - oldA0
        if len(np.unique(diff)) == 1: break
        oldA0 = A0
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
    r = dp / (2 * ang)
    return ang, r

if __name__ == "__main__":
    import numpy as np
    import random
    dp = 20
    x = [1, 2, 3, 4, 5, 5, 6, 6, 8, 8, 5, 3, 9, 10, 20]
    dds1 = np.array([x1 * dp + random.randint(-8, 15) * 1.0 for x1 in x])
    A0 = np.arange(len(dds1))
    fit_integer(dds1, 20)
