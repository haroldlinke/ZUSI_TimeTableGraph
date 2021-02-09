#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ********************************************************************
# *        TimetableGraph
# *
# * provides a timetable graph for ZUSI schedules
# * Informatzion about ZUSI can be found here: https://www.zusi.de/
# *
# *
# * Version: 0.08
# * Author: Harold Linke
# * Date: February 5th, 2021
# * 
# * Copyright (C) 2021  Harold Linke
# *
# * Soucre code and Programm can be downloaded from GitHub
# * https://github.com/haroldlinke/ZUSI_TimeTableGraph
# *
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU Affero General Public License as
# * published by the Free Software Foundation, either version 3 of the
# * License, or (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU Affero General Public License for more details.
# *
# * You should have received a copy of the GNU Affero General Public License
# * along with this program.  If not, see <https://www.gnu.org/licenses/>.
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

    def __init__(self, controller, showTrainTimes, height, width, xml_filename="xml_filename"):
        self.controller = controller
        self.xml_filename = xml_filename
        self.TrainMinuteShow = showTrainTimes
        self.canvas_traintype_prop_dict = {}
        self.trainType_to_Width_dict = {}
        #self.timetable_dict = {}
        self.schedule_dict = {} # self.timetable_dict.get("Schedule",{})
        self.schedule_startHour = self.schedule_dict.get("StartHour",0)
        self.schedule_duration  = self.schedule_dict.get("Duration",0)
        self.schedule_stations_dict  = self.schedule_dict.get("Stations",{})
        self.schedule_startTime_min = self.schedule_startHour * 60
        self.schedule_stationIdx_write_next = 0
        self.schedule_trains_dict = self.schedule_dict.get("Trains",{}) 
        self.schedule_trainIdx_write_next = 0
        self.canvas_dimHeight = height
        self.canvas_dimWidth  = width
        self.bigFont = font.Font(family="SANS_SERIF", size=20)
        self.stdFont = font.Font(family="SANS_SERIF", size=10)
        self.smallFont = font.Font(family="SANS_SERIF", size=8)
        self.trainLineStops = []
        # ------------ global variables ------------
        self.stationGrid = {0: 0.01 }
        self.hour_to_XY_Map = {0: 0.01} 
        self.infoColWidth = 0
        self.graphHourOffset = 0
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
        #    ------------ train variables ------------
        #   Train
        self.trainName = ""
        self.trainLineProp = {}
        self.trainLineWidth = 0
        self.trainLine_dict = []
        #  Stop
        self.trainLineStopCnt = 0
        self.stopIdx = 0
        self.arriveTime = 0
        self.departTime = 0
        self.maxDistance = 0.0
        self.direction = ""
        self.trainLineFirstStop_Flag = False
        self.trainLineLastStop_Flag = False
        self.firstHourXY = 0.0
        self.lastHourXY = 0.0
        self.sizeMinute = 0.0

    def set_tt_traintype_prop(self,traintype_prop_dict):
        self.canvas_traintype_prop_dict = traintype_prop_dict.copy()
        
    def determine_headersize(self):
        if self.draw_stations_vertical: 
            return 140
        s_labelsize=self.controller.getConfigData("Bfp_S_LineLabelSize")
        s_labeldir=self.controller.getConfigData("Bfp_S_LineLabelDir_No")
        self.s_font = font.Font(family="SANS_SERIF", size=int(s_labelsize))             
        stationNameLengthMax = self.determine_stationNameLength()
        if s_labeldir==0:
            return 140
        elif s_labeldir==1:
            return stationNameLengthMax+100
        else:
            return int(stationNameLengthMax/1.4)+100
        return stationNameLengthMax

    def determine_stationNameLength(self):
        stationNameLengthMax=0
        for stationIdx in self.schedule_stations_dict:
            stationName = self.get_stationName(stationIdx)
            stationNameLength = self.s_font.measure(stationName)
            stationNameLengthMax = max(stationNameLength,stationNameLengthMax)
        return stationNameLengthMax

    def get_stationName(self, stationIdx):
        station = self.schedule_stations_dict.get(stationIdx,{})
        stationName = station.get("StationName","")
        return stationName

    def doPaint (self,canvas,starthour=12,duration=7):
        #try:
        if True:
            TLDirection = self.controller.getConfigData("TLDirection")
            self.draw_stations_vertical = (TLDirection=="vertical")                
            self.tt_canvas = canvas
            self.canvas_dimHeight =self.tt_canvas.winfo_reqheight()
            self.canvas_dimWidth = self.tt_canvas.winfo_reqwidth()                
            self.schedule_startHour=starthour
            self.schedule_startTime_min = self.schedule_startHour * 60
            self.schedule_duration = duration
            self.stationGrid  = {} 
            self.hourGrid     = []
            self.graphHeadersize = self.determine_headersize()
            self.graphTop = self.graphHeadersize
            self.graphHeight = self.canvas_dimHeight - self.graphTop - self.graphBottomsize
            self.graphBottom = self.graphTop + self.graphHeight
            self.graphLeft = self.graphLeftbordersize
            self.graphWidth = self.canvas_dimWidth - self.graphLeft - self.graphRightbordersize
            self.TrainMinuteSize = self.controller.getConfigData("Bfp_TrainMinuteSize")
            self.TrainMinuteFont = font.Font(family="SANS_SERIF", size=int(self.TrainMinuteSize))
            self.TrainMinuteShow = self.TrainMinuteSize > 0
            self.InOutBoundTrainsShow = self.controller.getConfigData("InOutBoundTrainsShow")
            self.InOutBoundTrainsNoOneStop = self.controller.getConfigData("InOutBoundTrainsNoOneStop")
            self.InOutBoundTrainsNoStartStation = self.controller.getConfigData("InOutBoundTrainsNoStartStation")
            self.InOutBoundTrainsNoEndStation = self.controller.getConfigData("InOutBoundTrainsNoEndStation")
            self.InOutBoundTrainsShowMinutes = self.controller.getConfigData("InOutBoundTrainsShowMinutes")
            self.startstationName = self.schedule_stations_dict[0]["StationName"]
            self.stationsCntMax = len(self.schedule_stations_dict)-1
            self.endstationName = self.schedule_stations_dict[self.stationsCntMax]["StationName"]
            self.dashline_pattern = "-"

            # Draw the left column components
            self.drawInfoSection()
            self.drawStationSection()
            # Set the horizontal graph dimensions based on the width of the left column
            if self.draw_stations_vertical:
                self.graphLeft = self.infoColWidth + 50.0
                self.graphWidth = self.canvas_dimWidth - self.infoColWidth - 65.0
            else:
                self.graphTop = self.graphHeadersize + 10
                self.graphHeight = self.canvas_dimHeight - self.graphTop - self.graphBottomsize
                self.graphBottom = self.graphTop + self.graphHeight            
            
            self.graphRight = self.graphLeft + self.graphWidth
            self.drawHours()
            self.drawGraphGrid()
            self.drawTrains()
        #except BaseException as e:
            #logging.debug("Error DoPaint: %s", e)

    def determine_xy_point(self, stop, time):
        if self.draw_stations_vertical:
            x = self.calculateTimePos(time)
            y = self.stationGrid.get(stop.get("StationIdx",0),0)
        else:
            y = self.calculateTimePos(time)
            x = self.stationGrid.get(stop.get("StationIdx",0),0)                        
        return x,y

    def determine_station_xy_point(self, stationName, distance):
        self.infoColWidth = max(self.infoColWidth, self.s_font.measure(stationName) + 5)
        if self.draw_stations_vertical:
            y = ((self.graphHeight - 50) / self.maxDistance) * distance + self.graphTop + 30  #// calculate the Y offset                
            x = 15.0
        else:
            x = ((self.graphWidth - 50) / self.maxDistance) * distance + self.graphLeft + 30  #// calculate the Y offset                
            y = self.graphTop - 10                        
        return x,y

    def print_station(self, stationIdx, stationName, distance, stationkm):
        #s_color=self.controller.getConfigData("Bfp_S_LineColor")
        s_labelsize=self.controller.getConfigData("Bfp_S_LineLabelSize")
        s_labeldir=self.controller.getConfigData("Bfp_S_LineLabelDir_No")
        self.s_font = font.Font(family="SANS_SERIF", size=int(s_labelsize))
        x, y=self.determine_station_xy_point(stationName, distance)
        textwidth = self.s_font.measure(stationName)
        textheight = 12
        if self.draw_stations_vertical:
            self.stationGrid[stationIdx] = y
            stationName = stationName + " (km "+str(f"{stationkm:.1f}")+")"
            s_obj=self.tt_canvas.create_text(x, y, text=stationName, anchor="w",font=self.s_font)
        else:
            self.stationGrid[stationIdx] = x
            if s_labeldir==0:
                yName = y - 15 * (stationIdx%2)
                self.tt_canvas.create_rectangle(x-textwidth/2, yName-textheight/2, x+textwidth/2, yName+textheight/2, fill="white",width=0,outline="white")
                s_obj=self.tt_canvas.create_text(x, yName, text=stationName, anchor="center",font=self.s_font)
            elif s_labeldir==1:
                s_labelangle=90
                yName = y - 15
                #self.tt_canvas.create_rectangle(x, yName-textheight/2, x, yName+textheight/2, fill="white",width=0,outline="white")
                s_obj=self.tt_canvas.create_text(x, yName, text=stationName, anchor="w",font=self.s_font)                
                self.tt_canvas.itemconfig(s_obj, angle=s_labelangle)
            elif s_labeldir==2:
                yName = y - 15
                #self.tt_canvas.create_rectangle(x, yName-textheight/2, x, yName+textheight/2, fill="white",width=0,outline="white")
                s_obj=self.tt_canvas.create_text(x, yName, text=stationName, anchor="w",font=self.s_font)                
                s_labelangle=45
                self.tt_canvas.itemconfig(s_obj, angle=s_labelangle)            
            yKm = y + 12
            self.tt_canvas.create_text(x, yKm, text=str(f"{stationkm:.1f}"), anchor="center",font=self.s_font)

    def print_hour(self, i, currentHour):
        #th_color=self.controller.getConfigData("Bfp_TH_LineColor")
        th_labelsize=self.controller.getConfigData("Bfp_TH_LineLabelSize")
        #th_labeldir=self.controller.getConfigData("Bfp_TH_LineLabelDir_No")
        th_font = font.Font(family="SANS_SERIF", size=int(th_labelsize))
        hourString = str(currentHour)+":00"
        hOffset = self.stdFont.measure(hourString) / 2 # hOffset = self.g2.getFontMetrics().stringWidth(hourString) / 2;
        if self.draw_stations_vertical:
            hourXY = (self.hourWidth * i) + self.graphHourOffset + self.graphLeft
            self.tt_canvas.create_text(hourXY - hOffset, self.graphBottom + 20, text = hourString, anchor="w",fill="black",font=th_font)
            self.tt_canvas.create_text(hourXY - hOffset, self.graphTop - 8, text = hourString, anchor="w",fill="black",font=th_font)
        else:
            hourXY = (self.hourWidth * i) + self.graphHourOffset + self.graphTop
            self.tt_canvas.create_text(self.graphLeft-10,hourXY, text = hourString, anchor="e",fill="black",font=th_font)
        self.hour_to_XY_Map[currentHour] = hourXY
        self.hourGrid.append(hourXY);
        if (i == 0):
            self.firstHourXY = hourXY# - hOffset;
        if (i == self.schedule_duration):
            self.lastHourXY = hourXY# - hOffset;
        return

    def calculateTimePos(self, time):
        if (time < 0): time = 0;
        if (time > 1439): time = 1439;
        hour = int(time / 60)
        min = int(time % 60)
        timeposhour = self.hour_to_XY_Map.get(hour,None)
        if timeposhour:
            timeposhour = timeposhour + (min * self.sizeMinute)
            if timeposhour > self.lastHourXY:
                timeposhour = self.lastHourXY
        else:
            if hour > self.schedule_startHour + self.schedule_duration:
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

    def check_stationtypeZFS(self,stationName):
        # check if statiotype is ZugFolgeStelle
        for zfs_id in self.zfs_id_list:
            if stationName.startswith(zfs_id):
                return True
        return False
    
    def drawStationSection(self):
        stationIdx_last = len(self.schedule_stations_dict)-1
        if stationIdx_last > 0:
            self.maxDistance = self.schedule_stations_dict[stationIdx_last].get("Distance",100)
            self.stationGrid = {}
            self.stationTypeZFS_list = []
            zfs_id_str=self.controller.getConfigData("Bfp_ZFS_Id")
            zfs_id_str = zfs_id_str.replace(" ","")
            if zfs_id_str =="":
                self.zfs_id_list=[]
            else:
                self.zfs_id_list = zfs_id_str.split(",")            
            for stationIdx in self.schedule_stations_dict:
                station = self.schedule_stations_dict.get(stationIdx,{})
                stationName = station.get("StationName","")
                stationkm = station.get("StationKm",0.00)
                distance = station.get("Distance",0.00)
                if stationkm == None:
                    print("Error: Stationkm = None - ",stationName)
                    stationkm = 0
                #stationName = stationName# + " (km "+str(f"{stationkm:.2f}")+")"
                stationType_ZFS=self.check_stationtypeZFS(stationName)
                self.stationTypeZFS_list.append(stationType_ZFS)
                self.print_station(stationIdx, stationName, distance, stationkm)

    def drawHours(self):
        currentHour = self.schedule_startHour
        try:
            if self.draw_stations_vertical:
                self.hourWidth = self.graphWidth / (self.schedule_duration)
            else:
                self.hourWidth = self.graphHeight / (self.schedule_duration)
        except:
            print("error")
        self.graphHourOffset = 0 #hourWidth / 2
        self.hourGrid = []
        for i in range(0, self.schedule_duration+1):
            self.print_hour(i, currentHour)
            currentHour+= 1
            if (currentHour > 23):
                currentHour -= 24

    def drawGraphGrid(self):
        # Print the graph box
        self.tt_canvas.create_rectangle(self.graphLeft, self.graphTop, self.graphLeft+self.graphWidth, self.graphTop + self.graphHeight)
        # Print the grid lines
        s_color=self.controller.getConfigData("Bfp_S_LineColor")
        s_width=self.controller.getConfigData("Bfp_S_LineWidth")
        s_linedashed=self.controller.getConfigData("Bfp_S_LineDashed")
        zfs_color=self.controller.getConfigData("Bfp_ZFS_LineColor")
        zfs_width=self.controller.getConfigData("Bfp_ZFS_LineWidth")
        zfs_linedashed=self.controller.getConfigData("Bfp_ZFS_LineDashed")
        th_color=self.controller.getConfigData("Bfp_TH_LineColor")
        th_width=self.controller.getConfigData("Bfp_TH_LineWidth")
        th_linedashed=self.controller.getConfigData("Bfp_TH_LineDashed")
        tm_color=self.controller.getConfigData("Bfp_TM_LineColor")
        tm_width=self.controller.getConfigData("Bfp_TM_LineWidth")
        tm_linedashed=self.controller.getConfigData("Bfp_TM_LineDashed")
        tm_distance=int(self.controller.getConfigData("Bfp_TM_LineDistance"))
        if self.draw_stations_vertical:
            for stationidx,y in self.stationGrid.items():
                if self.stationTypeZFS_list[stationidx]:
                    if not zfs_linedashed:
                        objid = self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=zfs_width, fill=zfs_color)
                    else:
                        objid = self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=zfs_width, fill=zfs_color,dash=self.dashline_pattern)
                else:
                    if not s_linedashed:
                        objid = self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=s_width, fill=s_color)
                    else:
                        objid = self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=s_width, fill=s_color,dash=self.dashline_pattern)
                self.controller.ToolTip_canvas(self.tt_canvas, objid, text="Station: "+self.get_stationName(stationidx), key="",button_1=True)
            for x in self.hourGrid:
                if not th_linedashed:
                    self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=th_width, fill=th_color)
                else:
                    self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=th_width, fill=th_color,dash=self.dashline_pattern)
                if tm_width > 0 and x != self.hourGrid[-1]:
                    number_of_min_lines = int(60/tm_distance)-1
                    distance_per_line = tm_distance * self.hourWidth/60
                    for min_line in range(0,number_of_min_lines):
                        if not tm_linedashed:
                            self.tt_canvas.create_line(x+distance_per_line*(min_line+1), self.graphTop, x+distance_per_line*(min_line+1), self.graphBottom, width=tm_width, fill=tm_color)
                        else:
                            self.tt_canvas.create_line(x+distance_per_line*(min_line+1), self.graphTop, x+distance_per_line*(min_line+1), self.graphBottom, width=tm_width, fill=tm_color,dash=self.dashline_pattern)
        else:
            for y in self.hourGrid:
                if not th_linedashed:
                    self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=th_width, fill=th_color)
                else:
                    self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=th_width, fill=th_color,dash=self.dashline_pattern)
                if tm_width > 0 and y != self.hourGrid[-1]:
                    number_of_min_lines = int(60/tm_distance)-1
                    distance_per_line = tm_distance * self.hourWidth/60
                    for min_line in range(0,number_of_min_lines):
                        if not tm_linedashed:
                            self.tt_canvas.create_line(self.graphLeft, y+distance_per_line*(min_line+1), self.graphRight, y+distance_per_line*(min_line+1), width=tm_width, fill=tm_color)
                        else:
                            self.tt_canvas.create_line(self.graphLeft, y+distance_per_line*(min_line+1), self.graphRight, y+distance_per_line*(min_line+1), width=tm_width, fill=tm_color,dash=self.dashline_pattern)
                        
            for stationidx,x in self.stationGrid.items():
                if self.stationTypeZFS_list[stationidx]:
                    if not zfs_linedashed:
                        objid = self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=th_width, fill=zfs_color)
                    else:
                        objid = self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=th_width, fill=zfs_color,dash=self.dashline_pattern)
                else:
                    if not s_linedashed:
                        objid = self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=th_width, fill=s_color)
                    else:
                        objid = self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=th_width, fill=s_color,dash=self.dashline_pattern)
                    self.controller.ToolTip_canvas(self.tt_canvas, objid, text="Station: "+self.get_stationName(stationidx), key="",button_1=True)

