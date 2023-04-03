
# In IR Band if the left frame has spectra to the right of right frame, move positive


# must run brew install python-tk
import tkinter as tk
import customtkinter as ctk
import json
from lvmi_lab import xcor_frames, get_positions_on_ccd, hartman_focus_by_peak_finding
from astropy.io import fits
from pylab import *
import os 
import subprocess as SP

import numpy as np
from sklearn.linear_model import HuberRegressor, LinearRegression
from sklearn.datasets import make_regression


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")


def regress(x, y):
    """ Returns a linear fitting function """
    X = np.zeros((x.shape[0],1))
    X[:,0] = x
    huber = HuberRegressor(epsilon=1)
    huber.fit(X,y)

    return np.poly1d([huber.coef_[0], huber.intercept_])



def handle(f1, f2):

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

    tl, tr, ox, oy = hartman_focus_by_peak_finding(d1,d2, threshold=5000)
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
    reg = regress(y, ox)
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

    if bad:
        text(0,0,"Images not in correct order!!", fontdict={'color':'red', 'size':20})

    savefig("%s-%s-%s-fig.pdf" % (flav,l,r))
    ion()
    show()

    return xslope, yslope, np.median(ox)



##### GUI Stuff below

class BS:
    Expose = "Expose"
    Rsync = "Rsync"
    Measure_Focus = "Measure Focus"
    Do_all = "Do all"

class LS:
    """ GUI Labels """
    Steps = "Steps"
    Inputs = "Inputs"
    Band = "Band/Number"
    DeltaX = "DeltaX"
    DeltaY = "DeltaY"
    Defocus = "Defocus"
    ABCs = "ABCs in"
    ABCs_out = "ABCs out"
    Options = "Options"
    Image_Number = "Image Number"
    Rsync_cmd = "Rsync Command [opt]" # don't remove [opt] from the name
    Path = "Path [opt]" # don't remove [opt] from the name

