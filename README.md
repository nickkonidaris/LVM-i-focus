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



- Plug Gauge 1 or A into Top, 2 or B into Right, and 3 or C into left.
- Increasing the distance is a clockwise turn (i.e. you're shortening the distance).
- Tool for the screws is a 2.5 mm wrench (not 2.0 mm as indicated by winlight document).
- For locking the screws and nuts down.
	- Make sure all screws and nuts are at the torque spec. Record TRL values.
	- Loosen both by the requistie amount (quarter to half turn). Record TRL values.
	- The difference between the TRL values (tight - loose) is the offset. Your goal is to go to focus position - offset.
- 
