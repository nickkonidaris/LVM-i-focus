# LVM-i-focus (LIF) 

Author: Nick Konidaris (npk@carnegiescience.edu)

![[gui.png]]

GUI has tow buttons:
* Measure Focus - Opens the files /in/the/path/sdR-s-[band][number]-[Image Number].fits.gz, computes the Hartmannogram, fits a slope and offset, and populates the fields: DeltaX, DeltaY, Defocus.
* Compute - Takes the aforementioned inpus, and computes how far you'd move from ABCs in

Some notes to help focusing LVM-i
- When first refocusing, make sure to generate a Hartmannogam before adjusting the actuators. 
- If you're more than 30 microns out of focus, only fix the defocus term. Do this by setting DeltaX and DeltaY to zero.
- If the tilts are more than 50 µm/4096 pixels, then only adjust one tilt axis at a time.
