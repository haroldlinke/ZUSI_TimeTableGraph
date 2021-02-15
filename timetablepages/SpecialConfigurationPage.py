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
from tkinter import ttk
#from tkcolorpicker.spinbox import Spinbox
#from tkcolorpicker.limitvar import LimitVar
from scrolledFrame.ScrolledFrame import VerticalScrolledFrame,HorizontalScrolledFrame,ScrolledFrame
from timetablepages.ConfigPageTemplate import ConfigPagetemplate
from tools.xmltodict import parse
#import uuid

#from locale import getdefaultlocale
import logging
#import time
#import platform

from timetablepages.DefaultConstants import LARGE_FONT, SMALL_FONT, VERY_LARGE_FONT, PROG_VERSION

# ----------------------------------------------------------------
# Class SpecialConfigurationPage
# ----------------------------------------------------------------
class SpecialConfigurationPage(ConfigPagetemplate):

    def __init__(self, parent, controller):
        
        self.tabClassName = "SpecialConfigurationPage"
        super().__init__(parent, controller, self.tabClassName, generic_methods=None) 
        
        self.get_stationlist_for_station_chooser()
        return
    
    """
    
        self.controller = controller
        self.arduino_portlist = {}
        tk.Frame.__init__(self,parent)
        self.tabClassName = "SpecialConfigurationPage"
        macrodata = self.controller.MacroDef.data.get(self.tabClassName,{})
        self.tabname = macrodata.get("MTabName",self.tabClassName)
        self.title = macrodata.get("Title",self.tabClassName)
        self.startcmd_filename = ""
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.frame=ttk.Frame(self,relief="ridge", borderwidth=1)
        self.frame.grid_columnconfigure(0,weight=1)
        self.frame.grid_rowconfigure(0,weight=1)        
        self.scroll_main_frame = ScrolledFrame(self.frame)
        self.scroll_main_frame.grid_columnconfigure(0,weight=1)
        self.scroll_main_frame.grid_rowconfigure(0,weight=1)
        self.main_frame = ttk.Frame(self.scroll_main_frame.interior, relief="ridge", borderwidth=2)
        self.main_frame.grid_columnconfigure(0,weight=1)
        self.main_frame.grid_rowconfigure(2,weight=1) 
        title_frame = ttk.Frame(self.main_frame, relief="ridge", borderwidth=2)
        label = ttk.Label(title_frame, text=self.title, font=LARGE_FONT)
        label.pack(padx=5,pady=(5,5))
        #self.scroll_configframe = VerticalScrolledFrame(self.main_frame)
        #config_frame = self.controller.create_macroparam_frame(self.scroll_configframe.interior,self.tabClassName, maxcolumns=1,startrow =10,style="CONFIGPage")        
        config_frame = self.controller.create_macroparam_frame(self.main_frame,self.tabClassName, maxcolumns=1,startrow =10,style="CONFIGPage")  
        # --- Buttons
        self.button_frame = ttk.Frame(self.main_frame)
        button1_text = macrodata.get("Button_1",self.tabClassName)
        self.update_button = ttk.Button(self.button_frame, text=button1_text, command=self.save_config)
        self.update_button.pack(side="right", padx=10)
        self.button_frame2 = ttk.Frame(self.main_frame)
        self.update_button2 = ttk.Button(self.button_frame2, text=button1_text, command=self.save_config)
        self.update_button2.pack(side="right", padx=10)

        # --- placement
        # Tabframe
        self.frame.grid(row=0,column=0)
        self.scroll_main_frame.grid(row=0,column=0,sticky="nesw")
        # scroll_main_frame
        self.main_frame.grid(row=0,column=0)
        # main_frame        
        title_frame.grid(row=0, column=0, pady=10, padx=10)
        self.button_frame.grid(row=1, column=0,pady=10, padx=10)
        config_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nesw")
        self.button_frame2.grid(row=3, column=0,pady=10, padx=10)
        
        self.get_stationlist_for_station_chooser()
        
        self.controller.update_variables_with_config_data(self.tabClassName)
        

        self.save_config()

        # ----------------------------------------------------------------
        # Standardprocedures for every tabpage
        # ----------------------------------------------------------------

    def tabselected(self):
        #self.controller.currentTabClass = self.tabClassName
        #self.ledmaxcount.set(self.controller.get_maxLEDcnt())
        logging.debug("Tabselected: %s",self.tabname)
        self.controller.set_statusmessage("")
        self.store_old_config()
        self.get_stationlist_for_station_chooser()

    
    def tabunselected(self):
        logging.debug("Tabunselected: %s",self.tabname)
        if self.check_if_config_data_changed():
            answer = tk.messagebox.askyesnocancel ('Sie verlassen die Einstellungen','Die Einstellungen wurden verändert. Sollen die geänderten Einstellungen gesichert werden?',default='no')
            if answer == None:
                return # cancelation return to "ConfigurationOage"
            if answer:
                self.save_config()
       
    def cancel(self):
        self.save_config()

    def getConfigPageParams(self):
        pass
    
    def getConfigData(self, key):
        return self.controller.getConfigData(key)
    
    def readConfigData(self):
        self.controller.readConfigData()
        
    def setConfigData(self,key, value):
        self.controller.setConfigData(key, value)
        
    def setConfigDataDict(self,paramdict):
        self.controller.setConfigDataDict(paramdict)
        
    def get_macroparam_var_values(self,macro):
        return self.controller.get_macroparam_var_values(macro)        

    def setParamData(self,key, value):
        self.controller.setParamData(key, value)

    def MenuUndo(self,_event=None):
        logging.debug("MenuUndo: %s",self.tabname)
        pass
    
    def MenuRedo(self,_event=None):
        logging.debug("MenuRedo: %s",self.tabname)
        pass

    # ----------------------------------------------------------------
    # ConfigurationPage save_config
    # ----------------------------------------------------------------
    def save_config(self):
        self.setConfigData("pos_x",self.winfo_x())
        self.setConfigData("pos_y",self.winfo_y())
        param_values_dict = self.get_macroparam_var_values(self.tabClassName)
        self.setConfigDataDict(param_values_dict)
        self.store_old_config()
        self.controller.SaveConfigData()
        logging.debug("SaveConfig: %s - %s",self.tabname,repr(self.controller.ConfigData.data))

    def store_old_config(self):
        self.old_param_values_dict = self.get_macroparam_var_values(self.tabClassName)
    
    def check_if_config_data_changed(self):
        param_values_dict = self.get_macroparam_var_values(self.tabClassName)
        if self.old_param_values_dict != param_values_dict:
            return True
        return False
        
    """
    
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
    
    def get_station_list_from_tt_xml_file(self,xml_filename):
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
                    logging.debug("FplZeile conversion Error %s ",repr(FplZeile_dict),e)
                    continue # entry format wrong
        return stationName_list
    
    def get_stationlist_for_station_chooser(self):
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
        
        
                
        