
from lvmi_lab import xcor_frames, get_positions_on_ccd, hartman_focus_by_peak_finding
from astropy.io import fits

import numpy as np
from pylab import *

from sklearn.linear_model import HuberRegressor


def regress(x, y, epsilon=1):
    """ Returns a linear fitting function """
    X = np.zeros((x.shape[0],1))
    X[:,0] = x
    huber = HuberRegressor(epsilon=epsilon)
    huber.fit(X,y)

    return np.poly1d([huber.coef_[0], huber.intercept_])




def handle(f1, f2, threshold=800):

    pix_to_µm_defocus = -12/0.2 # The magic number here comes from zemax.
                            # converts pixels of defocus to microns
    hdu1 = fits.open(f1)
    hdu2 = fits.open(f2)
    bad = False
    HARTMANN = "HARTMANN"

    if hdu1[0].header[HARTMANN] != '1 0':
        print("LEFT IS NOT LEFT!!! -- LIKELY SIGN IS WRONG!!!")
        bad = True
    if hdu2[0].header[HARTMANN] != '0 1':
        print("RIGHT IS NOT RIGHT -- LIKELY SIGN IS WRONG!!!")
        bad = True

    d1 = hdu1[0].data.astype(np.float64)
    d2 = hdu2[0].data.astype(np.float64)

    tl, tr, ox, oy = hartman_focus_by_peak_finding(d1,d2, threshold=threshold, fwhm_pix=3.7)
    x,y = tl.data.T[0], tl.data.T[1]
    ox *= pix_to_µm_defocus


    l,r = map(lambda x: x.rstrip(".fits").split("-")[-1], [f1,f2])
    flav = f1.split("-")[2]

    lims = [-80,80]

    ### Top Left
    fig = figure(figsize=(7,7))
    subplot(2,2,1)
    scatter(x,y,c=ox) ; colorbar()
    clim(*lims)
    title("%s: %s/%s" % (flav, l, r))

    ### Top Right Position as a function of defocus
    subplot(2,2,2)
    XR = np.arange(0,4096,300)
    plot(y, ox, '.') ; grid(True)
    reg = regress(y, ox, epsilon=2.0)
    plot(XR, reg(XR), lw=3)
    axhline(np.median(ox))
    xlabel("Defocus [micron]")
    title("Y Slope is %3.1f [µm/4096 pix]" % (reg.coef[0]*4096))
    yslope = reg.coef[0] * 4096
    ylim(*lims)

    ### Defocus as a function of position
    subplot(2,2,3)
    XR = np.arange(0,4096,300)
    plot(x, ox,'.') ; grid(True)
    reg = regress(x, ox)
    plot(XR, reg(XR), lw=3)
    axhline(np.median(ox))
    title("X Slope is %3.1f [µm/4096 pix]" % (reg.coef[0]*4096))
    xslope = reg.coef[0]*4096

    ylabel("Defocus [micron]")
    ylim(*lims)

    subplot(2,2,4)
    hist(ox, range=[-30,30], bins=50)
    xlabel("Defocus [µm]")
    q10,q90 = np.quantile(ox, [0.1, 0.9])
    title("90percent within %3.1f to %3.1f" % (q10,q90))

    if bad:
        text(0,0,"Images not in correct order!!", fontdict={'color':'red', 'size':20})

    savefig("%s-%s-%s-fig.pdf" % (flav,l,r))
    ion()
    show()

    return xslope, yslope, np.median(ox)
