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


from timetablepages.ConfigPageTemplate import ConfigPagetemplate
from timetablepages.ZUSI_TCP_class import ZUSI_TCP
import logging
from tools.xmltodict import parse

# ----------------------------------------------------------------
# Class ConfigurationPage
# ----------------------------------------------------------------
class TCPConfigPage(ConfigPagetemplate):

    def __init__(self, parent, controller):
        
        self.tabClassName = "TCPConfigPage"
        super().__init__(parent, controller, self.tabClassName)
        self.monitor_dist = 0
        self.monitor_km = 0
        self.monitor_hour = 0
        self.monitor_minute = 0
        self.monitor_second = 0
        self.monitor_fpn_filepathname= ""
        self.monitor_trainNumber = ""
        self.monitor_ladepause = False
        return
    
    def connect_to_ZUSI_server(self):
        self.controller.ZUSI_TCP_var.addcallbackforNeededFunctions(0x000A,(0x01,),self.cb_speed)
        self.controller.ZUSI_TCP_var.addcallbackforNeededFunctions(0x000A,(0x10,0x11,0x12),self.cb_time)
        self.controller.ZUSI_TCP_var.addcallbackforNeededFunctions(0x000A,(0x19,0x61,),self.cb_distance)
        self.controller.ZUSI_TCP_var.addcallbackforNeededFunctions(0x000C,(0x01,0x02),self.cb_status,valuetype="String")
        self.controller.ZUSI_TCP_var.addcallbackforNeededFunctions(0x000C,(0x04,),self.cb_status,valuetype="Datei")
        self.controller.ZUSI_TCP_var.addcallbackforNeededFunctions(0x000C,(0x03,),self.cb_status,valuetype="Byte")
        if self.controller.ZUSI_TCP_var.open_connection(callback=self.cb_connection_status):
            self.after(1000,self.controller.ZUSI_TCP_var.sendNeededData)
            return True
        else:
            return False
        
    def disconnect_from_ZUSI_server(self):
        self.controller.ZUSI_TCP_var.close_connection()
        
    def cancel(self):
        self.save_config()
        self.controller.ZUSI_TCP_var.close_connection()
        
    def cb_connection_status(self,status="",message=""):
        self.connection_status = status
        self.controller.timetable_main.timetable.monitor_set_connection_status(status, message)
        
    def cb_time(self,event):
        if self.controller.ZUSI_monitoring_started and self.controller.timetable_activ:
            print("cb_time:", repr(event))
            if event["Attribute"]== 16: # hour
                self.monitor_hour = int(event["Value"])
            elif event["Attribute"]== 17: # minute
                self.monitor_minute = int(event["Value"])
            elif event["Attribute"]== 18: # second
                self.monitor_second = int(event["Value"])
                self.controller.timetable_main.timetable.monitor_set_time(self.monitor_hour,self.monitor_minute,self.monitor_second)
    
    def cb_distance(self,event):
        if self.controller.ZUSI_monitoring_started and self.controller.timetable_activ:
            print("cb_distance:", repr(event))
            if event["Attribute"]== 25: # distance
                self.monitor_dist = int(event["Value"])
                self.controller.timetable_main.timetable.monitor_set_dist(self.monitor_dist)   
            elif event["Attribute"]== 97: # km
                self.monitor_km = event["Value"]
                self.controller.timetable_main.timetable.monitor_set_km(self.monitor_km) 
                
    def cb_speed(self,event):
        if self.controller.ZUSI_monitoring_started and self.controller.timetable_activ:
            print("cb_speed:", repr(event))
            self.monitor_speed = event["Value"]
            self.controller.timetable_main.timetable.monitor_set_speed(self.monitor_speed)   
    
    def cb_status(self,event):
        if self.controller.ZUSI_monitoring_started:
            print("cb_status:", repr(event))
            if event["Attribute"]== 1: #
                self.monitor_fpn_filepathname= event["Value"]
            elif event["Attribute"]== 2: # 
                self.monitor_trainNumber = event["Value"]
            elif event["Attribute"]== 3: # 
                self.monitor_ladepause = bool(event["Value"])
            elif event["Attribute"]== 4: # 
                timetable_file = event["Value"]
                timetable_str = str(timetable_file,"UTF-8") # String
                xml_start = timetable_str.find("<?xml")
                if xml_start != -1:
                    timetable_str = timetable_str[xml_start:]
                    #print("timetable_str:",timetable_str)
                    self.controller.simu_timetable_dict = parse(timetable_str)
                    self.controller.timetable_main.timetable.monitor_set_timetable_updated()   
            self.controller.timetable_main.timetable.monitor_set_status(self.monitor_fpn_filepathname,self.monitor_trainNumber,self.monitor_ladepause)
                
        