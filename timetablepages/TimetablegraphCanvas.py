#!/usr/bin/env python3

from tkinter import Tk, Canvas, Frame, BOTH, font, filedialog
import uuid

from tkinter import ttk
from tools.xmltodict import parse
from collections import OrderedDict
from datetime import datetime
from timetablepages.DefaultConstants import STD_FONT

import os
import logging

#from PIL import Image, ImageGrab

"""
    * The left column has the layout information along with the station names next to the diagram box.
    * The column width is dynamic based on the width of the items.
    * Across the top, lined up with the diagram box, are the throttle lines.
    * The main section is the diagram box.
    * Across the bottom, lined up with the diagram box, is the hours section.
    * <pre>
    *       +--------- canvas -------------+
    *       | info    | throttle lines     |
    *       |         |+------------------+|
    *       | station ||                  ||
    *       | station || diagram box      ||
    *       | station ||                  ||
    *       |         |+------------------+|
    *       |         | hours              |
    *       +------------------------------+
    * </pre>
    * A normal train line will be "a-b-c-d-e" for a through train, or "a-b-c-b-a" for a turn.
    * <p>
    * A multi-segment train will be "a1-b1-c1-x2-y2-z2" where c is the junction. The
    * reverse will be "z2-y2-z2-c2-b1-a1".  Notice:  While c is in both segments, for
    * train stop purposes, the arrival "c" is used and the departure "c" is skipped.
    */
"""

import math

class Point:
        def __init__(self, x, y):
                self.x = x
                self.y = y

        def __add__(self, other: 'Vector'):
                return Vector(other.x + self.x, other.y + self.y)

        def __sub__(self, other):
                return Vector(self.x - other.x, self.y - other.y)

        def __iter__(self):
                yield self.x
                yield self.y

        def __str__(self):
                return f'{self.__class__.__name__}({self.x}, {self.y})'


class Vector:
        def __init__(self, x, y):
                self.x = x
                self.y = y

        def __add__(self, other):
                return Point(other.x + self.x, other.y + self.y)

        def __sub__(self, other):
                return Vector(other.x - self.x, other.y - self.y)

        def scale(self, scalar):
                return Vector(self.x * scalar, self.y * scalar)

        def normal(self):
                norm = self.norm()
                if norm == 0:
                        return Vector(self.x,self.y)
                else:
                        return Vector(self.x / norm, self.y / norm)

        def norm(self):
                return math.hypot(self.x, self.y)

        def perp(self):
                x, y = self.normal()
                return Vector(y, -x)

        def angle(self):
                return math.atan2(-self.y, self.x) * (180 / math.pi)

        def __iter__(self):
                yield self.x
                yield self.y

        def __str__(self):
                return f'{self.__class__.__name__}({self.x}, {self.y})'
        

class TimeTableGraphCommon():

