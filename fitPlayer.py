# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 16:19:59 2019

@author: Baptiste
"""
import numpy
import wave
import os
import subprocess
import datetime
import parse
from platform import system
from subprocess import TimeoutExpired 
from fitParameters import sampleRate,fftsize,step,SoundVolume,TeslaVolume,fitsFolder,wavsFolder
from tools import getCleanedData,searchExt,joinPath,directory,fileName
import gc

system = system()
tempPath12000 = joinPath(wavsFolder,"temp_12000.wav")
alreadyPlayedPaths = set()
waveLength = 15*60*sampleRate + fftsize
noise = numpy.random.rand(waveLength) -0.5 #numpy.ones(waveLength) #
win = 0.5 - 0.5 * numpy.cos(2 * numpy.pi * numpy.arange(fftsize) / (fftsize - 1))
waveArray = numpy.zeros(waveLength)
wave16bit = numpy.zeros((waveLength,2),dtype = numpy.int16)
window_sum= numpy.zeros(fftsize)
winSquare = win*win
iminmax = int(fftsize/step)
for i in range (-iminmax,iminmax+1):
    start = i*step
    end = start+fftsize
    window_sum_start = max(start,0)
    window_sum_end = min(end,fftsize)
    window_square_start = window_sum_start-start
    window_square_end = window_sum_end -start 
    window_sum[window_sum_start:window_sum_end] += winSquare[window_square_start:window_square_end]
winOut = win / window_sum
playingWavePath = None
dateDone = set()
playProcess = None
j = -1 
while True : 
    paths = searchExt(fitsFolder,"gz",recursive = True)
    for path in reversed(paths):
        result = parse.parse("{year}-{month}-{day} {hour}h{minute} {rating} {location}.fit.gz", fileName(path)) 
        date = datetime.datetime(year = int(result["year"]),month = int(result["month"]),day = int(result["day"]), hour = int(result["hour"]), minute = int(result["minute"]))
        if date not in dateDone :
            fitData = getCleanedData(path)   
            if fitData is not None and len(fitData)==  3600  :    
                print(path)
                waveArray[:] = 0.
                for sliceNumber ,fitSlice in enumerate(fitData):
                    for repeat in [0,1]:
                        i = (sliceNumber*2)+repeat
                        start = i * step
                        stop = start + fftsize
                        noiseRaw = noise[start:stop]
                        noiseWindowed = noiseRaw * win
                        del(noiseRaw)
                        noiseFFt = numpy.fft.rfft(noiseWindowed)
                        del(noiseWindowed)
                        fitAmplitudes = numpy.zeros(int(fftsize/2+1))
                        fitAmplitudes[len(fitSlice)-1::-1] = fitSlice
                        fitSpectrogram = noiseFFt[:len(fitAmplitudes)]* fitAmplitudes
                        del(noiseFFt)
                        del(fitAmplitudes)
                        wave_est = numpy.real(numpy.fft.irfft(fitSpectrogram))#[::-1] 
                        del(fitSpectrogram)
                        waveArray[start:stop] += (winOut*wave_est)
                waveArray /= numpy.abs(waveArray).max()
                wave16bit[:,0] = waveArray * (SoundVolume*32767.0)
                wave16bit[:,1] = waveArray * (TeslaVolume*32767.0)
                j = (j+1)%2 
                tempPath48000 = joinPath(wavsFolder,"temp_48000_%d.wav"%j)
                if os.path.exists(tempPath12000):
                    os.remove(tempPath12000)
                if os.path.exists(tempPath48000):
                    os.remove(tempPath48000)
                Wave_write = wave.open(tempPath12000,"wb")
                Wave_write.setnchannels(2)
                Wave_write.setsampwidth(2)
                Wave_write.setframerate(sampleRate)
                Wave_write.setnframes(len(waveArray))                    
                Wave_write.writeframesraw(wave16bit)
                Wave_write.close()
                gc.collect()
                os.system('ffmpeg -i "%s" -ar 48000 -loglevel error "%s"'%(tempPath12000,tempPath48000))
                os.remove(tempPath12000)
                if playProcess is not None : 
                    print("wait")
                    playProcess.wait()
                if system == 'Windows':  
                    args = ['cmdmp3', tempPath48000]
                else :
                    args = ['mplayer','-ao','alsa', tempPath48000]
                print(" ".join(args))                
                playProcess = subprocess.Popen(args)
                if (playingWavePath is not None) and os.path.exists(playingWavePath):
                    os.remove(playingWavePath)
                playingWavePath = tempPath48000 
                try : 
                    playProcess.wait(timeout=10*60) # # attend 10 min, pour ce laisser 5 minutes de calcule pour prochain son 
                except TimeoutExpired : 
                    pass
                dateDone.add(date)
                break           
    else:
        dateDone = set() # permet de relire tout si on est arrivé au bout des fichiers et que y'en a pas de nouveaux