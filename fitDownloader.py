# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 16:56:21 2019

@author: Baptiste
"""
import datetime
import parse 
import os 
import time 
from tools import blockingUrlRead ,htmlFromUrl,getCleanedData,getRating,joinPath, directory,searchExt,fileName
from fitParameters import fitsFolder,keepDeltaTime


lastHtml = None 
fitNameDones = set()
tempFitPath =  joinPath(fitsFolder,"temp.fit")

def delOldFit():    
    paths = searchExt(fitsFolder,"gz",recursive = True)
    for path in paths : 
        result = parse.parse("{year}-{month}-{day} {hour}h{minute} {location}.fit.gz", fileName(path)) 
        fileDate = datetime.datetime(year = int(result["year"]),month = int(result["month"]),day = int(result["day"]), hour = int(result["hour"]), minute = int(result["minute"]))
        if fileDate < datetime.datetime.utcnow() - keepDeltaTime:
            os.remove(path)
    
while True : 
    today = datetime.datetime.utcnow()
    yesterday = today- datetime.timedelta(days=1)
    for date in [today, yesterday]: # download today and yesterday fit files 
        dateFolderLink = "http://soleil.i4ds.ch/solarradio/data/2002-20yy_Callisto/{year}/{month:0>2}/{day:0>2}/".format(root = fitsFolder,year = date.year,month = date.month,day = date.day )
        html = htmlFromUrl(dateFolderLink)
        if  html != lastHtml: # un nouveau Html est disponible 
            delOldFit() # remove old fit files 
            for result in parse.findall('<a href="{}">',html):
                fitName = result.fixed[0]
                if fitName.endswith(".fit.gz") and (fitName not in fitNameDones):
                    result = parse.parse("{location}_{date}_{time}_{num}", fitName)
                    location = result["location"]
                    hour , minute = divmod(int(round(int(result["time"][:2])*60 + int(result["time"][2:4]))/15)*15,60)  
                    fileDate = datetime.datetime(year=date.year,month=date.month,day=date.day,hour=hour,minute= minute)
                    if fileDate > datetime.datetime.utcnow() - keepDeltaTime:
                        link  = dateFolderLink+fitName
                        dataGz = blockingUrlRead(link)
                        if os.path.exists(tempFitPath):
                            os.remove(tempFitPath)
                        dataFile = open(tempFitPath,"wb")
                        dataFile.write(dataGz)
                        dataFile.close()
                        fitData = getCleanedData(tempFitPath)
                        if fitData is not None :
                            rating = round(getRating(fitData),1)
                            newFileName = "{year}-{month:0>2}-{day:0>2} {hour:0>2}h{minute:0>2} {rating} {location}".format(root= fitsFolder, year = date.year,month = date.month,day = date.day, hour=hour, minute= minute, rating = rating, location = location)                    
                            path = joinPath(fitsFolder,newFileName,"fit.gz")
                            if not os.path.exists(path) :
                                print(path)
                                if not os.path.exists(directory(path)):
                                    os.makedirs(directory(path))
                                os.rename(tempFitPath,path)
    time.sleep(1)
        
        
        
        