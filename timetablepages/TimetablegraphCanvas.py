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
from timetablepages.DefaultConstants import LARGE_STD_FONT,XML_ERROR_LOG_FILENAME
from timetablepages.ZUSI_fpn_class import ZUSI_fpn
import os
import logging
import math
import xml.etree.ElementTree as ET
import os
from timetablepages.PopupWinClone import popup_win_clone
from logging import FileHandler
from logging import Formatter
import inspect

LOG_FORMAT = (
            "%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d")
LOG_LEVEL = logging.DEBUG

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
        if self.master.editflag:
            self.right_click_menu.add_command(label="Zeiten zurück auf .trn Zeiten setzen", command=self.edit_stop_original)
            self.right_click_menu.add_separator()
            self.right_click_menu.add_command(label="Zugfahrplan in .trn-Datei exportieren", command=self.edit_export_to_trn)
            self.right_click_menu.add_separator()
            self.right_click_menu.add_command(label="Zugfahrplan klonen", command=self.edit_clone_schedule) #,state="disabled")            
            self.right_click_menu.add_separator()
        if self.master.controller.ZUSI_monitoring_started:
            #self.right_click_menu.add_command(label="Mit ZUSI Server verbinden", command=self.edit_connect_ZUSI)
            #self.right_click_menu.add_command(label="Von ZUSI Server trennen", command=self.edit_disconnect_ZUSI)    
            self.right_click_menu.add_command(label="Zug in ZUSI starten (mit Fahrplanneustart)", command=self.edit_run_schedule)
            self.right_click_menu.add_separator()
        if self.master.controller.edit_TrainNamePos:    
            self.right_click_menu.add_command(label="Zugnummer in diesem Segment anzeigen", command=self.show_trainNum_here)       
        

    def popup_text(self,event,cvobject):
        if not self.master.editflag and not self.master.controller.ZUSI_monitoring_started and not self.master.controller.edit_TrainNamePos:
            return
        self.objectid = cvobject
        self.event = event
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
        self.master.edit_run_schedule(self.objectid,restart_fpn=True)
        
    def edit_run_schedule2(self):
        #print("edit_stop")
        self.master.edit_run_schedule(self.objectid,restart_fpn=False)
        
    def show_trainNum_here(self):
        #print("edit_stop")
        #print("show_trainNum_here",self.objectid,repr(self.event))
        self.master.show_trainNum_here(self.objectid,self.event)
        
    def edit_connect_ZUSI(self):
        #print("edit_stop")
        self.master.edit_connect_ZUSI(self.objectid)
        
    def edit_disconnect_ZUSI(self):
        #print("edit_stop")
        self.master.edit_disconnect_ZUSI(self.objectid)
        
class RightClickMenu_TrainName(tk.Frame):   
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
        self.right_click_menu.add_command(label="Zugnummer entfernen", command=self.edit_remove_trainnum)

    def popup_text(self,event,cvobject):
        if not self.master.controller.edit_TrainNamePos:
            return        
        self.objectid = cvobject
        self.event = event
        self.right_click_menu.post(event.x_root, event.y_root)
            
    def destroy_menu(self, event):
        self.right_click_menu.destroy()

    def edit_remove_trainnum(self):
        #print("edit_stop")
        self.master.edit_remove_trainnum(self.objectid)

