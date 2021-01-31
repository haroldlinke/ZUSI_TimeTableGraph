#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#         TimetableGraph
#
# * Version: 0.01
# * Author: Harold Linke
# * Date: January 12th, 2021
# * Copyright: Harold Linke 2021
# *
# *
# ***************************************************************************

from tkinter import Tk, Canvas, Frame, BOTH, font, filedialog
import uuid
from tkinter import ttk
from tools.xmltodict import parse
#from collections import OrderedDict
from datetime import datetime
#from timetablepages.DefaultConstants import STD_FONT
import os
import logging
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

    def __init__(self, controller, showTrainTimes, height, width, xml_filename="xml_filename"):
        self.controller = controller
        self.xml_filename = xml_filename
        self.showTrainTimes = showTrainTimes
        self.ZugGattung_to_Color = {}
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
        self.bigFont = font.Font(family="SANS_SERIF", size=20)
        self.stdFont = font.Font(family="SANS_SERIF", size=10)
        self.smallFont = font.Font(family="SANS_SERIF", size=8)
        self.gridstroke = 0.5
        self.stroke = 2.0
        self.segmentId = 0
        self.scheduleId = 0
        self.stops = []
        # ------------ global variables ------------
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
        self.graphHeadersize = 140
        self.graphBottomsize = 20
        self.graphLeftbordersize = 50
        self.graphRightbordersize = 20
        self.tt_canvas = None 
        self.pf = 0
        TLDirection = self.controller.getConfigData("TLDirection")
        self.draw_stations_vertical = (TLDirection=="vertical")
        #    ------------ train variables ------------
        self.textLocation = [(0,0,5,5)]
        #   Train
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
        self.firstHourXY = 0.0
        self.lastHourXY = 0.0
        self.sizeMinute = 0.0
        self.throttleX = 0.0

    def set_zuggattung_to_color(self,traintype_to_color_dict):
        self.ZugGattung_to_Color = traintype_to_color_dict.copy()

    def doPaint (self,canvas,starthour=12,duration=7):
        TLDirection = self.controller.getConfigData("TLDirection")
        self.draw_stations_vertical = (TLDirection=="vertical")                
        self.tt_canvas = canvas
        self.dimHeight =self.tt_canvas.winfo_reqheight()
        self.dimWidth = self.tt_canvas.winfo_reqwidth()                
        self.startHour=starthour
        self.startTime_min = self.startHour * 60
        self.duration = duration
        self.stationGrid  = {} 
        self.hourGrid     = []
        self.textLocation = []
        self.graphTop = self.graphHeadersize
        self.graphHeight = self.dimHeight - self.graphTop - self.graphBottomsize
        self.graphBottom = self.graphTop + self.graphHeight
        self.graphLeft = self.graphLeftbordersize
        self.graphWidth = self.dimWidth - self.graphLeft - self.graphRightbordersize
        # Draw the left column components
        self.drawInfoSection()
        self.drawStationSection()
        # Set the horizontal graph dimensions based on the width of the left column
        if self.draw_stations_vertical:
            self.graphLeft = self.infoColWidth + 50.0
            self.graphWidth = self.dimWidth - self.infoColWidth - 65.0
        self.graphRight = self.graphLeft + self.graphWidth
        self.drawHours()
        self.drawGraphGrid()
        self.drawTrains()

    def determine_xy_point(self, stop, time):
        if self.draw_stations_vertical:
            x = self.calculateTimePos(time)
            y = self.stationGrid.get(stop.get("StationIdx",0),0)
        else:
            y = self.calculateTimePos(time)
            x = self.stationGrid.get(stop.get("StationIdx",0),0)                        
        return x,y

    def determine_station_xy_point(self, stationName, distance):
        self.infoColWidth = max(self.infoColWidth, self.stdFont.measure(stationName) + 5)
        if self.draw_stations_vertical:
            y = ((self.graphHeight - 50) / self.maxDistance) * distance + self.graphTop + 30  #// calculate the Y offset                
            x = 15.0
        else:
            x = ((self.graphWidth - 50) / self.maxDistance) * distance + self.graphLeft + 30  #// calculate the Y offset                
            y = self.graphTop - 20                        
        return x,y

    def print_station(self, stationIdx, stationName, distance, stationkm):
        x, y=self.determine_station_xy_point(stationName, distance)
        textwidth = self.stdFont.measure(stationName)
        textheight = 12
        if self.draw_stations_vertical:
            self.stationGrid[stationIdx] = y
            stationName = stationName + " (km "+str(f"{stationkm:.1f}")+")"
            self.tt_canvas.create_text(x, y, text=stationName, font=self.stdFont, anchor="w")
        else:
            self.stationGrid[stationIdx] = x
            yName = y - 15 * (stationIdx%2)
            self.tt_canvas.create_rectangle(x-textwidth/2, yName-textheight/2, x+textwidth/2, yName+textheight/2, fill="white",width=0,outline="white")
            self.tt_canvas.create_text(x, yName, text=stationName, font=self.stdFont, anchor="center")
            yKm = y + 12
            self.tt_canvas.create_text(x, yKm, text=str(f"{stationkm:.1f}"), font=self.stdFont, anchor="center")

    def print_hour(self, i, currentHour):
        hourString = str(currentHour)+":00"
        hOffset = self.stdFont.measure(hourString) / 2 # hOffset = self.g2.getFontMetrics().stringWidth(hourString) / 2;
        if self.draw_stations_vertical:
            hourXY = (self.hourWidth * i) + self.hourOffset + self.graphLeft
            self.tt_canvas.create_text(hourXY - hOffset, self.graphBottom + 20, text = hourString, anchor="w")
            self.tt_canvas.create_text(hourXY - hOffset, self.graphTop - 8, text = hourString, anchor="w")
        else:
            hourXY = (self.hourWidth * i) + self.hourOffset + self.graphTop
            self.tt_canvas.create_text(self.graphLeft-10,hourXY, text = hourString, anchor="e")
        self.hourMap[currentHour] = hourXY
        self.hourGrid.append(hourXY);
        if (i == 0):
            self.firstHourXY = hourXY# - hOffset;
        if (i == self.duration):
            self.lastHourXY = hourXY# - hOffset;
        return

    def calculateTimePos(self, time):
        if (time < 0): time = 0;
        if (time > 1439): time = 1439;
        hour = int(time / 60)
        min = int(time % 60)
        timeposhour = self.hourMap.get(hour,None)
        if timeposhour:
            timeposhour = timeposhour + (min * self.sizeMinute)
            if timeposhour > self.lastHourXY:
                timeposhour = self.lastHourXY
        else:
            if hour > self.startHour + self.duration:
                timeposhour = self.lastHourXY
            else:
                timeposhour = self.firstHourXY
        return timeposhour      

    def drawInfoSection(self):
        scheduleName = self.schedule_dict.get("Name","")
        self.tt_canvas.create_text(10, 10, text="ZUSI Bildfahrplan", font=self.bigFont, anchor="nw")
        self.tt_canvas.create_text(10, 40, text="Fahrplan:"+scheduleName, font=self.stdFont, anchor="nw")
        self.tt_canvas.create_text(10, 55, text="Buchfahrplanstrecke:"+self.xml_filename, font=self.stdFont, anchor="nw")
        self.tt_canvas.create_text(10, 70, text="Zugfahrplandateien:"+ self.controller.getConfigData("TLFileType"), font=self.stdFont, anchor="nw");

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
                stationName = stationName# + " (km "+str(f"{stationkm:.2f}")+")"
                self.print_station(stationIdx, stationName, distance, stationkm)

    def drawHours(self):
        currentHour = self.startHour
        try:
            if self.draw_stations_vertical:
                self.hourWidth = self.graphWidth / (self.duration)
            else:
                self.hourWidth = self.graphHeight / (self.duration)
        except:
            print("error")
        self.hourOffset = 0 #hourWidth / 2
        self.hourgrid = []
        for i in range(0, self.duration+1):
            self.print_hour(i, currentHour)
            currentHour+= 1
            if (currentHour > 23):
                currentHour -= 24

    def drawGraphGrid(self):
        # Print the graph box
        self.tt_canvas.create_rectangle(self.graphLeft, self.graphTop, self.graphLeft+self.graphWidth, self.graphTop + self.graphHeight)
        # Print the grid lines
        if self.draw_stations_vertical:
            for y in self.stationGrid.values():
                self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=2, fill="gray")
            for x in self.hourGrid:
                self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=2, fill="gray")
        else:
            for y in self.hourGrid:
                self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=2, fill="gray")
            for x in self.stationGrid.values():
                self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=2, fill="gray")                        