class App(ctk.CTk):
    button_names: list[str] = [BS.Expose, BS.Rsync, BS.Measure_Focus, BS.Do_all]
    autoincrement: bool = False

    
    # Text labels have a name and a row position and a number of entries
    labels: list[tuple[str, int, int]] = [
        (LS.Steps, 0, 0),
        (LS.Inputs, 4, 0),
        (LS.Band, 5, 0),
        (LS.DeltaX, 6, 1),
        (LS.DeltaY, 7, 1),
        (LS.Defocus, 8, 1),
        (LS.ABCs, 9, 1),
        (LS.ABCs_out, 10, 1),
        (LS.Options, 12, 0),
        (LS.Image_Number, 13, 1),
        (LS.Rsync_cmd, 14, 1),
        (LS.Path, 15, 1),
    ]

    entries = {}

    def change_entry(self, *args):
        ''' Callback whenever an entry changes '''
        self.save_config()

    def add_labels(self):
        def doit(name, column, row, **kwargs):
            lbl = ctk.CTkLabel(self, text=name)
            lbl.grid(column=column, row=row, **kwargs)
        
        def doitE(name, column, row, **kwargs):
            doit(name,column,row, sticky="E", padx=10, **kwargs)
        
        def add_entry(name: str, column: int, row: int):
            v = ctk.StringVar(name=name)
            v.trace('w', self.change_entry) 


            if "[opt]" in name:
                e = ctk.CTkEntry(self, width=400, textvariable=v)
                e.grid(column=column, row=row, columnspan=3)
            elif "ABC" in name:
                e = ctk.CTkEntry(self, textvariable=v, width=200)
                e.grid(column=column, row=row, columnspan=2, sticky="W")
            else:
                e = ctk.CTkEntry(self, textvariable=v)
                e.grid(column=column, row=row, sticky="W")
            

            self.entries[name] = v

        
        for lbl, row, nentries in self.labels:
            doitE(lbl, 0, row)

            if nentries > 0:
                for i in range(nentries):
                    add_entry(lbl, i+1, row)

        add_entry("band", 1, 5)
        add_entry("spec_number", 2, 5)


    def add_buttons(self):
        def doit(name, column, row, **kwargs):
            but = ctk.CTkButton(self, text=name, command=lambda: self.button_callback(name))
            but.grid(column=column, row=row, **kwargs)

            if name == BS.Expose:
                pass
                #c1 = ctk.CTkCheckBox(self, text="Auto increment?", command= lambda: self.checkbox_callback("autoincrement"))
                #c1.grid(column=column+1,row=row)

        for i,n in enumerate(self.button_names):
            doit(n, 1, i)

    def checkbox_callback(self, checkbox):
        if checkbox == "autoincrement":
            self.autoincrement = not self.autoincrement
            print(self.autoincrement)

    def button_callback(self, cmd):
        print("#" * 80)

        if cmd == BS.Rsync:
            todo = self.entries[LS.Rsync_cmd].get()
            res = SP.run(todo.split())
            print(res.stdout)

        if cmd == BS.Measure_Focus:
            print("Measuring ...")
            path = self.entries[LS.Path].get()
            band = self.entries["band"].get()
            number = int(self.entries["spec_number"].get())
            frame = int(self.entries[LS.Image_Number].get())
            f1 = os.path.join(path, f"sdR-s-{band}{number}-{frame:08}.fits.gz")
            f2 = os.path.join(path, f"sdR-s-{band}{number}-{frame+1:08}.fits.gz")
            xslope, yslope, defocus = handle(f1,f2)
            
            print("slopes: %4.1f %4.1f" % (xslope, yslope))
            self.entries[LS.DeltaX].set("%4.1f" % xslope)
            self.entries[LS.DeltaY].set("%4.1f" % yslope)
            self.entries[LS.Defocus].set("%4.1f" % defocus)

        if cmd == BS.Expose:
            cur = self.entries[LS.Image_Number].get()
            self.entries[LS.Image_Number].set(int(cur)+2)


        """ 
        band X [CW] Y [CW] 
        z    B+ C-   

        
        """
        if cmd == "Do all":
            band = self.entries["band"].get()

            print(band)
            if band == "r":
                sign = -1
                foc_sign = -1
            elif band == "z":
                sign = -1
                foc_sign = 1
            elif band == "b":
                sign = 1
                foc_sign = 1
            
            CCD_dimension = 70
            Triangle_height = 235.50
            AB_height = 271.93
            micron_to_mm = 1e-3
            A,B,C = map(float, self.entries[LS.ABCs].get().split())
            Dx = float(self.entries[LS.DeltaX].get())*micron_to_mm
            Dy = float(self.entries[LS.DeltaY].get())*micron_to_mm
            offset = foc_sign*float(self.entries[LS.Defocus].get())*micron_to_mm


            Qx = sign*Dy/CCD_dimension
            Qy = Dx/CCD_dimension

            print("Tilts: %1.4f %1.4f [rad]" % (Qx, Qy))

            dA = np.tan(Qx)*Triangle_height
            dB = np.tan(Qy)*AB_height/2
            dC = -dB

            print("dA dB dC: %1.3f %1.3f %1.3f" % (dA, dB, dC))

            m = np.mean([dA, dB, dC])
            print("mean: %1.3f" % m)

            Ap = A-(dA-m+offset)
            Bp = B-(dB-m+offset)
            Cp = C-(dC-m+offset)

            d = np.array([Ap-A, Bp-B,Cp-C])
            print("actual d: ", d)
            print("mean: %1.3f" % np.mean(d))

            self.entries[LS.ABCs_out].set("%2.3f %2.3f %2.3f" % (Ap, Bp, Cp))




    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)

            for k,v in self.entries.items():
                self.entries[k].set(config[k])
        except FileNotFoundError:
            self.entries[LS.Path].set("/Users/npk/lvmdata/60009/")
            self.entries[LS.Image_Number].set("25")
            self.save_config()



    def entries_to_ascii_dict(self):
        new = {}
        for k,v in self.entries.items():
            new[k] = v.get()

        return new

    def save_config(self, *args):
        d = self.entries_to_ascii_dict()
        with open("config.json", "w") as f:
            json.dump(d, f)


    def __init__(self):
        super().__init__()

        #self.geometry("500x300")
        self.title("LVM-i Focus Software")

        self.add_labels()
        self.add_buttons()
        self.load_config()




if __name__ == "__main__":
    app = App()
    app.mainloop()