# -*- coding: utf-8 -*-
#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2010 Heiko Jakob <heiko.jakob@gediegos.de>        *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************
# Modificaiotn by F. Nivoix to integrate
# in Airplane workbench 2019 -
# V0.1, V0.2 & V0.3
#***************************************************************************

import FreeCAD,FreeCADGui,Part,re
from FreeCAD import Base

FreeCADGui.addLanguagePath(":/translations")

# Qt translation handling
def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)

#################################################
#  This module provides tools to build a
#  wing panel
#################################################
if open.__module__ in ['__builtin__','io', '_io']:
    pythonopen = open


def readpointsonfile(filename):
    # The common airfoil dat format has many flavors, This code should work with almost every dialect,
    # Regex to identify data rows and throw away unused metadata
    regex = re.compile(r'^\s*(?P<xval>(\-|\d*)\.\d+(E\-?\d+)?)\,?\s*(?P<yval>\-?\s*\d*\.\d+(E\-?\d+)?)\s*$')
    afile = pythonopen(filename,'r')
    coords=[]
    name = "unknown"
    # Collect the data for the upper and the lower side separately if possible
    linenum=0
    for lin in afile:
        curdat = regex.match(lin)
        if curdat != None:
            x = float(curdat.group("xval"))
            y = 0#posY
            z = float(curdat.group("yval"))
            #ignore points out of range, small tolerance for x value and arbitrary limit for y value, this is necessary because Lednicer
            #format airfoil files include a line indicating the number of coordinates in the same format of the coordinates.
            if (x < 1.01) and (z < 1) and (x > -0.01) and (z > -1):
                coords.append(FreeCAD.Vector(x,y,z))
            else:
                coords.append(FreeCAD.Vector(x,y,z))
                #FreeCAD.Console.PrintWarning("Ignoring coordinates out of range -0.01<x<1.01 and/or -1<z<1. If this is a Lednicer format airfoil this is normal.")
        else:
          if linenum == 0:
            name = lin.strip("\n\t ")
        linenum +=1
        # End of if curdat != None
    # End of for lin in file
    afile.close

    if len(coords) < 3:
        FreeCAD.Console.PrintError('Did not find enough coordinates\n')
        return
    # sometimes coords are divided in upper an lower side
    # so that x-coordinate begin new from leading or trailing edge
    # check for start coordinates in the middle of list

    if coords[0:-1].count(coords[0]) > 1:
        flippoint = coords.index(coords[0],1)
        coords[:flippoint+1]=coords[flippoint-1::-1]

    return name, coords