#     * Create the train line for each train with labels.  Include times if
#     * selected.
#     * <p>
#     * All defined trains their stops are processed.  If a stop has a station
#     * in the segment, it is included.  Most trains only use a single segment.

    def drawTrains(self):
        self.baseTime = self.startHour * 60
        if self.draw_stations_vertical:
            self.sizeMinute = self.graphWidth / ((self.duration) * 60)
        else:
            self.sizeMinute = self.graphHeight / ((self.duration) * 60)
        self.throttleX = 0
        self.default_trainColor = self.ZugGattung_to_Color.get("*","black")
        for trainidx in self.trains:
            self.tt_canvas.update()
            train = self.trains.get(trainidx,{})
            self.trainType = train.get("TrainType","X-Deko")
            self.trainName = self.trainType + train.get("TrainName","0000")
            self.trainLineName = train.get("TrainLine","")
            self.trainEngine = train.get("TrainEngine","")
            self.outgoing_station = train.get("Outgoing_Station","")
            self.incoming_station = train.get("Incoming_Station","") 
            if (self.trainTypeList != [] and not self.trainType in self.trainTypeList):
                break
            self.trainColor = self.ZugGattung_to_Color.get(self.trainType,self.default_trainColor)
            if self.trainColor == "": 
                continue
            self.trainLine = []
            self.stops = train.get("Stops",{});
            self.stopCnt = len(self.stops);
            self.firstStop = True;
            self.lastStop = False;
            self.prevStop = None
            self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan für Zug - "+self.trainName) 
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
                        # One stop route or only one stop in current segment
                        self.setEnd(self.stopStation, False)
                        break
                    continue
                self.drawLine(self.stopStation);
                if (self.lastStop):
                    # At the end, do the end process
                    self.setEnd(self.stopStation, False)
                    break
        self.controller.set_statusmessage("") 