#     * Create the train line for each train with labels.  Include times if
#     * selected.
#     * <p>
#     * All defined trains their stops are processed.  If a stop has a station
#     * in the segment, it is included.  Most trains only use a single segment.

    def drawTrains(self):
        self.baseTime = self.schedule_startHour * 60
        if self.draw_stations_vertical:
            self.sizeMinute = self.graphWidth / ((self.schedule_duration) * 60)
        else:
            self.sizeMinute = self.graphHeight / ((self.schedule_duration) * 60)
        self.throttleX = 0
        const_default_trainprop = {
            "Bfp_TrainType": "*",
            "Bfp_TrainTypeColor": "black",
            "Bfp_TrainTypeWidth": 1,
            "Bfp_TrainTypeLabel": "Alle Segmente",
            "Bfp_TrainTypeLabel_No": 0,
            "Bfp_TrainTypeLabelSize": 10
        }
        self.default_trainprop = self.canvas_traintype_prop_dict.get("*",const_default_trainprop)
        for trainidx in self.schedule_trains_dict:
            self.process_train(trainidx)
        self.controller.set_statusmessage("") 

    def process_train(self,trainidx):
        self.tt_canvas.update()
        train = self.schedule_trains_dict.get(trainidx,{})
        self.trainType = train.get("TrainType","X-Deko")
        self.trainName = self.trainType + train.get("TrainName","0000")
        self.trainLineName = train.get("TrainLineName","")
        self.trainEngine = train.get("TrainEngine","")
        self.trainOutgoingStation = train.get("Outgoing_Station","")
        self.trainIncomingStation = train.get("Incoming_Station","") 
        self.trainLineProp = self.canvas_traintype_prop_dict.get(self.trainType,self.default_trainprop)
        self.trainColor = self.trainLineProp.get("Bfp_TrainTypeColor","Black")
        self.trainLineWidth = int(self.trainLineProp.get("Bfp_TrainTypeWidth","2"))
        self.TrainLabelPos = self.trainLineProp.get("Bfp_TrainTypeLabel_No","")
        self.TrainLabelSize = self.trainLineProp.get("Bfp_TrainTypeLabelSize","10")
        self.TrainLineDashed = self.trainLineProp.get("Bfp_TrainTypeLineDashed",False)
        self.TrainLabelFont = font.Font(family="SANS_SERIF", size=int(self.TrainLabelSize))
        if self.trainColor == "" or self.trainLineWidth == 0:
            return
        self.trainLine_dict = []
        self.trainLineStops = train.get("Stops",{})
        self.trainLineStopCnt = len(self.trainLineStops)
        self.trainLineStopMiddleIdx=int(self.trainLineStopCnt/2)
        if self.trainLineStopMiddleIdx < 0:
            self.trainLineStopMiddleIdx = 0
        self.trainLineFirstStop_Flag = True;
        self.trainLineLastStop_Flag = False;
        #self.trainLinePrevStop_dict = None
        self.drawTrainName_Flag = self.TrainLabelPos in [0,1,2,3]
        self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan für Zug - "+self.trainName)
        self.process_trainStops()
        return

    def process_trainStops(self):
        for self.stopIdx,stop_dict in self.trainLineStops.items():
            self.arriveTime = stop_dict.get("ArriveTime",0)
            self.departTime = stop_dict.get("DepartTime",0)
            station_dict = self.schedule_stations_dict.get(stop_dict.get("StationIdx"))
            self.stationName = station_dict.get("StationName")
            self.stopStation  = stop_dict
            if (self.stopIdx > 0): 
                self.trainLineFirstStop_Flag = False
            if (self.stopIdx == self.trainLineStopCnt - 1): 
                self.trainLineLastStop_Flag = True
            if (self.trainLineFirstStop_Flag):
                self.setBegin(self.stopStation,self.stationName)
                if (self.trainLineLastStop_Flag):
                    # One stop route or only one stop in current segment
                    self.setEnd(self.stopStation, self.stationName)
                    break
                continue
            self.drawLine(self.stopStation);
            if (self.trainLineLastStop_Flag):
                # At the end, do the end process
                self.setEnd(self.stopStation, self.stationName)
                break

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
    def xdrawTrainName( self, x,  y,  justify,  invert,  throttle):
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
        trainName_objid = self.tt_canvas.create_text(x , y, activefill="red",text = self.trainName, anchor = "w")
        self.controller.ToolTip_canvas(self.tt_canvas, trainName_objid, text="Zug: "+self.trainName+" "+self.direction, key=self.trainName,button_1=True)

    def drawTrainTime(self, time,  mode,  x,  y):
        if (not self.TrainMinuteShow):
            return
        if not (time in range(self.schedule_startTime_min,self.schedule_startTime_min + self.schedule_duration * 60)):
            return                
        minutes = "{:02d}".format(time % 60) 
        hours = "{:02d}".format(int(time/60))
        if mode ==  "begin" :
            mode_txt = "Start"
        elif mode == "arrive":
            mode_txt = "Ankunft"
        elif mode == "depart":
            mode_txt = "Abfahrt"
        elif mode == "end":
            mode_txt = "Ziel"
        else:
            return        
        if self.draw_stations_vertical:
            if (self.direction== "down"):
                anchor="n"
            else:
                anchor="s"            
        else:
            if (self.direction== "down"):
                anchor="w"
            else:
                anchor="e"            
        trainTime_objid = self.tt_canvas.create_text(x , y, text = minutes, anchor=anchor,activefill="red",font=self.TrainMinuteFont)
        if self.trainLineName == None:
            self.trainLineName = ""
        self.controller.ToolTip_canvas(self.tt_canvas, trainTime_objid, text=hours+":"+minutes+"\nZug: "+self.trainName+" - "+mode_txt+" "+self.stationName+"\n"+self.trainLineName, key=self.trainName,button_1=True)
  
    def determine_DirectionofTravel(self):
        if (self.trainLineStopCnt == 1):
            # Single stop train, default to down
            self.direction = "down"
            return;
        stop = self.trainLineStops.get(self.stopIdx,{});
        currStation_Idx = stop.get("StationIdx",0)
        currStation = self.schedule_stations_dict.get(currStation_Idx,{})
        currkm = currStation.get("Distance",0)
        if (self.trainLineFirstStop_Flag):
            # For the first stop, use the next stop to set the direction
            nextStation = self.get_StationData(self.stopIdx + 1)
            nextkm = nextStation.get("Distance",0)
            if nextkm > currkm:
                self.direction = "down" 
            else:  
                self.direction = "up"
            return
        if (self.trainLineLastStop_Flag):    
            #prevStation_Idx = self.trainLineStops.get(self.stopIdx - 1).get("StationIdx",0)
            prevStation = self.get_StationData(self.stopIdx - 1)
            # For the last stop, use the previous stop to set the direction
            # Last stop may also be only stop after segment change; if so wait for next "if"
            prevkm = prevStation.get("Distance",0)
            if prevkm < currkm:
                self.direction = "down" 
            else :  
                self.direction = "up"                                
            return
        # For all other stops in the active segment, use the next stop.
        nextStation = self.get_StationData(self.stopIdx + 1)
        nextkm = nextStation.get("Distance",0)
        if nextkm > currkm:
            self.direction = "down"
        else: 
            self.direction = "up";  
        return

    def get_StationData(self, stopIdx):
        Station_Idx = self.trainLineStops.get(stopIdx).get("StationIdx",0)
        Station = self.schedule_stations_dict.get(Station_Idx,{})
        return Station
    
    def check_time_in_range(self,time):
        return time in range(self.schedule_startTime_min,self.schedule_startTime_min + self.schedule_duration * 60)

    def setBegin(self, stop,stationName):
        self.firstStationName = stationName
        if not self.check_time_in_range(self.arriveTime):
            return                
        if self.trainIncomingStation=="" or self.InOutBoundTrainsShowMinutes:
            self.arriveTime = stop.get("ArriveTime",0)
        x,y = self.determine_xy_point(stop,self.arriveTime)
        if y == None:
            return
        self.trainLine_dict = [x, y]
        self.determine_DirectionofTravel()
        self.arriveTime = stop.get("ArriveTime",0)
        if not(self.trainLineLastStop_Flag):
            self.drawTrainTime(self.arriveTime, "begin", x, y)
        # Check for stop duration before depart
        self.departTime = stop.get("DepartTime",0)
        if (self.departTime - self.arriveTime > 0):
            x,y = self.determine_xy_point(stop,self.departTime)
            self.trainLine_dict.extend([x, y])
            if not (self.trainLineLastStop_Flag):
                self.drawTrainTime(self.departTime, "depart", x, y)

    def drawLine(self, stop):
        if not (self.check_time_in_range(self.departTime) or self.check_time_in_range(self.arriveTime)):
            return
        x,y = self.determine_xy_point(stop,self.arriveTime)
        if y==None:
            return
        self.trainLine_dict.extend([x, y])
        self.drawTrainTime(self.arriveTime, "arrive", x, y);  #
        if len(self.trainLine_dict)>3:
            self.draw_trainName_parallel(self.trainName, self.trainLine_dict[-4],self.trainLine_dict[-3],x, y)
        self.determine_DirectionofTravel();
        # Check for duration after arrive
        if (self.departTime - self.arriveTime) > 0 :
            if not (self.check_time_in_range(self.departTime) or self.check_time_in_range(self.arriveTime)):
                return                        
            x,y = self.determine_xy_point(stop,self.departTime)
            self.trainLine_dict.extend([x, y])
            self.drawTrainTime(self.departTime, "depart", x, y);  #

    def check_draw_OutBoundArrow(self,endstationName, oneStopOnly):
        if self.InOutBoundTrainsShow and not (oneStopOnly and self.InOutBoundTrainsNoOneStop) and not ((endstationName == self.endstationName and self.InOutBoundTrainsNoEndStation) or (endstationName == self.startstationName and self.InOutBoundTrainsNoStartStation)):
            return True
        else:
            return False
        
    def check_draw_InBoundArrow(self,startstationName, oneStopOnly):
        if self.InOutBoundTrainsShow and not (oneStopOnly and self.InOutBoundTrainsNoOneStop) and not ((startstationName == self.endstationName and self.InOutBoundTrainsNoEndStation) or (startstationName == self.startstationName and self.InOutBoundTrainsNoStartStation)):
            return True
        else:
            return False    
    
    def setEnd(self, stop, stationName):
        try:
            skipLine = False
            oneStopOnly = False
            if self.trainLine_dict == []:
                return
            if (len(self.trainLineStops) == 1):
                x = self.trainLine_dict[-2]
                y = self.trainLine_dict[-1]
                skipLine = True
                oneStopOnly = True
            else:
                if  self.check_time_in_range(self.arriveTime):
                    x,y = self.determine_xy_point(stop,self.arriveTime)
                else:
                    x = self.trainLine_dict[-2]
                    y = self.trainLine_dict[-1]
            if (not skipLine):
                if y==None:
                    logging.debug("SetEnd Error: %s %s",self.trainType+self.trainName,repr(stop))
                    return
                self.trainLine_dict.extend([x, y])
                if self.TrainLineDashed:
                    train_line_objid = self.tt_canvas.create_line(self.trainLine_dict,fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,dash=self.dashline_pattern)
                else:
                    train_line_objid = self.tt_canvas.create_line(self.trainLine_dict,fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2)
                self.controller.ToolTip_canvas(self.tt_canvas, train_line_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, key=self.trainName,button_1=True)

            arrowwidth = self.trainLineWidth
            if arrowwidth<4:
                arrowwidth=4
            if self.trainOutgoingStation!="": # draw outgoing arrow
                if self.check_draw_OutBoundArrow(stationName,oneStopOnly):
                    logging.debug("Print Outgoing-Station: %s %s %s %s %s",self.trainType+self.trainName,stationName,self.trainOutgoingStation,self.startstationName,self.endstationName)
                    if self.direction == "down":
                        arrow_delta = 10
                    else:
                        arrow_delta = -10
                    if self.draw_stations_vertical:
                        train_line_out_objid = self.tt_canvas.create_line([x,y,x,y+arrow_delta],fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,arrow="last",arrowshape=(10,10,arrowwidth))
                    else:
                        train_line_out_objid = self.tt_canvas.create_line([x,y,x+arrow_delta,y],fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,arrow="last",arrowshape=(10,10,arrowwidth))
                    self.controller.ToolTip_canvas(self.tt_canvas, train_line_out_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nNach "+self.trainOutgoingStation, key=self.trainName,button_1=True)
                
            if self.trainIncomingStation!="": # draw incoming arrow
                startstationname = self.firstStationName
                if self.check_draw_InBoundArrow(startstationname,oneStopOnly):
                    logging.debug("Print Incoming-Station: %s %s %s %s %s",self.trainType+self.trainName,self.trainIncomingStation,stationName,self.startstationName,self.endstationName)
                    if self.direction == "down":
                        arrow_delta = 10
                    else:
                        arrow_delta = -10
                    x = self.trainLine_dict[0]
                    y = self.trainLine_dict[1]                    
                    if self.draw_stations_vertical:
                        train_line_in_objid = self.tt_canvas.create_line([x,y,x,y-arrow_delta],fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,arrow="first",arrowshape=(10,10,arrowwidth))
                    else:
                        train_line_in_objid = self.tt_canvas.create_line([x,y,x-arrow_delta,y],fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,arrow="first",arrowshape=(10,10,arrowwidth))
                    self.controller.ToolTip_canvas(self.tt_canvas, train_line_in_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nVon "+self.trainIncomingStation, key=self.trainName,button_1=True)                
        except BaseException as e:
            logging.debug("SetEnd Error %s %s",self.trainType+self.trainName+"-"+repr(self.trainLine_dict),e)
            return  

    def draw_trainName_parallel(self,trainName,x0,y0,x1,y1):
        if self.TrainLabelSize==0:
            return
        if self.stopIdx == self.trainLineStopMiddleIdx and self.TrainLabelPos in [1,4]:  # draw middle label
            self.drawTrainName_Flag=True
        if self.stopIdx == self.trainLineStopCnt-1 and self.TrainLabelPos in [1,2,5]: # draw End label
            self.drawTrainName_Flag=True            
        p0=Point(x0,y0)
        p1=Point(x1,y1)
        segment = p1 - p0
        mid_point = segment.scale(0.5) + p0
        #offset = segment.perp().scale(self.trainLineWidth+4)
        trainName_len = self.TrainLabelFont.measure(self.trainName)
        segment_len = segment.norm()
        if segment_len > trainName_len+15:
            if self.drawTrainName_Flag:
                txt = self.tt_canvas.create_text(*(mid_point), text=trainName,activefill="red",font=self.TrainLabelFont,anchor="s")
                self.controller.ToolTip_canvas(self.tt_canvas, txt, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, key=self.trainName,button_1=True)
                if self.TrainLabelPos!=0: # if not draw at all segments, no trainname anymore
                    self.drawTrainName_Flag=False
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

        for stationIdx in self.schedule_stations_dict:
            station_data = self.schedule_stations_dict.get(stationIdx,0)
            if station_data.get("StationName","") == stationName:
                return stationIdx
        if not self.addStation:
            # check if currentStation = Startstation
            if stationName == self.StartStation:
                self.addStation = True
            else:
                return -1
        # check if currentStation = Endstation
        if stationName == self.EndStation and self.teilstrecke_flag:
            self.addStation = False            
        self.schedule_stations_dict[self.schedule_stationIdx_write_next] = {"StationName": stationName, 
                                                                            "Distance": distance,
                                                                            "StationKm": stationKm}
        self.schedule_stationIdx_write_next +=1
        return self.schedule_stationIdx_write_next - 1

    def enter_schedule_trainLine_data(self,trainNumber,trainType,ZugLauf,ZugLok):
        color = self.canvas_traintype_prop_dict.get(trainType,"black")
        width = self.trainType_to_Width_dict.get(trainType,"1")
        self.schedule_trains_dict[self.schedule_trainIdx_write_next] = {"TrainName"     : trainNumber,
                                                                        "TrainType"     : trainType,
                                                                        "TrainLineName" : ZugLauf,
                                                                        "TrainEngine"   : ZugLok,
                                                                        "Color"         : color,
                                                                        "Width"         : width,
                                                                        "Stops"         : {}
                                                                        }
        self.schedule_trainIdx_write_next += 1
        return self.schedule_trainIdx_write_next-1

    def search_station(self, stationName):
        for stationIdx in self.schedule_stations_dict:
            iter_stationName=self.get_stationName(stationIdx)
            if iter_stationName == stationName:
                return stationIdx
        return -1

    def enter_trainLine_stop(self, train_idx, trainstop_idx, FplName, FplAnk_min, FplAbf_min):
        train_dict = self.schedule_trains_dict.get(train_idx)
        trainstops_dict = train_dict.get("Stops",{})
        station_idx = self.search_station(FplName)
        if FplAnk_min == 0:
            FplAnk_min = FplAbf_min
        arriveTime = FplAnk_min
        departTime = FplAbf_min
        trainstops_dict[trainstop_idx] = {"StationIdx" : station_idx,
                                          "ArriveTime" : arriveTime,
                                          "DepartTime" : departTime
                                       }
        return trainstop_idx + 1
        
    def set_trainline_data(self,trainIdx, key, data):
        logging.debug("set_trainline_data: %s %s %s",trainIdx, key, data)
        train_dict = self.schedule_trains_dict.get(trainIdx)
        train_dict[key] = data    
        
    def get_trainline_data(self,trainIdx, key):
        logging.debug("get_trainline_data: %s %s",trainIdx, key)
        train_dict = self.schedule_trains_dict.get(trainIdx)
        data = train_dict.get(key,None)
        if data == None:
            logging.debug("Error get_trainline_data - key not found: %s %s",trainIdx, key)
        return data
    
    def enter_train_incoming_station(self, trainIdx, stationName):
        self.set_trainline_data(trainIdx, "Incoming_Station", stationName)
        return
    
    def enter_train_outgoing_station(self, trainIdx, stationName):
        self.set_trainline_data(trainIdx, "Outgoing_Station", stationName)
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

    def convert_zusi_fpn_dict_to_schedule_dict(self, zusi_fpn_dict, define_stations=False):
        Zusi_dict = zusi_fpn_dict.get("Zusi")
        Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan",{})
        if Buchfahrplan_dict=={}:
            return False
        #kmStart = float(Buchfahrplan_dict.get("@kmStart","0.00"))
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
        self.schedule_dict["Name"] = fpn_dateiname
        Datei_trn_dict = Buchfahrplan_dict.get("Datei_trn",{})
        if Datei_trn_dict == {}:
            return False
        trn_dateiname = Datei_trn_dict.get("@Dateiname","")
        train_idx = self.enter_schedule_trainLine_data(ZugNummer,ZugGattung,Zuglauf,ZugLok)
        train_stop_idx = 0
        FplRglGgl_str = self.controller.getConfigData("FplRglGgl")
        showstationonly = not self.controller.getConfigData("ExtraShowAlleZFS")
        if FplRglGgl_str !="":
            self.FplRglGgl = FplRglGgl_str.split(",")
        else:
            self.FplRglGgl = []
        FplZeile_list = Buchfahrplan_dict.get("FplZeile",{})
        stationdistance = 0
        last_km = 0
        station_idx = 0
        
        self.teilstrecke_flag = self.controller.getConfigData("TeilStreckeCheckButton")
        self.addStation = not self.teilstrecke_flag
        self.StartStation = self.controller.getConfigData("StartStation")
        self.StartStation = self.StartStation.replace("_"," ")
        self.EndStation = self.controller.getConfigData("EndStation")
        self.EndStation = self.EndStation.replace("_"," ")
        if FplZeile_list=={}:
            logging.info("timetable.xml file error: %s",trn_dateiname )
            self.controller.set_statusmessage("Error: ZUSI entry not found in fpl-file: "+trn_dateiname)            
            return False
        for FplZeile_dict in FplZeile_list:
            try:
                FplRglGgl=FplZeile_dict.get("@FplRglGgl","")
            except:
                print("Error:",ZugGattung,ZugNummer," ",repr(FplZeile_dict))
                FplRglGgl = ""
            if FplRglGgl != "":
                if not (FplRglGgl in self.FplRglGgl):
                    continue # keine Umwege über Gegengleis
                
            #determine distance between station - detect KmSprung
            try:
                FplSprung = self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@FplSprung",default="")
                Fplkm = float(self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@km",default=0))

                if (Fplkm == 0):
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
               
                if FplAbf == "" and showstationonly:
                    continue # only use station with "Abf"-Entry

                if FplAbf != "":
                    FplAbf_obj = datetime.strptime(FplAbf, '%Y-%m-%d %H:%M:%S')
                    FplAbf_min = FplAbf_obj.hour * 60 + FplAbf_obj.minute
                else:
                    FplAbf_min = 0
                FplAnk = self.get_fplZeile_entry(FplZeile_dict, "FplAnk","@Ank")
                if FplAnk!="":
                    FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                    FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute
                else:
                    FplAnk_min = 0
                FplName = self.get_fplZeile_entry(FplZeile_dict,"FplName","@FplNameText",default="")
                if FplName == "" and not showstationonly:
                    continue
                if self.schedule_stationIdx_write_next == 0:
                    stationdistance = 0
                Fpldistance = stationdistance # abs(kmStart - Fplkm)
                if define_stations:
                    station_idx = self.enter_station(FplName,Fpldistance,Fplkm)
                else:
                    station_idx = self.search_station(FplName)
                    if station_idx != -1:
                        train_stop_idx = self.enter_trainLine_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min)
                    else:
                        if train_stop_idx == 0:
                            # train is comming from another station
                            self.enter_train_incoming_station(train_idx, FplName)
                                 
            except BaseException as e:
                logging.debug("FplZeile conversion Error %s %s",ZugGattung+ZugNummer+"-"+repr(FplZeile_dict),e)
                continue # entry format wrong
        if station_idx == -1:
            #last station is unknown
            self.enter_train_outgoing_station(train_idx, FplName)             
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
            train_idx = self.enter_schedule_trainLine_data(ZugNummer,ZugGattung,Zuglauf,ZugLok)
            train_stop_idx = 0
            FplZeile_list = zusi_trn_zug_dict.get("FahrplanEintrag",{})
            if FplZeile_list=={}:
                return
            #Fpl_Zeile_cnt_max = len(FplZeile_list)
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
                    train_stop_idx = self.enter_trainLine_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min)
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
        
    def open_zusi_trn_zug_dict(self,trn_zug_dict,fpn_filepathname,trn_filepathname=""):
        
        TLFileType = self.controller.getConfigData("TLFileType")
        if TLFileType == ".timetable.xml":
            fahrplan_gruppe = trn_zug_dict.get("@FahrplanGruppe","")
            zugGattung = trn_zug_dict.get("@Gattung","")
            zugNummer = trn_zug_dict.get("@Nummer","")
            zugLauf = trn_zug_dict.get("@Zuglauf","")            
            Buchfahrplan_dict = trn_zug_dict.get("BuchfahrplanRohDatei",{})
            Bfpl_Dateiname = Buchfahrplan_dict.get("@Dateiname","")
            trn_filepath, trn_filename = os.path.split(fpn_filepathname)
            if Buchfahrplan_dict != {}:
                timetable_filepathname = Buchfahrplan_dict.get("@Dateiname")
                timetable_filecomp = timetable_filepathname.split("\\")
                Bfpl_filepathname = os.path.join(trn_filepath,timetable_filecomp[-2],timetable_filecomp[-1])
            else:
                asc_zugGattung = zugGattung.replace("Ü","Ue").replace("ü","ue").replace("Ä","Ae").replace("ä","ae").replace("Ö","Oe").replace("ö","oe")
                trn_filecomp = trn_filepathname.split("\\")
                Bfpl_filepathname = os.path.join(trn_filepath,trn_filecomp[-2],asc_zugGattung+zugNummer+".timetable.xml")                
                if not os.path.exists(Bfpl_filepathname):
                    logging.info("Kein BuchfahrplanRohDatei Element gefunden %s%s %s", zugGattung,zugNummer,trn_filepath)
                    self.controller.set_statusmessage("Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath)
                    return             
               
            with open(Bfpl_filepathname,mode="r",encoding="utf-8") as fd:
                xml_text = fd.read()
                Bfpl_timetable_dict = parse(xml_text)
                #enter train-timetable
                result_ok = self.timetable.convert_zusi_fpn_dict_to_schedule_dict(Bfpl_timetable_dict)
           
            
        else:
            self.timetable.convert_zusi_trn_to_timetable_train_x(trn_zug_dict)        

    def open_zusi_trn_file(self, trn_filepathname,fpn_filepathname):

        with open(trn_filepathname,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            trn_dict = parse(xml_text)
        trn_zusi_dict = trn_dict.get("Zusi",{})
        trn_zug_dict = trn_zusi_dict.get("Zug",{})        
        self.open_zusi_trn_zug_dict(trn_zug_dict, fpn_filepathname,trn_filepathname=trn_filepathname)

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
            asc_zugGattung = zugGattung.replace("Ü","Ue").replace("ü","ue").replace("Ä","Ae").replace("ä","ae").replace("Ö","Oe").replace("ö","oe")
            
            Bfpl_filepathname = os.path.join(trn_filepath,asc_zugGattung+zugNummer+".timetable.xml")                
            if not os.path.exists(Bfpl_filepathname):
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
        self.timetable.set_tt_traintype_prop(self.main_traintype_prop_dict)
        
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
        self.timetable.set_tt_traintype_prop(self.main_traintype_prop_dict)
        #define stops via selected train-timetable
        result_ok = self.timetable.convert_zusi_fpn_dict_to_schedule_dict(zusi_timetable_dict,define_stations=True)
        if  not result_ok:
            return
        result_ok = self.open_zusi_master_schedule(fpn_filename=fpl_filename)
        if not result_ok:
            return
        self.timetable.doPaint(self.canvas,starthour=starthour,duration=duration)                

    def set_traintype_prop(self,traintype_prop_dict):
        self.main_traintype_prop_dict = traintype_prop_dict

    def initUI(self):
        showTrainTimes = True
        height =self.canvas.winfo_reqheight()
        width = self.canvas.winfo_reqwidth()

