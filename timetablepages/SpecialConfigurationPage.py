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
from tools.xmltodict import parse
import logging

# ----------------------------------------------------------------
# Class SpecialConfigurationPage
# ----------------------------------------------------------------
class SpecialConfigurationPage(ConfigPagetemplate):

    def __init__(self, parent, controller):
        
        self.tabClassName = "SpecialConfigurationPage"
        super().__init__(parent, controller, self.tabClassName, generic_methods=None) 
        
        self.get_stationlist_for_station_chooser()
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

    
    def get_stationlist_for_station_chooser(self):
        
        self.controller.get_stationlist_for_station_chooser()
        return
    """
        xml_filename = self.getConfigData("Bfp_trainfilename")
        self.stationlist = self.controller.get_stationlist_from_tt_xml(xml_filename)
        self.controller.set_macroparam_val("SpecialConfigurationPage", "StationChooser", self.stationlist)
        paramkey = "StationChooser"
        configdatakey = self.controller.getConfigDatakey(paramkey)
        value = self.getConfigData(configdatakey)
        listbox_var = self.controller.macroparams_var[self.tabClassName][paramkey]
        for i in range(0,listbox_var.size()):
            if listbox_var.get(i) in value:
                listbox_var.select_set(i) 
    """
        
        
                
        