# 
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
#        
    def drawTrainName( self, x,  y,  justify,  invert,  throttle):

        textbox_x= self.stdFont.measure(self.trainName)
        # Position train name
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
        x = textRect[0]
        trainName_objid = self.tt_canvas.create_text(x , y, activefill="red",text = self.trainName, anchor = "w")
        self.controller.ToolTip_canvas(self.tt_canvas, trainName_objid, text="Zug: "+self.trainName+" "+self.direction, key=self.trainName,button_1=True)
        self.textLocation.append(textRect)

#    
#        * Draw the minutes value on the graph if enabled.
#        * @param time The time in total minutes.  Converted to remainder minutes.
#        * @param mode Used to set the x and y offsets based on type of time.
#        * @param x The base x coordinate.
#        * @param y The base y coordinate.
#
    def drawTrainTime(self, time,  mode,  x,  y):
        if (not self.showTrainTimes):
            return;
        if not (time in range(self.startTime_min,self.startTime_min + self.duration * 60)):
            return                
        minutes = "{:02d}".format(time % 60) 
        hours = "{:02d}".format(int(time/60))   
        textbox_x = self.stdFont.measure(minutes)
        if self.draw_stations_vertical:
            if mode ==  "begin" :
                mode_txt = "Start"
                if (self.direction== "down"):
                    x = x + 4
                    y = y + 10
                else:
                    x = x + 4
                    y = y - 10
            elif mode == "arrive":
                mode_txt = "Ankunft"
                if (self.direction== "down"):
                    x = x - 4
                    y = y + 10
                else:
                    x = x - 4
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
                if (self.direction== "down"):
                    x = x - 4
                    y = y + 10
                else:
                    x = x - 4
                    y = y - 10
            else:
                return
        else:
            if mode ==  "begin" :
                mode_txt = "Start"
                if (self.direction== "down"):
                    x = x + 10
                    y = y + 4
                else:
                    x = x -10
                    y = y + 4
            elif mode == "arrive":
                mode_txt = "Ankunft"
                if (self.direction== "down"):
                    x = x + 10
                    y = y - 4
                else:
                    x = x - 10
                    y = y - 4
            elif mode == "depart":
                mode_txt = "Abfahrt"
                if (self.direction== "down"):
                    x = x - 10
                    y = y - 4
                else:
                    x = x + 10
                    y = y - 4  
            elif mode == "end":
                mode_txt = "Ziel"
                if (self.direction== "down"):
                    x = x - 10
                    y = y - 4
                else:
                    x = x + 10
                    y = y - 4  
            else:
                return        
        #textRect = (
        #            x,
        #                y,
        #                textbox_x,
        #                10
        #       )

        trainTime_objid = self.tt_canvas.create_text(x , y, text = minutes, anchor="center",activefill="red")
        if self.trainLineName == None:
            self.trainLineName = ""
        self.controller.ToolTip_canvas(self.tt_canvas, trainTime_objid, text=hours+":"+minutes+"\nZug: "+self.trainName+" - "+mode_txt+"\n"+self.trainLineName, key=self.trainName,button_1=True)
        #self.textLocation.append(textRect)                

