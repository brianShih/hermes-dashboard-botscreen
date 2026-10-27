package require Tk
wm title . "Bot Screen Integration - Real input acceptance"
wm geometry . 1000x500+80+60
label .title -text "Bot Screen: isolated Linux framebuffer" -font {Sans 24}
place .title -x 30 -y 40
entry .entry -font {Sans 24} -width 40
place .entry -x 100 -y 130 -width 700 -height 60
label .note -text "Synthetic text only. No account sign-in or model calls." -font {Sans 16}
place .note -x 30 -y 250
update
focus -force .entry
bind .entry <Button-1> {focus -force .entry}
set geometry [open /lab/input-target.json w]
puts $geometry [format {{"x":%d,"y":%d}} [expr {[winfo rootx .entry]+100}] [expr {[winfo rooty .entry]+30}]]
close $geometry
bind .entry <KeyRelease> {set f [open /lab/input-proof.txt w]; puts -nonewline $f [.entry get]; close $f}
