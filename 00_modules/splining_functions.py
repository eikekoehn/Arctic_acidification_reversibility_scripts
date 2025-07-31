"""
date: Nov 13, 2024
author: Eike E. Köhn
description: contains functions defined by Jim Orr for the usage of his fastspline package.

#### Getting fastpline

To get fastspline software, just create a directory, cd to that, and type
`git clone https://github.com/jamesorr/fastspline`
Then go to the newly created subdirectory (fastspline) and type 
`make`
Finally change the name of the directory in the cell below and execute that cell

#### Some documentation for fastspline

see also https://github.com/jamesorr/fastspline

#### Other documentation

print(fastspline.mcspline.cspline.__doc__)

x,xony,score = cspline(y,r,t,jj,lam,[n])

Wrapper for ``cspline``.

Parameters
----------
y : input rank-1 array('d') with bounds (n)
r : input int
t : input float
jj : input int
lam : input float

Other Parameters
----------------
n : input int, optional
    Default: shape(y, 0)

Returns
-------
x : rank-1 array('d') with bounds (-1 + r + n * r)
xony : rank-1 array('d') with bounds (n)
score : float

"""

#%% Import fastspline package
#fastspline_dir = "/home/jomce/Software/fortran/fastspline"         #on ciclad: 
#fastspline_dir = "/home/jomce/Software/fortran/python_meso-3.9/fastspline"  #on ciclad: for python/meso-3.9
fastspline_dir = "/home/ekoehn/software/fortran/spirit/fastspline"  #on spirit1 and spirit2

import numpy as np
import numpy.ma as ma
import sys
sys.path.append(fastspline_dir)
import fastspline

#from xrmasking_functions import * 

#%% Define functions

def xrfspline(daTYX,temporal_resolution='monthly'):
    
    import fastspline
    
    # optimal parameters
    r=2
    if temporal_resolution == 'annual':
        T=0.03  # Good choice for yearly output
    elif temporal_resolution == 'monthly':
        T=0.003  # Good choice for monthly output
    elif temporal_resolution == 'daily':
        T=0.001 # this value is just randomly chosen by EEK
    J=6
    lam=6

    # get the values
    print('get the value array')
    arrayTYX = daTYX.values
    
    # sizes of each dimension (X, Y, T)
    idim = np.size(arrayTYX, axis=2)
    jdim = np.size(arrayTYX, axis=1)
    ldim = np.size(arrayTYX, axis=0)
    
    # initialize new arrays (to store fastpline results)
    arrayTYXs = np.zeros((ldim, jdim, idim)) 
    #score     = np.zeros((      jdim, idim))
    
    # Compute spline: save in parallel array (same dimensions as input)
    for i in range(0,idim) :
        #print(i,idim)
        #if np.mod(i,100) == 0:
        #    print('i = ', i, 'of', idim)
        for j in range(0,jdim) :
            yy = arrayTYX[:,j,i]
            (dummy_2xpts, yys, s) = fastspline.mcspline(yy, r, T, J, lam)
            arrayTYXs[:,j,i] = yys
            #score[j, i] = s
            
    return arrayTYXs


def fspline1D(arrayT, T=0.03):
    import fastspline
    
    # optimal parameters
    r=2
    #T=0.03  # Good choice for yearly output
    #T=0.003  # Good choice for monthly output
    J=6
    lam=6
    
    # sizes of each dimension (X, Y, T)
    ldim = np.size(arrayT, axis=0)
    
    # initialize new arrays (to store fastpline results)
    arrayTs = np.zeros((ldim)) 
    #score     = np.zeros((1))
    
    # Compute spline: save in parallel array (same dimensions as input)
    yy = arrayT[:]
    (dummy_2xpts, yys, s) = fastspline.mcspline(yy, r, T, J, lam)
    arrayTs[:] = yys
    #score = s
    
    return arrayTs



"""
def fspline_ma(arrayTYX, T=0.03):
    ""
    fspline function, slightly modified for input and output arrays to be masked arrays
    
    INPUT
    arrayTYX: masked array
    T:        T=0.03  is good choice for yearly output
              T=0.003 is good choice for monthly output
              
    OUTPUT
    arrayTYXs: smoothed version of arrayTYX (smoothed along the T axis)
    
    James Orr
    LSCE/IPSL, CEA-CNRS-UVSQ, Gif-sur-Yvette, France
    
    07 September 2023
    ""
    
    global v_mask
    
    # optimal parameters
    r=2
    J=6
    lam=6
    
    # sizes of each dimension (X, Y, T)
    idim = np.size(arrayTYX, axis=2)
    jdim = np.size(arrayTYX, axis=1)
    ldim = np.size(arrayTYX, axis=0)
    
    # initialize new arrays (to store fastpline results)
    #arrayTYXs = ma.zeros((ldim, jdim, idim))
    arrayTYXs = ma.zeros((ldim, jdim, idim), dtype=np.float32) 
    #score     = ma.zeros((      jdim, idim))
    
    # Compute spline: save in parallel array (same dimensions as input)
    for i in range(0,idim) :
        for j in range(0,jdim) :
            yy = arrayTYX[:,j,i]
            (dummy_2xpts, yys, s) = fastspline.mcspline(yy, r, T, J, lam)
            arrayTYXs[:,j,i] = np.float32(yys)
            del dummy_2xpts, s
            #score[j, i] = s
    
    # Convert back to masked array (masked with 1e20 as fill_value)
    #arrayTYXs = ma.masked_array(arrayTYXs, mask=arrayTYX.mask, dtype=np.float32)
    #arrayTYXs.mask = arrayTYX.mask
    #arrayTYXs = np.float32(arrayTYXs)
    arrayTYXs = ma.masked_array(arrayTYXs, mask=v_mask, dtype=np.float32)
    #arrayTYXs = ma.masked_outside(arrayTYXs, -1e6, 1e6)
    arrayTYXs = ma.masked_outside(arrayTYXs, -1e3, 1.5e3)
    #arrayTYXs = ma.masked_outside(arrayTYXs, -2., 50.)
    arrayTYXs = fillval(arrayTYXs)
    #print('*[fspline_ma] (b) ma.min(arrayTYXs), ma.max(arrayTYXs):', ma.min(arrayTYXs), ma.max(arrayTYXs))
            
    return arrayTYXs

"""