#    
#        * Move text that overlaps existing text.
#        * @param textRect The proposed text rectangle.
#        * @return The resulting rectangle
#        
    def adjustText(self, textRect):
        return textRect

#    
#    Determine direction of travel on the graph: up or down
#    
    def setDirection(self):
        if (self.stopCnt == 1):
            # Single stop train, default to down
            self.direction = "down"
            return;
        stop = self.stops.get(self.stopIdx,{});
        currStation_Idx = stop.get("StationIdx",0)
        currStation = self.stations.get(currStation_Idx,{})
        currkm = currStation.get("Distance",0)
        if (self.firstStop):
            # For the first stop, use the next stop to set the direction
            nextStation_Idx = self.stops.get(self.stopIdx + 1).get("StationIdx",0)
            nextStation = self.stations.get(nextStation_Idx,{})
            nextkm = nextStation.get("Distance",0)
            if nextkm > currkm:
                self.direction = "down" 
            else:  
                self.direction = "up"
            return
        if (self.lastStop):    
            prevStation_Idx = self.stops.get(self.stopIdx - 1).get("StationIdx",0)
            prevStation = self.stations.get(prevStation_Idx,{})
            # For the last stop, use the previous stop to set the direction
            # Last stop may also be only stop after segment change; if so wait for next "if"
            prevkm = prevStation.get("Distance",0)
            if prevkm < currkm:
                self.direction = "down" 
            else :  
                self.direction = "up"                                
            return
        # For all other stops in the active segment, use the next stop.
        nextStation_Idx = self.stops.get(self.stopIdx + 1).get("StationIdx",0)
        nextStation = self.stations.get(nextStation_Idx)
        nextkm = nextStation.get("Distance",0)
        if nextkm > currkm:
            self.direction = "down"
        else: 
            self.direction = "up";  
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
        x,y = self.determine_xy_point(stop,self.arriveTime)
        if y == None:
            return
        self.trainLine = [x, y]
        self.setDirection()
        self.arriveTime = stop.get("ArriveTime",0)
        self.drawTrainTime(self.arriveTime, "begin", x, y)
        # Check for stop duration before depart
        self.departTime = stop.get("DepartTime",0)
        if (self.departTime - self.arriveTime > 0):
            x,y = self.determine_xy_point(stop,self.departTime)
            self.trainLine.extend([x, y])
            self.drawTrainTime(self.departTime, "depart", x, y)

