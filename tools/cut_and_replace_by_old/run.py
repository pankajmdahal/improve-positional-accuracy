import os

os.system("python cut_replace.py")
os.system("python validate.py")
os.system("python modify_fipsrr.py")


print "alllinks.shp and FIPSRR.csv were copied to RAIL/gis and input respectively"