#     * Initialize the data used by paint() and supporting methods when the
#     * panel is displayed.
#     * @param segmentId The segment to be displayed.  For multiple segment
#     * layouts separate graphs are required.
#     * @param scheduleId The schedule to be used for this graph.
#     * @param showTrainTimes When true, include the minutes portion of the
#     * train times at each station.
#     * @param height Display height
#     * @param width Display width
#     * @param displayType (not currently used)

        def __init__(self, controller, showTrainTimes, height, width):
                self.controller = controller
                self.showTrainTimes = showTrainTimes
                self.ZugGattung_to_Color = { "D" : "red",
                                             "E" : "blue"}
                self.trainTypeList = [] #["D","E"]
                
                # init timetable with dummy data
                self.timetable_dict = {"Schedule":
                                        {"Name": "Testschedule",
                                         "StartHour": 12,
                                         "Duration" : 7,
                                         "Stations":
                                         {0:
                                               {"StationName" : "",
                                                "Distance"    : 0,
                                                "data"        : "Data1"
                                               }
                                           },                                 
                                         "Trains":
                                         {1: 
                                          {"TrainName":"Train1",
                                           "Color" : "red",
                                           "Stops" : 
                                           {0:
                                            {"StationIdx" : 0,
                                             "ArriveTime" : 10,
                                             "DepartTime" : 15,
                                             "Direction"  : "down"
                                             },
                                            },
                                          2:
                                          {"TrainName":"Train2",
                                           "Color" : "blue",
                                           "Stops" : 
                                           {0:
                                            {"StationIdx" : 0,
                                             "ArriveTime"    : 60,
                                             "DepartTime"  : 65,
                                             "Direction"  : "down"
                                             },
                                            1:
                                            {"StationIdx" : 1,
                                              "ArriveTime": 70,
                                              "DepartTime" : 75,
                                              "Direction" : "down"
                                        }
                                       }
                                      }
                                    }
                                  }
                                }
                                }

                self.schedule_dict = self.timetable_dict.get("Schedule",{})
                
                self.schedule = self.schedule_dict        
                
                self.startHour = self.schedule_dict.get("StartHour",0)
                self.duration  = self.schedule_dict.get("Duration",0)
                self.stations  = self.schedule_dict.get("Stations",{})
                self.startTime_min = self.startHour * 60
                self.stationIdx_max = 0
                self.trains    = self.schedule_dict.get("Trains",{}) 
                self.trainIdx_max = 0
                self.dimHeight = height
                self.dimWidth  = width

                self.stdFont = font.Font(family="SANS_SERIF", size=10)
                self.smallFont = font.Font(family="SANS_SERIF", size=8)
                self.gridstroke = 0.5
                self.stroke = 2.0

                self.segmentId = 0
                self.scheduleId = 0

                self.stops = []

                #// ------------ global variables ------------
                self.stationGrid = {0: 0.01 }
                self.hourMap = {0: 0.01} 
                self.hourgrid = [] 
                self.infoColWidth = 0
                self.hourOffset = 0
                self.graphHeight = 0
                self.graphWidth = 0
                self.graphTop = 0
                self.graphBottom = 0
                self.graphLeft = 0
                self.graphRight = 0
                self.tt_canvas = None 
                self.pf = 0 

                #    // ------------ train variables ------------
                self.textLocation = [(0,0,5,5)]
                #    // Train
                self.trainName = ""
                self.trainThrottle = 0
                self.trainColor = 0 
                self.trainLine = []

                #  Stop
                self.stopCnt = 0
                self.stopIdx = 0
                self.arriveTime = 0
                self.departTime = 0
                self.maxDistance = 0.0
                self.direction = ""
                self.firstStop = False
                self.lastStop = False

                self.firstX = 0.0
                self.lastX = 0.0

                self.sizeMinute = 0.0
                self.throttleX = 0.0

        def doPaint (self,canvas,starthour=12,duration=7):
                self.tt_canvas = canvas
                height =self.tt_canvas.winfo_reqheight()
                width = self.tt_canvas.winfo_reqwidth()                
                self.dimHeight = height
                self.dimWidth  = width
                self.startHour=starthour
                self.startTime_min = self.startHour * 60
                self.duration = duration
                self.stationGrid  = {} 
                self.hourGrid     = []
                self.textLocation = []
                self.graphTop = 70.0
                self.graphHeight = self.dimHeight - self.graphTop - 30.0
                self.graphBottom = self.graphTop + self.graphHeight

                # Draw the left column components
                self.drawInfoSection()
                self.drawStationSection()

                # Set the horizontal graph dimensions based on the width of the left column
                self.graphLeft = self.infoColWidth + 50.0
                self.graphWidth = self.dimWidth - self.infoColWidth - 65.0
                self.graphRight = self.graphLeft + self.graphWidth

                self.drawHours()
                self.drawGraphGrid()
                self.drawTrains()
                self.save_as_png(self.tt_canvas,"test_zusi")

        def drawInfoSection(self):
                scheduleName = self.schedule_dict.get("Name","")
                self.tt_canvas.create_text(10, 40, text=scheduleName, font=self.stdFont, anchor="nw");

        def drawStationSection(self):
                stationIdx_last = len(self.stations)-1
                if stationIdx_last > 0:
                        self.maxDistance = self.stations[stationIdx_last].get("Distance",100)
                        self.stationGrid = {}
                        for stationIdx in self.stations:
                                station = self.stations.get(stationIdx,{})
                                stationName = station.get("StationName","")
                                stationkm = station.get("StationKm",0.00)
                                distance = station.get("Distance",0.00)
                                if stationkm == None:
                                        print("Error: Stationkm = None - ",stationName)
                                        stationkm = 0
                                stationName = stationName + " (km "+str(f"{stationkm:.2f}")+")"
                                self.infoColWidth = max(self.infoColWidth, self.stdFont.measure(stationName) + 5)
                                stationY = ((self.graphHeight - 50) / self.maxDistance) * distance + self.graphTop + 30  #// calculate the Y offset
                                self.tt_canvas.create_text(15.0, stationY, text=stationName, font=self.stdFont, anchor="w")
                                self.stationGrid[stationIdx] = stationY

        def drawHours(self):
                currentHour = self.startHour
                hourWidth = self.graphWidth / (self.duration)
                self.hourOffset = 0 #hourWidth / 2
                self.hourgrid = []
                
                for i in range(0, self.duration+1):
                        hourString = str(currentHour)+":00"
                        hourX = (hourWidth * i) + self.hourOffset + self.graphLeft;
                        hOffset = self.stdFont.measure(hourString) / 2 # hOffset = self.g2.getFontMetrics().stringWidth(hourString) / 2;
                        self.tt_canvas.create_text(hourX - hOffset, self.graphBottom + 20, text = hourString, anchor="w")
                        self.tt_canvas.create_text(hourX - hOffset, self.graphTop - 8, text = hourString, anchor="w")
                        self.hourMap[currentHour] = hourX
                        self.hourGrid.append(hourX);
                        if (i == 0):
                                self.firstX = hourX - hOffset;
                        if (i == self.duration):
                                self.lastX = hourX - hOffset;
                        currentHour+= 1
                        if (currentHour > 23):
                                currentHour -= 24;
            
        def drawGraphGrid(self):
                # Print the graph box
                self.tt_canvas.create_rectangle(self.graphLeft, self.graphTop, self.graphLeft+self.graphWidth, self.graphTop + self.graphHeight)
        
                # Print the grid lines
                for y in self.stationGrid.values():
                        self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=2, fill="gray")
                for x in self.hourGrid:
                        self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=2, fill="gray");