def process(filename,airfoilname,scale,thickness,tegap,teblendig,posX,posY,posZ,rotX,rotY,rotZ,rot,useSpline,splitSpline,millTeLength,coords=[]):
    
    if len(coords) == 0 :
        airfoilname, coords = readpointsonfile(filename)
        
    maxZ = minZ = coords[0].z
    for k in range(1, len(coords)):
        if coords[k].z > maxZ:
            maxZ = coords[k].z
        if coords[k].z < minZ:
            minZ = coords[k].z
    print("min/max Z coords: " + str(minZ) + "/" + str(maxZ))
    thickness = (maxZ - minZ) * 100
    print("min/max thickness: {:.2f}".format(thickness))
    
    maxdiff = 0.0
    for k in range(1, int(len(coords)/2)):
        diff = coords[k].z - coords[-k].z
        if diff > maxdiff:
          maxdiff = diff
    thickness = maxdiff * 100
    print("diff thickness: {:.2f}".format(thickness))
          
    # process the trailing edge gap settings
    currentTEGap = (coords[0].z - coords[-1].z)*scale.Value
    print("TE Gap : {:.2f}".format(currentTEGap))
    print("TE Gap calc: "+"{:.2f}".format(tegap*scale.Value))
    
    if abs(tegap*scale.Value - currentTEGap) > 0.1:
      # TODO code for TE processing
      pass
      
    tcoords = coords.copy()

    # do we use a BSpline?
    if millTeLength > 0.0:
        millTePercent = millTeLength / scale
        # find the two up and down TE vectors
        for i in range(0,3,1):
          print("v["+str(i)+"] : " + repr(tcoords[i]))
        for i in range(-1,-4,-1):
          print("v["+str(i)+"] : " + repr(tcoords[i]))
        # 
        print ("mill modifications one: ")
        x0 = tcoords[0].x
        z0 = tcoords[0].z
        x1 = tcoords[1].x
        z1 = tcoords[1].z
        print ("xz[0]=" + str(x0) + "/" + str(z0))
        print ("xz[1]=" + str(x1) + "/" + str(z1))
        v = FreeCAD.Vector(x0 - (x0-x1)/3*2, 0, z0+abs(z0-z1)/3*2)
        
        tcoords.insert(1, v)
        v = FreeCAD.Vector(x0 - (x0-x1)/3, 0, z0+abs(z0-z1)/3)
        tcoords.insert(1, v)
        
        tcoords.insert(0, FreeCAD.Vector(1.0+(millTePercent*0.1),tcoords[0].y,tcoords[0].z))
        tcoords.insert(0, FreeCAD.Vector(1.0+(millTePercent*0.2),tcoords[0].y,tcoords[0].z))
        tcoords.insert(0, FreeCAD.Vector(1.0+(millTePercent*0.4),tcoords[0].y,tcoords[0].z))
        tcoords.insert(0, FreeCAD.Vector(1.0+(millTePercent*0.6),tcoords[0].y,tcoords[0].z))
        tcoords.insert(0, FreeCAD.Vector(1.0+(millTePercent*1.0),tcoords[0].y,tcoords[0].z))

        x0 = tcoords[-1].x
        z0 = tcoords[-1].z
        x1 = tcoords[-2].x
        z1 = tcoords[-2].z
        print ("xz[-1]=" + str(x0) + "/" + str(z0))
        print ("xz[-2]=" + str(x1) + "/" + str(z1))
        v = FreeCAD.Vector(x0 - (x0-x1)/3*2, 0, z0+(z1-z0)/3*2)
        tcoords.insert(-1, v)
        v = FreeCAD.Vector(x0 - (x0-x1)/3, 0, z0+(z1-z0)/3)
        tcoords.insert(-1, v)

        tcoords.append(FreeCAD.Vector(1.0+(millTePercent*0.1),tcoords[-1].y,tcoords[-1].z))
        tcoords.append(FreeCAD.Vector(1.0+(millTePercent*0.2),tcoords[-1].y,tcoords[-1].z))
        tcoords.append(FreeCAD.Vector(1.0+(millTePercent*0.4),tcoords[-1].y,tcoords[-1].z))
        tcoords.append(FreeCAD.Vector(1.0+(millTePercent*0.6),tcoords[-1].y,tcoords[-1].z))
        tcoords.append(FreeCAD.Vector(1.0+(millTePercent*1.0),tcoords[-1].y,tcoords[-1].z))

        print ("version 4")

        for i in range(0,9,1):
          print("v["+str(i)+"] : " + repr(tcoords[i]))
        for i in range(-1,-10,-1):
          print("v["+str(i)+"] : " + repr(tcoords[i]))



    if useSpline:
        if splitSpline: #do we split between upper and lower side?
            if tcoords.__contains__(FreeCAD.Vector(0,0,0)): # lgtm[py/modification-of-default-value]
                flippoint = tcoords.index(FreeCAD.Vector(0,0,0))
            else:
                lengthList=[v.Length for v in tcoords]
                flippoint = lengthList.index(min(lengthList))
            splineLower = Part.BSplineCurve()
            splineUpper = Part.BSplineCurve()
            splineUpper.interpolate(tcoords[:flippoint+1])
            splineLower.interpolate(tcoords[flippoint:])
            if tcoords[0] != tcoords[-1]:
                wire = Part.Wire([splineUpper.toShape(),splineLower.toShape(),Part.makeLine(tcoords[0],tcoords[-1])])
            else:
                wire = Part.Wire([splineUpper.toShape(),splineLower.toShape()])
        else:
            spline = Part.BSplineCurve()
            spline.interpolate(tcoords)
            if tcoords[0] != tcoords[-1]:
                wire = Part.Wire([spline.toShape(),Part.makeLine(tcoords[0],tcoords[-1])])
            else:
                wire = Part.Wire(spline.toShape())
    else:
        # alternate solution, uses common Part Faces
        lines = []
        first_v = None
        last_v = None
        for v in tcoords:
            if first_v is None:
                first_v = v
            # End of if first_v is None
            # Line between v and last_v if they're not equal
            if (last_v != None) and (last_v != v):
                lines.append(Part.makeLine(last_v, v))
            # End of if (last_v != None) and (last_v != v)
            # The new last_v
            last_v = v
        # End of for v in upper
        # close the wire if needed
        if last_v != first_v:
                lines.append(Part.makeLine(last_v, first_v))
        wire = Part.Wire(lines)

    #face = Part.Face(wire).scale(scale) #Scale the foil, # issue31 doesn't work with v0.18
    face = Part.Face(wire)
    myScale = Base.Matrix() # issue31
    myScale.scale(scale,scale,scale)# issue31
    face=face.transformGeometry(myScale)# issue31

    face.Placement.Rotation.Axis.x=rotX
    face.Placement.Rotation.Axis.y=rotY
    face.Placement.Rotation.Axis.z=rotZ
    face.Placement.Rotation.Angle=rot

    #face.Placement(FreeCAD.Vector(0,0,0),FreeCAD.Rotation(FreeCAD.Vector(rotX,rotY,rotZ),rot))
    #face.rotate([0,0,0],FreeCAD.Vector(rotX, rotY, rotZ),rot)


    return face, coords
