import numpy as np
def get_grid(ratio=1.1,wc_thickness=1E-4,nx=32):
    dx_c = wc_thickness*(1-ratio)/(1-ratio**nx)
    dx = []
    for x_c in range(nx):
        dx.append(dx_c)
        dx_c *= ratio
    return np.cumsum(dx) -0.5*np.array(dx)