#     * Create the train line for each train with labels.  Include times if
#     * selected.
#     * <p>
#     * All defined trains their stops are processed.  If a stop has a station
#     * in the segment, it is included.  Most trains only use a single segment.

        def drawTrains(self):
                self.baseTime = self.startHour * 60;
                self.sizeMinute = self.graphWidth / ((self.duration) * 60);
                self.throttleX = 0;
                for trainidx in self.trains:
                        train = self.trains.get(trainidx,{})
                        self.trainType = train.get("TrainType","X-Deko")
                        self.trainName = self.trainType + train.get("TrainName","0000")
                        self.trainLineName = train.get("TrainLine","")
                        self.trainEngine = train.get("TrainEngine","")
                        if (self.trainTypeList != [] and not self.trainType in self.trainTypeList):
                                break
                        self.trainColor = train.get("Color","black")
                        self.trainLine = []
                        self.stops = train.get("Stops",{});
                        self.stopCnt = len(self.stops);
                        self.firstStop = True;
                        self.lastStop = False;
                        self.prevStop = None
            
                        for self.stopIdx,stop_dict in self.stops.items():
                                self.arriveTime = stop_dict.get("ArriveTime",0)
                                self.departTime = stop_dict.get("DepartTime",0)
                                self.stopStation  = stop_dict
                                if (self.stopIdx > 0): 
                                        self.firstStop = False
                                if (self.stopIdx == self.stopCnt - 1): 
                                        self.lastStop = True
                                if (self.firstStop):
                                        self.setBegin(self.stopStation)
                                        if (self.lastStop):
                                                #// One stop route or only one stop in current segment
                                                self.setEnd(self.stopStation, False)
                                                break
                                        continue
                                self.drawLine(self.stopStation);
                                if (self.lastStop):
                                                #// At the end, do the end process
                                                self.setEnd(self.stopStation, False);
                                                break;

#    /**
#        * Draw a train name on the graph.
#        * <p>
#        * The base location is provided by x and y.  justify is used to offset
#        * the x axis.  invert is used to flip the y offsets.
#        * @param x The x coordinate.
#        * @param y The y coordinate.
#        * @param justify "Center" moves the string left half of the distance.  "Right"
#        * moves the string left the full width of the string.
#        * @param invert If true, the y coordinate offset is flipped.
#        * @param throttle If true, a throttle line item.
#        */
        def drawTrainName( self, x,  y,  justify,  invert,  throttle):
                
                textbox_x= self.stdFont.measure(self.trainName)
                #// Position train name
                if justify =="Center": # 
                        x = x - textbox_x /2
                else:
                        if justify == "Right": 
                                x = x - textbox_x
        
                if (invert):
                        if (self.direction== "down" or throttle):
                                y = y - 7 #20
                        else:
                                y = y + 13 # 20  
                else:
                        if (self.direction== "down" or throttle):
                                y = y + 13
                        else:
                                y = y - 7                    

                textRect = (
                        x,
                        y,
                        textbox_x,
                        10
                        )
                textRect = self.adjustText(textRect)
                x = textRect[0] # textRect.getX();
                #self.g2.create_rectangle(x,y,x+textbox_x,y+12,fill="white")
                trainName_objid = self.tt_canvas.create_text(x , y, activefill="red",text = self.trainName, anchor = "w") #anchor="nw")
                self.controller.ToolTip_canvas(self.tt_canvas, trainName_objid, text="Zug: "+self.trainName+" "+self.direction, key=self.trainName,button_1=True)
                self.textLocation.append(textRect)


