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

from tools.xmltodict import parse
import xml.etree.ElementTree as ET
import logging
from datetime import datetime

# ----------------------------------------------------------------
# Class ConfigurationPage
# ----------------------------------------------------------------
class ZUSI_trn():

    def __init__(self, trn_filepathname, controller):
        logging.debug("Init ZUSI_trn: " + trn_filepathname)
        self.controller = controller
        self.trn_filepathname = trn_filepathname
        
    def read_trn_file_as_dict(self):
        logging.debug("read_trn_as_dict ZUSI_trn: " + self.trn_filepathname)
        try:
            with open(self.trn_filepathname,mode="r",encoding="utf-8") as fd:
                xml_text = fd.read()
            self.trn_dict = parse(xml_text)
            return True
        except BaseException as e:
            logging.debug("Init ZUSI_trn Error: " + self.trn_filepathname + "\n"+ e)
            return False
            
    def get_trn_dict(self):
        return self.trn_dict
    
    def read_trn_file_as_xml(self,backup=False):
        try:
            logging.debug("read_trn_file_as_xml: " + self.trn_filepathname)
            self.trn_tree = ET.parse(self.trn_filepathname)
            if backup:
                self.trn_tree.write(self.trn_filepathname+".bak",encoding="UTF-8",xml_declaration=True)
            self.trn_root = self.trn_tree.getroot()
            return True
        except BaseException as e:
            logging.debug("read_trn_file_as_xml Error: " + self.trn_filepathname + "\n"+ str(e))
            return False            
    
    def write_trn_file_from_xml(self,trn_filepathname = ""):
        try:
            logging.debug("write_trn_file_from_xml: " + self.trn_filepathname)        
            if trn_filepathname == "":
                trn_filepathname = self.trn_filepathname
            self.trn_tree.write(trn_filepathname,encoding="UTF-8",xml_declaration=True)
            return True
        except BaseException as e:
            logging.debug("write_trn_file_from_xml Error: " + self.trn_filepathname + "\n"+ e)
            return False

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
    
    def update_time_entries(self,deltatime):
        for FahrplanEintrag_tag in self.trn_root.findall('Zug/FahrplanEintrag'):
            ank = FahrplanEintrag_tag.get('Ank')
            if ank != None:
                new_ank = self.calculate_updated_time(ank,deltatime)
                FahrplanEintrag_tag.set("Ank",new_ank)
            abf = FahrplanEintrag_tag.get('Abf')            
            if abf != None:
                new_abf = self.calculate_updated_time(abf,deltatime)
                FahrplanEintrag_tag.set("Abf",new_abf)                
        pass
    
    def update_train_entry(self,gattung,nummer):
        for zug_tag in self.trn_root.findall('Zug'):
            zug_tag.set("Gattung",gattung)
            zug_tag.set("Nummer",nummer)
        pass    
    
    def get_elememt_list(self,element_tree_str):
        return self.trn_root.findall(element_tree_str) # ('Zug/FahrplanEintrag'):
    
    
    
    
    
    
 