#    
#        * Extend the train line with additional stops.
#        * @param stop The current stop.
#        
    def drawLine(self, stop):
        if not (self.departTime in range(self.startTime_min,self.startTime_min + self.duration * 60) or self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
            return
        x,y = self.determine_xy_point(stop,self.arriveTime)
        if y==None:
            return
        self.trainLine.extend([x, y])
        self.drawTrainTime(self.arriveTime, "arrive", x, y);  #
        if len(self.trainLine)>3:
            self.draw_trainName_parallel(self.trainName, self.trainLine[-4],self.trainLine[-3],x, y)                
        self.setDirection();
        # Check for duration after arrive
        if (self.departTime - self.arriveTime) > 0 :
            if not (self.departTime in range(self.startTime_min,self.startTime_min + self.duration * 60) or self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                return                        
            x,y = self.determine_xy_point(stop,self.departTime)
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
            else:
                if (self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                    x,y = self.determine_xy_point(stop,self.arriveTime)
                else:
                    x = self.trainLine[-2]
                    y = self.trainLine[-1]
            if (not skipLine):
                if y==None:
                    logging.debug("SetEnd Error: %s %s",self.trainType+self.trainName,repr(stop))
                    return
                self.trainLine.extend([x, y])
                train_line_objid = self.tt_canvas.create_line(self.trainLine,fill=self.trainColor,width=4,activewidth=8)
                self.controller.ToolTip_canvas(self.tt_canvas, train_line_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, key=self.trainName,button_1=True)
                if self.outgoing_station!="": # draw outgoing arrow
                    if self.direction == "down":
                        arrow_delta = 10
                    else:
                        arrow_delta = -10
                    if self.draw_stations_vertical:
                        train_line_out_objid = self.tt_canvas.create_line([x,y,x,y+arrow_delta],fill=self.trainColor,width=4,activewidth=8,arrow="last",arrowshape=(10,10,4))
                    else:
                        train_line_out_objid = self.tt_canvas.create_line([x,y,x+arrow_delta,y],fill=self.trainColor,width=4,activewidth=8,arrow="last",arrowshape=(10,10,4))
                    self.controller.ToolTip_canvas(self.tt_canvas, train_line_out_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nNach "+self.outgoing_station, key=self.trainName,button_1=True)
                    
                if self.incoming_station!="": # draw outgoing arrow
                    if self.direction == "down":
                        arrow_delta = 10
                    else:
                        arrow_delta = -10
                    x = self.trainLine[0]
                    y = self.trainLine[1]                    
                    if self.draw_stations_vertical:
                        train_line_in_objid = self.tt_canvas.create_line([x,y,x,y-arrow_delta],fill=self.trainColor,width=4,activewidth=8,arrow="first",arrowshape=(10,10,4))
                    else:
                        train_line_in_objid = self.tt_canvas.create_line([x,y,x-arrow_delta,y],fill=self.trainColor,width=4,activewidth=8,arrow="first",arrowshape=(10,10,4))
                    self.controller.ToolTip_canvas(self.tt_canvas, train_line_in_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nVon "+self.incoming_station, key=self.trainName,button_1=True)                
        except BaseException as e                    :
                    
            logging.debug("SetEnd Error %s %s",self.trainType+self.trainName+"-"+repr(self.trainLine),e)
            return  
#            
#                * Convert the time value, 0 - 1439 to the x graph position.
#                * @param time The time value.
#                * @return the x value.
#                

    def draw_trainName_parallel(self,trainName,x0,y0,x1,y1):
        p0=Point(x0,y0)
        p1=Point(x1,y1)
        segment = p1 - p0
        mid_point = segment.scale(0.5) + p0
        offset = segment.perp().scale(10)
        trainName_len = self.stdFont.measure(self.trainName)
        segment_len = segment.norm()
        if segment_len > trainName_len+15:
            txt = self.tt_canvas.create_text(*(offset + mid_point), text=trainName,activefill="red")
            self.controller.ToolTip_canvas(self.tt_canvas, txt, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, key=self.trainName,button_1=True)
            if y0 != y1:
                angle = segment.angle()
                if angle>90:
                    angle -= 180
                if angle<-90:
                    angle+=180

                self.tt_canvas.itemconfig(txt, angle=angle)                

    def enter_station(self,stationName, distance, stationKm):
        if stationKm == None:
            print("Error: km=None -",stationName)
            stationKm = 0

        for stationIdx in self.stations:
            station_data = self.stations.get(stationIdx,0)
            if station_data.get("StationName","") == stationName:
                return stationIdx
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
    
    def enter_train_incoming_station(self, train_idx, FplName):
        train_dict = self.trains.get(train_idx)
        train_dict["Incoming_Station"] = FplName
        return
    
    def enter_train_outgoing_station(self, train_idx, FplName):
        train_dict = self.trains.get(train_idx)
        train_dict["Outgoing_Station"] = FplName
        return

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

    def convert_zusi_fpn_dict_to_timetable_train_x(self, zusi_fpn_dict, define_stations=False):
        Zusi_dict = zusi_fpn_dict.get("Zusi")
        Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan",{})
        if Buchfahrplan_dict=={}:
            return False
        kmStart = float(Buchfahrplan_dict.get("@kmStart","0.00"))
        ZugNummer = Buchfahrplan_dict.get("@Nummer","")
        ZugGattung = Buchfahrplan_dict.get("@Gattung","")
        ZugLok = Buchfahrplan_dict.get("@BR","")
        if ZugGattung == "X-Deko":
            return False
        Zuglauf = Buchfahrplan_dict.get("@Zuglauf","")
        Datei_fpn_dict = Buchfahrplan_dict.get("Datei_fpn",{})
        if Datei_fpn_dict == {}:
            return False
        fpn_dateiname = Datei_fpn_dict.get("@Dateiname","")

        Datei_trn_dict = Buchfahrplan_dict.get("Datei_trn",{})
        if Datei_trn_dict == {}:
            return False
        trn_dateiname = Datei_trn_dict.get("@Dateiname","")
        
        self.schedule_dict["Name"] = fpn_dateiname
        train_idx = self.enter_train_data(ZugNummer,ZugGattung,Zuglauf,ZugLok)
        train_stop_idx = 0
        FplRglGgl_default = 2
        FplZeile_list = Buchfahrplan_dict.get("FplZeile",{})
        stationdistance = 0
        last_km = 0
        station_idx = 0
        if FplZeile_list=={}:
            logging.info("timetable.xml file error: %s",trn_dateiname )
            self.controller.set_statusmessage("Error: ZUSI entry not found in fpl-file: "+trn_dateiname)            
            return False
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
                    stationdistance = stationdistance + abs(Fplkm - last_km)
                    last_km = Fplkm
                else:
                    stationdistance = stationdistance + abs(Fplkm - last_km)
                    Neukm = float(self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@FplkmNeu",default=0))
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
                if define_stations:
                    station_idx = self.enter_station(FplName,Fpldistance,Fplkm)
                else:
                    station_idx = self.search_station(FplName)
                    if station_idx != -1:
                        train_stop_idx = self.enter_train_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min)
            except BaseException as e:
                logging.debug("FplZeile conversion Error %s %s",ZugGattung+ZugNummer+"-"+repr(FplZeile_dict),e)
                continue # entry format wrong                                                
        return True
    
    def convert_zusi_trn_to_timetable_train_x(self, zusi_trn_zug_dict):
        try:
            if zusi_trn_zug_dict=={}:
                return
            ZugNummer = zusi_trn_zug_dict.get("@Nummer","")
            ZugGattung = zusi_trn_zug_dict.get("@Gattung","")
            ZugLok = zusi_trn_zug_dict.get("@BR","")
            if ZugGattung == "X-Deko":
                return
            Zuglauf = zusi_trn_zug_dict.get("@Zuglauf","")
            Datei_fpn_dict = zusi_trn_zug_dict.get("Datei",{})
            if Datei_fpn_dict == {}:
                return
            fpn_dateiname = Datei_fpn_dict.get("@Dateiname","")
            self.schedule_dict["Name"] = fpn_dateiname
            train_idx = self.enter_train_data(ZugNummer,ZugGattung,Zuglauf,ZugLok)
            train_stop_idx = 0
            FplZeile_list = zusi_trn_zug_dict.get("FahrplanEintrag",{})
            if FplZeile_list=={}:
                return
            Fpl_Zeile_cnt_max = len(FplZeile_list)
            for FplZeile_dict in FplZeile_list:
                FplAbf = FplZeile_dict.get("@Abf","")
                if FplAbf == "":
                    continue # only use station with "Abf"-Entry
                FplAbf_obj = datetime.strptime(FplAbf, '%Y-%m-%d %H:%M:%S')
                FplAbf_min = FplAbf_obj.hour * 60 + FplAbf_obj.minute
                FplAnk = FplZeile_dict.get("@Ank","")
                if FplAnk!="":
                    FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                    FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute
                else:
                    FplAnk_min = 0
                FplName = FplZeile_dict.get("@Betrst","----")
                station_idx = self.search_station(FplName)
                if station_idx != -1:
                    train_stop_idx = self.enter_train_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min)
                else:
                    if train_stop_idx == 0:
                        # train is comming from another station
                        self.enter_train_incoming_station(train_idx, FplName)
            if station_idx == -1:
                #last station is unknown
                self.enter_train_outgoing_station(train_idx, FplName)
                
        except BaseException as e:
            logging.debug("FplZeile conversion Error %s %s",ZugGattung+ZugNummer+"-"+repr(FplZeile_dict),e)
                                             
        return    

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
        
    def open_zusi_trn_zug_dict(self,trn_zug_dict,fpn_filepathname):
        
        TLFileType = self.controller.getConfigData("TLFileType")
        if TLFileType == ".timetable.xml":
            Buchfahrplan_dict = trn_zug_dict.get("BuchfahrplanRohDatei",{})
            if Buchfahrplan_dict != {}:
                timetable_filepathname = Buchfahrplan_dict.get("@Dateiname")
                trn_filepath, trn_filename = os.path.split(fpn_filepathname)
                #timetable_filepath, timetable_filename = os.path.split(timetable_filepathname)
                timetable_filecomp = timetable_filepathname.split("\\")
                Bfpl_filepathname = os.path.join(trn_filepath,timetable_filecomp[-2],timetable_filecomp[-1])                
                
                #Bfpl_filepathname = os.path.join(trn_filepath,Bfpl_file_name)
                
                with open(Bfpl_filepathname,mode="r",encoding="utf-8") as fd:
                    xml_text = fd.read()
                    Bfpl_timetable_dict = parse(xml_text)
                    #enter train-timetable
                    result_ok = self.timetable.convert_zusi_fpn_dict_to_timetable_train_x(Bfpl_timetable_dict) 
        else:
            self.timetable.convert_zusi_trn_to_timetable_train_x(trn_zug_dict)        

    def open_zusi_trn_file(self, trn_filepathname,fpn_filepathname):

        with open(trn_filepathname,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            trn_dict = parse(xml_text)
        trn_zusi_dict = trn_dict.get("Zusi",{})
        trn_zug_dict = trn_zusi_dict.get("Zug",{})        
        self.open_zusi_trn_zug_dict(trn_zug_dict, fpn_filepathname)

    def open_zusi_master_schedule(self,fpn_filename=""):
        self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+fpn_filename)
        self.controller.update()
        if fpn_filename == "": return
        fpl_path, fpl_file = os.path.split(fpn_filename)
        logging.info('Input File, %s.' % fpn_filename)
        with open(fpn_filename,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            self.zusi_master_timetable_dict = parse(xml_text)

        zusi_dict = self.zusi_master_timetable_dict.get("Zusi",{})
        if zusi_dict == {}:
            logging.info("ZUSI Entry not found")
            self.controller.set_statusmessage("Error: ZUSI entry not found in file: "+fpn_filename)
            return False
            
        fahrplan_dict = zusi_dict.get("Fahrplan",{})
        if fahrplan_dict == {}:
            logging.info("Fahrplan Entry not found")
            self.controller.set_statusmessage("Error: Fahrplan entry not found in fpl-file: "+fpn_filename)
            return False
        
        zug_list = fahrplan_dict.get("Zug",{})
        if zug_list == {}:
            # integrate fpl file
            self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+fpn_filename)
            for trn_zug_dict in fahrplan_dict.get("trn",{}):
                self.open_zusi_trn_zug_dict(trn_zug_dict, fpn_filename)
                self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+fpn_filename)
        else:
            for zug in zug_list:
                datei_dict = zug.get("Datei")
                trn_filename = datei_dict.get("@Dateiname")
                trn_filename_comp = trn_filename.split("\\")
                trn_file_and_path = os.path.join(fpl_path,trn_filename_comp[-2],trn_filename_comp[-1])
                self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+trn_file_and_path)
                self.controller.update()
                self.open_zusi_trn_file(trn_file_and_path,fpn_filename)
        self.controller.set_statusmessage(" ")
        return True

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
    
    def create_zusi_trn_list_from_zug_dict(self,trn_zug_dict, trn_filepath):
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
            logging.info("Kein BuchfahrplanRohDatei Element gefunden %s%s %s", zugGattung,zugNummer,trn_filepath)
            self.controller.set_statusmessage("Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath)
            return

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
        
        return

    def create_zusi_trn_list(self, trn_filepathname):

        with open(trn_filepathname,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            trn_dict = parse(xml_text)

        trn_filepath, trn_filename = os.path.split(trn_filepathname)

        trn_zusi_dict = trn_dict.get("Zusi")
        if trn_zusi_dict == {}:
            logging.info("ZUSI Entry not found")
            self.controller.set_statusmessage("Error: ZUSI entry not found in trn-file: "+trn_filepathname)
            return
        
        trn_zug_dict = trn_zusi_dict.get("Zug")
        
        self.create_zusi_trn_list_from_zug_dict(trn_zug_dict, trn_filepath)
        
        return

    def create_zusi_zug_liste(self, fpn_filename=""):
        if fpn_filename == "": return

        fpl_path, fpl_file = os.path.split(fpn_filename)

        print('Input File, %s.' % fpn_filename)
        with open(fpn_filename,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            self.zusi_master_timetable_dict = parse(xml_text)
        zusi_dict = self.zusi_master_timetable_dict.get("Zusi")
        if zusi_dict == {}:
            logging.info("ZUSI Entry not found")
            self.controller.set_statusmessage("Error: ZUSI entry not found in fpn-file: "+fpn_filename)
            return {}
        
        fahrplan_dict = zusi_dict.get("Fahrplan")
        
        zug_list = fahrplan_dict.get("Zug",{})
        if fahrplan_dict == {}:
            logging.info("Fahrplan Entry not found")
            self.controller.set_statusmessage("Error: Fahrplan entry not found in fpn-file: "+fpn_filename)
            return {}
        
        self.zusi_zuglist_dict = {}
        self.zusi_zuglist_xmlfilename_dict ={}
        if zug_list == {}:
            # integrate fpl file
            #self.controller.set_statusmessage("Integrierte Fahrpläne werden nicht unterstützt - "+fpl_filename)
            #return {}
        
            for trn_zug_dict in fahrplan_dict.get("trn",{}):
                file_name, file_extension = os.path.splitext(fpn_filename)
                trn_filepath = os.path.join(fpl_path,file_name)
                self.create_zusi_trn_list_from_zug_dict(trn_zug_dict, trn_filepath)
                self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+fpn_filename)            
            
        else:
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
        #self.timetable.set_zuggattung_to_color(self.traintype_to_color_dict)
        return zusi_zug_list_main_dict


    def resize_canvas(self,width,height,starthour,duration):
        self.canvas.delete("all")
        self.canvas.update()
        self.canvas.config(width=width,height=height,scrollregion=(0,0,width,height))
        self.timetable.set_zuggattung_to_color(self.traintype_to_color_dict)
        
        self.timetable.doPaint(self.canvas,starthour=starthour,duration=duration)


    def redo_fpl_and_canvas(self,width,height, starthour=8, duration=9,fpl_filename="", xml_filename = ""):
        if fpl_filename == "":
            fpl_filename=r"D:\Zusi3\_ZusiData\Timetables\Deutschland\Ruhrtalbahn\Hagen-Kassel_Fahrplan1981_12Uhr-19Uhr.fpn"
        if xml_filename == "":
            xml_filename = r"D:\Zusi3\_ZusiData\Timetables\Deutschland\Ruhrtalbahn\Hagen-Kassel_Fahrplan1981_12Uhr-19Uhr\D843.timetable.xml"
        self.canvas.delete("all")
        self.canvas.config(width=width,height=height,scrollregion=(0,0,width,height))
        self.canvas.update()
        self.controller.set_statusmessage("Erzeuge Bahnhofsliste - "+xml_filename)
        self.controller.update()
        print('Input File master train timetable, %s.' % xml_filename)
        with open(xml_filename,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            zusi_timetable_dict = parse(xml_text)
        self.timetable = TimeTableGraphCommon(self.controller, True, height, width,xml_filename=xml_filename)
        self.timetable.set_zuggattung_to_color(self.traintype_to_color_dict)
        #define stops via selected train-timetable
        result_ok = self.timetable.convert_zusi_fpn_dict_to_timetable_train_x(zusi_timetable_dict,define_stations=True)
        if  not result_ok:
            return
        result_ok = self.open_zusi_master_schedule(fpn_filename=fpl_filename)
        if not result_ok:
            return
        self.timetable.doPaint(self.canvas,starthour=starthour,duration=duration)                

    def set_zuggattung_to_color(self,traintype_to_color_dict):
        self.traintype_to_color_dict = traintype_to_color_dict

    def initUI(self):
        showTrainTimes = True
        height =self.canvas.winfo_reqheight()
        width = self.canvas.winfo_reqwidth()

