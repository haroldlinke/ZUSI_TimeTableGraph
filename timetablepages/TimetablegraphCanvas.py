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
import tkinter as tk
from tkinter import Tk, Canvas, Frame, font
from tools.xmltodict import parse
from datetime import datetime
from timetablepages.DefaultConstants import LARGE_STD_FONT
import os
import logging
import math
import xml.etree.ElementTree as ET
import os
from timetablepages.PopupWinClone import popup_win_clone

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
    
class RightClickMenu(tk.Frame):   
    def __init__(self, parent, objectid):
        self.master = parent
        tk.Frame.__init__(self, self.master)  
        self.objectid = objectid
        self.edit_own_object = False
        self.create_widgets()

    def create_widgets(self):
        self.create_right_click_menu()

    def create_right_click_menu(self):
        self.right_click_menu = tk.Menu(self.master, tearoff=0, relief='sunken')
        self.right_click_menu.add_command(label="Zeiten zurück auf .trn Zeiten setzen", command=self.edit_stop_original)
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Zugfahrplan in .trn-Datei exportieren", command=self.edit_export_to_trn)
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Zugfahrplan in ZUSI starten", command=self.edit_run_schedule)        
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Zugfahrplan klonen", command=self.edit_clone_schedule,state="disabled")

    def popup_text(self, event,cvobject):
        if not self.master.editflag:
            return
        self.objectid = cvobject
        self.right_click_menu.post(event.x_root, event.y_root)
            
    def destroy_menu(self, event):
        self.right_click_menu.destroy()

    def edit_stop_original(self):
        #print("edit_stop")
        self.master.edit_stop_original(self.objectid)
    
    def edit_export_to_trn(self):
        #print("edit_stop")
        self.master.edit_export_to_trn(self.objectid)
        
    def edit_clone_schedule(self):
        #print("edit_stop")
        self.master.edit_clone_schedule(self.objectid)
        
    def edit_run_schedule(self):
        #print("edit_stop")
        self.master.edit_run_schedule(self.objectid)