#    /**
#        * Draw the minutes value on the graph if enabled.
#        * @param time The time in total minutes.  Converted to remainder minutes.
#        * @param mode Used to set the x and y offsets based on type of time.
#        * @param x The base x coordinate.
#        * @param y The base y coordinate.
#        */
        def drawTrainTime(self, time,  mode,  x,  y):
                if (not self.showTrainTimes):
                        return;
                
                if not (time in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                        return                
                
                minutes = "{:02d}".format(time % 60) #str(time % 60).format("%02d")
                hours = "{:02d}".format(int(time/60))   #str(int(time/60)).format("%02d")
                textbox_x = self.stdFont.measure(minutes)
                if mode ==  "begin" :
                        mode_txt = "Start"
                        if (self.direction== "down"):
                                x = x + 2
                                y = y + 10
                        else:
                                x = x + 2
                                y = y - 10
                elif mode == "arrive":
                        mode_txt = "Ankunft"
                        if (self.direction== "down"):
                                x = x - 8
                                y = y + 10
                        else:
                                x = x - 8
                                y = y - 10
                elif mode == "depart":
                        mode_txt = "Abfahrt"
                        if (self.direction== "down"):
                                x = x - 4
                                y = y - 10
                        else:
                                x = x - 4
                                y = y + 10   
                elif mode == "end":
                        mode_txt = "Ziel"
                        x = x
                        y = y
                        
                else:
                        return;
                
                textRect = (
                        x,
                        y,
                        textbox_x,
                        10
                        )
                #textRect = self.adjustText(textRect)
                #x = textRect[0] # textRect.getX();
        
                #self.g2.setFont(self.stdFont);
                #s self.g2.setColor(Color.GRAY);
                #self.g2.create_rectangle(textRect[0],textRect[1],textRect[0]+textbox_x,textRect[1]+12,fill="white")
                trainTime_objid = self.tt_canvas.create_text(x , y, text = minutes, anchor="w")
                if self.trainLineName == None:
                        self.trainLineName = ""
                self.controller.ToolTip_canvas(self.tt_canvas, trainTime_objid, text=hours+":"+minutes+"\nZug: "+self.trainName+" - "+mode_txt+"\n"+self.trainLineName, key=self.trainName,button_1=True)
                #self.g2.drawString(self.trainName, x, y);
                self.textLocation.append(textRect)                

#    /**
#        * Move text that overlaps existing text.
#        * @param textRect The proposed text rectangle.
#        * @return The resulting rectangle
#        */
        def adjustText(self, textRect):
                xLoc = textRect[0] 
                yLoc = textRect[1] 
                xLen = textRect[2] 
        
                wrkX = xLoc;
                chgX = False;

                for workRect in self.textLocation:
                        if workRect[1] == yLoc:
                                xMin = workRect[0]
                                xMax = xMin + workRect[3]
                
                                if (xLoc > xMin and xLoc < xMax):
                                        wrkX = xMax + 2;
                                        chgX = True;
                                
                
                                if (xLoc + xLen > xMin and xLoc + xLen < xMax):
                                        wrkX = xMin - xLen -2;
                                        chgX = True;
                if (chgX):
                        textRect = (
                                wrkX,
                                yLoc,
                                textRect[2], 
                                textRect[3]
                                )
                return textRect

#    
#    Determine direction of travel on the graph: up or down
#    
        def setDirection(self):
                #print("Set Direction:", self.trainName, "-",self.stopIdx)        
                if (self.stopCnt == 1):
                        # Single stop train, default to down
                        self.direction = "down"
                        return;
                
        
                stop = self.stops.get(self.stopIdx,{});
                currStation_Idx = stop.get("StationIdx",0)
                currStation = self.stations.get(currStation_Idx,{})
                #print(repr(currStation))
                currkm = currStation.get("Distance",0)
        
                if (self.firstStop):
                        #// For the first stop, use the next stop to set the direction
                        nextStation_Idx = self.stops.get(self.stopIdx + 1).get("StationIdx",0)
                        nextStation = self.stations.get(nextStation_Idx,{})
                        #print("FirstStop:",repr(nextStation))
                        nextkm = nextStation.get("Distance",0)
                        if nextkm > currkm:
                                self.direction = "down" 
                        else:  
                                self.direction = "up"
                        #print("Direction:",self.direction)
                        return
                if (self.lastStop):    
                        prevStation_Idx = self.stops.get(self.stopIdx - 1).get("StationIdx",0)
                        prevStation = self.stations.get(prevStation_Idx,{})
                        #// For the last stop, use the previous stop to set the direction
                        #// Last stop may also be only stop after segment change; if so wait for next "if"
                        #if (prevStation.get(SegmentId() == self.segmentId):
                        #self.direction = (prevStation.getDistance() < currDistance) ? "down" : "up";
                        #print("LastStop:",repr(prevStation))
                        prevkm = prevStation.get("Distance",0)
                        if prevkm < currkm:
                                self.direction = "down" 
                        else :  
                                self.direction = "up"                                
                        #print("Direction:",self.direction)
                        return
            
                #// For all other stops in the active segment, use the next stop.
                
                nextStation_Idx = self.stops.get(self.stopIdx + 1).get("StationIdx",0)
                nextStation = self.stations.get(nextStation_Idx)
                #print("NextStop:",repr(nextStation))
                nextkm = nextStation.get("Distance",0)
                if nextkm > currkm:
                        self.direction = "down"
                else: 
                        self.direction = "up";  
                #print("Direction:",self.direction)
                return


#        * Set the starting point for the self.trainLine path.
#        * The normal case will be the first stop (aka start) for the train.
#        * <p>
#        * The other case is a multi-segment train.  The first stop in the current
#        * segment will be the station AFTER the junction.  That means the start
#        * will actually be at the junction station.
#        * @param stop The current stop.

        def setBegin(self, stop):
                if not (self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                        return                
                self.arriveTime = stop.get("ArriveTime",0)
                x = self.calculateX(self.arriveTime)
                y = self.stationGrid.get(stop.get("StationIdx",0),0)
                if y == None:
                        return
                self.trainLine = [x, y]
                self.setDirection()
                self.arriveTime = stop.get("ArriveTime",0)
                self.drawTrainTime(self.arriveTime, "begin", x, y)
                #// Check for stop duration before depart
                self.departTime = stop.get("DepartTime",0)
                if (self.departTime - self.arriveTime > 0):
                        x = self.calculateX(self.departTime)
                        self.trainLine.extend([x, y])
                        self.drawTrainTime(self.departTime, "depart", x, y)

#    /**
#        * Extend the train line with additional stops.
#        * @param stop The current stop.
#        */
        def drawLine(self, stop):
                if not (self.departTime in range(self.startTime_min,self.startTime_min + self.duration * 60) or self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                        return
                x = self.calculateX(self.arriveTime)
                y = self.stationGrid.get(stop.get("StationIdx"),0)
                if y==None:
                        return
                self.trainLine.extend([x, y])
                self.drawTrainTime(self.arriveTime, "arrive", x, y);  #
                if len(self.trainLine)>3:
                        self.draw_trainName_parallel(self.trainName, self.trainLine[-4],self.trainLine[-3],x, y)                
        
                self.setDirection();
                #// Check for duration after arrive
                if (self.departTime - self.arriveTime) > 0 :
                        if not (self.departTime in range(self.startTime_min,self.startTime_min + self.duration * 60) or self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                                return                        
                        x = self.calculateX(self.departTime);
                        self.trainLine.extend([x, y])
                        self.drawTrainTime(self.departTime, "depart", x, y);  #

#    
#        * Finish the train line, draw it, the train name and the throttle line if used.
#        * @param stop The current stop.
#        * @param endSegment final segment
#        
        def setEnd(self, stop, endSegment):
                try:
                        skipLine = False;
                        if self.trainLine == []:
                                return
                        if (len(self.stops) == 1):
                                x = self.trainLine[-2]
                                y = self.trainLine[-1]
                                skipLine = True
                                #self.drawTrainName(x, y+10, "Center", False, False) 
                        else:
                                if (self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                                        x = self.calculateX(self.arriveTime)
                                        y = self.stationGrid.get(stop.get("StationIdx",0),0)
                                        #self.drawTrainName(x, y, "Center", False, False)
                                else:
                                        x = self.trainLine[-2]
                                        y = self.trainLine[-1]
                                        #self.drawTrainName(x, y, "Center", False, False)
                        if (not skipLine):
                                if y==None:
                                        logging.debug("SetEnd Error: %s %s",self.trainType+self.trainName,repr(stop))
                                        return
                                self.trainLine.extend([x, y])
                                train_line_objid = self.tt_canvas.create_line(self.trainLine,fill=self.trainColor,width=4,activewidth=8)
                                self.controller.ToolTip_canvas(self.tt_canvas, train_line_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, key=self.trainName,button_1=True)
                except BaseException as e:
                                logging.debug("SetEnd Error %s %s",self.trainType+self.trainName+"-"+repr(self.trainLine),e)
                                return  
        
#            
#                * Convert the time value, 0 - 1439 to the x graph position.
#                * @param time The time value.
#                * @return the x value.
#                
        def calculateX(self, time):
                if (time < 0): time = 0;
                if (time > 1439): time = 1439;
        
                hour = int(time / 60)
                min = int(time % 60)
        
                return self.hourMap.get(hour,self.firstX) + (min * self.sizeMinute)
        
        
        def draw_trainName_parallel(self,trainName,x0,y0,x1,y1):
                p0, p1 = Point(x0,y0), Point(x1,y1)
                segment = p1 - p0
                mid_point = segment.scale(0.5) + p0
               
                offset = segment.perp().scale(10)
                # canvas.create_line(*mid_point, *(mid_point+offset))
                trainName_len = self.stdFont.measure(self.trainName)
                segment_len = segment.norm()
                if segment_len > trainName_len+15:
                        txt = self.tt_canvas.create_text(*(offset + mid_point), text=trainName)
                        if y0 != y1:
                                angle = segment.angle()
                                self.tt_canvas.itemconfig(txt, angle=angle)                

        def enter_station(self,stationName, distance, stationKm):
                
                if stationKm == None:
                        print("Error: km=None -",stationName)
                        stationKm = 0
                        
                for stationIdx in self.stations:
                        station_data = self.stations.get(stationIdx,0)
                        if station_data.get("StationName","") == stationName:
                                return
                
                self.stations[self.stationIdx_max] = {"StationName": stationName, 
                                                      "Distance": distance,
                                                      "StationKm": stationKm}
                self.stationIdx_max +=1
                
                return self.stationIdx_max - 1
                
        def enter_train_data(self,ZugNummer,ZugGattung,ZugLauf,ZugLok):
                
                color = self.ZugGattung_to_Color.get(ZugGattung,"black")
                
                self.trains[self.trainIdx_max] = {"TrainName": ZugNummer,
                                                  "TrainType": ZugGattung,
                                                  "TrainLine": ZugLauf,
                                                  "TrainEngine" : ZugLok,
                                                  "Color"    : color,
                                                  "Stops"    : {}
                                                   }
                self.trainIdx_max += 1
                
                return self.trainIdx_max-1
        
        def search_station(self, stationName):
                for stationIdx in self.stations:
                        station_data = self.stations.get(stationIdx)
                        if station_data.get("StationName") == stationName:
                                return stationIdx
                
                return -1
                
                
        
        def enter_train_stop(self, train_idx, trainstop_idx,FplName,FplAnk_min,FplAbf_min):
                
                train_dict = self.trains.get(train_idx)
                
                trainstops = train_dict.get("Stops",{})
                
                station_idx = self.search_station(FplName)
                
                if FplAnk_min == 0:
                        FplAnk_min = FplAbf_min
                        
                arriveTime = FplAnk_min
                departTime = FplAbf_min
                trainstops[trainstop_idx] = {"StationIdx" : station_idx,
                                             "ArriveTime" : arriveTime,
                                             "DepartTime" : departTime
                                             }
                return trainstop_idx + 1
        
        def get_fplZeile_entry(self, FplZeile_dict, main_key, key, default=""):
                try:
                        Fpl_dict_list = FplZeile_dict.get(main_key)
                except:
                        Fpl_dict_list = None
                if Fpl_dict_list:
                        try:
                                result = Fpl_dict_list.get(key,default)
                        except:
                                Fpl_dict = Fpl_dict_list[0]
                                if Fpl_dict == None:
                                        Fpl_dict = Fpl_dict_list[1]
                                result = Fpl_dict.get(key,default)
                else: 
                        result = default
                return result
        
        def convert_zusi_tt_to_timetable_train_x(self, zusi_tt, define_stations=False):
                Zusi_dict = zusi_tt.get("Zusi")
                Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan",{})
                if Buchfahrplan_dict=={}:
                        return
                
                kmStart = float(Buchfahrplan_dict.get("@kmStart","0.00"))
                ZugNummer = Buchfahrplan_dict.get("@Nummer","")
                ZugGattung = Buchfahrplan_dict.get("@Gattung","")
                ZugLok = Buchfahrplan_dict.get("@BR","")
                if ZugGattung == "X-Deko":
                        return
                Zuglauf = Buchfahrplan_dict.get("@Zuglauf","")
                Datei_fpn_dict = Buchfahrplan_dict.get("Datei_fpn",{})
                if Datei_fpn_dict == {}:
                        return
                fpn_dateiname = Datei_fpn_dict.get("@Dateiname","")
                self.schedule_dict["Name"] = fpn_dateiname
                train_idx = self.enter_train_data(ZugNummer,ZugGattung,Zuglauf,ZugLok)
                train_stop_idx = 0
                FplRglGgl_default = 2
                FplZeile_list = Buchfahrplan_dict.get("FplZeile",{})
                stationdistance = 0
                last_km = 0
                station_idx = 0
                if FplZeile_list=={}:
                        return
                for FplZeile_dict in FplZeile_list:
                        try:
                                FplRglGgl=int(FplZeile_dict.get("@FplRglGgl",FplRglGgl_default))
                        except:
                                print("Error:",ZugGattung,ZugNummer," ",repr(FplZeile_dict))
                                FplRglGgl = FplRglGgl_default
                                
                        if FplRglGgl != FplRglGgl_default:
                                continue # keine Umwege über Gegengleis
                        #determine distance between station - detect KmSprung
                        try:
                                
                                FplSprung = self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@FplSprung",default="")
                                Fplkm = float(self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@km",default=0))

                                if Fplkm == 0:
                                        continue # kein km Eintrag, nicht bearbeiten
                                if last_km == 0:
                                         # first entry
                                        last_km=Fplkm
                                if FplSprung == "":
                                        #print("FplSprung=",FplSprung," lastkm=",last_km," Fplkm=",Fplkm," Distance=",stationdistance)
                                        stationdistance = stationdistance + abs(Fplkm - last_km)
                                        #print("New Stationdistance:",stationdistance)
                                        last_km = Fplkm
                                else:
                                        #print("FplSprung=",FplSprung," lastkm=",last_km," Fplkm=",Fplkm," Distance=",stationdistance)
                                        stationdistance = stationdistance + abs(Fplkm - last_km)
                                        #print("New Stationdistance:",stationdistance)
                                        Neukm = float(self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@FplkmNeu",default=0))
                                        #print("Neukm=",Neukm)
                                        if Neukm == 0:
                                                print("ERROR: Neukm Eintrag fehlt",ZugGattung,ZugNummer,"-",repr(FplZeile_dict))
                                        else:
                                                last_km = Neukm
        
                                FplAbf = self.get_fplZeile_entry(FplZeile_dict, "FplAbf","@Abf")
                                if FplAbf == "":
                                        continue # only use station with "Abf"-Entry
                                
                                FplAbf_obj = datetime.strptime(FplAbf, '%Y-%m-%d %H:%M:%S')
                                FplAbf_min = FplAbf_obj.hour * 60 + FplAbf_obj.minute
                                
                                FplAnk = self.get_fplZeile_entry(FplZeile_dict, "FplAnk","@Ank")
                                if FplAnk!="":
                                        
                                        FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                                        FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute
                                else:
                                        FplAnk_min = 0
                                
                                FplName = self.get_fplZeile_entry(FplZeile_dict,"FplName","@FplNameText",default="---")
                                
                                if self.stationIdx_max == 0:
                                        stationdistance = 0
                                        
                                Fpldistance = stationdistance # abs(kmStart - Fplkm)
                                #print("Fpldistance=",Fpldistance)
                                
                                #FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                                
                                #print(FplName,"-",Fplkm,"-",FplAnk_min,"-",FplAbf_min,"-",Fpldistance)
                                
                                if define_stations:
                                        station_idx = self.enter_station(FplName,Fpldistance,Fplkm)
                                else:
                                        station_idx = self.search_station(FplName)
                                        if station_idx != -1:
                                                train_stop_idx = self.enter_train_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min)
                        except BaseException as e:
                                logging.debug("FplZeile conversion Error %s %s",ZugGattung+ZugNummer+"-"+repr(FplZeile_dict),e)
                                continue # entry format wrong                                                
                return
        
        def save_as_png(self, canvas, fileName):
                # save postscipt image 
                canvas.update()
                canvas.postscript(file = fileName + '.eps',colormode='color') 
                # use PIL to convert to PNG 
                #img = Image.open(fileName + '.eps')
                #try:
                        
                #        img.save(fileName + '.png', 'png')
                #except: 
                #        print("Error while generating png-file- Ghostscript not found")
                #        pass

class Timetable_main(Frame):
        
        def __init__(self,controller,canvas):
                super().__init__()
                self.controller = controller
                self.zusi_master_timetable_dict = {}
                self.canvas = canvas
                self.canvas_width = self.controller.getConfigData("Bfp_width")
                self.canvas_height = self.controller.getConfigData("Bfp_height")
        
                self.fpl_filename = self.controller.getConfigData("Bfp_filename")
                self.xml_filename = self.controller.getConfigData("Bfp_trainfilename")
                self.starthour = self.controller.getConfigData("Bfp_start")
                self.duration = self.controller.getConfigData("Bfp_duration")                
        
                self.initUI()
                
        def open_zusi_trn_file(self, trn_filepathname):
                
                with open(trn_filepathname,mode="r",encoding="utf-8") as fd:
                        xml_text = fd.read()
                        trn_dict = parse(xml_text)
                        
                trn_filepath, trn_filename = os.path.split(trn_filepathname)
                
                trn_zusi_dict = trn_dict.get("Zusi",{})
                trn_zug_dict = trn_zusi_dict.get("Zug",{})
                Buchfahrplan_dict = trn_zug_dict.get("BuchfahrplanRohDatei",{})
                if Buchfahrplan_dict != {}:
                        Bfpl_Dateiname = Buchfahrplan_dict.get("@Dateiname")
                        
                        Bfpl_file_path, Bfpl_file_name = os.path.split(Bfpl_Dateiname)
                        
                        Bfpl_filepathname = os.path.join(trn_filepath,Bfpl_file_name)
                        
                        with open(Bfpl_filepathname,mode="r",encoding="utf-8") as fd:
                                xml_text = fd.read()
                                Bfpl_timetable_dict = parse(xml_text)
        
                                #enter train-timetable
                                self.timetable.convert_zusi_tt_to_timetable_train_x(Bfpl_timetable_dict)                
                
                
        def open_zusi_master_schedule(self,fpl_filename=""):
                #fpl_filename = r"D:\Zusi3\_ZusiData\Timetables\Deutschland\Ruhrtalbahn\Hagen-Kassel_Fahrplan1981_12Uhr-19Uhr.fpn"
                #fpl_filename = filedialog.askopenfilename(title="Select Zusi Master Schedule",filetypes=(("Zusi-Master-Fahrplan","*.fpn"),("all files","*.*")))
                                
                if fpl_filename == "": return
                
                fpl_path, fpl_file = os.path.split(fpl_filename)
        
                print('Input File, %s.' % fpl_filename)
                with open(fpl_filename,mode="r",encoding="utf-8") as fd:
                        xml_text = fd.read()
                        self.zusi_master_timetable_dict = parse(xml_text)
                zusi_dict = self.zusi_master_timetable_dict.get("Zusi")        
                fahrplan_dict = zusi_dict.get("Fahrplan")       
                zug_list = fahrplan_dict.get("Zug")
                
                for zug in zug_list:
                        datei_dict = zug.get("Datei")
                        trn_filename = datei_dict.get("@Dateiname")
                        trn_filename_comp = trn_filename.split("\\")
                        trn_file_and_path = os.path.join(fpl_path,trn_filename_comp[-2],trn_filename_comp[-1])
                        
                        self.open_zusi_trn_file(trn_file_and_path)
        
        def get_station_list(self,trn_zug_dict):
                station_list = []
                FplEintrag_list = trn_zug_dict.get("FahrplanEintrag")
                for FplEintrag in FplEintrag_list:
                        #print(repr(FplEintrag))
                        try:
                                betrst = FplEintrag.get("@Betrst","")
                        except:
                                continue
                        if betrst != "":
                                if not (betrst in station_list):
                                        station_list.append(betrst)

                return station_list
                
        def create_zusi_trn_list(self, trn_filepathname):
                
                with open(trn_filepathname,mode="r",encoding="utf-8") as fd:
                        xml_text = fd.read()
                        trn_dict = parse(xml_text)
                        
                trn_filepath, trn_filename = os.path.split(trn_filepathname)
                
                trn_zusi_dict = trn_dict.get("Zusi")
                trn_zug_dict = trn_zusi_dict.get("Zug")
                
                fahrplan_gruppe = trn_zug_dict.get("@FahrplanGruppe","")
                zugGattung = trn_zug_dict.get("@Gattung","")
                zugNummer = trn_zug_dict.get("@Nummer","")
                zugLauf = trn_zug_dict.get("@Zuglauf","")
                
                Buchfahrplan_dict = trn_zug_dict.get("BuchfahrplanRohDatei",{})
                Bfpl_Dateiname = Buchfahrplan_dict.get("@Dateiname","")
                if Bfpl_Dateiname != "":
                        
                        Bfpl_file_path, Bfpl_file_name = os.path.split(Bfpl_Dateiname)
                        Bfpl_filepathname = os.path.join(trn_filepath,Bfpl_file_name)
                else:
                        Bfpl_filepathname = ""
                
                station_list = self.get_station_list(trn_zug_dict)
                
                zusi_fahrplan_gruppe_dict = self.zusi_zuglist_dict.get(fahrplan_gruppe,{})
                station_list_str = repr(station_list)
                if zusi_fahrplan_gruppe_dict == {}:
                        self.zusi_zuglist_dict[fahrplan_gruppe] = {zugGattung+zugNummer: station_list_str}
                else:
                        station_found=False
                        for key,value in zusi_fahrplan_gruppe_dict.items():
                                if value == station_list_str:
                                        station_found=True
                                        break
                        if not station_found:
                                self.zusi_zuglist_dict[fahrplan_gruppe][zugGattung+zugNummer] = station_list_str
                self.zusi_zuglist_xmlfilename_dict[zugGattung+zugNummer]=Bfpl_filepathname
                
        def create_zusi_zug_liste(self,fpl_filename=""):
                if fpl_filename == "": return
                
                fpl_path, fpl_file = os.path.split(fpl_filename)
        
                print('Input File, %s.' % fpl_filename)
                with open(fpl_filename,mode="r",encoding="utf-8") as fd:
                        xml_text = fd.read()
                        self.zusi_master_timetable_dict = parse(xml_text)
                zusi_dict = self.zusi_master_timetable_dict.get("Zusi")        
                fahrplan_dict = zusi_dict.get("Fahrplan")       
                zug_list = fahrplan_dict.get("Zug")
                self.zusi_zuglist_dict = {}
                self.zusi_zuglist_xmlfilename_dict ={}
                
                for zug in zug_list:
                        datei_dict = zug.get("Datei")
                        trn_filename = datei_dict.get("@Dateiname")
                        trn_filename_comp = trn_filename.split("\\")
                        trn_file_and_path = os.path.join(fpl_path,trn_filename_comp[-2],trn_filename_comp[-1])
                        self.create_zusi_trn_list(trn_file_and_path)
                
                # sort entries
                for train_line in self.zusi_zuglist_dict:
                        train_line_dict = self.zusi_zuglist_dict.get(train_line, {})
                        train_line_sorted_keys = sorted(train_line_dict.items())
                        self.zusi_zuglist_dict[train_line] = {}
                        for key,value in train_line_sorted_keys:
                                self.zusi_zuglist_dict[train_line][key] = value
                        
                        
                print(repr(self.zusi_zuglist_dict))
                
                zusi_zug_list_main_dict={}
                zusi_zug_list_main_dict["Trainlist"]=self.zusi_zuglist_dict
                zusi_zug_list_main_dict["XML_Filenamelist"]=self.zusi_zuglist_xmlfilename_dict

                return zusi_zug_list_main_dict
                
                
        def resize_canvas(self,width,height):
                self.canvas.delete("all")
                self.canvas.config(width=width,height=height,scrollregion=(0,0,width,height))
                self.timetable.doPaint(self.canvas)
                
        def redo_fpl_and_canvas(self,width,height, starthour=8, duration=9,fpl_filename="", xml_filename = ""):
                if fpl_filename == "":
                        fpl_filename=r"D:\Zusi3\_ZusiData\Timetables\Deutschland\Ruhrtalbahn\Hagen-Kassel_Fahrplan1981_12Uhr-19Uhr.fpn"
                if xml_filename == "":
                        xml_filename = r"D:\Zusi3\_ZusiData\Timetables\Deutschland\Ruhrtalbahn\Hagen-Kassel_Fahrplan1981_12Uhr-19Uhr\D843.timetable.xml"
                
                self.canvas.delete("all")
                self.canvas.config(width=width,height=height,scrollregion=(0,0,width,height))
                self.canvas.update()
                print('Input File master train timetable, %s.' % xml_filename)
                with open(xml_filename,mode="r",encoding="utf-8") as fd:
                        xml_text = fd.read()
                        zusi_timetable_dict = parse(xml_text)

                self.timetable = TimeTableGraphCommon(self.controller, True, height, width)
                #define stops via selected train-timetable
                self.timetable.convert_zusi_tt_to_timetable_train_x(zusi_timetable_dict,define_stations=True)
                self.open_zusi_master_schedule(fpl_filename=fpl_filename)
                self.timetable.doPaint(self.canvas,starthour=starthour,duration=duration)                

    
        def initUI(self):
    
                #self.master.title("Timetable")
                #self.pack(fill=BOTH, expand=1)
        
                #canvas = Canvas(self)
                #canvas.create_line(15, 25, 200, 25)
                #canvas.create_line(300, 35, 300, 200, dash=(4, 2))
                #canvas.create_line(55, 85, 155, 85, 105, 180, 55, 85)
                showTrainTimes = True
                height =self.canvas.winfo_reqheight()
                width = self.canvas.winfo_reqwidth()
                
                #self.redo_fpl_and_canvas(width, height)
                

                #xml_filename = r"D:\Zusi3\_ZusiData\Timetables\Deutschland\Ruhrtalbahn\Hagen-Kassel_Fahrplan1981_12Uhr-19Uhr\D843.timetable.xml"
                #xml_filename = filedialog.askopenfilename(title="ZUSI Zugfahrplan",filetypes=(("Timetable","*.xml"),("all files","*.*")))
                                
                #if xml_filename == "": return
        
                #print('Input File master train timetable, %s.' % xml_filename)
                #with open(xml_filename,mode="r",encoding="utf-8") as fd:
                #        xml_text = fd.read()
                #        zusi_timetable_dict = parse(xml_text)

                #self.timetable = TimeTableGraphCommon(self.controller, showTrainTimes, height, width)
                #define stops via selected train-timetable
                #self.timetable.convert_zusi_tt_to_timetable_train_x(zusi_timetable_dict,define_stations=True)
                
                #self.open_zusi_master_schedule()

                #self.timetable.doPaint(self.canvas)
                
                #self.timetable.save_as_png(canvas, xml_filename)
        
                #canvas.pack(fill=BOTH, expand=1)
