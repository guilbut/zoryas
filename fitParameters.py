SoundVolume = 0.15
TeslaVolume = 1. 
fitsFolder = "/mnt/mydisk/FIT"
wavsFolder = "/mnt/mydisk"
# -------------------
import datetime
sampleRate = 12000
fftsize = 4096
step = int(sampleRate/ 8)
keepDeltaTime =  datetime.timedelta(days=1)