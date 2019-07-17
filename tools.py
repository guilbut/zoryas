# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 16:11:20 2019

@author: Baptiste de La Gorce
"""
import numpy
import time
from astropy.io import fits
from urllib.request import urlopen
import os
import os.path

def iterable(elt):
    if isinstance(elt,(list,tuple,set)): 
        return elt
    else : 
        return [elt]
    
def joinPath(directory , name , ext = None):
    if directory :
        if name :
            string = cleanPath(directory, endSlash = True) + name     
        else :
            string = cleanPath(directory)
    else : 
        string = name
    if name and ext:
        string =  string + '.' + ext
    return string

def directory(path):
    #realpath   = os.path.realpath(path)
    #return cleanPath(os.path.dirname(realpath))
    return cleanPath(os.path.dirname(path))

def cleanPath(path, endSlash = False):
    cleanedPath = path.replace('\\','/').replace('//','\\\\')
    if len(cleanedPath)> 0 :
        if cleanedPath[-1] == '/':
            if not endSlash :
                cleanedPath = cleanedPath[:-1]
        else : 
            if endSlash : 
                cleanedPath = cleanedPath + '/'
    return cleanedPath

def fileName(path):
    directory ,fileName= os.path.split(path)
    return fileName
    
        
def ext(path):
    return os.path.splitext(path)[1][1:].lower()

def searchExt(rootdirectory,extensions,recursive = False ):
    # permet de lire fichier avec nom unicode  
    rootdirectories = [cleanPath(root,endSlash = True ) for root in iterable(rootdirectory)]
    # mise en forme des extensions : 
    extensionsLower= set([e.lower() for e in iterable(extensions)])
    # recherche des fichiers
    result = []
    for rootdirectory in rootdirectories  : 
        if recursive == False: 
            fileNames = os.listdir(rootdirectory)
            for fileName in fileNames:
                if ext(fileName) in extensionsLower:
                    result.append(joinPath(rootdirectory,fileName))
        else: 
            for root, dirs, fileNames in os.walk(rootdirectory):
                for fileName in fileNames:
                    if ext(fileName) in extensionsLower:
                        #print root
                        result.append(joinPath(root,fileName))    
        result.sort()
    return result


def changeExt(path,ext):
    return os.path.splitext(path)[0]+ '.' + ext

def name(path):
    return splitPath(path)[1]
        

def splitPath(path):
    # splitFileName ne separe pas le nom du drive , car n'aura quasiment jamais a changer le nom du drive
    if path : 
        #realpath   = os.path.realpath(path)
        #directory , fileName= os.path.split(realpath )  
        directory , fileName= os.path.split(path)
        directory = directory.replace('\\','/').replace('//','\\\\') # pour etre ok avec serveurs
        name , ext = os.path.splitext(fileName)  	
        ext = ext[1:].lower()
        return directory, name , ext
    else : 
        return "","",""



def blockingUrlopen(url):
    printedWait = False
    while True: 
        try: 
            resource = urlopen(url)
            return resource
        except :
            if not printedWait:
                print("waiting internet connection for %s"%url)
                printedWait = True
            time.sleep(1)
    
def htmlFromUrl(url):
    resource = blockingUrlopen(url)
    charset = resource.headers.get_content_charset()
    if charset is None: 
        charset = "utf-8"
    html =  resource.read().decode(charset)
    return html

def getCleanedData(path):
    with fits.open(path) as hdul: 
        try:
            data = hdul[0].data 
            # peut planter
            """
              File "/usr/local/lib/python3.5/dist-packages/astropy/utils/decorators.py", line 744, in __get__
                val = self.fget(obj)
              File "/usr/local/lib/python3.5/dist-packages/astropy/io/fits/hdu/image.py", line 230, in data
                data = self._get_scaled_image_data(self._data_offset, self.shape)
              File "/usr/local/lib/python3.5/dist-packages/astropy/io/fits/hdu/image.py", line 696, in _get_scaled_image_data
                raw_data = self._get_raw_data(shape, code, offset)
              File "/usr/local/lib/python3.5/dist-packages/astropy/io/fits/hdu/base.py", line 508, in _get_raw_data
                return self._file.readarray(offset=offset, dtype=code, shape=shape)
              File "/usr/local/lib/python3.5/dist-packages/astropy/io/fits/file.py", line 338, in readarray
                data = _array_from_file(self._file, dtype, count)
              File "/usr/local/lib/python3.5/dist-packages/astropy/io/fits/util.py", line 586, in _array_from_file
                array = np.frombuffer(s, dtype=dtype, count=count)
              ValueError: buffer is smaller than
            """
        except : 
            return None 
        if len(data) > 20 : 
            data = data[20:-20]
        percent = 30  # x% est en dessous
        dataPercentile = numpy.percentile(data,percent,axis = 1) 
        cleanedData = numpy.maximum(data - dataPercentile[:,None],0)
        #cleanedData = numpy.power(cleanedData,1.5)
        #cleanedData =  scipy.ndimage.filters.median_filter(cleanedData,size = (3,3))   
        #cv2.medianBlur(image.RemovedGaussianScalledUint8,ksize = downSize) 
        return cleanedData
    return None


def getRating(data):
    return data.mean()