class TimeTableGraphCommon():
    def __init__(self, controller, showTrainTimes, height, width, xml_filename="xml_filename",ttmain_page=None,tt_page=None):
        self.controller = controller
        self.ttmain_page = ttmain_page
        self.ttpage = tt_page
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
        self.largeFont = font.Font(family="SANS_SERIF", size=12)
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
        self.graphRightbordersize = 40
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
        self.translate_dict = {"DepartTime": "Abfahrt",
                               "ArriveTime" : "Ankunft"} 
        self.define_key_bindings()
        
    def define_key_bindings(self):
        self.key_to_method_dict = { "onTimeDecMinute"       : self.onTimeDecMinute,
                                    "onTimeIncMinute"       : self.onTimeIncMinute,
                                    "onNextStationTime"     : self.onNextStationTime,
                                    "onPreviousStationTime" : self.onPreviousStationTime,
                                    "onNextTrainTime"       : self.onNextTrainTime,
                                    "onPreviousTrainTime"   : self.onPreviousTrainTime,
                                 }
        
    def bind_right_click_menu_to_trainline(self, trainlineid):
        self.popup = RightClickMenu(self.ttmain_page, trainlineid)
        self.tt_canvas.tag_bind(trainlineid,"<Button-3>",lambda e,Object=trainlineid:self.popup.popup_text(e,Object))
        self.tt_canvas.bind("<Destroy>",self.popup.destroy_menu,add="+")

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
            return stationNameLengthMax+140
        else:
            return int(stationNameLengthMax/1.4)+140
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
        if len(self.schedule_stations_dict) == 0:
            logging.debug("Error - no stations in list")
            return
        TLDirection = self.controller.getConfigData("TLDirection")
        self.draw_stations_vertical = (TLDirection=="vertical")                
        self.tt_canvas = canvas
        self.canvas_dimHeight =self.tt_canvas.winfo_reqheight()
        self.canvas_dimWidth = self.tt_canvas.winfo_reqwidth()                
        self.schedule_startHour=starthour
        self.schedule_startTime_min = self.schedule_startHour * 60
        if self.schedule_startTime_min == 0:
            self.schedule_startTime_min = 1
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
        self.showTrainDir = self.controller.getConfigData("Bfp_show_train_dir")
        self.trainLineFirstStationIdx = -1
        self.trainLineLastStationIdx = 0
        self.tt_canvas_cvobject_rect = -1
        
        if self.showTrainDir == None:
            self.showTrainDir = "all"
        self.dashline_pattern = "-"
        self.tt_canvas_dropdragflg = False
        self.edit_trainline_tag = ""
        self.mm_canvas_coord_idx=-1
        self.mm_trainName = ""
        self.mm_currtime_str = ""
        self.mm_stoptimemode = ""
        self.mm_trainName = ""
        self.mm_stationName = ""
        self.controller.edit_active = False
        self.controller.active_id = -1
        self.edit_panel_ok = False

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
        self.edit_panel_currtime_objectid = -1
        self.edit_panel_stationName_objectid = -1
        self.edit_panel_trainName_objectid = -1
        self.print_edit_panel()

    def determine_xy_point(self, stop, time):
        delta=self.controller.getConfigData("Bfp_TrainLine_Distance_from_Stationline")
        if self.draw_stations_vertical:
            x = self.calculateTimePos(time)
            y = self.stationGrid.get(stop.get("StationIdx",0),0)
            if self.direction=="down":
                y+=delta
            else:
                y-=delta
        else:
            y = self.calculateTimePos(time)
            x = self.stationGrid.get(stop.get("StationIdx",0),0)
            if self.direction=="down":
                x+=delta
            else:
                x-=delta
        x = x*self.controller.total_scalefactor
        y = y*self.controller.total_scalefactor
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
        if self.trainLineFirstStationIdx == -1:
            self.trainLineFirstStationIdx = stationIdx
        self.trainLineLastStationIdx = stationIdx
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
                self.tt_canvas.create_rectangle(x-textwidth/2, yName-textheight/2, x+textwidth/2, yName+textheight/2, fill="white",width=0,outline="white",tags=("Station",stationName))
                s_obj=self.tt_canvas.create_text(x, yName, text=stationName, anchor="center",font=self.s_font)
            elif s_labeldir==1:
                s_labelangle=90
                yName = y - 15
                #self.tt_canvas.create_rectangle(x, yName-textheight/2, x, yName+textheight/2, fill="white",width=0,outline="white")
                s_obj=self.tt_canvas.create_text(x, yName, text=stationName, anchor="w",font=self.s_font,tags=("Station",stationName))                
                self.tt_canvas.itemconfig(s_obj, angle=s_labelangle)
            elif s_labeldir==2:
                yName = y - 15
                #self.tt_canvas.create_rectangle(x, yName-textheight/2, x, yName+textheight/2, fill="white",width=0,outline="white")
                s_obj=self.tt_canvas.create_text(x, yName, text=stationName, anchor="w",font=self.s_font,tags=("Station",stationName))
                overlap = self.test_overlap(s_obj)
                if overlap: 
                    overlap_obj = overlap[0]
                    xov,y0v = self.tt_canvas.coords(overlap_obj)
                    self.tt_canvas.delete(s_obj)
                    x=xov+20
                    s_obj=self.tt_canvas.create_text(x, yName, text=stationName, anchor="w",font=self.s_font,tags=("Station",stationName))
                    if self.test_overlap(s_obj):
                        self.tt_canvas.delete(s_obj)
                    else:
                        s_labelangle=45
                        self.tt_canvas.itemconfig(s_obj, angle=s_labelangle)                                
                else:
                    s_labelangle=45
                    self.tt_canvas.itemconfig(s_obj, angle=s_labelangle)            
            yKm = y + 12
            km_obj=self.tt_canvas.create_text(x, yKm, text=str(f"{stationkm:.1f}"), anchor="center",font=self.s_font,tags=("Station",stationName))
            if self.test_overlap(km_obj):
                self.tt_canvas.delete(km_obj)

    def test_overlap(self, objId,objlist=[]):
        rectangle = self.tt_canvas.bbox(objId)
        overlap = self.tt_canvas.find_overlapping(rectangle[0],rectangle[1],rectangle[2], rectangle[3])
        if len(overlap)>1:
            if objlist != []:
                pass
            else:
                return overlap
        return None

    def print_hour(self, i, currentHour):
        self.coord_null_item = self.tt_canvas.create_text(0,0, text = "0,0")
        th_labelsize=self.controller.getConfigData("Bfp_TH_LineLabelSize")
        th_font = font.Font(family="SANS_SERIF", size=int(th_labelsize))
        hourString = str(currentHour)+":00"
        hOffset = self.stdFont.measure(hourString) / 2
        if self.draw_stations_vertical:
            hourXY = (self.hourWidth * i) + self.graphHourOffset + self.graphLeft
            self.tt_canvas.create_text(hourXY - hOffset, self.graphBottom + 20, text = hourString, anchor="w",fill="black",font=th_font,tags="Hour")
            self.tt_canvas.create_text(hourXY - hOffset, self.graphTop - 8, text = hourString, anchor="w",fill="black",font=th_font)
        else:
            hourXY = (self.hourWidth * i) + self.graphHourOffset + self.graphTop
            self.tt_canvas.create_text(self.graphLeft-10,hourXY, text = hourString, anchor="e",fill="black",font=th_font,tags="Hour")
        self.hour_to_XY_Map[currentHour] = hourXY
        self.hourGrid.append(hourXY);
        if (i == 0):
            self.firstHourXY = hourXY
        if (i == self.schedule_duration):
            self.lastHourXY = hourXY
        return
    
    def print_edit_panel(self):
        self.edit_panel_currtime_objectid = self.tt_canvas.create_text(self.graphRight-10, 40, text = self.mm_currtime_str, font=LARGE_STD_FONT,anchor="c",fill="black",tags="PanelCurrTime")
        self.edit_panel_stoptimemode_objectid = self.tt_canvas.create_text(self.graphRight-80, 40, text = self.translate_dict.get(self.mm_stoptimemode,""), font=LARGE_STD_FONT,anchor="e",fill="black",tags="PanelCurrTime")
        self.edit_panel_trainName_objectid = self.tt_canvas.create_text(self.graphRight-200, 40, text = self.mm_trainName, font=LARGE_STD_FONT,anchor="e",fill="black",tags="PanelTrainName")
        self.edit_panel_stationName_objectid = self.tt_canvas.create_text(self.graphRight-400, 40, text = self.mm_stationName, font=LARGE_STD_FONT, anchor="e",fill="black",tags="PanelStationName")
        
    def update_edit_panel (self):
        self.tt_canvas.itemconfigure(self.edit_panel_trainName_objectid, text = self.mm_trainName)
        self.tt_canvas.itemconfigure(self.edit_panel_stoptimemode_objectid, text = self.translate_dict[self.mm_stoptimemode])
        self.tt_canvas.itemconfigure(self.edit_panel_stationName_objectid, text = self.mm_stationName)
        self.tt_canvas.itemconfigure(self.edit_panel_currtime_objectid, text = self.mm_currtime_str)
        
    def calculateTimePos(self, time):
        if (time < 0): time = 0;
        if (time > 1439): time = 1439;
        hour = int(time / 60)
        min = (time % 60)
        timeposhour = self.hour_to_XY_Map.get(hour,None)
        if timeposhour:
            timeposhour = int(timeposhour + (min * self.sizeMinute))
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
                    if zfs_linedashed !="no line":
                        objid = self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=zfs_width, fill=zfs_color,dash=zfs_linedashed)
                else:
                    if s_linedashed !="no line":
                        objid = self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=s_width, fill=s_color,dash=s_linedashed)
                self.controller.ToolTip_canvas(self.tt_canvas, objid, text="Station: "+self.get_stationName(stationidx),button_1=True)
            for x in self.hourGrid:
                if th_linedashed !="no line":
                    self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=th_width, fill=th_color,dash=th_linedashed)
                if tm_width > 0 and x != self.hourGrid[-1]:
                    number_of_min_lines = int(60/tm_distance)-1
                    distance_per_line = tm_distance * self.hourWidth/60
                    for min_line in range(0,number_of_min_lines):
                        if tm_linedashed !="no line":
                            self.tt_canvas.create_line(x+distance_per_line*(min_line+1), self.graphTop, x+distance_per_line*(min_line+1), self.graphBottom, width=tm_width, fill=tm_color,dash=tm_linedashed)
        else:
            for y in self.hourGrid:
                if th_linedashed  !="no line":
                    self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=th_width, fill=th_color,dash=th_linedashed)
                if tm_width > 0 and y != self.hourGrid[-1]:
                    number_of_min_lines = int(60/tm_distance)-1
                    distance_per_line = tm_distance * self.hourWidth/60
                    for min_line in range(0,number_of_min_lines):
                        if tm_linedashed !="no line":
                            self.tt_canvas.create_line(self.graphLeft, y+distance_per_line*(min_line+1), self.graphRight, y+distance_per_line*(min_line+1), width=tm_width, fill=tm_color,dash=tm_linedashed)
                        
            for stationidx,x in self.stationGrid.items():
                if self.stationTypeZFS_list[stationidx]:
                    if zfs_linedashed  !="no line":
                        objid = self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=zfs_width, fill=zfs_color,dash=zfs_linedashed)
                else:
                    if s_linedashed  !="no line":
                        objid = self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=s_width, fill=s_color,dash=s_linedashed)
                    self.controller.ToolTip_canvas(self.tt_canvas, objid, text="Station: "+self.get_stationName(stationidx),button_1=True)

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
        for self.trainIdx in self.schedule_trains_dict:
            self.process_train(self.trainIdx)
        self.controller.set_statusmessage("") 
        
    def remove_leading_zeros(self,number):
        if self.controller.getConfigData("SO_remove_leading_Zero"):
            for i in range(0,len(number)):
                if number[0] == "0":
                    number=number[1:]
                else:
                    break
        return number

    def process_train(self,trainidx):
        self.tt_canvas.update()
        train = self.schedule_trains_dict.get(trainidx,{})
        self.trainType = train.get("TrainType","X-Deko")
        self.trainNumber = train.get("TrainName","0000")
        self.trainName = self.trainType + self.trainNumber
        self.trainPrintName = self.trainType + self.remove_leading_zeros(self.trainNumber)
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
        self.trainLineFirstStop_Flag = True
        self.trainLineLastStop_Flag = False
        self.drawTrainName_Flag = self.TrainLabelPos in [0,1,2,3]
        self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan für Zug - "+self.trainName)
        self.trainLine_dict = []
        self.trainLine_dict_idx = -1        
        self.process_trainStops()
        return

    def process_trainStops(self):
        for self.stopIdx,stop_dict in self.trainLineStops.items():
            self.arriveTime = stop_dict.get("ArriveTime",0)
            self.departTime = stop_dict.get("DepartTime",0)
            station_dict = self.schedule_stations_dict.get(stop_dict.get("StationIdx"))
            self.stationName = station_dict.get("StationName")
            self.signal = stop_dict.get("Signal")
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

    def drawTrainTime(self, time,  mode,  x,  y):
        if (not self.TrainMinuteShow):
            return
        if not (int(time) in range(self.schedule_startTime_min,self.schedule_startTime_min + self.schedule_duration * 60)):
            return
        minutes = "{:02d}".format(int(time % 60))
        hours = "{:02d}".format(int(time/60))
        sec1 = time-int(time)
        sec2 = round(sec1*60)
        seconds = "{:02d}".format(sec2)
        if mode ==  "begin" :
            mode_txt = "Start"
            timetag = "ArriveTime"
        elif mode == "arrive":
            mode_txt = "Ankunft"
            timetag = "ArriveTime"
        elif mode == "depart":
            mode_txt = "Abfahrt"
            timetag = "DepartTime"
        elif mode == "end":
            mode_txt = "Ziel"
            timetag = "ArriveTime"
        else:
            return        
        if self.draw_stations_vertical:
            if (self.direction== "down"):
            # down
                if mode in ["end","arrive"]:
                    anchor="sw"
                else:
                    anchor="ne"
            else:
            # up
                if mode in ["end","arrive"]:
                    anchor="nw"
                else:
                    anchor="se"      
        else:
            if (self.direction== "down"):
            # left to right
                if mode in ["end","arrive"]:
                    anchor="se"
                else:
                    anchor="nw"
            else:
            # right to left
                if mode in ["end","arrive"]:
                    anchor="sw"
                else:
                    anchor="ne"
                    
        time_str = self.determine_time_str(time)
        stationName_tag = self.stationName
        stationName_tag=stationName_tag.replace("(","[")
        stationName_tag=stationName_tag.replace(")","]")        
        trainTime_objid = self.tt_canvas.create_text(x , y, text = minutes, anchor=anchor,activefill="red",font=self.TrainMinuteFont,tags=(self.trainName,stationName_tag,timetag,"LI_"+str(self.trainLine_dict_idx),"S_"+str(self.stopIdx),self.direction,"T_"+time_str+"_"+timetag[0],self.direction))
        self.draw_background(trainTime_objid,tags=["O_"+str(trainTime_objid)])
        #self.bind_right_click_menu_to_trainline(trainTime_objid)
        if self.trainLineName == None:
            self.trainLineName = ""
        if self.signal != None and self.signal != "":
            signal_str = "("+self.signal+")"
        else:
            signal_str = ""
        self.controller.ToolTip_canvas(self.tt_canvas, trainTime_objid, text=hours+":"+minutes+":"+seconds+"\nZug: "+self.trainName+"\n"+mode_txt+" "+self.stationName+signal_str + "\n"+self.trainLineName, button_1=True)
        self.tt_canvas.tag_bind(trainTime_objid,"<Button-1>" ,lambda e,Object=trainTime_objid:self.MouseButton1(e,Object))
        self.tt_canvas.tag_bind(trainTime_objid,"<Control-1>" ,lambda e,Object=trainTime_objid:self.MouseButton1(e,Object,trainline_mode="part"))
        self.tt_canvas.tag_bind(trainTime_objid,"<Shift-1>" ,lambda e,Object=trainTime_objid:self.MouseButton1(e,Object,seconds_flag=True))
        self.tt_canvas.tag_bind(trainTime_objid,"<Alt-1>" ,lambda e,Object=trainTime_objid:self.MouseButton1(e,Object,trainline_mode="complete"))
        self.tt_canvas.tag_bind(trainTime_objid,"<ButtonRelease 1>",lambda e,Object=trainTime_objid:self.MouseRelease1())
        self.tt_canvas.tag_bind(trainTime_objid,"<Shift-Control-1>" ,lambda e,Object=trainTime_objid:self.MouseButton1(e,Object,trainline_mode="part",seconds_flag=True))
        self.tt_canvas.tag_bind(trainTime_objid,"<Shift-Alt-1>" ,lambda e,Object=trainTime_objid:self.MouseButton1(e,Object,trainline_mode="complete",seconds_flag=True))
        
        # Event für Mausbewegung
        self.tt_canvas.tag_bind(trainTime_objid,"<B1-Motion>",lambda e,Object=trainTime_objid:self.MouseMove(e,Object))
        self.tt_canvas.tag_bind(trainTime_objid,"<Shift-B1-Motion>",lambda e,Object=trainTime_objid:self.MouseMove(e,Object,seconds_flag=True))
        self.tt_canvas.tag_bind(trainTime_objid,"<Control-B1-Motion>",lambda e,Object=trainTime_objid:self.MouseMove(e,Object,trainline_mode="part"))
        self.tt_canvas.tag_bind(trainTime_objid,"<Alt-B1-Motion>",lambda e,Object=trainTime_objid:self.MouseMove(e,Object,trainline_mode="complete"))
        self.tt_canvas.tag_bind(trainTime_objid,"<Shift-Control-B1-Motion>",lambda e,Object=trainTime_objid:self.MouseMove(e,Object,trainline_mode="part",seconds_flag=True))
        self.tt_canvas.tag_bind(trainTime_objid,"<Shift-Alt-B1-Motion>",lambda e,Object=trainTime_objid:self.MouseMove(e,Object,trainline_mode="complete",seconds_flag=True))

    def get_trainline_id(self, trainName,stationName):
        id_list = self.tt_canvas.find_withtag("L_"+trainName)
        #print(id_list)
        return id_list[0]
    
    def get_trainStationTime_id(self, trainName,stationName, stoptimemode):
        stationName=stationName.replace("(","[")
        stationName=stationName.replace(")","]")
        id_list = self.tt_canvas.find_withtag(trainName+"&&"+stationName+"&&"+stoptimemode)
        if len(id_list) == 0:
            return -1
        else:
            return id_list[0]    
    
    def determine_time_value(self,time_str):
        time_min = 0
        if time_str != "":
            time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            time_min = time_obj.hour * 60 + time_obj.minute + time_obj.second/60        
        return time_min
                
    def determine_time_str(self,time,timeformat="hh:mm:ss"):
        try:
            if timeformat == "hh:mm:ss":
                self.mm_minutes = int(time % 60)
                minutes = "{:02d}".format(self.mm_minutes)
                self.mm_hours = int(time/60)
                hours = "{:02d}".format(self.mm_hours)
                sec1 = time-int(time)
                self.mm_seconds = round(sec1*60)
                seconds = "{:02d}".format(self.mm_seconds)
                return hours+":"+minutes+":"+seconds
            elif timeformat == "hh:mm":
                self.mm_minutes = int(time % 60)
                minutes = "{:02d}".format(self.mm_minutes)
                self.mm_hours = int(time/60)
                hours = "{:02d}".format(self.mm_hours)
                return hours+":"+minutes
            elif timeformat == "mm":
                self.mm_minutes = int(time % 60)
                minutes = "{:02d}".format(self.mm_minutes)
                return minutes
            else:
                return " "
        except:
            print(time)
            return " "
        
    def delete_train(self,trainName):
        self.tt_canvas.delete(trainName)
            
    def get_train_idx_from_Name(self,trainName,scalefactor=1):
        for trainIdx in self.schedule_trains_dict:
            train = self.schedule_trains_dict.get(trainIdx,{})
            search_trainType = train.get("TrainType","X-Deko")
            search_trainName = search_trainType + train.get("TrainName","0000")
            if search_trainName == trainName:
                if train.get("Stops",{}) != {}:
                    return trainIdx
        return -1
    
    def get_trainline_station_data(self,trainName,stationName):
        self.trainIdx = self.get_train_idx_from_Name(trainName)
        train = self.schedule_trains_dict.get(self.trainIdx,{})
        search_stops = train.get("Stops",{})
        for stopIdx,stop_dict in search_stops.items():
            station_dict = self.schedule_stations_dict.get(stop_dict.get("StationIdx"))
            search_stationName = station_dict.get("StationName")
            if search_stationName == stationName:
                return stopIdx,stop_dict
            
    def get_trainline_stationidx_data(self,trainName,stopidx):
        self.trainIdx = self.get_train_idx_from_Name(trainName)
        train = self.schedule_trains_dict.get(self.trainIdx,{})
        search_stops = train.get("Stops",{})
        stop_dict = search_stops.get(stopidx,{})
        return stop_dict    
  
    def determine_DirectionofTravel(self):
        if (self.trainLineStopCnt == 1):
            # Single stop train, default to down
            self.direction = "down"
            return;
        stop = self.trainLineStops.get(self.stopIdx,{});
        currStation_Idx = stop.get("StationIdx",0)
        currStation = self.schedule_stations_dict.get(currStation_Idx,{})
        currkm = currStation.get("Distance",0)
        if (self.trainLineLastStop_Flag):    
            prevStation = self.get_StationData(self.stopIdx - 1)
            # For the last stop, use the previous stop to set the direction
            prevkm = prevStation.get("Distance",0)
            if prevkm < currkm:
                self.direction = "down" 
            else :  
                self.direction = "up"                                
        else:
            # For all other stops use the next stop.
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
        return int(time) in range(self.schedule_startTime_min,self.schedule_startTime_min + self.schedule_duration * 60)

    def setBegin(self, stop,stationName):
        self.determine_DirectionofTravel()
        if self.showTrainDir != "all" and self.showTrainDir != self.direction:
            return
        self.firstStationName = stationName
        if self.trainIncomingStation=="" or self.InOutBoundTrainsShowMinutes:
            self.arriveTime = stop.get("ArriveTime",0)
            show_arrive_time = True
        else:
            show_arrive_time = False
        # Check for stop duration before depart
        self.departTime = stop.get("DepartTime",0)
        xd,yd = self.determine_xy_point(stop,self.departTime)        
        if self.check_time_in_range(self.arriveTime):
            xa,ya = self.determine_xy_point(stop,self.arriveTime)
            if ya == None:
                return
            self.trainLine_dict = [xa, ya]
            self.trainLine_dict_idx = 0
            self.arriveTime = stop.get("ArriveTime",0)
            if not(self.trainLineLastStop_Flag) and show_arrive_time:
                self.drawTrainTime(self.arriveTime, "begin", xa, ya)
            self.trainLine_dict.extend([xd, yd])
            self.trainLine_dict_idx += 1
        else:
            self.trainLine_dict = [xd, yd]
            self.trainLine_dict_idx = 0            
        if not (self.trainLineLastStop_Flag):
            self.drawTrainTime(self.departTime, "depart", xd, yd)

    def drawLine(self, stop):
        self.determine_DirectionofTravel()
        if self.showTrainDir != "all" and self.showTrainDir != self.direction:
            return        
        y=None
        if self.arriveTime > 0:
            if self.check_time_in_range(self.arriveTime):
                xa,ya = self.determine_xy_point(stop,self.arriveTime)
                if ya==None:
                    return
                if self.direction=="down":
                    self.trainLine_dict.extend([xa, ya])
                    self.trainLine_dict_idx += 1
                else:              
                    self.trainLine_dict.extend([xa, ya])
                    self.trainLine_dict_idx += 1
                self.drawTrainTime(self.arriveTime, "arrive", xa, ya)
                if (len(self.trainLine_dict)>3) and ya!=None:
                    self.draw_trainName_parallel(self.trainPrintName, self.trainLine_dict[-4],self.trainLine_dict[-3],xa, ya)
                if self.check_time_in_range(self.departTime):
                    xd,yd = self.determine_xy_point(stop,self.departTime)
                    if yd==None:
                        return
                    self.trainLine_dict.extend([xd, yd])
                    self.trainLine_dict_idx += 1
                    if not self.trainLineLastStop_Flag:
                        self.drawTrainTime(self.departTime, "depart", xd, yd)
        else:
            if self.check_time_in_range(self.departTime):
                xd,yd = self.determine_xy_point(stop,self.departTime)
                if yd==None:
                    return
                self.trainLine_dict.extend([xd, yd])
                self.trainLine_dict_idx += 1
                if not self.trainLineLastStop_Flag or self.arriveTime == 0:
                    self.drawTrainTime(self.departTime, "depart", xd, yd)
                if (len(self.trainLine_dict)>3) and yd!=None:
                    self.draw_trainName_parallel(self.trainPrintName, self.trainLine_dict[-4],self.trainLine_dict[-3],xd, yd)               
                    
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
                if self.showTrainDir == "all" or self.showTrainDir == self.direction:
                    self.trainLine_dict.extend([x, y])
                    self.trainLine_dict_idx += 1
                if self.TrainLineDashed != "no line":
                    train_line_objid = self.tt_canvas.create_line(self.trainLine_dict,fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,dash=self.TrainLineDashed,tags=(self.trainName,"L_"+self.trainName,str(self.trainIdx)))
                    self.controller.ToolTip_canvas(self.tt_canvas, train_line_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, button_1=True)
                    self.bind_right_click_menu_to_trainline(train_line_objid)
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
                        train_line_out_objid = self.tt_canvas.create_line([x,y,x,y+arrow_delta],fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,arrow="last",arrowshape=(10,10,arrowwidth),tags=(self.trainName))
                    else:
                        train_line_out_objid = self.tt_canvas.create_line([x,y,x+arrow_delta,y],fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,arrow="last",arrowshape=(10,10,arrowwidth),tags=(self.trainName))
                    self.controller.ToolTip_canvas(self.tt_canvas, train_line_out_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nNach "+self.trainOutgoingStation, button_1=True)
                
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
                        train_line_in_objid = self.tt_canvas.create_line([x,y,x,y-arrow_delta],fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,arrow="first",arrowshape=(10,10,arrowwidth),tags=(self.trainName))
                    else:
                        train_line_in_objid = self.tt_canvas.create_line([x,y,x-arrow_delta,y],fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,arrow="first",arrowshape=(10,10,arrowwidth),tags=(self.trainName))
                    self.controller.ToolTip_canvas(self.tt_canvas, train_line_in_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nVon "+self.trainIncomingStation, button_1=True)                
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
        trainName_len = self.TrainLabelFont.measure(self.trainName)
        segment_len = segment.norm()
        if segment_len > trainName_len+15:
            if self.drawTrainName_Flag:
                txtobj = self.tt_canvas.create_text(*(mid_point), text=trainName,activefill="red",font=self.TrainLabelFont,anchor="s",tags=(self.trainName,"TrainName"))
                rectangle = self.tt_canvas.bbox(txtobj)
                #rectobj= self.tt_canvas.create_rectangle(rectangle[0]+1,rectangle[1]+1,rectangle[2]-1,rectangle[3]-1,fill="white",outline="",tags=(self.trainName,"Background"),width=0)                
                if y0 != y1:
                    angle = segment.angle()
                    if angle>90:
                        angle -= 180
                    if angle<-90:
                        angle+=180
                    self.tt_canvas.itemconfig(txtobj, angle=angle)
                    self.print_rotated_rectangle(rectangle,angle)
                if self.test_overlap(txtobj,objlist=("TrainName")):
                    self.tt_canvas.delete(txtobj)
                else:
                    self.controller.ToolTip_canvas(self.tt_canvas, txtobj, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, button_1=True)
                    #self.draw_background(txtobj,tags=[self.trainName])
                    if self.TrainLabelPos!=0:
                        self.drawTrainName_Flag=False

    def print_rotated_rectangle(self,rectangle,angle):
        
        pass
    

    def draw_background(self, objId,tags=[],fill="white"):
        b_list = ["Background"]
        tags.extend(b_list)
        rectangle = self.tt_canvas.bbox(objId)
        self.tt_canvas.create_rectangle(rectangle[0]+1,rectangle[1]+1,rectangle[2]-1,rectangle[3]-1,fill=fill,outline=fill,tags=tags,width=0)
        self.tt_canvas.tag_raise(objId)
                    
    def enter_station(self,stationName, distance, stationKm):
        if stationKm == None:
            print("Error: km=None -",stationName)
            stationKm = 0
        for stationIdx in self.schedule_stations_dict:
            station_data = self.schedule_stations_dict.get(stationIdx,0)
            if station_data.get("StationName","") == stationName:
                return stationIdx
        #if not self.addStation:
            # check if currentStation = Startstation
        #    if stationName == self.StartStation:
        #        self.addStation = True
        #    else:
        #        return -1
        # check if currentStation = Endstation
        #if stationName == self.EndStation and self.teilstrecke_flag:
        #    self.addStation = False
        if (len(self.select_stationlist) < 2) or (stationName in self.select_stationlist):     
            self.schedule_stations_dict[self.schedule_stationIdx_write_next] = {"StationName": stationName, 
                                                                                "Distance": distance,
                                                                                "StationKm": stationKm}
            self.schedule_stationIdx_write_next +=1
        else:
            return -1
        return self.schedule_stationIdx_write_next - 1

    def enter_schedule_trainLine_data(self,trainNumber,trainType,ZugLauf,ZugLok,trn_filepathname=""):
        color = self.canvas_traintype_prop_dict.get(trainType,"black")
        width = self.trainType_to_Width_dict.get(trainType,"1")
        self.schedule_trains_dict[self.schedule_trainIdx_write_next] = {"TrainName"     : trainNumber,
                                                                        "trn_filename"  : trn_filepathname,
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

    def enter_trainLine_stop(self, train_idx, trainstop_idx, FplName, FplAnk_min, FplAbf_min,signal=""):
        #print("enter_trainline_stop:", train_idx, FplName, FplAnk_min, FplAbf_min)
        train_dict = self.schedule_trains_dict.get(train_idx)
        trainstops_dict = train_dict.get("Stops",{})
        station_idx = self.search_station(FplName)
        do_not_override_station = False
        last_station_arriveTime = 0
        if trainstop_idx>0:
            last_station_idx = trainstops_dict[trainstop_idx-1]["StationIdx"]
            if station_idx == last_station_idx:
                trainstop_idx -= 1  # update only extisting train stop
                last_station_arriveTime = trainstops_dict[trainstop_idx]["ArriveTime"]
                if last_station_arriveTime > 0 and FplAnk_min==0:
                    do_not_override_station = True
        if not do_not_override_station:
            if last_station_arriveTime>0:
                arriveTime = last_station_arriveTime
            else:
                arriveTime = FplAnk_min
            departTime = FplAbf_min
            trainstops_dict[trainstop_idx] = {"StationIdx"     : station_idx,
                                              "ArriveTime"     : arriveTime,
                                              "ArriveTimeOrig" : arriveTime,
                                              "DepartTime"     : departTime,
                                              "DepartTimeOrig" : departTime,
                                              "Signal"         : signal
                                           }
        return trainstop_idx + 1
        
    def set_trainline_data(self,trainIdx, key, data):
        #logging.debug("set_trainline_data: %s %s %s",trainIdx, key, data)
        train_dict = self.schedule_trains_dict.get(trainIdx)
        train_dict[key] = data    
        
    def get_trainline_data(self,trainIdx, key):
        #logging.debug("get_trainline_data: %s %s",trainIdx, key)
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
    
    def set_trainline_data_changed_flag(self,trainIdx):
        self.set_trainline_data(trainIdx, "DataChanged", "True")
        
    def reset_trainline_data_changed_flag(self,trainIdx):
        self.set_trainline_data(trainIdx, "DataChanged", "False")        
        
    def test_trainline_data_changed_flag(self):
        for trainIdx,train_dict in self.schedule_trains_dict.items():
            data = train_dict.get("DataChanged",None)
            if data == "True":
                return True
        return False        

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

    def convert_tt_xml_dict_to_schedule_dict(self, tt_xml_dict, define_stations=False):
        Zusi_dict = tt_xml_dict.get("Zusi")
        Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan",{})
        if Buchfahrplan_dict=={}:
            return False
        ZugNummer = Buchfahrplan_dict.get("@Nummer","")
        ZugGattung = Buchfahrplan_dict.get("@Gattung","")
        ZugLok = Buchfahrplan_dict.get("@BR","")
        if ZugGattung == "X-Deko" and not define_stations:
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
        #showstationonly = not self.controller.getConfigData("ExtraShowAlleZFS")
        if FplRglGgl_str !="":
            self.FplRglGgl = FplRglGgl_str.split(",")
        else:
            self.FplRglGgl = []
        FplZeile_list = Buchfahrplan_dict.get("FplZeile",{})
        stationdistance = 0
        last_km = 0
        station_idx = 0
        #self.teilstrecke_flag = self.controller.getConfigData("TeilStreckeCheckButton")
        #self.addStation = True #not self.teilstrecke_flag
        #self.StartStation = self.controller.getConfigData("StartStation")
        #self.StartStation = self.StartStation.replace("_"," ")
        #self.EndStation = self.controller.getConfigData("EndStation")
        #self.EndStation = self.EndStation.replace("_"," ")
        #if self.StartStation == "":
        #    self.addStation = True
        self.select_stationlist  = self.controller.get_macroparam_val("SpecialConfigurationPage","StationChooser") #self.controller.getConfigData("StationChooser")
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
                        
                if Fplkm<0:
                    Fplkm = 0.0

                FplAbf = self.get_fplZeile_entry(FplZeile_dict, "FplAbf","@Abf")
                if FplAbf == "":
                    continue # only use station with "Abf"-Entry
                if FplAbf != "":
                    FplAbf_obj = datetime.strptime(FplAbf, '%Y-%m-%d %H:%M:%S')
                    FplAbf_min = FplAbf_obj.hour * 60 + FplAbf_obj.minute + FplAbf_obj.second/60
                else:
                    FplAbf_min = 0
                FplAnk = self.get_fplZeile_entry(FplZeile_dict, "FplAnk","@Ank")
                if FplAnk!="":
                    FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                    FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute + FplAnk_obj.second/60
                else:
                    FplAnk_min = 0
                FplName = self.get_fplZeile_entry(FplZeile_dict,"FplName","@FplNameText",default="")
                if FplName == "":
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
    
    def convert_trn_dict_to_schedule_dict(self, zusi_trn_dict,trn_filepathname=""):
        try:
            if zusi_trn_dict=={}:
                return
            ZugNummer = zusi_trn_dict.get("@Nummer","")
            ZugGattung = zusi_trn_dict.get("@Gattung","")
            ZugLok = zusi_trn_dict.get("@BR","")
            if ZugGattung == "X-Deko":
                return
            Zuglauf = zusi_trn_dict.get("@Zuglauf","")
            Datei_fpn_dict = zusi_trn_dict.get("Datei",{})
            if Datei_fpn_dict == {}:
                return
            fpn_dateiname = Datei_fpn_dict.get("@Dateiname","")
            self.schedule_dict["Name"] = fpn_dateiname
            train_idx = self.enter_schedule_trainLine_data(ZugNummer,ZugGattung,Zuglauf,ZugLok,trn_filepathname=trn_filepathname)
            train_stop_idx = 0
            FplZeile_list = zusi_trn_dict.get("FahrplanEintrag",{})
            if FplZeile_list=={}:
                return
            #Fpl_Zeile_cnt_max = len(FplZeile_list)
            for FplZeile_dict in FplZeile_list:
                #print(repr(FplZeile_dict))
               
                FplAbf = FplZeile_dict.get("@Abf","")
                if FplAbf == "":
                    continue # only use station with "Abf"-Entry
                FplAbf_obj = datetime.strptime(FplAbf, '%Y-%m-%d %H:%M:%S')
                FplAbf_min = FplAbf_obj.hour * 60 + FplAbf_obj.minute + FplAbf_obj.second/60
                FplAnk = FplZeile_dict.get("@Ank","")
                if FplAnk!="":
                    FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                    FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute + FplAnk_obj.second/60
                else:
                    FplAnk_min = 0
                FahrplanSignal = None
                Fpl_SignalEintrag_dict = FplZeile_dict.get("FahrplanSignalEintrag",None)
                if Fpl_SignalEintrag_dict:
                    try:
                        FahrplanSignal = Fpl_SignalEintrag_dict.get("@FahrplanSignal",None)
                    except: # list instead of dict
                        FahrplanSignal = ""
                        for signal in Fpl_SignalEintrag_dict:
                            FahrplanSignal += " "+signal.get("@FahrplanSignal","")+" "
                FplName = FplZeile_dict.get("@Betrst","")
                if FplName == "":
                    continue                
                station_idx = self.search_station(FplName)
                if station_idx != -1:
                    train_stop_idx = self.enter_trainLine_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min,signal=FahrplanSignal)
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
    
    def MouseButton1(self,mouse,cvobject,seconds_flag=False,trainline_mode=""):
        #~~~Setzt die Bewegungsflag
        if self.edit_trainline_tag == self.tt_canvas.gettags(cvobject)[0] or self.ttmain_page.fast_editflag:
            
            if self.tt_canvas_cvobject_rect != -1:
                self.tt_canvas.delete(self.tt_canvas_cvobject_rect)
            self.edit_trainline_mode=trainline_mode
            trainName = self.tt_canvas.gettags(cvobject)[0]
            if (trainName != self.mm_trainName) and (self.mm_trainName != ""):
                    self.edit_train_schedule_stop() # reset previous trainline                     
            stationName = self.tt_canvas.gettags(cvobject)[1]
            stationName=stationName.replace("[","(")
            stationName=stationName.replace("]",")")
            self.mm_stoptimemode = self.tt_canvas.gettags(cvobject)[2]
            trainLine_idx_str = self.tt_canvas.gettags(cvobject)[3]
            stopIdx = self.tt_canvas.gettags(cvobject)[4]
            trainLine_idx_split = trainLine_idx_str.split("_")
            self.mm_trainLine_idx = int(trainLine_idx_split[1])
            self.tt_canvas.tag_raise(cvobject,None)
            if trainName == None and stationName == None:
                return
            stopIdx,self.mm_stop_dict = self.get_trainline_station_data(trainName,stationName)
            #if mode =="depart":
            #    self.mm_stoptimemode="DepartTime"
            #else:
            #    self.mm_stoptimemode="ArriveTime"
            self.mm_currtime_int = self.mm_stop_dict[self.mm_stoptimemode]
            self.mm_currtime_str = self.determine_time_str(self.mm_currtime_int)
            x1,y1 = self.tt_canvas.coords(cvobject)
            #xc1 = self.tt_canvas.canvasx(x1)
            xc1 = x1
            #yc1 = self.tt_canvas.canvasy(y1)
            yc1 = y1
            self.tt_canvas_cvobject = cvobject
            self.tt_canvas.itemconfigure(self.tt_canvas_cvobject,text=self.mm_currtime_str,font=self.largeFont,fill="red")
            rectangle = self.tt_canvas.bbox(self.tt_canvas_cvobject)
            self.tt_canvas_cvobject_rect=self.tt_canvas.create_rectangle(rectangle,fill="white",outline="red",tags=(self.trainName))
            #print("Button-1",self.tt_canvas_cvobject_rect)
            self.tt_canvas.tag_raise(self.tt_canvas_cvobject_rect,None)
            self.tt_canvas.tag_raise(cvobject,None)
            self.tt_canvas_dropdragflg = True
            self.mm_canvas_x_org = xc1
            self.mm_canvas_y_org = yc1
            self.mm_canvas_t_org = self.mm_currtime_int
            self.mm_trainlineid = self.get_trainline_id(trainName,stationName)
            self.mm_canvas_coord_list = self.tt_canvas.coords(self.mm_trainlineid)
            self.mm_canvas_coord_list_org = self.mm_canvas_coord_list.copy()
            self.mm_canvas_coord_idx = self.mm_trainLine_idx
            self.mm_stopIdx = stopIdx
            self.mm_trainName = trainName
            self.mm_stationName = stationName
            self.mm_seconds_flag = seconds_flag
            self.ttpage.block_Canvas_movement(True)
            self.controller.edit_active = True
            if not self.edit_panel_ok:
                self.print_edit_panel()
                self.edit_panel_ok = True
            else:
                self.update_edit_panel()
            
    def update_stop_time(self,stop_dict,delta_t):
        arriveTime = stop_dict["ArriveTime"]
        if arriveTime >0:
            stop_dict["ArriveTime"] = delta_t + arriveTime
        departTime = stop_dict["DepartTime"]
        if departTime > 0:
            stop_dict["DepartTime"] = delta_t + departTime        
                
    def update_mm_stop_times(self,stopIdx,stopTimeMode):
        delta_t = self.mm_currtime_int - self.mm_canvas_t_org
        self.update_mm_stop_times_delta(delta_t, stopTimeMode)

    def update_mm_stop_times_delta(self, delta_t, stopTimeMode):
        train = self.schedule_trains_dict.get(self.trainIdx,{})
        stops_dict = train.get("Stops",{})       
        if self.edit_trainline_mode == "complete":
            for idx in range(0,len(stops_dict)):
                stop_dict = stops_dict[idx]
                self.update_stop_time(stop_dict,delta_t)
        elif self.edit_trainline_mode == "part":
            for idx in range(self.mm_stopIdx,len(stops_dict)):
                stop_dict = stops_dict[idx]
                self.update_stop_time(stop_dict,delta_t)
        else:
            stop_dict = stops_dict[self.mm_stopIdx]
            stop_dict[stopTimeMode] += delta_t
            
        if delta_t != 0:
            self.set_trainline_data_changed_flag(self.trainIdx)

    def MouseRelease1(self):
        if self.tt_canvas_dropdragflg:
            self.tt_canvas_dropdragflg = False
            #print("Button-Release",self.tt_canvas_cvobject_rect)
            #minutes = "{:02d}".format(int(self.mm_currtime_int % 60))
            #self.tt_canvas.itemconfigure(self.tt_canvas_cvobject,text=minutes)
            self.update_mm_stop_times(self.mm_stopIdx,self.mm_stoptimemode)
            #self.mm_stop_dict[self.mm_stoptimemode] = self.mm_currtime_int
            self.tt_canvas.delete(self.tt_canvas_cvobject_rect)
            self.delete_train(self.mm_trainName)
            self.tt_canvas.update_idletasks()
            trainidx = self.get_train_idx_from_Name(self.mm_trainName)
            self.process_train(trainidx)
            self.tt_canvas_cvobject = self.get_trainStationTime_id(self.mm_trainName,self.mm_stationName,self.mm_stoptimemode)
            try:
                self.tt_canvas.itemconfigure(self.edit_trainline_tag,font=self.largeFont,fill="red")
            except:
                pass
            self.tt_canvas.itemconfigure(self.tt_canvas_cvobject,text=self.mm_currtime_str)
            rectangle = self.tt_canvas.bbox(self.tt_canvas_cvobject)
            self.tt_canvas_cvobject_rect=self.tt_canvas.create_rectangle(rectangle,fill="white",outline="red",tags=(self.trainName))
            #print("Button-1 release",self.tt_canvas_cvobject_rect)
            self.tt_canvas.tag_raise(self.tt_canvas_cvobject_rect,None)
            self.tt_canvas.tag_raise(self.tt_canvas_cvobject,None)            
            self.update_edit_panel()
            self.ttpage.block_Canvas_movement(False)
            #if self.ttmain_page.fast_editflag:
            #    self.controller.edit_active = False

    def MouseMove(self,mouse,cvobject,seconds_flag=False,trainline_mode=""):
        if self.tt_canvas_dropdragflg == True:
            self.edit_trainline_mode=trainline_mode
            #x1 = mouse.x
            y1 = mouse.y
            x0,y0 = self.tt_canvas.coords(cvobject)
            #xc0 = self.tt_canvas.canvasx(x0)
            xc0 = x0
            yc1 = self.tt_canvas.canvasy(y1)
            scaled_size_minute = self.sizeMinute *self.controller.total_scalefactor
            delta_y = yc1-self.mm_canvas_y_org
            if self.mm_seconds_flag:
                delta_y_scaled = delta_y
            else:
                delta_y_scaled = int(delta_y / scaled_size_minute) * scaled_size_minute
            #print(delta_y, delta_y_scaled)
            yc1 = self.mm_canvas_y_org + delta_y_scaled
            delta_t = delta_y / scaled_size_minute
            if not seconds_flag:
                delta_t = int(delta_t) # ignore seconds
            self.mm_currtime_int = self.mm_canvas_t_org + delta_t
            self.mm_currtime_str = self.determine_time_str(self.mm_currtime_int)
            self.tt_canvas.coords(cvobject,xc0,yc1)
            self.tt_canvas.itemconfigure(cvobject,text=self.mm_currtime_str)
            #print("Button-Move",self.tt_canvas_cvobject_rect)
            rectangle = self.tt_canvas.bbox(self.tt_canvas_cvobject)
            self.tt_canvas.coords(self.tt_canvas_cvobject_rect,rectangle)
            self.tt_canvas.tag_raise(self.tt_canvas_cvobject_rect,None)
            self.tt_canvas.tag_raise(cvobject,None)            
            if self.edit_trainline_mode == "complete":
                point_no = int(len(self.mm_canvas_coord_list)/2)
                for point in range(0,point_no):
                    self.mm_canvas_coord_list[point*2+1]= self.mm_canvas_coord_list_org[point*2+1] + delta_y_scaled
            elif self.edit_trainline_mode == "part":
                point_no = int(len(self.mm_canvas_coord_list)/2)
                for point in range(self.mm_canvas_coord_idx,point_no):
                    self.mm_canvas_coord_list[point*2+1]= self.mm_canvas_coord_list_org[point*2+1] + delta_y_scaled
            else:
                self.mm_canvas_coord_list[self.mm_canvas_coord_idx*2+1] = yc1
            #print(self.mm_canvas_coord_list, self.mm_trainlineid)
            self.tt_canvas.coords(self.mm_trainlineid,self.mm_canvas_coord_list)
            self.update_edit_panel()
            self.tt_canvas.update_idletasks()
            self.ttpage.block_Canvas_movement(True)
            
    def enter_canvas(self,event=None):
        self.tt_canvas.focus_set()
    
    def edit_bindings(self):
        self.tt_canvas.bind("<Enter>",self.enter_canvas)
        for action,method in self.key_to_method_dict.items():
            key_str = self.controller.get_key_for_action(action)
            self.tt_canvas.bind(key_str,method)
        return
        
    def process_change_stop_time(self,delta):
        if not self.controller.edit_active:
            return
        self.update_mm_stop_times_delta(delta,self.mm_stoptimemode)
        self.delete_train(self.mm_trainName)
        self.tt_canvas.update_idletasks()
        trainidx = self.get_train_idx_from_Name(self.mm_trainName)
        self.process_train(trainidx)
        self.mm_currtime_int = self.mm_stop_dict[self.mm_stoptimemode]
        self.mm_currtime_str = self.determine_time_str(self.mm_currtime_int)
        self.tt_canvas_cvobject = self.get_trainStationTime_id(self.mm_trainName,self.mm_stationName,self.mm_stoptimemode)
        try:
            self.tt_canvas.itemconfigure(self.edit_trainline_tag,font=self.largeFont,fill="red")
        except:
            pass
        self.tt_canvas.itemconfigure(self.tt_canvas_cvobject,text=self.mm_currtime_str)
        rectangle = self.tt_canvas.bbox(self.tt_canvas_cvobject)
        self.tt_canvas_cvobject_rect=self.tt_canvas.create_rectangle(rectangle,fill="white",outline="red",tags=(self.trainName))
        self.tt_canvas.tag_raise(self.tt_canvas_cvobject_rect,None)
        self.tt_canvas.tag_raise(self.tt_canvas_cvobject,None)
        self.update_edit_panel()
        self.tt_canvas.update_idletasks()        
    
    def isKthBitSet(self, n, k): 
        if n & (1 << (k - 1)): 
            return True 
        else: 
            return False         
        
    def onTimeIncMinute(self, event):
        self.edit_trainline_mode = "single"
        if self.isKthBitSet(event.state,1):
            delta_t = 1/60
        else:
            delta_t = 1
        if self.isKthBitSet(event.state,3):
            self.edit_trainline_mode = "part"
        if self.isKthBitSet(event.state,18):
            self.edit_trainline_mode = "complete"                    
        self.process_change_stop_time(delta_t)    

    def onTimeDecMinute(self, event):
        self.edit_trainline_mode = "single"
        if self.isKthBitSet(event.state,1):
            delta_t = -1/60
        else:
            delta_t = -1
        if self.isKthBitSet(event.state,3):
            self.edit_trainline_mode = "part"
        if self.isKthBitSet(event.state,18):
            self.edit_trainline_mode = "complete"             
        self.process_change_stop_time(delta_t)            

    def onPreviousStationTime(self, event):
        self.active_next_stop_time(direction="previousStationTime")
    
    def onNextStationTime(self, event):
        self.active_next_stop_time(direction="nextStationTime")
        
    def onPreviousTrainTime(self, event):
        self.active_next_stop_time(direction="previousTrainTime")
    
    def onNextTrainTime(self, event):
        self.active_next_stop_time(direction="nextTrainTime")
        
    def get_allTrainTimesForTrainName(self,trainName):
        #get all objects for trainName
        trainTimesObjectDict = {}
        trainId_list = self.tt_canvas.find_withtag(trainName)
        if len(trainId_list) == 0:
            return False
        for objid in trainId_list:
            taglist = self.tt_canvas.gettags(objid)
            if len(taglist)>= 7:
                timetag = taglist[6]
                if timetag.startswith("T_"):
                    trainTimesObjectDict[objid] = timetag
        return trainTimesObjectDict
    
    def get_allStationTimesForStationName(self,stationName):
        #get all objects for trainName
        stationTimesObjectDict = {}
        stationName_tag = stationName
        stationName_tag=stationName_tag.replace("(","[")
        stationName_tag=stationName_tag.replace(")","]")              
        stationId_list = self.tt_canvas.find_withtag(stationName)
        if len(stationId_list) == 0:
            return False
        for objid in stationId_list:
            taglist = self.tt_canvas.gettags(objid)
            if len(taglist)>= 7:
                timetag = taglist[6]
                if timetag.startswith("T_"):
                    stationTimesObjectDict[objid] = timetag
        return stationTimesObjectDict    
    
    def activate_time_entry(self,objectid):
        self.MouseButton1(None, objectid)
        self.MouseRelease1()
        pass
    
    def active_next_stop_time(self,direction=""):
        if direction in ["nextTrainTime","previousTrainTime"]:
            self.active_nexttraintime(direction=direction)
        elif direction in ["nextStationTime","previousStationTime"]:
            self.active_nextstationtime(direction=direction)
        else:
            return
        return
    
    def active_nextstationtime(self, direction=""):
        trainTimesObjectDict = self.get_allStationTimesForStationName(self.mm_stationName)
        if trainTimesObjectDict == {}:
            return
        cur_timetag = trainTimesObjectDict.get(self.tt_canvas_cvobject,"")
        if cur_timetag == "":
            return
        if direction == "previousStationTime":
            next_timetag = ""
            next_objectid = self.tt_canvas_cvobject
            for objectid, timetag in trainTimesObjectDict.items():
                if timetag > cur_timetag:
                    if next_timetag == "":
                        next_timetag = timetag
                        next_objectid = objectid
                    elif next_timetag > timetag:
                        next_timetag = timetag
                        next_objectid = objectid
        elif direction == "nextStationTime":
            next_timetag = ""
            next_objectid = self.tt_canvas_cvobject
            for objectid, timetag in trainTimesObjectDict.items():
                if timetag < cur_timetag:
                    if next_timetag == "":
                        next_timetag = timetag
                        next_objectid = objectid
                    elif next_timetag < timetag:
                        next_timetag = timetag
                        next_objectid = objectid            
        self.activate_time_entry(next_objectid)
        return        
    
    def active_nexttraintime(self, direction=""):
        taglist = self.tt_canvas.gettags(self.tt_canvas_cvobject)
        train_direction = taglist[7]
        if train_direction != "down":
            if direction == "nextTrainTime":
                direction = "previousTrainTime"
            else:
                direction = "nextTrainTime"
        trainTimesObjectDict = self.get_allTrainTimesForTrainName(self.mm_trainName)
        if trainTimesObjectDict == {}:
            return
        cur_timetag = trainTimesObjectDict.get(self.tt_canvas_cvobject,"")
        if cur_timetag == "":
            return
        if direction == "nextTrainTime":
            next_timetag = ""
            next_objectid = self.tt_canvas_cvobject
            for objectid, timetag in trainTimesObjectDict.items():
                if timetag > cur_timetag:
                    if next_timetag == "":
                        next_timetag = timetag
                        next_objectid = objectid
                    elif next_timetag > timetag:
                        next_timetag = timetag
                        next_objectid = objectid
        elif direction == "previousTrainTime":
            next_timetag = ""
            next_objectid = self.tt_canvas_cvobject
            for objectid, timetag in trainTimesObjectDict.items():
                if timetag < cur_timetag:
                    if next_timetag == "":
                        next_timetag = timetag
                        next_objectid = objectid
                    elif next_timetag < timetag:
                        next_timetag = timetag
                        next_objectid = objectid            
        self.activate_time_entry(next_objectid)
        return    
            
    def get_stationName_from_StopDict(self,stop_dict):
        station_idx = stop_dict.get("StationIdx")
        return self.get_stationName(station_idx)
    
    def determine_first_and_last_stop_idx(self):
        self.trainLineFirstStopIdx = -1
        self.trainIdx = self.get_train_idx_from_Name(self.mm_trainName)
        train = self.schedule_trains_dict.get(self.trainIdx,{})
        search_stops = train.get("Stops",{})
        #search first stop from left:
        for stopIdx,stop_dict in search_stops.items():
            stopstationName = self.get_stationName_from_StopDict(stop_dict)
            for stationIdx in self.schedule_stations_dict:
                station = self.schedule_stations_dict.get(stationIdx,{})
                stationName = station.get("StationName","")                    
                if stationName == stopstationName:
                    if self.trainLineFirstStopIdx == -1:
                        self.trainLineFirstStopIdx = stopIdx
                        self.trainLineFirstStopName = stopstationName
                    self.trainLineLastStopIdx = stopIdx
                    self.trainLineLastStopName = stopstationName
        return 
    
    def edit_train_schedule(self,objectid,mode):
        #print("edit_train_schedule %s %s",objectid,mode,self.tt_canvas.gettags(objectid))
        self.edit_bindings()
        if objectid != -1:
            self.controller.edit_active = True
            self.controller.active_id = objectid
            self.edit_trainline_tag = self.tt_canvas.gettags(objectid)[0]
            self.controller.edit_trainline_tag = self.edit_trainline_tag
            self.edit_trainline_mode = mode
            self.mm_stoptimemode = "DepartTime"
            self.mm_trainName = self.edit_trainline_tag
            self.determine_first_and_last_stop_idx()
            self.mm_stopIdx = self.trainLineFirstStopIdx
            self.mm_stationName = self.trainLineFirstStopName
            self.mm_stop_dict = self.get_trainline_stationidx_data(self.mm_trainName,self.mm_stopIdx)
            try:
                self.tt_canvas.itemconfigure(self.edit_trainline_tag,font=self.largeFont,fill="red")
            except:
                pass
        else:
            self.controller.active_id = -1
            self.edit_trainline_tag = ""
            self.controller.edit_trainline_tag = self.edit_trainline_tag
            self.edit_trainline_mode = mode
            self.mm_stoptimemode = "DepartTime"
            self.mm_trainName = self.edit_trainline_tag
            #self.determine_first_and_last_stop_idx()
            self.mm_stopIdx = 0
            self.mm_stationName = ""
            self.mm_stop_dict = {}

        
    def edit_train_schedule_stop(self):
        #print("edit_train_schedule %s %s",objectid,mode,self.tt_canvas.gettags(objectid))
        self.controller.edit_active = False
        self.controller.active_id = -1
        self.delete_train(self.mm_trainName)
        trainidx = self.get_train_idx_from_Name(self.mm_trainName)
        self.process_train(trainidx)
        self.edit_trainline_tag = ""
        self.controller.edit_trainline_tag = ""
        self.edit_trainline_mode = ""
        #self.edit_unbind()
        
    def edit_stop_original(self,objectid):
        #print("edit_stop_original",self.controller.edit_trainline_tag)
        trainIdx = int(self.tt_canvas.gettags(objectid)[2])
        train_dict = self.schedule_trains_dict.get(trainIdx,{})
        stops_dict = train_dict.get("Stops",{})
        for stopIdx in stops_dict:
            stop_dict = stops_dict.get(stopIdx,{})
            stop_dict["ArriveTime"] =  stop_dict["ArriveTimeOrig"]
            stop_dict["DepartTime"] =  stop_dict["DepartTimeOrig"]
        self.delete_train(self.mm_trainName)
        trainidx = self.get_train_idx_from_Name(self.mm_trainName)
        self.process_train(trainidx)
        self.controller.edit_active = False
        self.controller.active_id = -1
        self.edit_trainline_tag = ""
        self.controller.edit_trainline_tag = ""
        self.edit_trainline_mode = ""
        self.reset_trainline_data_changed_flag(self.trainIdx)
        #self.edit_unbind()
    
    def search_stop_for_betrst(self,train_dict, betrst):
        stops_dict = train_dict.get("Stops",{})
        for stopIdx in stops_dict:
            stop_dict = stops_dict.get(stopIdx,{})
            stationIdx = stop_dict.get("StationIdx",-1)
            stationName = self.get_stationName(stationIdx)
            if stationName == betrst:
                return stop_dict
        return {}
    
    def calculate_updated_time(self,datetime_str,time_delta):
        newtime_str = datetime_str
        if datetime_str != None:
            if time_delta != 0:
                date_str, time_str = datetime_str.split(" ")
                time_min = self.determine_time_value(datetime_str)
                newtime_min = time_min + time_delta
                newtime_str = date_str+" "+ self.determine_time_str(newtime_min)
                return newtime_str
            else:
                return None
        else:
            return None
    
    def update_trn_xml_data(self,FahrplanEintrag_tag, train_dict):
        betrst = FahrplanEintrag_tag.get('Betrst')
        if self.update_trn_old_betrst != betrst:
            self.update_trn_main_entry_found = False
            self.update_trn_old_betrst = betrst
        ank = FahrplanEintrag_tag.get('Ank')
        abf = FahrplanEintrag_tag.get('Abf')
        #print(betrst,ank,abf)
        stop_dict = self.search_stop_for_betrst(train_dict,betrst)
        if stop_dict == {}:
            return
        ArriveTime = stop_dict.get("ArriveTime",0)
        ArriveTimeOrig = stop_dict.get("ArriveTimeOrig",0)
        ArriveTimedelta = ArriveTime - ArriveTimeOrig
        DepartTime = stop_dict.get("DepartTime","")
        DepartTimeOrig = stop_dict.get("DepartTimeOrig","")
        DepartTimedelta = DepartTime - DepartTimeOrig
        if ank != None:
            self.update_trn_main_entry_found = True
            new_ank = self.calculate_updated_time(ank,ArriveTimedelta)
            if new_ank!=None:
                FahrplanEintrag_tag.set("Ank",new_ank)
                self.edit_update_logfile.write(betrst + " Update Ankunft:" + ank + " ==> " + new_ank + "\n")
                stop_dict["ArriveTimeOrig"] = ArriveTime
        if self.update_trn_main_entry_found or (ArriveTime == 0):
            new_abf = self.calculate_updated_time(abf,DepartTimedelta)
        else:
            new_abf = self.calculate_updated_time(abf,ArriveTimedelta)
        if new_abf!=None:
            FahrplanEintrag_tag.set("Abf",new_abf)
            self.edit_update_logfile.write(betrst + " Update Abfahrt:" + abf + " ==> " + new_abf + "\n")
            stop_dict["DepartTimeOrig"] = DepartTime
    
    def edit_export_to_trn(self,objectid):
        trainIdx = int(self.tt_canvas.gettags(objectid)[2])
        self.edit_export_to_trn_via_train_idx(trainIdx)
        
    def edit_export_to_all_trn(self):
        for trainIdx,train_dict in self.schedule_trains_dict.items():
            data = train_dict.get("DataChanged",None)
            if data == "True":
                self.edit_export_to_trn_via_train_idx(trainIdx)

    def edit_export_to_trn_via_train_idx(self, trainIdx):
        train_dict = self.schedule_trains_dict.get(trainIdx,{})
        trn_filepathname = train_dict.get("trn_filename","")
        trn_tree = ET.parse(trn_filepathname)
        trn_tree.write(trn_filepathname+".bak",encoding="UTF-8",xml_declaration=True)
        trn_root = trn_tree.getroot()
        with open(trn_filepathname+".update.log", 'w', encoding='utf-8') as self.edit_update_logfile:
            self.edit_update_logfile.write(trn_filepathname+"\n")
            self.update_trn_old_betrst = ""
            for FahrplanEintrag_tag in trn_root.findall('Zug/FahrplanEintrag'):
                self.update_trn_xml_data(FahrplanEintrag_tag,train_dict)
        trn_tree.write(trn_filepathname,encoding="UTF-8",xml_declaration=True)
        self.controller.set_statusmessage("Änderungen in exportiert in Datei: "+trn_filepathname)
        self.reset_trainline_data_changed_flag(trainIdx)
        
    def edit_clone_schedule(self,objectid):
        #print("edit_clone_schedule",self.controller.edit_trainline_tag)
        trainIdx = int(self.tt_canvas.gettags(objectid)[2])
        train_dict = self.schedule_trains_dict.get(trainIdx,{})
        trn_filepathname = train_dict.get("trn_filename","")
        
        self.popwin = popup_win_clone(self,self.controller,trn_filepathname)
        
        pass
    
    def edit_run_schedule(self,objectid):
        trainIdx = int(self.tt_canvas.gettags(objectid)[2])
        train_dict = self.schedule_trains_dict.get(trainIdx,{})
        trn_filepathname = train_dict.get("trn_filename","")
        if trn_filepathname != "":
            
            os.startfile(trn_filepathname)

class Timetable_main(Frame):

    def __init__(self,controller,canvas,parent):
        super().__init__()
        self.ttpage = parent
        self.controller = controller
        self.zusi_master_timetable_dict = {}
        self.canvas = canvas
        self.canvas_width = self.controller.getConfigData("Bfp_width")
        self.canvas_height = self.controller.getConfigData("Bfp_height")
        self.fpl_filename = self.controller.getConfigData("Bfp_filename")
        self.xml_filename = self.controller.getConfigData("Bfp_trainfilename")
        self.starthour = self.controller.getConfigData("Bfp_start")
        self.duration = self.controller.getConfigData("Bfp_duration")
        
    def edit_train_schedule(self,objectid,mode):
        self.timetable.edit_train_schedule(objectid,mode)
        
    def edit_stop_original(self,objectid):
        self.timetable.edit_stop_original(objectid)
           
    def edit_export_to_trn(self,objectid):
        self.timetable.edit_export_to_trn(objectid)
        
    def edit_export_to_all_trn(self):
        self.timetable.edit_export_to_all_trn()    
        
    def edit_run_schedule(self,objectid):
        self.timetable.edit_run_schedule(objectid)    
                
    def edit_clone_schedule(self,objectid):
        self.timetable.edit_clone_schedule(objectid)
        
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
                tt_xml__filepathname = os.path.join(trn_filepath,timetable_filecomp[-2],timetable_filecomp[-1])
            else:
                asc_zugGattung = zugGattung.replace("Ü","Ue").replace("ü","ue").replace("Ä","Ae").replace("ä","ae").replace("Ö","Oe").replace("ö","oe")
                trn_filecomp = trn_filepathname.split("\\")
                tt_xml__filepathname = os.path.join(trn_filepath,trn_filecomp[-2],asc_zugGattung+zugNummer+".timetable.xml")                
                if not os.path.exists(tt_xml__filepathname):
                    logging.info("Kein BuchfahrplanRohDatei Element gefunden %s%s %s", zugGattung,zugNummer,trn_filepath)
                    self.controller.set_statusmessage("Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath)
                    return             
            with open(tt_xml__filepathname,mode="r",encoding="utf-8") as fd:
                xml_text = fd.read()
                tt_xml_timetable_dict = parse(xml_text)
                #enter train-timetable
                result_ok = self.timetable.convert_tt_xml_dict_to_schedule_dict(tt_xml_timetable_dict)
        else:
            self.timetable.convert_trn_dict_to_schedule_dict(trn_zug_dict,trn_filepathname=trn_filepathname)        

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
            # integrated fpl file
            self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+fpn_filename)
            for trn_zug_dict in fahrplan_dict.get("trn",{}):
                self.open_zusi_trn_zug_dict(trn_zug_dict, fpn_filename)
                self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+fpn_filename)
        else:
            for zug in zug_list:
                try:
                    datei_dict = zug.get("Datei")
                except (AttributeError, TypeError):
                    datei_dict = zug_list.get("Datei")
                trn_filename = datei_dict.get("@Dateiname")
                trn_filename_comp = trn_filename.split("\\")
                trn_file_and_path = os.path.join(fpl_path,trn_filename_comp[-2],trn_filename_comp[-1])
                self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+trn_file_and_path)
                self.controller.update()
                self.open_zusi_trn_file(trn_file_and_path,fpn_filename)
        self.controller.set_statusmessage(" ")
        return True
    
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
    
    def xx_get_station_list_from_tt_xml_file(self,xml_filename):
        stationName_list = []
        with open(xml_filename,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            xml_timetable_dict = parse(xml_text)
            #enter train-timetable
            Zusi_dict = xml_timetable_dict.get("Zusi")
            Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan",{})
            if Buchfahrplan_dict=={}:
                return False
            #kmStart = float(Buchfahrplan_dict.get("@kmStart","0.00"))
            Datei_trn_dict = Buchfahrplan_dict.get("Datei_trn",{})
            if Datei_trn_dict == {}:
                return False
            trn_dateiname = Datei_trn_dict.get("@Dateiname","")
            
            FplRglGgl_str = self.controller.getConfigData("FplRglGgl")
            if FplRglGgl_str =="":
                FplRglGgl_str = "1,2"
            self.FplRglGgl = FplRglGgl_str.split(",")

            FplZeile_list = Buchfahrplan_dict.get("FplZeile",{})
            if FplZeile_list=={}:
                logging.info("timetable.xml file error: %s",trn_dateiname )
                self.controller.set_statusmessage("Error: ZUSI entry not found in fpl-file: "+trn_dateiname)            
                return False
            for FplZeile_dict in FplZeile_list:
                try:
                    FplRglGgl=FplZeile_dict.get("@FplRglGgl","")
                except:
                    print("Error:",repr(FplZeile_dict))
                    if not (FplRglGgl in self.FplRglGgl):
                        continue # keine Umwege über Gegengleis
                try:
                    FplAbf = self.get_fplZeile_entry(FplZeile_dict, "FplAbf","@Abf")
                    if FplAbf == "":
                        continue # only use station with "Abf"-Entry
                    FplName = self.get_fplZeile_entry(FplZeile_dict,"FplName","@FplNameText",default="")
                    if FplName == "":
                        continue
                    else:
                        stationName_list.append(FplName)
                except BaseException as e:
                    logging.debug("FplZeile conversion Error %s",trn_dateiname+"-"+repr(FplZeile_dict),e)
                    continue # entry format wrong
        

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
        #print('Input File, %s.' % fpn_filename)
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
                try:
                    datei_dict = zug.get("Datei")
                except (AttributeError, TypeError):
                    datei_dict = zug_list.get("Datei")
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
        #print(repr(self.zusi_zuglist_dict))
        zusi_zug_list_main_dict={}
        zusi_zug_list_main_dict["Trainlist"]=self.zusi_zuglist_dict
        zusi_zug_list_main_dict["XML_Filenamelist"]=self.zusi_zuglist_xmlfilename_dict
        #self.timetable.set_zuggattung_to_color(self.traintype_to_color_dict)
        return zusi_zug_list_main_dict

    def xx_resize_canvas(self,width,height,starthour,duration):
        self.canvas.delete("all")
        self.canvas.update()
        self.canvas.config(width=width,height=height,scrollregion=(0,0,width,height))
        self.timetable.set_tt_traintype_prop(self.main_traintype_prop_dict)
        self.editflag = self.controller.getConfigData("Edit_Permission") in ("Edit_allowed","Fast_Edit_allowed")
        self.fast_editflag = self.controller.getConfigData("Edit_Permission") == "Fast_Edit_allowed"
        self.timetable.doPaint(self.canvas,starthour=starthour,duration=duration)
        if self.editflag:
            self.edit_train_schedule(-1,"single")
    
    def regenerate_canvas(self):
        #first_call = True
        if not self.ttpage.canvas_init:
            #self.canvas.delete("all")
            self.canvas.destroy()
            self.canvas = self.ttpage.create_canvas()
            self.controller.tooltip_var_dict={}
        self.ttpage.canvas_init = False
        self.controller.total_scalefactor = 1
        self.canvas.config(width=self.canvas_width,height=self.canvas_height,scrollregion=(0,0,self.canvas_width,self.canvas_height))
        self.canvas.update()
        self.controller.set_statusmessage("Erzeuge Bahnhofsliste - "+self.xml_filename)
        self.controller.update()
        #print('Input File master train timetable, %s.' % xml_filename)
        with open(self.xml_filename,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            zusi_timetable_dict = parse(xml_text)
        self.timetable = TimeTableGraphCommon(self.controller, True, self.height, self.width,xml_filename=self.xml_filename,ttmain_page=self,tt_page=self.ttpage)
        self.timetable.set_tt_traintype_prop(self.main_traintype_prop_dict)
        #define stops via selected train-timetable
        result_ok = self.timetable.convert_tt_xml_dict_to_schedule_dict(zusi_timetable_dict,define_stations=True)
        if  not result_ok:
            return
        result_ok = self.open_zusi_master_schedule(fpn_filename=self.fpl_filename)
        if not result_ok:
            return
        self.editflag = self.controller.getConfigData("Edit_Permission") in ("Edit_allowed","Fast_Edit_allowed")
        self.fast_editflag = self.controller.getConfigData("Edit_Permission") == "Fast_Edit_allowed"
        self.timetable.doPaint(self.canvas,starthour=self.starthour,duration=self.duration)
        if self.editflag:
            self.edit_train_schedule(-1,"single")        

    def redo_fpl_and_canvas(self,width,height, starthour=8, duration=9,fpl_filename="", xml_filename = ""):
        self.fpl_filename = fpl_filename
        self.xml_filename = xml_filename
        self.width = width
        self.height = height
        self.starthour = starthour
        self.duration = duration
        self.regenerate_canvas()
        return

    def set_traintype_prop(self,traintype_prop_dict):
        self.main_traintype_prop_dict = traintype_prop_dict