class TimeTableGraphCommon():
    def __init__(self, controller, showTrainTimes, height, width, xml_filename="",fpn_filename="",ttmain_page=None,tt_page=None):
        self.controller = controller
        self.ttmain_page = ttmain_page
        self.ttpage = tt_page
        self.xml_filename = xml_filename
        self.fpn_filename = fpn_filename
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
        self.schedule_stations_list = []
        self.schedule_trains_dict = self.schedule_dict.get("Trains",{}) 
        self.FPL_starttime = -1
        self.FPL_endtime = -1
        self.schedule_trainIdx_write_next = 0
        self.canvas_dimHeight = height
        self.canvas_dimWidth  = width
        self.bigFont = font.Font(family="SANS_SERIF", size=20)
        self.largeFont = font.Font(family="SANS_SERIF", size=12)
        self.stdFont = font.Font(family="SANS_SERIF", size=10)
        self.smallFont = font.Font(family="SANS_SERIF", size=8)
        self.controller.allow_TRN_files = self.controller.getConfigData("SCP_AllowTRN",default="")
        self.controller.showalltrains = self.controller.getConfigData("Bfp_Showalltrains",default=False)
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
        self.monitor_start = False
        self.monitor_timetable_updated = False
        self.monitor_distance_of_first_station = 0
        self.monitor_distance_of_last_station = 0
        self.monitor_curr_train_distance_to_first_station = 0
        self.monitor_curr_train_direction_of_travel = ""
        self.monitor_tooltiptext = ""
        self.pendelstations = []
        
        # xml_error_logger logger
        xml_logfilename = os.path.join(self.controller.userfile_dir, XML_ERROR_LOG_FILENAME)
        self.xml_error_logger = logging.getLogger("XML_Error")
        self.xml_error_logger.setLevel(LOG_LEVEL)
        self.xml_error_logger_file_handler = FileHandler(xml_logfilename)
        self.xml_error_logger_file_handler.setLevel(LOG_LEVEL)
        self.xml_error_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))
        self.xml_error_logger.addHandler(self.xml_error_logger_file_handler)        
        
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
    
    def bind_right_click_menu_to_trainname(self, trainnameid):
        self.popup_TN = RightClickMenu_TrainName(self.ttmain_page, trainnameid)
        self.tt_canvas.tag_bind(trainnameid,"<Button-3>",lambda e,Object=trainnameid:self.popup_TN.popup_text(e,Object))
        self.tt_canvas.bind("<Destroy>",self.popup_TN.destroy_menu,add="+")

    def set_tt_traintype_prop(self,traintype_prop_dict):
        self.canvas_traintype_prop_dict = traintype_prop_dict.copy()
        
    def determine_headersize(self):
        if self.draw_stations_vertical: 
            return 140
        s_labelsize=self.controller.getConfigData("Bfp_S_LineLabelSize",default="")
        s_labeldir=self.controller.getConfigData("Bfp_S_LineLabelDir_No",default="")
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

    def doPaint (self,canvas,starthour=12,duration=7,timeauto=False):
        if timeauto==True:
            starthour = self.FPL_starttime
            duration = self.FPL_endtime-self.FPL_starttime+1

        if len(self.schedule_stations_dict) == 0:
            logging.debug("Error - no stations in list")
            return
        TLDirection = self.controller.getConfigData("TLDirection",default="")
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
        self.TrainMinuteSize = self.controller.getConfigData("Bfp_TrainMinuteSize",default="")
        self.TrainMinuteFont = font.Font(family="SANS_SERIF", size=int(self.TrainMinuteSize))
        self.TrainMinuteShow = self.TrainMinuteSize > 0
        self.InOutBoundTrainsShow = self.controller.getConfigData("InOutBoundTrainsShow",default="")
        self.InOutBoundTrainsNoOneStop = self.controller.getConfigData("InOutBoundTrainsNoOneStop",default="")
        self.InOutBoundTrainsNoStartStation = self.controller.getConfigData("InOutBoundTrainsNoStartStation",default="")
        self.InOutBoundTrainsNoEndStation = self.controller.getConfigData("InOutBoundTrainsNoEndStation",default="")
        self.InOutBoundTrainsShowMinutes = self.controller.getConfigData("InOutBoundTrainsShowMinutes",default="")
        self.startstationName = self.schedule_stations_dict[0]["StationName"]
        self.stationsCntMax = len(self.schedule_stations_dict)-1
        self.endstationName = self.schedule_stations_dict[self.stationsCntMax]["StationName"]
        self.showTrainDir = self.controller.getConfigData("Bfp_show_train_dir")
        self.trainLineFirstStationIdx = -1
        self.trainLineLastStationIdx = 0
        self.tt_canvas_cvobject_rect = -1
        self.monitor_start = True
        self.monitor_currdist = 0
        self.monitor_currkm = 0
        self.monitor_time = 0
        self.monitor_currspeed = 0
        self.controller.ZUSI_monitoring_started = self.controller.getConfigData("Monitoring_Checkbutton",default="")
        self.controller.edit_TrainNamePos = self.controller.getConfigData("TrainNamePos_Checkbutton",default="")
        self.monitor_curr_trainline_objectid = -1
        self.monitor_curr_timeline_objectid = -1
        self.monitor_start_time = 0
        self.monitor_panel_con_status_objectid = -1
        self.monitor_panel_currfpn_objectid  = -1
        self.station_delta_table = {}
        
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
        self.drawstation_tracks()
        self.edit_panel_currtime_objectid = -1
        self.edit_panel_stationName_objectid = -1
        self.edit_panel_trainName_objectid = -1
        self.print_edit_panel()
        self.controller.timetable_activ = True
        
    def determine_station_delta(self, stop, time):
        delta = self.controller.getConfigData("Bfp_TrainLine_Distance_from_Stationline",default=0)
        signal_str = stop.get("Signal","")
        self.signal = signal_str
        self.signal_txt=""
        if signal_str == "" or signal_str==None:
            return delta
        signal_list = signal_str.split("-")
        if len(signal_list)>1:
            signal = signal_list[1]
        else:
            signal = signal_list[0]
        self.signal_txt = signal
        station_idx = stop.get("StationIdx",0)

        search_str = str(station_idx)+self.direction 
        signal_list = self.station_delta_table.get(search_str,[])
        if signal in signal_list:
            delta_factor = signal_list.index(signal)+1
        else:
            signal_list.append(signal)
            self.station_delta_table[search_str] = signal_list
            delta_factor=len(signal_list)
        delta_update=delta_factor*delta
        return delta_update

    def determine_xy_point(self, stop, time):
        delta=0 # self.determine_station_delta(stop, time)
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
    
    def determine_xy_point_with_delta(self, stop, time):
        delta=self.determine_station_delta(stop, time)
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
    
    def print_station(self, stationIdx, stationName, distance, stationkm,neukm=0,FplRglGgl=""):
        if self.trainLineFirstStationIdx == -1:
            self.trainLineFirstStationIdx = stationIdx
        self.trainLineLastStationIdx = stationIdx
        s_labelsize=self.controller.getConfigData("Bfp_S_LineLabelSize",default="10")
        s_labeldir=self.controller.getConfigData("Bfp_S_LineLabelDir_No",default=0)
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
                    
            # draw trackline (1 or 2 tracks)
    
            tl_color=self.controller.getConfigData("Bfp_TL_LineColor",default="#ff8000")
            tl_width=self.controller.getConfigData("Bfp_TL_LineWidth",default=2)
            tl_linedashed=self.controller.getConfigData("Bfp_TL_LineDashed",default="")
            if self.last_station_x>0:
                yline1=y-5
                yline2=y
                if tl_linedashed !="no line":
                    objid = self.tt_canvas.create_line(self.last_station_x, yline1, x, yline1, width=tl_width, fill=tl_color,dash=tl_linedashed)
                    if FplRglGgl != "1": # line has 2nd track
                        objid = self.tt_canvas.create_line(self.last_station_x, yline2, x, yline2, width=tl_width, fill=tl_color,dash=tl_linedashed)
            self.last_station_x = x
            
            yKm = y + 12
            km_str = str(f"{stationkm:.1f}")
            if neukm != 0:
                km_str = km_str +"\n"+ str(f"{abs(neukm):.1f}")
            
            #km_str = km_str + "("+ FplRglGgl +")"
            km_obj=self.tt_canvas.create_text(x, yKm, text=km_str, anchor="center",font=self.s_font,tags=("Station",stationName))
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
        th_labelsize=self.controller.getConfigData("Bfp_TH_LineLabelSize",default="10")
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
        self.edit_panel_currtime_objectid = self.tt_canvas.create_text(self.graphRight-10, 20, text = self.mm_currtime_str, font=LARGE_STD_FONT,anchor="c",fill="black",tags="PanelCurrTime")
        self.edit_panel_stoptimemode_objectid = self.tt_canvas.create_text(self.graphRight-80, 20, text = self.translate_dict.get(self.mm_stoptimemode,""), font=LARGE_STD_FONT,anchor="e",fill="black",tags="PanelCurrTime")
        self.edit_panel_trainName_objectid = self.tt_canvas.create_text(self.graphRight-200, 20, text = self.mm_trainName, font=LARGE_STD_FONT,anchor="e",fill="black",tags="PanelTrainName")
        self.edit_panel_stationName_objectid = self.tt_canvas.create_text(self.graphRight-400, 20, text = self.mm_stationName, font=LARGE_STD_FONT, anchor="e",fill="black",tags="PanelStationName")
        
    def update_edit_panel (self):
        self.tt_canvas.itemconfigure(self.edit_panel_trainName_objectid, text = self.mm_trainName)
        self.tt_canvas.itemconfigure(self.edit_panel_stoptimemode_objectid, text = self.translate_dict[self.mm_stoptimemode])
        self.tt_canvas.itemconfigure(self.edit_panel_stationName_objectid, text = self.mm_stationName)
        self.tt_canvas.itemconfigure(self.edit_panel_currtime_objectid, text = self.mm_currtime_str)
        
    def print_monitor_panel(self):
        if self.monitor_panel_con_status_objectid !=-1:
            self.update_monitor_panel()
        else:
            self.tt_canvas.create_text(1000, 10, text="ZUSI Simulator", font=self.bigFont, anchor="nw")
            self.monitor_panel_con_status_objectid = self.tt_canvas.create_text(1200, 10, text="(Nicht Verbunden)", font=self.stdFont, anchor="nw")
            self.tt_canvas.create_text(1000, 55, text = "Uhrzeit:", font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrTime")
            self.tt_canvas.create_text(1200, 55, text = "KM:", font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrKm")
            self.tt_canvas.create_text(1400, 55, text = "Geschwindigkeit:", font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrSpeed")        
            self.monitor_panel_currtime_objectid = self.tt_canvas.create_text(1100, 55, text = self.monitor_currtime_str, font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrTime")
            self.monitor_panel_currkm_objectid = self.tt_canvas.create_text(1250, 55, text = self.monitor_currkm_str, font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrKm")
            self.monitor_panel_currspeed_objectid = self.tt_canvas.create_text(1500, 55, text = self.monitor_currspeed_str, font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrSpeed")
            #self.monitor_panel_currdist_objectid = self.tt_canvas.create_text(1350, 55, text = self.monitor_currdist_str, font=LARGE_STD_FONT,anchor="e",fill="black",tags="MonitorCurrDist")
         
    def print_monitor_status_panel(self):
        if self.monitor_panel_currfpn_objectid  !=-1:
            self.update_monitor_status_panel()
        else:
            self.tt_canvas.create_text(1000, 40, text = "ZugFahrplan:", font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrTime")
            #self.tt_canvas.create_text(1000, 70, text = "Zugnummer:", font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrKm")
            #self.tt_canvas.create_text(1000, 85, text = "Status:", font=self.stdFont,anchor="nw",fill="black",tags="MonitorCurrSpeed")        
            self.monitor_panel_currfpn_objectid = self.tt_canvas.create_text(1100, 40, text = self.monitor_fpn_filepathname, font=self.stdFont,anchor="nw",fill="black",tags="MonitorFpn")
            #self.monitor_panel_currtrainNum_objectid = self.tt_canvas.create_text(1100, 70, text = self.monitor_trainNumber, font=self.stdFont,anchor="nw",fill="black",tags="MonitorTrainNumber")
            #if self.monitor_ladepause:
            #    self.monitor_panel_currladestatus_objectid = self.tt_canvas.create_text(1100,85, text = "Status: Ladepause", font=self.stdFont,anchor="nw",fill="black",tags="MonitorStatus")
            #else:
            #    self.monitor_panel_currladestatus_objectid = self.tt_canvas.create_text(1100,85, text = "Status: Geladen", font=self.stdFont,anchor="nw",fill="black",tags="MonitorStatus")
        
    def update_monitor_panel (self):
        self.tt_canvas.itemconfigure(self.monitor_panel_currtime_objectid,text = self.monitor_currtime_str)
        self.tt_canvas.itemconfigure(self.monitor_panel_currkm_objectid, text = self.monitor_currkm_str)
        self.tt_canvas.itemconfigure(self.monitor_panel_currspeed_objectid, text = self.monitor_currspeed_str)
        #self.tt_canvas.itemconfigure(self.monitor_panel_currdist_objectid, text = self.monitor_currdist_str)
            
    def update_monitor_status_panel (self):
        self.tt_canvas.itemconfigure(self.monitor_panel_currfpn_objectid, text = self.monitor_fpn_filepathname)
        #self.tt_canvas.itemconfigure(self.monitor_panel_currtrainNum_objectid, text = self.monitor_trainNumber)
        #if self.monitor_ladepause:
        #    self.tt_canvas.itemconfigure(self.monitor_panel_currladestatus_objectid, text = "Status: Ladepause")
        #else:
        #    self.tt_canvas.itemconfigure(self.monitor_panel_currladestatus_objectid, text = "Status: Geladen")
    
    def update_monitor_conn_status_panel (self):
        if self.tt_canvas:
            if self.monitor_conn_status == "Connected":
                self.tt_canvas.itemconfigure(self.monitor_panel_con_status_objectid , text = "Verbunden", fill="green")
            elif self.monitor_conn_status == "Not Connected":
                self.tt_canvas.itemconfigure(self.monitor_panel_con_status_objectid , text = "Nicht Verbunden", fill="red" )
            elif self.monitor_conn_status == "Connecting":
                self.tt_canvas.itemconfigure(self.monitor_panel_con_status_objectid , text = "Verbindungsaufbau", fill="yellow")
            else:
                self.tt_canvas.itemconfigure(self.monitor_panel_con_status_objectid , text = "Zusi sendet keine Daten (mehr)", fill="orange")
            
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
        self.tt_canvas.create_text(10, 70, text="Zugfahrplandateien:"+ self.controller.getConfigData("TLFileType",default=""), font=self.stdFont, anchor="nw");

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
            zfs_id_str=self.controller.getConfigData("Bfp_ZFS_Id",default="")
            zfs_id_str = zfs_id_str.replace(" ","")
            if zfs_id_str =="":
                self.zfs_id_list=[]
            else:
                self.zfs_id_list = zfs_id_str.split(",")
            self.last_station_x = 0
            for stationIdx in self.schedule_stations_dict:
                station = self.schedule_stations_dict.get(stationIdx,{})
                stationName = station.get("StationName","")
                stationkm = station.get("StationKm",0.00)
                neukm = station.get("Neukm",0)
                distance = station.get("Distance",0.00)
                FplRglGgl = station.get("FplRglGgl","")
                if stationkm == None:
                    print("Error: Stationkm = None - ",stationName)
                    stationkm = 0
                #stationName = stationName# + " (km "+str(f"{stationkm:.2f}")+")"
                stationType_ZFS=self.check_stationtypeZFS(stationName)
                self.stationTypeZFS_list.append(stationType_ZFS)
                self.print_station(stationIdx, stationName, distance, stationkm,neukm=neukm,FplRglGgl=FplRglGgl)

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
                
    def get_line_properties(self,line_code):
        line_prop={}
        line_prop["Color"]=self.controller.getConfigData(line_code+"_LineColor",default="")
        line_prop["Width"]=self.controller.getConfigData(line_code+"_LineWidth",default="")
        line_prop["Dashed"]=self.controller.getConfigData(line_code+"_LineDashed",default="")
        return line_prop
    
    def monitor_create_line(self,point_list,line_prop):
        if line_prop["Dashed"]!="no line":
            train_line_objid = self.tt_canvas.create_line(point_list, width=line_prop["Width"], fill=line_prop["Color"],activewidth=line_prop["Width"]*2,dash=line_prop["Dashed"],tags=(self.trainName,"M_"+self.trainName,str(self.trainIdx)))
            #train_line_objid = self.tt_canvas.create_line(self.trainLine_dict,fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,dash=self.TrainLineDashed,tags=(self.trainName,"L_"+self.trainName,str(self.trainIdx)))
            self.controller.ToolTip_canvas(self.tt_canvas, train_line_objid, text=self.monitor_tooltiptext, button_1=True)            
        else:
            train_line_objid = -1
        return train_line_objid

    def drawGraphGrid(self):
        # Print the graph box
        self.tt_canvas.create_rectangle(self.graphLeft, self.graphTop, self.graphLeft+self.graphWidth, self.graphTop + self.graphHeight)
        # Print the grid lines
        s_color=self.controller.getConfigData("Bfp_S_LineColor",default="")
        s_width=self.controller.getConfigData("Bfp_S_LineWidth",default="")
        s_linedashed=self.controller.getConfigData("Bfp_S_LineDashed",default="")
        zfs_color=self.controller.getConfigData("Bfp_ZFS_LineColor",default="")
        zfs_width=self.controller.getConfigData("Bfp_ZFS_LineWidth",default="")
        zfs_linedashed=self.controller.getConfigData("Bfp_ZFS_LineDashed",default="")
        th_color=self.controller.getConfigData("Bfp_TH_LineColor",default="")
        th_width=self.controller.getConfigData("Bfp_TH_LineWidth",default="")
        th_linedashed=self.controller.getConfigData("Bfp_TH_LineDashed",default="")
        tm_color=self.controller.getConfigData("Bfp_TM_LineColor",default="")
        tm_width=self.controller.getConfigData("Bfp_TM_LineWidth",default="")
        tm_linedashed=self.controller.getConfigData("Bfp_TM_LineDashed",default="")
        tm_distance=int(self.controller.getConfigData("Bfp_TM_LineDistance",default=""))
        if self.draw_stations_vertical:
            for stationidx,y in self.stationGrid.items():
                if self.stationTypeZFS_list[stationidx]:
                    if zfs_linedashed !="no line":
                        objid = self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=zfs_width, fill=zfs_color,dash=zfs_linedashed,tag="Grid")
                else:
                    if s_linedashed !="no line":
                        objid = self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=s_width, fill=s_color,dash=s_linedashed,tag="Grid")
                self.controller.ToolTip_canvas(self.tt_canvas, objid, text="Station: "+self.get_stationName(stationidx),button_1=True)
            for x in self.hourGrid:
                if th_linedashed !="no line":
                    self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=th_width, fill=th_color,dash=th_linedashed,tag="Grid")
                if tm_width > 0 and x != self.hourGrid[-1]:
                    number_of_min_lines = int(60/tm_distance)-1
                    distance_per_line = tm_distance * self.hourWidth/60
                    for min_line in range(0,number_of_min_lines):
                        if tm_linedashed !="no line":
                            self.tt_canvas.create_line(x+distance_per_line*(min_line+1), self.graphTop, x+distance_per_line*(min_line+1), self.graphBottom, width=tm_width, fill=tm_color,dash=tm_linedashed,tag="Grid")
        else:
            for y in self.hourGrid:
                if th_linedashed  !="no line":
                    self.tt_canvas.create_line(self.graphLeft, y, self.graphRight, y, width=th_width, fill=th_color,dash=th_linedashed,tag="Grid")
                if tm_width > 0 and y != self.hourGrid[-1]:
                    number_of_min_lines = int(60/tm_distance)-1
                    distance_per_line = tm_distance * self.hourWidth/60
                    for min_line in range(0,number_of_min_lines):
                        if tm_linedashed !="no line":
                            self.tt_canvas.create_line(self.graphLeft, y+distance_per_line*(min_line+1), self.graphRight, y+distance_per_line*(min_line+1), width=tm_width, fill=tm_color,dash=tm_linedashed,tag="Grid")
                        
            for stationidx,x in self.stationGrid.items():
                if self.stationTypeZFS_list[stationidx]:
                    if zfs_linedashed  !="no line":
                        objid = self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=zfs_width, fill=zfs_color,dash=zfs_linedashed,tag="Grid")
                else:
                    if s_linedashed  !="no line":
                        objid = self.tt_canvas.create_line(x, self.graphTop, x, self.graphBottom, width=s_width, fill=s_color,dash=s_linedashed,tag="Grid")
                    self.controller.ToolTip_canvas(self.tt_canvas, objid, text="Station: "+self.get_stationName(stationidx),button_1=True)
        #self.tt_canvas.tag_lower("Grid","Station")
        
    def drawstation_tracks(self):
        delta = self.controller.getConfigData("Bfp_TrainLine_Distance_from_Stationline",default=0)
        if delta>0:
            s_color=self.controller.getConfigData("Bfp_ST_LineColor",default="")
            s_width=self.controller.getConfigData("Bfp_ST_LineWidth",default="")
            s_linedashed=self.controller.getConfigData("Bfp_ST_LineDashed",default="")
            if s_linedashed !="no line":
                self.controller.set_statusmessage("Erzeuge Gleisbelegungsanzeige")
                self.controller.update()
                if self.draw_stations_vertical:
                    for station_idx,y in self.stationGrid.items():
                        for direction in ["up","down"]:
                            search_str = str(station_idx)+direction
                            signal_list = self.station_delta_table.get(search_str,[])
                            for signal in signal_list:
                                delta_factor = signal_list.index(signal)+1
                                delta_update=delta_factor*delta                    
                                objid = self.tt_canvas.create_line(self.graphLeft, y+delta_update, self.graphRight, y+delta_update, width=s_width, activewidth=s_width*2,fill=s_color,dash=s_linedashed,tag="Grid")
                                self.controller.ToolTip_canvas(self.tt_canvas, objid, text="Station: "+self.get_stationName(station_idx)+"\nSignal:"+signal,button_1=True)
                else:
                    for station_idx,x in self.stationGrid.items():
                        for direction in ["up","down"]:
                            search_str = str(station_idx)+direction
                            signal_list = self.station_delta_table.get(search_str,[])
                            for signal in signal_list:
                                delta_factor = signal_list.index(signal)+1
                                delta_update=delta_factor*delta
                                if direction == "down":
                                    x_update = x+delta_update
                                else:
                                    x_update = x-delta_update
                                objid = self.tt_canvas.create_line(x_update, self.graphTop, x_update, self.graphBottom, width=s_width, activewidth=s_width*2, fill=s_color,dash=s_linedashed,tag="Grid")
                                self.controller.ToolTip_canvas(self.tt_canvas, objid, text="Station: "+self.get_stationName(station_idx)+"\nSignal:"+signal,button_1=True)
                self.tt_canvas.tag_lower("Grid","Station")
                self.controller.set_statusmessage("")
                self.controller.update()                

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
        #self.controller.set_statusmessage("") 
        
    def format_PrintTrainNumber(self,number_str):
        if self.controller.getConfigData("SO_remove_leading_Zero"):
            for i in range(0,len(number_str)):
                if number_str[0] == "0":
                    number_str=number_str[1:]
                else:
                    break
        if self.controller.getConfigData("SO_TN_add_blank"):
            number_str = " "+number_str
        return number_str
    
    def determine_trainNameLabel_indiv_pos_stops(self,trainName):
        if not self.controller.edit_TrainNamePos:
            return []            
        config_trainNameLabel_prop_dict = self.controller.getConfigData("TrainNamePosProp")
        if config_trainNameLabel_prop_dict:
            # search for complete name
            for i,value_dict in config_trainNameLabel_prop_dict.items():
                #print(repr(value_dict))
                trainNames = value_dict.get("TrainNamePos_Names","")
                if trainNames == "":
                    continue                
                trainNameslist = trainNames.split(",")
                if trainName in trainNameslist:
                    lablestop_list_str = value_dict.get("TrainNamePos_Stops","")
                    lablestop_list = lablestop_list_str.split(",")
                    return lablestop_list
            for i,value_dict in config_trainNameLabel_prop_dict.items():
                #print(repr(value_dict))
                trainNames = value_dict.get("TrainNamePos_Names","")
                if trainNames == "":
                    continue
                trainNameslist = trainNames.split(",")
                for testName in trainNameslist:
                    if trainName.startswith(testName):
                        lablestop_list_str = value_dict.get("TrainNamePos_Stops","")
                        lablestop_list = lablestop_list_str.split(",")
                        return lablestop_list            
        return []

    def process_train(self,trainidx):
        self.tt_canvas.update()
        train_dict = self.schedule_trains_dict.get(trainidx,{})
        self.trainIdx = trainidx
        self.trainType = train_dict.get("TrainType","X-Deko")
        self.trainNumber = train_dict.get("TrainName","0000")
        self.trainName = self.trainType + self.trainNumber
        self.trainPrintName = self.trainType + self.format_PrintTrainNumber(self.trainNumber)
        self.trainLineName = train_dict.get("TrainLineName","")
        self.trainFahrplangruppe = train_dict.get("Fahrplangruppe","")
        self.trainEngine = train_dict.get("TrainEngine","")
        self.trainOutgoingStation = train_dict.get("Outgoing_Station","")
        self.trainIncomingStation = train_dict.get("Incoming_Station","") 
        self.trainLineProp = self.canvas_traintype_prop_dict.get(self.trainEngine,None)
        if self.trainLineProp==None:
            self.trainLineProp = self.canvas_traintype_prop_dict.get(self.trainType,self.default_trainprop)        
        #self.trainLineProp = self.canvas_traintype_prop_dict.get(self.trainType,self.default_trainprop)
        self.trainColor = self.trainLineProp.get("Bfp_TrainTypeColor","Black")
        self.trainLineWidth = int(self.trainLineProp.get("Bfp_TrainTypeWidth","2"))
        if self.trainNumber == self.controller.arg_zn:
            self.trainLineWidth *= 2
        self.TrainLabelPos = self.trainLineProp.get("Bfp_TrainTypeLabel_No","")
        self.TrainLabelSize = self.trainLineProp.get("Bfp_TrainTypeLabelSize","10")
        self.TrainLineDashed = self.trainLineProp.get("Bfp_TrainTypeLineDashed",False)
        self.TrainLabelFont = font.Font(family="SANS_SERIF", size=int(self.TrainLabelSize))
        if self.trainColor == "" or self.trainLineWidth == 0:
            return
        self.trainLine_dict = []
        self.trainLineStops = train_dict.get("Stops",{})
        self.trainLineStopCnt = len(self.trainLineStops)
        self.trainLineStopMiddleIdx=int(self.trainLineStopCnt/2)
        if self.trainLineStopMiddleIdx < 0:
            self.trainLineStopMiddleIdx = 0
        self.trainLineFirstStop_Flag = True
        self.trainLineLastStop_Flag = False
        self.drawTrainName_Flag = self.TrainLabelPos in [0,1,2,3]
        #self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan für Zug - "+self.trainName)
        self.trainLine_dict = []
        self.trainLine_dict_idx = -1
        self.trainNameLabel_indiv_pos_stops = self.determine_trainNameLabel_indiv_pos_stops(self.trainName)
        self.segment_count = -1
        self.process_trainStops()
        train_dict["SegmentCount"] = self.segment_count
        return

    def process_trainStops(self):
        self.stationName = ""
        self.stopStation = {}
        for self.stopIdx,stop_dict in self.trainLineStops.items():
            self.arriveTime = stop_dict.get("ArriveTime",0)
            self.departTime = stop_dict.get("DepartTime",0)
            station_dict = self.schedule_stations_dict.get(stop_dict.get("StationIdx"))
            self.stationName = station_dict.get("StationName")
            self.signal = stop_dict.get("Signal","")
            self.stopStation  = stop_dict
            #if (self.stopIdx > 0): 
                #self.trainLineFirstStop_Flag = False
            if (self.stopIdx == self.trainLineStopCnt - 1): 
                self.trainLineLastStop_Flag = True
            if self.departTime == 0 and self.arriveTime == 0:
                continue                    
            if self.check_time_in_range(self.departTime):
                if (self.trainLineFirstStop_Flag):
                    self.setBegin(self.stopStation,self.stationName)
                    self.trainLineFirstStop_Flag = False
                    if (self.trainLineLastStop_Flag):
                        # One stop route or only one stop in current segment
                        #self.setEnd(self.stopStation, self.stationName)
                        break
                    continue
                self.drawLine(self.stopStation)
            if (self.trainLineLastStop_Flag):
                # At the end, do the end process
                #self.setEnd(self.stopStation, self.stationName)
                break
        if (self.trainLineLastStop_Flag):
            self.setEnd(self.stopStation, self.stationName)
            self.trainLineLastStop_Flag = False

    def drawTrainTime(self, time,  mode,  x,  y):
        if (not self.TrainMinuteShow):
            return
        if not self.check_time_in_range(time):
        #if not (int(time) in range(self.schedule_startTime_min,self.schedule_startTime_min + self.schedule_duration * 60)):
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
        if time <0:
            return ""
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
    
    def get_train_idx_from_TrainNumber(self,trainNumber):
        for trainIdx in self.schedule_trains_dict:
            train = self.schedule_trains_dict.get(trainIdx,{})
            search_trainName = train.get("TrainName","0000")
            if search_trainName == trainNumber:
                if train.get("Stops",{}) != {}:
                    return trainIdx
        return -1
    
    def get_trn_train_idx_from_TrainNumber(self,trn_trainNumber):
        for trainIdx in self.schedule_trains_dict:
            train = self.schedule_trains_dict.get(trainIdx,{})
            search_trainName = train.get("trn_trainname","0000")
            if search_trainName == trn_trainNumber:
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
        self.old_direction = self.direction
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
                self.direction = "up"
        return
    
    def determine_DirectionofTravel2(self,trainLineStops,stopIdx):
        trainLineStopsCnt = len(trainLineStops) 
        if trainLineStopsCnt == 1:
            # Single stop train, default to down
            direction = "down"
            return direction
        stop = trainLineStops.get(stopIdx,{});
        currStation_Idx = stop.get("StationIdx",0)
        currStation = self.schedule_stations_dict.get(currStation_Idx,{})
        currkm = currStation.get("Distance",0)
        if (stopIdx == trainLineStopsCnt-1):
            Station_Idx = trainLineStops.get(stopIdx-1).get("StationIdx",0)
            prevStation = self.schedule_stations_dict.get(Station_Idx,{})            
            # For the last stop, use the previous stop to set the direction
            prevkm = prevStation.get("Distance",0)
            if prevkm < currkm:
                direction = "down" 
            else :  
                direction = "up"                                
        else:
            # For all other stops use the next stop.
            Station_Idx = trainLineStops.get(stopIdx+1).get("StationIdx",0)
            nextStation = self.schedule_stations_dict.get(Station_Idx,{})                     
            nextkm = nextStation.get("Distance",0)
            if nextkm > currkm:
                direction = "down"
            else: 
                direction = "up";  
        return direction

    def get_StationData(self, stopIdx):
        Station_Idx = self.trainLineStops.get(stopIdx).get("StationIdx",0)
        Station = self.schedule_stations_dict.get(Station_Idx,{})
        return Station
    
    def check_time_in_range(self,time):
        
        time_ok = int(time) in range(self.schedule_startTime_min,self.schedule_startTime_min + self.schedule_duration * 60)
        
        if time_ok==False:
            if self.schedule_startTime_min + self.schedule_duration * 60 > 24 * 60: # check if time frame is over 0:00
                time_ok = int(time) in range(0,self.schedule_startTime_min + self.schedule_duration * 60 - 24*60)
        return time_ok
    

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
            self.segment_count += 1
            self.trainLine_dict = [xa, ya]
            self.trainLine_dict_idx = 0
            self.arriveTime = stop.get("ArriveTime",0)
            xa_delta,ya_delta = self.determine_xy_point_with_delta(stop,self.arriveTime)
            if xa != xa_delta or ya != ya_delta:
                self.trainLine_dict.extend([xa_delta, ya_delta])
                self.trainLine_dict_idx += 1            
            if not(self.trainLineLastStop_Flag) and show_arrive_time:
                self.drawTrainTime(self.arriveTime, "begin", xa, ya)
            xd_delta,yd_delta = self.determine_xy_point_with_delta(stop,self.departTime)
            if xd != xd_delta or yd != yd_delta:
                self.trainLine_dict.extend([xd_delta, yd_delta])
                self.trainLine_dict_idx += 1                     
            self.trainLine_dict.extend([xd, yd])
            self.trainLine_dict_idx += 1
            logging.info("Gleisbelegung;"+stationName+";"+self.signal_txt+";"+self.determine_time_str(self.arriveTime)+";"+self.determine_time_str(self.departTime)+";"+self.direction+";"+self.trainName+";"+self.signal)
        else:
            self.segment_count += 1
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
                xa_delta,ya_delta = self.determine_xy_point_with_delta(stop,self.arriveTime)
                self.trainLine_dict.extend([xa_delta, ya_delta])
                self.trainLine_dict_idx += 1
                self.drawTrainTime(self.arriveTime, "arrive", xa, ya)
                self.segment_count += 1
                if (len(self.trainLine_dict)>5) and ya!=None:
                    self.draw_trainName_parallel(self.trainPrintName, self.trainLine_dict[-6],self.trainLine_dict[-5],xa, ya)
                if self.check_time_in_range(self.departTime):
                    xd,yd = self.determine_xy_point(stop,self.departTime)
                    if yd==None:
                        return
                    xd_delta,yd_delta = self.determine_xy_point_with_delta(stop,self.departTime)
                    self.trainLine_dict.extend([xd_delta, yd_delta])                                        
                    self.trainLine_dict.extend([xd, yd])
                    self.trainLine_dict_idx += 1

                    if not self.trainLineLastStop_Flag:
                        self.drawTrainTime(self.departTime, "depart", xd, yd)
                try:
                    logging.info("Gleisbelegung;"+self.stationName+";"+self.signal_txt+";"+self.determine_time_str(self.arriveTime)+";"+self.determine_time_str(self.departTime)+";"+self.direction+";"+self.trainName+";"+self.signal)
                except BaseException as e:
                    logging.debug("Gleisbelegung Fehler:",e)
                    
        else:
            if self.check_time_in_range(self.departTime):
                xd,yd = self.determine_xy_point(stop,self.departTime)
                if yd==None:
                    return
                self.trainLine_dict.extend([xd, yd])
                xd_delta,yd_delta = self.determine_xy_point_with_delta(stop,self.departTime)
                self.trainLine_dict.extend([xd_delta, yd_delta])
                self.trainLine_dict.extend([xd, yd])
                self.segment_count += 1
                self.trainLine_dict_idx += 1
                if not self.trainLineLastStop_Flag or self.arriveTime == 0:
                    self.drawTrainTime(self.departTime, "depart", xd, yd)
                if (len(self.trainLine_dict)>3) and yd!=None:
                    self.draw_trainName_parallel(self.trainPrintName, self.trainLine_dict[-4],self.trainLine_dict[-3],xd, yd)
                try:
                    logging.info("Gleisbelegung;"+self.stationName+";"+self.signal_txt+";"+self.determine_time_str(self.arriveTime)+";"+self.determine_time_str(self.departTime)+";"+self.direction+";"+self.trainName+";"+self.signal)
                except BaseException as e:
                    logging.debug("Gleisbelegung Fehler:",e)
            
        if self.old_direction != self.direction:
            self.drawTrainName_Flag = True
                    
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
                    if self.departTime == 0:
                        self.trainLine_dict.extend([x, y])
                        self.trainLine_dict_idx += 1
                if self.TrainLineDashed != "no line":
                    train_line_objid = self.tt_canvas.create_line(self.trainLine_dict,fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,dash=self.TrainLineDashed,tags=(self.trainName,"L_"+self.trainName,str(self.trainIdx)))
                    #self.controller.ToolTip_canvas(self.tt_canvas, train_line_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, button_1=True)
                    self.controller.ToolTip_canvas(self.tt_canvas, train_line_objid, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\n"+self.trainFahrplangruppe+"\nBR "+self.trainEngine, button_1=True)
                    self.bind_right_click_menu_to_trainline(train_line_objid)
            arrowwidth = self.trainLineWidth
            if arrowwidth<4:
                arrowwidth=4
            if self.trainOutgoingStation!="": # draw outgoing arrow
                if self.check_draw_OutBoundArrow(stationName,oneStopOnly):
                    #logging.debug("Print Outgoing-Station: %s %s %s %s %s",self.trainType+self.trainName,stationName,self.trainOutgoingStation,self.startstationName,self.endstationName)
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
                    #logging.debug("Print Incoming-Station: %s %s %s %s %s",self.trainType+self.trainName,self.trainIncomingStation,stationName,self.startstationName,self.endstationName)
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
        trainNameLabel_indiv_pos = self.trainNameLabel_indiv_pos_stops != []
        if trainNameLabel_indiv_pos:
            stationName = self.get_stationName_from_StopIdx(self.stopIdx)
            last_segment = self.trainLineStopCnt
            from_last_segment = last_segment - self.segment_count
            self.drawTrainName_Flag= str(self.segment_count) in self.trainNameLabel_indiv_pos_stops or stationName in self.trainNameLabel_indiv_pos_stops or str(-from_last_segment) in self.trainNameLabel_indiv_pos_stops 
        else:
            direction_changed = (self.old_direction != self.direction)
            if self.TrainLabelSize==0:
                return
            if (self.stopIdx == self.trainLineStopMiddleIdx or direction_changed) and self.TrainLabelPos in [1,4]:  # draw middle label
                self.drawTrainName_Flag=True
            elif (self.stopIdx == self.trainLineStopCnt-1 or direction_changed) and self.TrainLabelPos in [1,2,5]: # draw End label
                self.drawTrainName_Flag=True
        p0=Point(x0,y0)
        p1=Point(x1,y1)
        segment = p1 - p0
        mid_point = segment.scale(0.5) + p0
        trainName_len = self.TrainLabelFont.measure(self.trainName)
        segment_len = segment.norm()
        if segment_len > trainName_len+30 or trainNameLabel_indiv_pos:
            if self.drawTrainName_Flag:
                trainname_id = self.tt_canvas.create_text(*(mid_point), text=trainName,activefill="red",font=self.TrainLabelFont,anchor="s",tags=(self.trainName,"TrainName",str(self.segment_count)))
                if y0 != y1:
                    angle = segment.angle()
                    if angle>90:
                        angle -= 180
                    if angle<-90:
                        angle+=180
                    self.tt_canvas.itemconfig(trainname_id, angle=angle)
                if self.test_overlap(trainname_id,objlist=("TrainName")):
                    self.tt_canvas.delete(trainname_id)
                else:
                    self.controller.ToolTip_canvas(self.tt_canvas, trainname_id, text="Zug: "+self.trainName+"\n"+self.trainLineName+"\nBR "+self.trainEngine, button_1=True)
                    self.bind_right_click_menu_to_trainname(trainname_id)
                    if self.TrainLabelPos!=0:
                        self.drawTrainName_Flag=False

    def draw_background(self, objId,tags=[],fill="white"):
        b_list = ["Background"]
        tags.extend(b_list)
        rectangle = self.tt_canvas.bbox(objId)
        self.tt_canvas.create_rectangle(rectangle[0]+1,rectangle[1]+1,rectangle[2]-1,rectangle[3]-1,fill=fill,outline=fill,tags=tags,width=0)
        self.tt_canvas.tag_raise(objId)
                    
    def enter_station(self,stationName, distance, stationKm,neukm=0,FplRglGgl=""):
        if stationKm == None:
            print("Error: km=None -",stationName)
            stationKm = 0
        for stationIdx in self.schedule_stations_dict:
            station_data = self.schedule_stations_dict.get(stationIdx,0)
            if station_data.get("StationName","") == stationName:
                return stationIdx
        if (len(self.select_stationlist) < 2) or (stationName in self.select_stationlist):     
            self.schedule_stations_dict[self.schedule_stationIdx_write_next] = {"StationName"     : stationName, 
                                                                                "Distance"        : distance,
                                                                                "StationKm"       : stationKm,
                                                                                "Neukm"           : neukm,
                                                                                "FplRglGgl"       : FplRglGgl}
            self.schedule_stationIdx_write_next +=1
            self.schedule_stations_list.append(stationName)
        else:
            return -1
        return self.schedule_stationIdx_write_next - 1

    #def enter_schedule_trainLine_data(self,trainNumber,trainType,ZugLauf,ZugLok,trn_filepathname="",pendelzug=False):
    def enter_schedule_trainLine_data(self,trainNumber,trainType,ZugLauf,ZugLok,trn_filepathname="",pendelzug=False,trn_fahrplangruppe="",trn_zugnummer=""):
        color = self.canvas_traintype_prop_dict.get(trainType,"black")
        width = self.trainType_to_Width_dict.get(trainType,"1")
        if trn_zugnummer =="":
            trn_zugnummer = trainNumber
        self.schedule_trains_dict[self.schedule_trainIdx_write_next] = {"TrainName"     : trainNumber,
                                                                        "trn_trainname" : trn_zugnummer,
                                                                        "trn_filename"  : trn_filepathname,
                                                                        "Fahrplangruppe" : trn_fahrplangruppe,
                                                                        "TrainType"     : trainType,
                                                                        "TrainLineName" : ZugLauf,
                                                                        "TrainEngine"   : ZugLok,
                                                                        "Color"         : color,
                                                                        "Width"         : width,
                                                                        "Pendelzug"     : pendelzug,
                                                                        "Stops"         : {},
                                                                        "Stoplist"      : [],
                                                                        "Starttime"     : -1
                                                                        }
        self.schedule_trainIdx_write_next += 1
        return self.schedule_trainIdx_write_next-1
    
    def enter_schedule_trainLine_starttime(self,trainidx,starttime):
        if self.controller.usetrain_starttime:
            self.controller.usetrain_starttime=False
            if self.schedule_trains_dict[trainidx]["Starttime"] == -1:
                self.schedule_trains_dict[trainidx]["Starttime"] = starttime
                self.controller.setConfigData("Bfp_start",starttime)



    def search_station(self, stationName):
        try:
            stationlistIdx = self.schedule_stations_list.index(stationName)
        except:
            stationlistIdx = -1
        
        return stationlistIdx
    
        #for stationIdx in self.schedule_stations_dict:
        #    iter_stationName=self.get_stationName(stationIdx)
        #    if iter_stationName == stationName:
        #        if stationlistIdx != stationIdx:
        #            print("search station error:", stationName,repr(self.schedule_stations_list),stationIdx,stationlistIdx)
        #        return stationIdx
        #if stationlistIdx != -1:
        #    print("search station error:", stationName,repr(self.schedule_stations_list),stationIdx,stationlistIdx)        
        #return -1

    def enter_trainLine_stop(self, train_idx, trainstop_idx, FplName, FplAnk_min, FplAbf_min,signal="",Richtungswechsel=False,FPLDistance=-1):
        #print("enter_trainline_stop:", train_idx, FplName, FplAnk_min, FplAbf_min)
        train_dict = self.schedule_trains_dict.get(train_idx)
        if Richtungswechsel:
            train_dict["Richtungswechsel"]=True
            #print(FplName,Richtungswechsel)
            pendelstops = train_dict.get("PendelStops",[])
            pendelstops.append(trainstop_idx)
            train_dict["Pendelstops"]=pendelstops
            #print("Pendelstops:",pendelstops)
        trainstops_dict = train_dict.get("Stops",{})
        station_idx = self.search_station(FplName)
        do_not_override_station = False
        last_station_arriveTime = 0
        if trainstop_idx>0:
            last_station_idx = trainstops_dict[trainstop_idx-1]["StationIdx"]
            if station_idx == last_station_idx and not self.train_line_interrupted:
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
            trainstops_dict[trainstop_idx] = {"StationIdx"      : station_idx,
                                              "ArriveTime"      : arriveTime,
                                              "ArriveTimeOrig"  : arriveTime,
                                              "DepartTime"      : departTime,
                                              "DepartTimeOrig"  : departTime,
                                              "Signal"          : signal,
                                              "Richtungswechsel": Richtungswechsel,
                                              "FplDistance"     : FPLDistance
                                           }
            train_dict["Stoplist"].append(FplName)
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

    #def convert_tt_xml_dict_to_schedule_dict(self, tt_xml_dict, define_stations=False,trn_filepathname="",fpn_filename=""):
    def convert_tt_xml_dict_to_schedule_dict(self, tt_xml_dict, define_stations=False,trn_filepathname="",fpn_filename="",trn_fahrplangruppe="",trn_zugnummer=""):
        Zusi_dict = tt_xml_dict.get("Zusi")
        Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan",{})
        if Buchfahrplan_dict=={}:
            return False
        try:
            ZugNummer = Buchfahrplan_dict.get("@Nummer","")
        except BaseException as e: # Buchfahrplan_dict containes a list of Buchfahrpläne. Only the first is used here (need to be updated)'
            logging.debug("open_zusi_trn_zug_dict - Buchfahrplan: Error open file %s - %s",trn_filepathname,e)
            self.controller.set_statusmessage("Buchfahrplan: Fehler beim Öffnen der Datei \n" + trn_filepathname)
            self.open_error = "Fehler in XML-Datei (Details siehe xml_error_logfile.log)\n" + trn_filepathname
            self.xml_error_logger.debug("open_zusi_trn_zug_dict - Buchfahrplan: Error open file %s - %s",trn_filepathname,e)
            
            Buchfahrplan_dict = Buchfahrplan_dict[0]
            ZugNummer = Buchfahrplan_dict.get("@Nummer","")

        Pendelzug_Flag = "_" in ZugNummer
        #if Pendelzug_Flag:
        #    print(ZugNummer,"Pendelzug")  
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
        #train_idx = self.enter_schedule_trainLine_data(ZugNummer,ZugGattung,Zuglauf,ZugLok,trn_filepathname=trn_filepathname,pendelzug=Pendelzug_Flag)
        train_idx = self.enter_schedule_trainLine_data(ZugNummer,ZugGattung,Zuglauf,ZugLok,trn_filepathname=trn_filepathname,pendelzug=Pendelzug_Flag,trn_fahrplangruppe=trn_fahrplangruppe,trn_zugnummer=trn_zugnummer)
        train_stop_idx = 0
        FplRglGgl_str = self.controller.getConfigData("FplRglGgl",default="")
        donotshowall = not self.controller.getConfigData("ExtraShowAlleZFS")
        if FplRglGgl_str and FplRglGgl_str !="":
            self.FplRglGgl = FplRglGgl_str.split(",")
        else:
            self.FplRglGgl = []
        FplZeile_list = Buchfahrplan_dict.get("FplZeile",{})
        FplRichtungswechsel_flag = False
        stationdistance = 0
        last_km = 0
        station_idx = 0
        self.select_stationlist  = self.controller.get_macroparam_val("SpecialConfigurationPage","StationChooser") #self.controller.getConfigData("StationChooser")
        if FplZeile_list=={}:
            logging.info("timetable.xml file error: %s",trn_dateiname )
            self.controller.set_statusmessage("Error: ZUSI entry not found in fpl-file: "+trn_dateiname)
            self.open_error = "Error: ZUSI entry not found in fpl-file: "+trn_dateiname
            self.xml_error_logger.debug("Error: ZUSI entry not found in fpl-file: "+trn_dateiname)
            return False
        self.train_line_interrupted = False
        lastFplRglGgl = ""
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
                lastFplRglGgl = FplRglGgl
            try:
                FplSprung = self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@FplSprung",default="")
                Fplkm = float(self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@km",default=0))
                if (Fplkm == 0):
                    continue # kein km Eintrag, nicht bearbeiten
                FplName = self.get_fplZeile_entry(FplZeile_dict,"FplName","@FplNameText",default="")
                if FplName == "" and FplSprung == "":
                        continue
                if last_km == 0:
                        # first entry
                    last_km=Fplkm                
                if FplSprung == "":
                    stationdistance = stationdistance + abs(Fplkm - last_km)
                    last_km = Fplkm
                    Neukm=0
                else:
                    stationdistance = stationdistance + abs(Fplkm - last_km)
                    Neukm = float(self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@FplkmNeu",default=0))
                    if Neukm == 0:
                        print("ERROR: Neukm Eintrag fehlt",ZugGattung,ZugNummer,"-",repr(FplZeile_dict))
                    else:
                        last_km = Neukm
                    #if FplName== "":
                    #   FplName = "* ("+str(Fplkm)+"-"+str(Neukm)+")"                    
                if Fplkm<0:
                    Fplkm = 0.0
                FplAbf = self.get_fplZeile_entry(FplZeile_dict, "FplAbf","@Abf")

                if FplAbf != "":
                    FplAbf_obj = datetime.strptime(FplAbf, '%Y-%m-%d %H:%M:%S')
                    FplAbf_min = FplAbf_obj.hour * 60 + FplAbf_obj.minute + FplAbf_obj.second/60
                    if self.FPL_starttime == -1 or self.FPL_starttime>FplAbf_obj.hour:
                        self.FPL_starttime = FplAbf_obj.hour
                    if self.FPL_endtime<FplAbf_obj.hour:
                        self.FPL_endtime = FplAbf_obj.hour
                        #self.enter_schedule_trainLine_starttime(train_idx,FplAbf_obj.hour)
                else:
                    FplAbf_min = -99999
                FplAnk = self.get_fplZeile_entry(FplZeile_dict, "FplAnk","@Ank")
                if FplAnk!="":
                    FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                    FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute + FplAnk_obj.second/60
                    if self.FPL_starttime == -1 or self.FPL_starttime>FplAnk_obj.hour:
                        self.FPL_starttime = FplAnk_obj.hour
                    if self.FPL_endtime<FplAnk_obj.hour:
                        self.FPL_endtime = FplAnk_obj.hour
                else:
                    FplAnk_min = -99999
                if FplAbf == "" and FplAnk=="" and FplSprung == "" and donotshowall:
                    continue # only use station with "Abf"or "Ank" -Entry                
                #FplName = self.get_fplZeile_entry(FplZeile_dict,"FplName","@FplNameText",default="")
                if FplName == "":
                    continue
                if self.schedule_stationIdx_write_next == 0:
                    stationdistance = 0
                Fpldistance = stationdistance # abs(kmStart - Fplkm)
                FplRichtungswechsel_flag = FplZeile_dict.get("FplRichtungswechsel","") == None and train_stop_idx > 0
                if define_stations:
                    station_idx = self.enter_station(FplName,Fpldistance,Fplkm,neukm=Neukm,FplRglGgl=lastFplRglGgl)
                    if FplRichtungswechsel_flag and Pendelzug_Flag:
                        break
                else:
                    station_idx = self.search_station(FplName)
                    if station_idx != -1:
                        train_stop_idx = self.enter_trainLine_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min,Richtungswechsel=FplRichtungswechsel_flag,FPLDistance=Fpldistance)
                        self.train_line_interrupted = False
                    else:
                        self.train_line_interrupted = True
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
    
    def convert_trn_dict_to_schedule_dict(self, zusi_trn_dict,define_stations=False,trn_filepathname=""):
        try:
            if zusi_trn_dict=={}:
                return
            trn_fahrplangruppe = zusi_trn_dict.get("@FahrplanGruppe","")
            ZugNummer = zusi_trn_dict.get("@Nummer","")
            ZugGattung = zusi_trn_dict.get("@Gattung","")
            ZugLok = zusi_trn_dict.get("@BR","")
            if ZugGattung == "X-Deko":
                return
            Zuglauf = zusi_trn_dict.get("@Zuglauf","")
            Pendelzug_Flag = "_" in ZugNummer
            #if Pendelzug_Flag:
            #    print(ZugNummer,"Pendelzug")            
            Datei_fpn_dict = zusi_trn_dict.get("Datei",{})
            if Datei_fpn_dict == {}:
                return
            fpn_dateiname = Datei_fpn_dict.get("@Dateiname","")
            self.schedule_dict["Name"] = fpn_dateiname
            #train_idx = self.enter_schedule_trainLine_data(ZugNummer,ZugGattung,Zuglauf,ZugLok,trn_filepathname=trn_filepathname,pendelzug=Pendelzug_Flag)
            train_idx = self.enter_schedule_trainLine_data(ZugNummer,ZugGattung,Zuglauf,ZugLok,trn_filepathname=trn_filepathname,pendelzug=Pendelzug_Flag,trn_fahrplangruppe=trn_fahrplangruppe)
            train_stop_idx = 0
            FplZeile_list = zusi_trn_dict.get("FahrplanEintrag",{})
            if FplZeile_list=={}:
                return
            #Fpl_Zeile_cnt_max = len(FplZeile_list)
            Fpldistance = 0
            FplAbfStartMin = 0
            if define_stations:
                self.select_stationlist  = self.controller.get_macroparam_val("SpecialConfigurationPage","StationChooser") #self.controller.getConfigData("StationChooser")
            for FplZeile_dict in FplZeile_list:
                #print(repr(FplZeile_dict))
                FplAbf = FplZeile_dict.get("@Abf","")
                if FplAbf == "":
                    continue # only use station with "Abf"-Entry
                FplAbf_obj = datetime.strptime(FplAbf, '%Y-%m-%d %H:%M:%S')
                FplAbf_min = FplAbf_obj.hour * 60 + FplAbf_obj.minute + FplAbf_obj.second/60
                if self.FPL_starttime == -1 or self.FPL_starttime>FplAbf_obj.hour:
                    self.FPL_starttime = FplAbf_obj.hour
                if self.FPL_endtime<FplAbf_obj.hour:
                    self.FPL_endtime = FplAbf_obj.hour
                if FplAbfStartMin==0:
                    FplAbfStartMin=FplAbf_min
                FplAnk = FplZeile_dict.get("@Ank","")
                if FplAnk!="":
                    FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                    FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute + FplAnk_obj.second/60
                    if self.FPL_starttime == -1 or self.FPL_starttime>FplAnk_obj.hour:
                        self.FPL_starttime = FplAnk_obj.hour
                    if self.FPL_endtime<FplAnk_obj.hour:
                        self.FPL_endtime = FplAnk_obj.hour
                else:
                    FplAnk_min = -99999
                FahrplanSignal = ""
                Fpl_SignalEintrag_dict = FplZeile_dict.get("FahrplanSignalEintrag",None)
                if Fpl_SignalEintrag_dict:
                    try:
                        FahrplanSignal = Fpl_SignalEintrag_dict.get("@FahrplanSignal","")
                    except: # list instead of dict
                        FahrplanSignal = ""
                        for signal in Fpl_SignalEintrag_dict:
                            FahrplanSignal += "-"+signal.get("@FahrplanSignal","")+"-"
                FplName = FplZeile_dict.get("@Betrst","")
                if FplName == "":
                    continue
                if define_stations:
                    Fpldistance = int(FplAbf_min-FplAbfStartMin)
                    Fplkm = Fpldistance
                    Neukm = 0
                    station_idx = self.enter_station(FplName,Fpldistance,Fplkm,neukm=Neukm)
                    FplRichtungswechsel_flag = FplZeile_dict.get("@FzgVerbandAktion","") == "2"
                    if FplRichtungswechsel_flag and Pendelzug_Flag:
                        break
                else:
                    station_idx = self.search_station(FplName)
                    if station_idx != -1:
                        FplRichtungswechsel_flag = FplZeile_dict.get("@FzgVerbandAktion","") == "2"
                        train_stop_idx = self.enter_trainLine_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min,signal=FahrplanSignal,Richtungswechsel=FplRichtungswechsel_flag)
                    else:
                        if train_stop_idx == 0:
                            # train is comming from another station
                            self.enter_train_incoming_station(train_idx, FplName)
                if station_idx == -1:
                    #last station is unknown
                    self.enter_train_outgoing_station(train_idx, FplName)
                
        except BaseException as e:
            logging.debug("FplZeile conversion Error %s %s",ZugGattung+ZugNummer+"-"+repr(FplZeile_dict),e)
        return True
    
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
        if not self.controller.popup_active:
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
    
    def get_stationName_from_StopIdx(self,stopIdx):
        stop_dict = self.trainLineStops.get(stopIdx,{})
        if stop_dict == {}:
            return ""
        station_idx = stop_dict.get("StationIdx")
        return self.get_stationName(station_idx)    
    
    def get_stationdistance_from_StopDict(self,stop_dict):
        stationIdx = stop_dict.get("StationIdx")
        station = self.schedule_stations_dict.get(stationIdx,{})
        stationDistance = station.get("Distance",0)
        return stationDistance        
    
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
        self.controller.set_statusmessage("Änderungen exportiert in Datei: "+trn_filepathname)
        self.reset_trainline_data_changed_flag(trainIdx)
        
    def edit_clone_schedule(self,objectid):
        #print("edit_clone_schedule",self.controller.edit_trainline_tag)
        trainIdx = int(self.tt_canvas.gettags(objectid)[2])
        train_dict = self.schedule_trains_dict.get(trainIdx,{})
        trn_filepathname = train_dict.get("trn_filename","")
        self.popwin = popup_win_clone(self.ttpage,self.controller,trn_filepathname,self.fpn_filename)
        Tk.wait_window(self.popwin)
    
    def edit_run_schedule(self,objectid,restart_fpn=True):
        self.run_trainIdx = int(self.tt_canvas.gettags(objectid)[2])
        if self.controller.ZUSI_TCP_var.getConnectionStatus():
            self.edit_start_schedule(restart_fpn=restart_fpn)
            return
        TCPPageFrame = self.controller.getFramebyName("TCPConfigPage")
        if TCPPageFrame.connect_to_ZUSI_server():
            self.ttmain_page.after(2000,self.edit_start_schedule)
            return
        #else:
        #    train_dict = self.schedule_trains_dict.get(self.run_trainIdx,{})
        #    trn_filepathname = train_dict.get("trn_filename","")
        #    if trn_filepathname != "":
        #        os.startfile(trn_filepathname)
        #        self.ttmain_page.after(3000,TCPPageFrame.connect_to_ZUSI_server) # try to conect to the ZUSI server after ZUSI has been started
                
    def edit_start_schedule(self,restart_fpn=True):
        train_dict = self.schedule_trains_dict.get(self.run_trainIdx,{})
        if self.controller.ZUSI_TCP_var.getConnectionStatus():
            if restart_fpn:
                fpn_filename = self.schedule_dict.get("Name","")
            else:
                fpn_filename = ""
            trainnumber = train_dict.get("TrainName","")
            self.controller.ZUSI_TCP_var.start_ZUSI_train(trainnumber,fpn_filename=fpn_filename)
            self.monitor_ladepause = True
            self.monitor_curr_trainline_objectid = -1
            self.update_monitor_status_panel()
        return
    
    def edit_connect_ZUSI(self,objectid):
        self.monitor_zusi_life_status = True
        self.monitor_time = 0
        self.monitor_currtime_str  = self.determine_time_str(self.monitor_time)
        self.monitor_currkm_str = "  "
        self.monitor_currdist_str = "  "
        self.monitor_currspeed_str = "  "
        self.monitor_fpn_filepathname = "  "
        self.monitor_ladepause = False
        self.monitor_trainNumber = "  " 
        self.print_monitor_panel()
        self.print_monitor_status_panel()
        self.monitor_start = False        
        TCPPageFrame = self.controller.getFramebyName("TCPConfigPage")
        if TCPPageFrame.connect_to_ZUSI_server():
            TCPPageFrame.cb_connection_status(status="Connected")
            pass
            #self.monitor_check_ZUSI_connection_alife()
    
    def edit_disconnect_ZUSI(self,objectid):
        TCPPageFrame = self.controller.getFramebyName("TCPConfigPage")
        TCPPageFrame.disconnect_from_ZUSI_server()
        TCPPageFrame.cb_connection_status(status="Not Connected")
        
    def show_trainNum_here(self,objectid,event):
        x0 = event.x
        x = self.tt_canvas.canvasx(x0)
        y0 = event.y
        y = self.tt_canvas.canvasy(y0)
        for i in range(len(self.stationGrid)):
            if x < self.stationGrid[i] :
                break
        stationName = self.get_stationName(i)
        trainIdx = int(self.tt_canvas.gettags(objectid)[2])
        train_dict = self.schedule_trains_dict.get(trainIdx,{})
        trainType = train_dict.get("TrainType","X")
        trainNumber = train_dict.get("TrainName","0000")
        trainName = trainType + trainNumber        
        #print(trainName,stationName)
        
        linecoords = self.tt_canvas.coords(objectid)
        last_segx = int(linecoords[0])
        last_segy = int(linecoords[1])
        segnum = 1
        for i in range(len(linecoords)):
            if i%2 == 0: # we need 2 coords for x and y
                segx = int(linecoords[i])
                segy = int(linecoords[i+1])
                
                if last_segx != segx:
                    # new segement
                    # check if (x,y) in this segement
                    if (x in range(last_segx,segx) or x in range(segx,last_segx)) and y in range(last_segy,segy):
                        break
                    segnum+=1
                    last_segx = segx
                    last_segy = segy
        #print("Segment:",segnum)
        
        paramconfig_dict = self.controller.MacroParamDef.data.get("TrainNamePosProp",{})
        mp_repeat  = paramconfig_dict.get("Repeat","")
        repeat_var = paramconfig_dict.get("RepeatVar","")
        if repeat_var != "":
            repeat_var_value  = self.controller.getConfigData(repeat_var)
            if repeat_var_value != None and repeat_var_value != "":
                mp_repeat = repeat_var_value 
        trainName_found = False
        trainName_index = -1
        for i in range(int(mp_repeat)):
            trainNames_str = self.controller.getConfigData_multiple("TrainNamePos_Names","TrainNamePosProp",i)
            if trainNames_str != None:
                if trainNames_str == "":
                    if trainName_index == -1:
                        trainName_index = i # empty line if no entry found
                else:
                    trainName_list = trainNames_str.split(",")
                    if trainName in trainName_list:
                        trainName_found = True
                        trainName_index = i 
                        break
                
            else:
                print("error: no entry")
                logging.debug("show_trainNum_here: error: no entry found")
        
        if trainName_found:
            trainStops_str = self.controller.getConfigData_multiple("TrainNamePos_Stops","TrainNamePosProp",trainName_index)
            if trainStops_str != "":
                trainStops_str = trainStops_str + "," + str(segnum)
            else:
                trainStops_str = str(segnum)
            self.controller.setConfigData_multiple("TrainNamePos_Stops","TrainNamePosProp",trainName_index,trainStops_str)
        else:
            if trainName_index >-1:
                trainStops_str = str(segnum)
                self.controller.setConfigData_multiple("TrainNamePos_Stops","TrainNamePosProp",trainName_index,trainStops_str)
                self.controller.setConfigData_multiple("TrainNamePos_Names","TrainNamePosProp",trainName_index,trainName)
                
        logging.debug("show_trainNum_here: %s %s, trainName,trainStops_str")
        
        self.delete_train(trainName)
        self.tt_canvas.update_idletasks()
        newtrainIdx = self.get_train_idx_from_Name(trainName)
        self.process_train(newtrainIdx)
        self.controller.set_statusmessage("Zugname eingetragen - "+self.trainName)
        
    def edit_remove_trainnum(self,objectid):
        trainName = self.tt_canvas.gettags(objectid)[0]
        segment_num = int(self.tt_canvas.gettags(objectid)[2])
        logging.debug("remove trainname: %s %s %s",objectid,trainName,segment_num)
        
        paramconfig_dict = self.controller.MacroParamDef.data.get("TrainNamePosProp",{})
        mp_repeat  = paramconfig_dict.get("Repeat","")
        repeat_var = paramconfig_dict.get("RepeatVar","")
        if repeat_var != "":
            repeat_var_value  = self.controller.getConfigData(repeat_var)
            if repeat_var_value != None and repeat_var_value != "":
                mp_repeat = repeat_var_value       
        trainName_found = False
        trainName_index = -1
        for i in range(int(mp_repeat)):
            trainNames_str = self.controller.getConfigData_multiple("TrainNamePos_Names","TrainNamePosProp",i)
            trainName_list = trainNames_str.split(",")
            if trainName in trainName_list:
                trainName_found = True
                trainName_index = i 
                break
            if trainNames_str == "":
                if trainName_index == -1:
                    trainName_index = i # empty line if no entry found
        
        if trainName_found:
            trainStops_str = self.controller.getConfigData_multiple("TrainNamePos_Stops","TrainNamePosProp",trainName_index)
            if trainStops_str != "":
                trainstops_list = trainStops_str.split(",")
                segment_num_str = str(segment_num)
                if segment_num_str in trainstops_list:
                    trainstops_list.remove(segment_num_str)
                else:
                    trainIdx = self.get_train_idx_from_Name(trainName)
                    train_dict = self.schedule_trains_dict.get(trainIdx,{})
                    last_segment_str = train_dict.get("SegmentCount","")
                    if last_segment_str != "":
                        last_segment_num = int(last_segment_str)+1
                        last_segment_num_str = str(segment_num-last_segment_num)
                        if last_segment_num_str in trainstops_list:
                            trainstops_list.remove(last_segment_num_str)
                    
                trainStops_str = ",".join(trainstops_list)
            else:
                trainStops_str = ""
            self.controller.setConfigData_multiple("TrainNamePos_Stops","TrainNamePosProp",trainName_index,trainStops_str)
        else:
            if trainName_index >-1:
                trainStops_str = ""
                self.controller.setConfigData_multiple("TrainNamePos_Stops","TrainNamePosProp",trainName_index,trainStops_str)
                self.controller.setConfigData_multiple("TrainNamePos_Names","TrainNamePosProp",trainName_index,trainName)
        
        self.delete_train(trainName)
        self.tt_canvas.update_idletasks()
        newtrainIdx = self.get_train_idx_from_Name(trainName)
        self.process_train(newtrainIdx)
        self.controller.set_statusmessage("Zugname entfernt - "+self.trainName)
        

    def monitor_set_time(self,hour,minute,second):
        self.monitor_zusi_life_status = True
        monitor_time = hour*60+minute+second/60.0
        if self.monitor_start:
            self.monitor_time = monitor_time
            self.monitor_currtime_str  = self.determine_time_str(self.monitor_time)
            self.monitor_currkm_str = "  "
            self.monitor_currdist_str = "  "
            self.monitor_currspeed_str = "  "
            self.monitor_fpn_filepathname = "  "
            self.monitor_ladepause = False
            self.monitor_trainNumber = "  "
            self.print_monitor_panel()
            self.print_monitor_status_panel()
            self.monitor_start = False
        else:
            if monitor_time != self.monitor_time:
                self.monitor_time = monitor_time
                self.monitor_currtime_str  = self.determine_time_str(self.monitor_time)
                self.update_monitor_panel()
                self.monitor_update_train_pos()

    def monitor_set_km(self,km):
        self.monitor_zusi_life_status = True
        if not self.monitor_start:
            if abs(km-self.monitor_currkm) > 0:
                self.monitor_currkm = km
                self.monitor_currkm_str = "{:.1f}".format(km)
                self.update_monitor_panel()
                #self.monitor_update_train_pos()
    
    def monitor_set_speed(self,speed):
        self.monitor_zusi_life_status = True
        if not self.monitor_start:
            speed = speed*3.6 # m/s in km/h
            if abs(speed-self.monitor_currspeed) > 0:
                self.monitor_currspeed = speed
                self.monitor_currspeed_str = "{:.1f}".format(speed)
                self.update_monitor_panel()    
            
    def monitor_set_dist(self,dist):
        self.monitor_zusi_life_status = True
        if not self.monitor_start:
            if abs(dist-self.monitor_currdist) > 0:
                self.monitor_currdist = dist
                self.monitor_currdist_str = str(dist)
                self.update_monitor_panel()
                
    def monitor_determine_last_station_distance(self,train_dict,train_stops):
        pendelstations = train_dict.get("Pendelstops",[])
        last_station_idx = len(train_stops)-1
        if pendelstations != []:
            
            return self.get_stationdistance_from_StopDict(train_stops.get(pendelstations[0],{}))
        else:
            return self.get_stationdistance_from_StopDict(train_stops.get(last_station_idx,{}))
                
    def monitor_set_timetable_updated(self, trainIdx=None):
        """
        if monitor_start:
            determine_train_number_from_curr_timetable_dict
            determine_first_station_in_timetablegraph(train_number)
            determine_distance_of_first_station_for_curr_train
            determine_direction_travel
        """        
        self.monitor_zusi_life_status = True
        if not self.monitor_start:
            if trainIdx==None:
                trainName = self.monitor_determine_trainnumber()
                trainIdx = self.get_train_idx_from_Name(trainName)

            train_dict = self.schedule_trains_dict.get(trainIdx,{})
            train_stops = train_dict.get("Stops",{})
            if train_stops=={}:
                return ""
            stopstationName = self.get_stationName_from_StopDict(train_stops.get(0,{}))
            if self.controller.simu_timetable_dict != {}:
                Zusi_dict = self.controller.simu_timetable_dict.get("Zusi",{})
                Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan",{})
                if Buchfahrplan_dict=={}:
                    return ""
                km_start = Buchfahrplan_dict.get("@kmStart","")
                datei_fpn_dict = Buchfahrplan_dict.get("Datei_fpn",{})
                datei_fpn = datei_fpn_dict.get("@Dateiname","")
                print(datei_fpn)
                FplZeile_list = Buchfahrplan_dict.get("FplZeile",{})
                stationdistance = 0
                if km_start != "":
                    last_km = float(km_start)
                else:
                    last_km = 0
                if FplZeile_list=={}:
                    logging.info("timetable.xml file error: %s",trainName )
                    self.controller.set_statusmessage("Error: ZUSI entry not found in fpl-file: "+trainName)
                    self.open_error = "Error: ZUSI entry not found in fpl-file: "+trainName
                    return False
                for FplZeile_dict in FplZeile_list:
                    try:
                        FplRglGgl=FplZeile_dict.get("@FplRglGgl","")
                    except:
                        print("Error:",trainName," ",repr(FplZeile_dict))
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
                        FplName = self.get_fplZeile_entry(FplZeile_dict,"FplName","@FplNameText",default="")
                        if FplName == "" and FplSprung == "":
                                continue                    
                        if FplSprung == "":
                            stationdistance = stationdistance + abs(Fplkm - last_km)
                            last_km = Fplkm
                        else:
                            stationdistance = stationdistance + abs(Fplkm - last_km)
                            Neukm = float(self.get_fplZeile_entry(FplZeile_dict,"Fplkm","@FplkmNeu",default=0))
                            if Neukm == 0:
                                print("ERROR: Neukm Eintrag fehlt",trainName,"-",repr(FplZeile_dict))
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
                            self.monitor_start_time = FplAbf_min
                        else:
                            FplAbf_min = 0
                        FplAnk = self.get_fplZeile_entry(FplZeile_dict, "FplAnk","@Ank")
                        if FplAnk!="":
                            FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                            FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute + FplAnk_obj.second/60
                            self.monitor_start_time = FplAnk_min
                        else:
                            FplAnk_min = 0                    
                        FplName = self.get_fplZeile_entry(FplZeile_dict,"FplName","@FplNameText",default="")
                        if FplName == "":
                            continue
                        if FplName == stopstationName:
                            break
                    except BaseException as e:
                        logging.debug("FplZeile conversion Error %s %s",trainName +"-"+repr(FplZeile_dict),e)
                        continue # entry format wrong
            else:
                firststop = train_stops.get(0,{})
                stationdistance = firststop.get("FplDistance",0)
            #check if pendelstation is the last station in trainline
            self.pendelstations = train_dict.get("Pendelstops",[])
            last_station_idx = len(train_stops)-1
            if self.pendelstations != [] and self.pendelstations[0]==last_station_idx:
                self.pendelstations = []
            self.monitor_curr_train_distance_to_first_station = stationdistance
            self.monitor_curr_train_direction_of_travel = self.determine_DirectionofTravel2(train_stops, 0)
            self.monitor_distance_of_first_station = self.get_stationdistance_from_StopDict(train_stops.get(0,{}))
            self.monitor_distance_of_last_station = self.monitor_determine_last_station_distance(train_dict,train_stops) #self.get_stationdistance_from_StopDict(train_stops.get(last_station_idx,{}))
            self.monitor_timetable_updated = True
            self.monitor_curr_trainline_objectid = -1
                
    def monitor_set_status(self,monitor_fpn_filepathname,monitor_trainNumber,monitor_ladestatus):
        self.monitor_zusi_life_status = True
        self.monitor_fpn_filepathname = monitor_fpn_filepathname
        self.monitor_trainNumber = monitor_trainNumber
        self.monitor_ladepause = monitor_ladestatus        
        if self.monitor_start:
            self.monitor_time = 0
            self.monitor_currtime_str  = self.determine_time_str(self.monitor_time)
            self.monitor_currkm_str = "  "
            self.monitor_currdist_str = "  "
            self.monitor_currspeed_str = "  "
            self.monitor_fpn_filepathname = "  "
            self.monitor_ladepause = False
            self.monitor_trainNumber = "  " 
            self.print_monitor_panel()
            self.print_monitor_status_panel()
            self.monitor_start = False
        else:
            self.update_monitor_status_panel()
            #self.monitor_update_train_pos()
            
    def monitor_set_connection_status(self, status, message):
        self.monitor_zusi_life_status = True
        self.monitor_conn_status = status
        self.monitor_conn_message = message
        self.update_monitor_conn_status_panel()
            
    def monitor_determine_trainnumber(self):
        Zusi_dict = self.controller.simu_timetable_dict.get("Zusi",{})
        Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan",{})
        if Buchfahrplan_dict=={}:
            return ""
        ZugNummer = Buchfahrplan_dict.get("@Nummer","")
        ZugGattung = Buchfahrplan_dict.get("@Gattung","")
        return ZugGattung+ZugNummer
    
    def create_circle(self, x, y, r, canvasName): #center coordinates, radius
        x0 = x - r
        y0 = y - r
        x1 = x + r
        y1 = y + r
        return canvasName.create_oval(x0, y0, x1, y1,fill="red",outline="red")
    
    def monitor_update_train_pos(self, train_idx=None, showtimeline=True,fahrtext=""):
        """
        if firstcall:
            determine_train_number_from_curr_timetable_dict
            determine_first_station_in_timetablegraph(train_number)
            determine_distance_of_first_station_for_curr_train
            determine_direction_travel
        
        get_distance_of_curr_train_from_start
        determine_distance_from_first_station
        determine_distance_on_timettablegraph
        
        draw_point_at_distance_and_time
        """
        trainName = self.monitor_determine_trainnumber()
        if trainName == "" and train_idx ==None:
            return
        distance_of_curr_train_from_start = self.monitor_currdist/1000
        distance_of_first_station = self.monitor_distance_of_first_station
        curr_distance_from_first_station = distance_of_curr_train_from_start - self.monitor_curr_train_distance_to_first_station
        train_pos_on_timetable = -1
        train_pos_in_range = False
        if curr_distance_from_first_station >= 0:
            if self.monitor_curr_train_direction_of_travel == "down":
                train_pos_on_timetable = distance_of_first_station + curr_distance_from_first_station
                if train_pos_on_timetable >= distance_of_first_station and train_pos_on_timetable <=self.monitor_distance_of_last_station:
                    train_pos_in_range = True
                else:
                    if train_pos_on_timetable > self.monitor_distance_of_last_station and self.pendelstations != []: # Pendelzug returns
                        if self.monitor_curr_train_distance_to_first_station-200 < distance_of_curr_train_from_start: # at first stop ignore direction change
                            self.monitor_curr_train_direction_of_travel = "up"
                        last_station_distance = self.monitor_distance_of_last_station
                        self.monitor_curr_train_distance_to_first_station = distance_of_curr_train_from_start # start is current station
                        self.monitor_distance_of_last_station = self.monitor_distance_of_first_station
                        self.monitor_distance_of_first_station = last_station_distance
                        
                        train_pos_in_range = True
            else:
                train_pos_on_timetable = distance_of_first_station - curr_distance_from_first_station
                if train_pos_on_timetable <= distance_of_first_station and train_pos_on_timetable >=self.monitor_distance_of_last_station:
                    train_pos_in_range = True
                else:
                    if train_pos_on_timetable < self.monitor_distance_of_last_station and self.pendelstations != []: # Pendelzug returns
                        if self.monitor_curr_train_distance_to_first_station-200 < distance_of_curr_train_from_start: # at first stop ignore direction change
                            self.monitor_curr_train_direction_of_travel = "down"                       
                        last_station_distance = self.monitor_distance_of_last_station
                        self.monitor_curr_train_distance_to_first_station = distance_of_curr_train_from_start # start is current station
                        self.monitor_distance_of_last_station = self.monitor_distance_of_first_station
                        self.monitor_distance_of_first_station = last_station_distance
                        
                        train_pos_in_range = True                
        curr_simu_time = self.monitor_time
        y = self.calculateTimePos(curr_simu_time)
        if curr_simu_time >= self.monitor_start_time and train_pos_in_range:
            x = self.determine_station_xy_point("",train_pos_on_timetable)[0]
            if self.monitor_curr_trainline_objectid == -1:
                self.monitor_points_count = 0
                self.monitor_trainLine_prop = self.get_line_properties("Monit_train")
                #self.monitor_curr_trainline_objectid = self.tt_canvas.create_line(x,y,x,y,fill="red",width=4)
                self.monitor_curr_trainline_objectid = self.monitor_create_line((x,y,x,y), self.monitor_trainLine_prop)
            else:
                line_coords = self.tt_canvas.coords(self.monitor_curr_trainline_objectid)
                self.monitor_points_count +=1
                if self.monitor_points_count == 10:
                    self.monitor_points_count = 0
                    line_coords = line_coords[:-18] # remove last 9 entries
                line_coords.extend([x,y])
                self.tt_canvas.coords(self.monitor_curr_trainline_objectid,line_coords)
                if fahrtext != "":
                    r = self.monitor_trainLine_prop["Width"]
                    fahrtext_objid = self.tt_canvas.create_oval(x-r,y-r, x+r, y+r, fill=self.monitor_trainLine_prop["Color"],outline=self.monitor_trainLine_prop["Color"],width=1, tags=(self.trainName,"MT_"+self.trainName,str(self.trainIdx)))
                    #train_line_objid = self.tt_canvas.create_line(self.trainLine_dict,fill=self.trainColor,width=self.trainLineWidth,activewidth=self.trainLineWidth*2,dash=self.TrainLineDashed,tags=(self.trainName,"L_"+self.trainName,str(self.trainIdx)))
                    self.controller.ToolTip_canvas(self.tt_canvas, fahrtext_objid, text=fahrtext, button_1=True)                                
        if showtimeline:
            if self.monitor_curr_timeline_objectid == -1:
                self.monitor_timeLine_prop = self.get_line_properties("Monit_time")
                self.monitor_curr_timeline_objectid = self.monitor_create_line((0,y,self.graphRight,y), self.monitor_timeLine_prop)
            else:
                self.tt_canvas.coords(self.monitor_curr_timeline_objectid,(self.graphLeft,y,self.graphRight,y))
            
                
        
        #self.create_circle(x, y, 3, self.tt_canvas)

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
        self.timeauto = self.controller.getConfigData("Bfp_TimeAuto")
        
        # xml_error_logger logger
        xml_logfilename = os.path.join(self.controller.userfile_dir, XML_ERROR_LOG_FILENAME)
        self.xml_error_logger = logging.getLogger("XML_Error")
        self.xml_error_logger.setLevel(LOG_LEVEL)
        self.xml_error_logger_file_handler = FileHandler(xml_logfilename,mode="w")
        self.xml_error_logger_file_handler.setLevel(LOG_LEVEL)
        self.xml_error_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))
        self.xml_error_logger.addHandler(self.xml_error_logger_file_handler)                
        
    def edit_train_schedule(self,objectid,mode):
        self.timetable.edit_train_schedule(objectid,mode)
        
    def edit_stop_original(self,objectid):
        self.timetable.edit_stop_original(objectid)
           
    def edit_export_to_trn(self,objectid):
        self.timetable.edit_export_to_trn(objectid)
        
    def edit_export_to_all_trn(self):
        self.timetable.edit_export_to_all_trn()    
        
    def edit_run_schedule(self,objectid,restart_fpn=True):
        self.timetable.edit_run_schedule(objectid,restart_fpn=restart_fpn)    
                
    def edit_clone_schedule(self,objectid):
        self.timetable.edit_clone_schedule(objectid)
        
    def edit_connect_ZUSI(self,objectid):
        self.timetable.edit_connect_ZUSI(objectid)
        
    def edit_disconnect_ZUSI(self,objectid):
        self.timetable.edit_disconnect_ZUSI(objectid)
    
    def show_trainNum_here(self,objectid,event):
        self.timetable.show_trainNum_here(objectid,event)
        
    def edit_remove_trainnum(self,objectid):
        self.timetable.edit_remove_trainnum(objectid)    
        
    def open_zusi_trn_zug_dict(self,trn_zug_dict,fpn_filepathname,trn_filepathname=""):
        TLFileType = self.controller.getConfigData("TLFileType",default="")
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
                if len(trn_filecomp)<2:
                    logging.info("Kein BuchfahrplanRohDatei Element gefunden %s%s %s", zugGattung,zugNummer,trn_filepath)
                    self.controller.set_statusmessage("Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath)
                    self.open_error = "Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath
                    return                    
                tt_xml__filepathname = os.path.join(trn_filepath,trn_filecomp[-2],asc_zugGattung+zugNummer+".timetable.xml")                
                if not os.path.exists(tt_xml__filepathname):
                    logging.info("Kein BuchfahrplanRohDatei Element gefunden %s%s %s", zugGattung,zugNummer,trn_filepath)
                    self.controller.set_statusmessage("Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath)
                    self.open_error = "Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath
                    return
            try:
                with open(tt_xml__filepathname,mode="r",encoding="utf-8") as fd:
                    xml_text = fd.read()
                    tt_xml_timetable_dict = parse(xml_text)
                    #enter train-timetable
                    #result_ok = self.timetable.convert_tt_xml_dict_to_schedule_dict(tt_xml_timetable_dict,trn_filepathname=trn_filepathname,fpn_filename=self.fpl_filename)
                    result_ok = self.timetable.convert_tt_xml_dict_to_schedule_dict(tt_xml_timetable_dict,trn_filepathname=trn_filepathname,fpn_filename=self.fpl_filename,trn_fahrplangruppe=fahrplan_gruppe,trn_zugnummer=zugNummer)
            except BaseException as e:
                logging.debug("open_zusi_trn_zug_dict - Error open file %s - %s",tt_xml__filepathname,e)
                self.controller.set_statusmessage("Fehler beim Öffnen der Datei \n" + tt_xml__filepathname)
                self.open_error = "Fehler in XML-Datei (Details siehe xml_error_logfile.log)\n" + tt_xml__filepathname
                self.xml_error_logger.debug("open_zusi_trn_zug_dict - Error open file %s - %s",tt_xml__filepathname,e)
                pass
        else:
            self.timetable.convert_trn_dict_to_schedule_dict(trn_zug_dict,trn_filepathname=trn_filepathname)        

    def open_zusi_trn_file(self, trn_filepathname,fpn_filepathname):
        try:
            with open(trn_filepathname,mode="r",encoding="utf-8") as fd:
                xml_text = fd.read()
                trn_dict = parse(xml_text)
            trn_zusi_dict = trn_dict.get("Zusi",{})
            trn_zug_dict = trn_zusi_dict.get("Zug",{})        
            self.open_zusi_trn_zug_dict(trn_zug_dict, fpn_filepathname,trn_filepathname=trn_filepathname)
        except BaseException as e:
            logging.debug("open_zusi_trn_file - Error open file %s - %s",trn_filepathname,e)
            self.xml_error_logger.debug("open_zusi_trn_file - Error open file %s - %s",trn_filepathname,e)
            self.controller.set_statusmessage("Fehler beim Öffnen der Datei \n" + trn_filepathname)
            self.open_error = "Fehler in XML-Datei (Details siehe xml_error_logfile.log)\n" + trn_filepathname
            pass
            

    def open_zusi_master_schedule(self,fpn_filename=""):
        try:
            self.open_error = ""
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
                self.xml_error_logger.debug("ZUSI Entry not found")
                self.controller.set_statusmessage("Error: ZUSI entry not found in file: "+fpn_filename)
                self.open_error = "Error: ZUSI entry not found in file: "+fpn_filename
                return False
            fahrplan_dict = zusi_dict.get("Fahrplan",{})
            if fahrplan_dict == {}:
                logging.info("Fahrplan Entry not found")
                self.xml_error_logger.debug("Fahrplan Entry not found")
                self.controller.set_statusmessage("Error: Fahrplan entry not found in fpl-file: "+fpn_filename)
                self.open_error = "Error: Fahrplan entry not found in fpl-file: "+fpn_filename
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
                    found=False
                    if not os.path.isfile(trn_file_and_path):
                        # check in private ZUSI directory
                        zusi_private_path = self.controller.getConfigData("Bfp_ZUSI_Dir_privat")
                        if zusi_private_path:
                            trn_file_and_path_pr = os.path.join(zusi_private_path,trn_filename)
                            if os.path.isfile(trn_file_and_path_pr):
                                trn_file_and_path = trn_file_and_path_pr
                                found = True
                        if not found:
                            # check in official ZUSI directory
                            zusi_official_path = self.controller.getConfigData("Bfp_ZUSI_Dir_official")
                            if zusi_official_path:
                                trn_file_and_path_of = os.path.join(zusi_official_path,trn_filename)
                                if os.path.isfile(trn_file_and_path_of):
                                    trn_file_and_path = trn_file_and_path_of
                    self.controller.set_statusmessage("Erzeuge ZUSI-Fahrplan - "+trn_file_and_path)
                    self.controller.update()
                    self.open_zusi_trn_file(trn_file_and_path,fpn_filename)
            if self.open_error == "":
                self.controller.set_statusmessage(" ")
            else:
                self.controller.set_statusmessage(self.open_error)
            return True
        
        except BaseException as e:
            v=inspect.trace()[-1]
            logging.debug("open_zusi_master_schedule - Error open file %s - %s - Line: %s - Procedure: %s",fpn_filename,e, v[2],v[3])
            self.xml_error_logger.debug("open_zusi_master_schedule - Error open file %s - %s",fpn_filename,e)
            self.controller.set_statusmessage("Fehler beim Öffnen der Datei \n" + fpn_filename)
    
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
            
            FplRglGgl_str = self.controller.getConfigData("FplRglGgl",default="")
            if FplRglGgl_str =="":
                FplRglGgl_str = "1,2"
            self.FplRglGgl = FplRglGgl_str.split(",")

            FplZeile_list = Buchfahrplan_dict.get("FplZeile",{})
            if FplZeile_list=={}:
                logging.info("timetable.xml file error: %s",trn_dateiname )
                self.xml_error_logger.debug("timetable.xml file error: %s",trn_dateiname )
                self.controller.set_statusmessage("Error: ZUSI entry not found in fpl-file: "+trn_dateiname)
                self.open_error = "Error: ZUSI entry not found in fpl-file: "+trn_dateiname
                return False
            for FplZeile_dict in FplZeile_list:
                try:
                    FplRglGgl=FplZeile_dict.get("@FplRglGgl","")
                except:
                    print("Error:",repr(FplZeile_dict))
                if (FplRglGgl !="") and not (FplRglGgl in self.FplRglGgl):
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
                richtungswechsel = FplEintrag.get("@FzgVerbandAktion","") == "2"
                if richtungswechsel:
                    break
        return station_list
    
    def create_zusi_trn_list_from_zug_dict(self,trn_zug_dict, trn_filepath,trn_filepathname=None):
        fahrplan_gruppe = trn_zug_dict.get("@FahrplanGruppe","")
        zugGattung = trn_zug_dict.get("@Gattung","")
        zugNummer = trn_zug_dict.get("@Nummer","")
        zugLauf = trn_zug_dict.get("@Zuglauf","")
        Buchfahrplan_dict = trn_zug_dict.get("BuchfahrplanRohDatei",{})
        Bfpl_Dateiname = Buchfahrplan_dict.get("@Dateiname","")
        if Bfpl_Dateiname != "":
            Bfpl_file_path, Bfpl_file_name = os.path.split(Bfpl_Dateiname)
            Bfpl_filepathname = os.path.join(trn_filepath,Bfpl_file_name)
            if not os.path.exists(Bfpl_filepathname):
                logging.info("Kein BuchfahrplanRohDatei Element gefunden %s%s %s", zugGattung,zugNummer,trn_filepath)
                if trn_filepathname!=None and self.controller.allow_TRN_files:
                    Bfpl_filepathname = trn_filepathname
                    logging.info("Bfpl_FilePathName %s ", trn_filepathname)

        else:
            asc_zugGattung = zugGattung.replace("Ü","Ue").replace("ü","ue").replace("Ä","Ae").replace("ä","ae").replace("Ö","Oe").replace("ö","oe")
            Bfpl_filepathname = os.path.join(trn_filepath,asc_zugGattung+zugNummer+".timetable.xml")                
            if not os.path.exists(Bfpl_filepathname):
                logging.info("Kein BuchfahrplanRohDatei Element gefunden %s%s %s", zugGattung,zugNummer,trn_filepath)
                self.xml_error_logger.info("Kein BuchfahrplanRohDatei Element gefunden %s%s %s", zugGattung,zugNummer,trn_filepath)
                self.controller.set_statusmessage("Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath)
                self.open_error = "Fehler: Kein BuchfahrplanRohDatei Element in der .trn Datei gefunden: "+zugGattung+zugNummer+"-"+trn_filepath
                return              
        station_list = self.get_station_list(trn_zug_dict)
        zusi_fahrplan_gruppe_dict = self.zusi_zuglist_dict.get(fahrplan_gruppe,{})
        station_list_str = repr(station_list)
        if zusi_fahrplan_gruppe_dict == {}:
            self.zusi_zuglist_dict[fahrplan_gruppe] = {zugGattung+zugNummer: station_list_str}
        else:
            if self.controller.showalltrains:
                self.zusi_zuglist_dict[fahrplan_gruppe][zugGattung+zugNummer] = station_list_str
            else: # check if a similar train is already in fahrplan_gruppe
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
        try:
            with open(trn_filepathname,mode="r",encoding="utf-8") as fd:
                xml_text = fd.read()
                trn_dict = parse(xml_text)
        except BaseException as e:
            logging.debug("open_zusi_trn_zug_dict - Error open file %s \n %s",trn_filepathname,e)
            self.xml_error_logger.info("open_zusi_trn_zug_dict - Error open file %s \n %s",trn_filepathname,e)
            self.controller.set_statusmessage("Fehler beim Öffnen der Datei \n" + trn_filepathname)
            self.open_error = "Fehler in XML-Datei (Details siehe xml_error_logfile.log)\n" + trn_filepathname
            return
        trn_filepath, trn_filename = os.path.split(trn_filepathname)
        trn_zusi_dict = trn_dict.get("Zusi")
        if trn_zusi_dict == {}:
            logging.info("ZUSI Entry not found")
            self.xml_error_logger.info("ZUSI Entry not found")
            self.controller.set_statusmessage("Error: ZUSI entry not found in trn-file: "+trn_filepathname)
            self.open_error = "Error: ZUSI entry not found in trn-file: "+trn_filepathname
            return
        trn_zug_dict = trn_zusi_dict.get("Zug")
        self.create_zusi_trn_list_from_zug_dict(trn_zug_dict, trn_filepath,trn_filepathname=trn_filepathname)
        return

    def create_zusi_zug_liste(self, fpn_filename=""):
        if fpn_filename == "": return
        fpl_path, fpl_file = os.path.split(fpn_filename)
        #print('Input File, %s.' % fpn_filename)
        try:
            with open(fpn_filename,mode="r",encoding="utf-8") as fd:
                xml_text = fd.read()
                self.zusi_master_timetable_dict = parse(xml_text)
        except BaseException as e:
            logging.debug("open_zusi_trn_zug_dict - Error open file %s \n %s",fpn_filename,e)
            self.xml_error_logger.debug("open_zusi_trn_zug_dict - Error open file %s \n %s",fpn_filename,e)
            self.controller.set_statusmessage("Fehler beim Öffnen der Datei \n" + fpn_filename)
            self.open_error = "Fehler in XML-Datei (Details siehe xml_error_logfile.log)\n" + fpn_filename
            return
        zusi_dict = self.zusi_master_timetable_dict.get("Zusi")
        if zusi_dict == {}:
            logging.info("ZUSI Entry not found")
            self.xml_error_logger.info("ZUSI Entry not found")
            self.controller.set_statusmessage("Error: ZUSI entry not found in fpn-file: "+fpn_filename)
            self.open_error = "Error: ZUSI entry not found in fpn-file: "+fpn_filename
            return {}
        fahrplan_dict = zusi_dict.get("Fahrplan")
        zug_list = fahrplan_dict.get("Zug",{})
        if fahrplan_dict == {}:
            logging.info("Fahrplan Entry not found")
            self.xml_error_logger.info("Fahrplan Entry not found")
            self.controller.set_statusmessage("Error: Fahrplan entry not found in fpn-file: "+fpn_filename)
            self.open_error = "Error: Fahrplan entry not found in fpn-file: "+fpn_filename
            return {}
        self.zusi_zuglist_dict = {}
        self.zusi_zuglist_xmlfilename_dict ={}
        if zug_list == {}:
            # integrate fpl file
            for trn_zug_dict in fahrplan_dict.get("trn",{}):
                file_name, file_extension = os.path.splitext(fpn_filename)
                trn_filepath = os.path.join(fpl_path,file_name)
                self.create_zusi_trn_list_from_zug_dict(trn_zug_dict, trn_filepath,trn_filepathname=None)
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

    def regenerate_canvas(self):
        self.controller.timetable_activ = False
        #first_call = True
        if not self.ttpage.canvas_init:
            self.canvas.delete("all")
            #self.ttpage.canvas_unbind()
            #self.ttpage.canvas.destroy()
            #self.ttpage.canvas = None
            self.canvas = self.ttpage.create_canvas()
            self.controller.tooltip_var_dict={}
        self.ttpage.canvas_init = False
        self.controller.total_scalefactor = 1
        self.canvas.config(width=self.canvas_width,height=self.canvas_height,scrollregion=(0,0,self.canvas_width,self.canvas_height))
        logging.debug("Regenerate_CANVAS - Canvas_height %s, width %s",self.canvas_height,self.canvas_width)
        self.canvas.update()
        self.controller.set_statusmessage("Erzeuge Bahnhofsliste - "+self.xml_filename)
        self.controller.update()
        #print('Input File master train timetable, %s.' % xml_filename)
        with open(self.xml_filename,mode="r",encoding="utf-8") as fd:
            xml_text = fd.read()
            zusi_timetable_dict = parse(xml_text)
        self.timetable = TimeTableGraphCommon(self.controller, True, self.height, self.width,xml_filename=self.xml_filename,fpn_filename=self.fpl_filename,ttmain_page=self,tt_page=self.ttpage)
        self.timetable.set_tt_traintype_prop(self.main_traintype_prop_dict)
        #define stops via selected train-timetable
        if os.path.splitext(self.xml_filename)[1]==".trn":
            trn_zusi_dict = zusi_timetable_dict.get("Zusi",{})
            trn_zug_dict = trn_zusi_dict.get("Zug",{})
            result_ok = self.timetable.convert_trn_dict_to_schedule_dict(trn_zug_dict,define_stations=True,trn_filepathname=self.xml_filename)     
        else:
            result_ok = self.timetable.convert_tt_xml_dict_to_schedule_dict(zusi_timetable_dict,define_stations=True,fpn_filename=self.fpl_filename)
        if  not result_ok:
            return
        result_ok = self.open_zusi_master_schedule(fpn_filename=self.fpl_filename)
        if not result_ok:
            return
        self.editflag = self.controller.getConfigData("Edit_Permission",default="") in ("Edit_allowed","Fast_Edit_allowed")
        self.fast_editflag = self.controller.getConfigData("Edit_Permission",default="") == "Fast_Edit_allowed"
        self.starthour = self.controller.getConfigData("Bfp_start")
        self.timeauto = self.controller.getConfigData("Bfp_TimeAuto")
        if self.timeauto:
            duration = self.timetable.FPL_endtime - self.timetable.FPL_starttime
            if self.canvas_height <= duration * 300:
                self.canvas_height = duration * 300
                self.canvas.config(width=self.canvas_width,height=self.canvas_height,scrollregion=(0,0,self.canvas_width,self.canvas_height))
            
        self.timetable.doPaint(self.canvas,starthour=self.starthour,duration=self.duration,timeauto=self.timeauto)
        if self.controller.ZUSI_monitoring_started:
            self.edit_connect_ZUSI(0)
        if self.editflag:
            self.edit_train_schedule(-1,"single")        

    def redo_fpl_and_canvas(self,width,height, starthour=8, duration=9,fpl_filename="", xml_filename = ""):
        self.fpl_filename = fpl_filename
        self.xml_filename = xml_filename
        self.width = width
        self.canvas_width = width
        self.height = height
        self.canvas_height = height
        self.starthour = starthour
        self.duration = duration
        self.regenerate_canvas()
        return

    def set_traintype_prop(self,traintype_prop_dict):
        self.main_traintype_prop_dict = traintype_prop_dict
        
    def FS_calculate_distance(self,FS_km):
        print(FS_km)
        print(self.FS_laststationIdx,self.FS_laststationname)
        FS_km_value = float(FS_km)
        laststationkm = self.timetable.schedule_stations_dict[self.FS_laststationIdx].get("StationKm",-1)
        neukm = self.timetable.schedule_stations_dict[self.FS_laststationIdx].get("Neukm",-1)
        if neukm > 0: 
            laststationkm = neukm
        laststationdistance = self.timetable.schedule_stations_dict[self.FS_laststationIdx].get("Distance",-1)
        nextstationkm = self.timetable.schedule_stations_dict[self.FS_nextstationIdx].get("StationKm",-1)
        distance = -1
        if FS_km_value >= laststationkm:
            if FS_km_value <= nextstationkm:
                distance = laststationdistance + FS_km_value-laststationkm
        else:
            if FS_km_value >= nextstationkm:
                distance = laststationdistance + laststationkm - FS_km_value
        return distance
        
    def import_one_Fahrtenschreiber(self,fileName):
        logging.info("import_one_Fahrtenschreiber - %s\n",fileName)
        try:
            timetable = self.timetable
        except:
            tk.messagebox.showerror("Fahrtenschreiber Import - Fehler", "Es wurde noch kein Bildfahrplan erstellt, in den die Fahrtenschreiber importiert werden können")
            logging.info("Fahrtenschreiber Import - Fehler: Es wurde noch kein Bildfahrplan erstellt, in den die Fahrtenschreiber importiert werden können")
            return
        
        try:
            with open(fileName,mode="r",encoding="utf-8") as fd:
                xml_text = fd.read()
                zusi_Fahrtenschreiber_dict = parse(xml_text)
                #repr(zusi_Fahrtenschreiber_dict)
        except BaseException as e:
            logging.debug("import_one_Fahrtenschreiber - Error open file %s \n %s",fileName,e)
            self.xml_error_logger.debug("import_one_Fahrtenschreiber - Error open file %s \n %s",fileName,e)
            self.controller.set_statusmessage("Fehler beim Öffnen der Datei \n" + fileName)
            self.open_error = "Fehler in XML-Datei (Details siehe xml_error_logfile.log)\n" + fileName
            return
        zusi_dict = zusi_Fahrtenschreiber_dict.get("Zusi")
        if zusi_dict == {}:
            logging.info("ZUSI Entry not found")
            self.xml_error_logger.info("ZUSI Entry not found")
            self.controller.set_statusmessage("Error: ZUSI entry not found in Fahrtenschreiber-file: "+fileName)
            self.open_error = "Error: ZUSI entry not found in Fahrtenschreiber-file: "+fileName
            return {}
        #info_dict = zusi_dict.get("Info")
        #print(repr(info_dict))
        result_dict = zusi_dict.get("result")
        if result_dict == {}:
            logging.info("Result Entry not found")
            self.xml_error_logger.info("Result Entry not found")
            self.controller.set_statusmessage("Error: Result entry not found in Fahrtenschreiber-file: "+fileName)
            self.open_error = "Error: Result entry not found in Fahrtenschreiber-file: "+fileName
            return {}        
        #print(repr(result_dict))
        self.FS_trainNumber = result_dict.get("@Zugnummer",0)
        print("Zugnummer:",self.FS_trainNumber)
        self.FS_trainIdx = self.timetable.get_trn_train_idx_from_TrainNumber(self.FS_trainNumber)
        if self.FS_trainIdx == -1:
            print(self.FS_trainNumber, "not found in trainlist")
            logging.info("Fahrtenschreiber: Trainnumber not found in current Trainlist:"+self.FS_trainNumber)
            self.controller.set_statusmessage("Fahrtenschreiber: Trainnumber not found in current Trainlist:"+self.FS_trainNumber)
            timetable.tt_canvas.update()
            return
        self.FS_train_stops = self.timetable.get_trainline_data(self.FS_trainIdx, "Stops")
        FS_stoplist = self.timetable.get_trainline_data(self.FS_trainIdx, "Stoplist")
        FS_train_stops=self.FS_train_stops
        #print(repr(self.FS_train_stops))

        FahrtEintrag_list = result_dict.get("FahrtEintrag",{})
        self.controller.set_statusmessage("Importiere Fahrtenschreiber - "+ fileName) 
        if FahrtEintrag_list == {}:
            logging.info("FahrEintrag Entry not found"+fileName)
            self.xml_error_logger.info("FahrtEintrag Entry not found" +fileName)
            self.controller.set_statusmessage("Error: FahrtEintrag entry not found in fpn-file: "+fileName)
            self.open_error = "Error: FahrtEintrag entry not found in fpn-file: "+fileName
            timetable.tt_canvas.update()
            return {}
        
        # init monitoring data
        timetable.monitor_start = False
        timetable.monitor_timetable_updated = False
        timetable.monitor_distance_of_first_station = 0
        timetable.monitor_distance_of_last_station = 0
        timetable.monitor_curr_train_distance_to_first_station = 0
        timetable.monitor_curr_train_direction_of_travel = ""        
        timetable.monitor_currdist = 0
        timetable.monitor_currkm = 0
        timetable.monitor_time = 0
        timetable.monitor_currspeed = 0
        timetable.controller.ZUSI_monitoring_started = True
        timetable.monitor_curr_trainline_objectid = -1
        timetable.monitor_curr_timeline_objectid = -1
        timetable.monitor_start_time = 0
        timetable.monitor_panel_con_status_objectid = -1
        timetable.monitor_panel_currfpn_objectid  = -1
        timetable.monitor_start = True
        timetable.trainName = self.FS_trainNumber
        timetable.monitor_tooltiptext = "Fahrtenschreiber Zug:"+ self.FS_trainNumber
        
        firststopdistance = -1
        FS_startstation_idx = 0
        
        fahrtwegstart = None
        
        #determine_start_station_idx
        for FahrtEintrag in FahrtEintrag_list:
            #print(repr(FahrtEintrag))
            FahrtTyp = FahrtEintrag.get("@FahrtTyp","")
            self.FS_laststationIdx = -1
            if FahrtTyp!="":
                if FahrtTyp=="2":
                    fahrtweg = float(FahrtEintrag.get("@FahrtWeg",-1))
                    if fahrtweg == -1:
                        FS_startstation_name = FahrtEintrag.get("@FahrtText",{})
                        #for train_stop_idx in self.FS_train_stops:
                        #    train_stop_dict = self.FS_train_stops.get(train_stop_idx,{})
                        #    if train_stop_dict != {}:
                        #        startstation_idx = train_stop_dict.get("StationIdx",-1)
                        #        if startstation_idx != -1:
                        #            stopname = self.timetable.schedule_stations_dict[startstation_idx].get("StationName","")
                        #        if stopname == FS_startstation_name:
                        #            FS_startstation_idx = train_stop_idx
                        #            break
                        try:
                            FS_startstation_idx = FS_stoplist.index(FS_startstation_name)
                        except:
                            FS_startstation_idx = 0
                        break # only check the first Fahrttyp 2 entry

        train_stop_dict = self.FS_train_stops.get(FS_startstation_idx,{})
        stopidx = train_stop_dict.get("StationIdx",-1)
        if stopidx != -1:
            stopname = self.timetable.schedule_stations_dict[stopidx].get("StationName","")
            stopdistance = self.timetable.schedule_stations_dict[stopidx].get("Distance","")
            firststopdistance=stopdistance
            timetable.monitor_distance_of_first_station = firststopdistance
        train_stop_dict = self.FS_train_stops.get(len(self.FS_train_stops)-1,{})
        stopidx = train_stop_dict.get("StationIdx",-1)
        if stopidx != -1:
            stopname = self.timetable.schedule_stations_dict[stopidx].get("StationName","")
            stopdistance = self.timetable.schedule_stations_dict[stopidx].get("Distance","")
            laststopdistance=stopdistance
            timetable.monitor_distance_of_last_station = laststopdistance                
        
        self.controller.simu_timetable_dict = {}
        
        
        timetable.monitor_set_status(fileName, self.FS_trainNumber, False)
        timetable.monitor_set_timetable_updated(trainIdx=self.FS_trainIdx)
        timetable.monitor_distance_of_first_station = firststopdistance
        
        
        #print(repr(self.timetable.schedule_stations_dict))
        lastfahrtext = ""

        for FahrtEintrag in FahrtEintrag_list:
            #print(repr(FahrtEintrag))
            FahrtTyp = FahrtEintrag.get("@FahrtTyp","")
            self.FS_laststationIdx = -1
            if FahrtTyp!="":
                tooltip_message = "Fahrttyp: " + FahrtTyp + "\nFahrtkm: " + FahrtEintrag.get("@Fahrtkm","") + "\nFahrtWeg: " + FahrtEintrag.get("@FahrtWeg","")+ "\nFahrtText: "+ FahrtEintrag.get("@FahrtText","")
                if lastfahrtext =="":
                    lastfahrtext= tooltip_message
                else:
                    try:
                        lastfahrtext= lastfahrtext + "\n---------------------------\n" + tooltip_message
                    except:
                        print(repr(FahrtEintrag.get("@FahrtText","")))
                if FahrtTyp=="x": #2":
                    self.FS_laststationname = FahrtEintrag.get("@FahrtText","")
                    temp_laststationIdx = -1
                    
                    for train_stop_idx in self.FS_train_stops:
                        train_stop_dict = self.FS_train_stops.get(train_stop_idx,{})
                        if train_stop_dict != {}:
                            stopidx = train_stop_dict.get("StationIdx",-1)
                            if stopidx != -1:
                                stopname = self.timetable.schedule_stations_dict[stopidx].get("StationName","")
                            if stopname == self.FS_laststationname:
                                temp_laststationIdx = train_stop_idx
                                stopdistance = self.timetable.schedule_stations_dict[stopidx].get("Distance","")
                                if firststopdistance == -1:
                                    firststopdistance=stopdistance
                                    timetable.monitor_distance_of_first_station = firststopdistance
                                break
                    #print(self.FS_laststationname, temp_laststationIdx)
                    if temp_laststationIdx >-1:
                        self.FS_laststationIdx = temp_laststationIdx
                        self.FS_nextstationIdx = len(self.timetable.schedule_stations_dict)-1
                        for station_idx in range(temp_laststationIdx+1,len(self.timetable.schedule_stations_dict)):
                            neukm = self.timetable.schedule_stations_dict[station_idx].get("Neukm",-1)
                            if neukm >0:
                                self.FS_nextstationIdx = station_idx
                                break
            else:
                if firststopdistance > -1:
                    
                    if fahrtwegstart==None:
                        fahrtwegstart = float(FahrtEintrag.get("@FahrtWeg",{}))
                    FahrtZeit_str = FahrtEintrag.get("@FahrtZeit",{})
                    Fahrtkm  = FahrtEintrag.get("@Fahrtkm",{})
                    Fahrtweg = float(FahrtEintrag.get("@FahrtWeg",{}))
                    timetable.monitor_dist = Fahrtweg -fahrtwegstart
                    #print("FahrtZeit:",FahrtZeit_str, " - Delta Fahrtweg:", timetable.monitor_dist, "- First_stop_distance:", firststopdistance)
                    #print("Fahrtkm:",Fahrtkm)
                    FahrtDistance = 0 #self.FS_calculate_distance(Fahrtkm)
                    #print("Distanz:",FahrtDistance)
                    #print("Fahrtweg:",Fahrtweg)
                    
                    #print("Delta Fahrtweg:", timetable.monitor_dist)
                    
                    dt = datetime.strptime(FahrtZeit_str, "%Y-%m-%d %H:%M:%S")
                    
                    timetable.monitor_hour = dt.hour
                    timetable.monitor_minute = dt.minute
                    timetable.monitor_second = dt.second
                    
                    timetable.monitor_set_time(timetable.monitor_hour,timetable.monitor_minute,timetable.monitor_second)
                    
                    timetable.monitor_set_dist(timetable.monitor_dist)
                    
                    timetable.monitor_update_train_pos(train_idx=self.FS_trainIdx,showtimeline=False,fahrtext=lastfahrtext)
                    lastfahrtext = ""
                    
                    timetable.monitor_start = False
        
        timetable.tt_canvas.update()
        logging.info("import_one_Fahrtenschreiber finished - %s \n",fileName)
                    
                     
               