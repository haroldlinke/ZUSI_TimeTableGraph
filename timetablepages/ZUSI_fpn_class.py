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
from xml.dom import minidom
import xml.etree.ElementTree as ET
import logging

# ----------------------------------------------------------------
# Class ConfigurationPage
# ----------------------------------------------------------------
class ZUSI_fpn():

    def __init__(self, fpn_filepathname, controller):
        logging.debug("Init ZUSI_fpn: " + fpn_filepathname)
        self.controller = controller
        self.fpn_filepathname = fpn_filepathname
        
    def read_fpn_file_as_dict(self):
        logging.debug("read_fpn_as_dict ZUSI_fpn: " + self.fpn_filepathname)
        try:
            with open(self.fpn_filepathname,mode="r",encoding="utf-8") as fd:
                xml_text = fd.read()
            self.fpn_dict = parse(xml_text)
            return True
        except BaseException as e:
            logging.debug("Init ZUSI_fpn Error: " + self.fpn_filepathname + "\n"+ e)
            return False
            
    def get_fpn_dict(self):
        return self.fpn_dict
    
    def read_fpn_file_as_xml(self,backup=False):
        try:
            logging.debug("read_fpn_file_as_xml: " + self.fpn_filepathname)
            self.fpn_tree = ET.parse(self.fpn_filepathname)
            if backup:
                self.fpn_tree.write(self.fpn_filepathname+".bak",encoding="UTF-8",xml_declaration=True)
            self.fpn_root = self.fpn_tree.getroot()
            self.edit_update_logfile = open(self.fpn_filepathname+".update.log", 'w', encoding='utf-8')
            return True
        except BaseException as e:
            logging.debug("read_fpn_file_as_xml Error: " + self.fpn_filepathname + "\n"+ str(e))
            return False            
    
    def write_fpn_file_from_xml(self,fpn_filepathname = ""):
        try:
            if fpn_filepathname == "":
                fpn_filepathname = self.fpn_filepathname
            #self.fpn_tree.write(fpn_filepathname,encoding="UTF-8",xml_declaration=True)
            logging.debug("write_fpn_file_from_xml: " + fpn_filepathname)    
            root = self.fpn_tree.getroot()
            raw = ET.tostring(root, encoding='unicode', method='xml')
            pretty = raw.replace("><",">\n<")
            with open(fpn_filepathname, 'w') as f:
                print(pretty)
                f.write(pretty)
            if fpn_filepathname == self.fpn_filepathname:
                self.edit_update_logfile.close()
            return True
        except BaseException as e:
            logging.debug("write_fpn_file_from_xml Error: %s \n %s" ,self.fpn_filepathname,e)
            return False           
    
    def add_fpn_zug_entry(self,trn_filepathname):
        trn_filedeltapathname = "Timetables"+trn_filepathname.split("Timetables")[1]
        fahrplan_tag = self.fpn_root.find("Fahrplan")
        zug_tag = ET.Element("Zug")
        datei_tag = ET.Element("Datei")
        datei_tag.set("Dateiname",trn_filedeltapathname)
        zug_tag.append(datei_tag)
        fahrplan_tag.insert(2,zug_tag)
        self.edit_update_logfile.write("Added: "+trn_filedeltapathname+"\n")
        pass
    
    def get_elememt_list(self,element_tree_str):
        return self.fpn_root.findall(element_tree_str) # ('Zug/FahrplanEintrag'):
    
    
    
    
    
    
 

