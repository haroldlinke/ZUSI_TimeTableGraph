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
#import uuid

#from locale import getdefaultlocale
import logging
#import time
#import platform

from timetablepages.DefaultConstants import LARGE_FONT, SMALL_FONT, VERY_LARGE_FONT, PROG_VERSION

# ----------------------------------------------------------------
# Class ConfigurationPage
# ----------------------------------------------------------------
class ConfigPagetemplate(tk.Frame):

    def __init__(self, parent, controller, tabname, generic_methods=None):
        self.controller = controller
        tk.Frame.__init__(self,parent)
        self.tabClassName = tabname
        macrodata = self.controller.MacroDef.data.get(self.tabClassName,{})
        if macrodata=={}:
            int_tabname = self.tabClassName+"_"+self.controller.arg_mode
            macrodata = self.controller.MacroDef.data.get(int_tabname,{})
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
        config_frame = self.controller.create_macroparam_frame(self.main_frame,self.tabClassName, maxcolumns=1,startrow =10,style="CONFIGPage",generic_methods=generic_methods)  
        # --- Buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame2 = ttk.Frame(self.main_frame)
        
        button1_text = macrodata.get("Button_1",self.tabClassName)
        self.update_button1a = ttk.Button(self.button_frame, text=button1_text, command=self.save_config)
        self.update_button1a.pack(side="right", padx=10)
        self.update_button1b = ttk.Button(self.button_frame2, text=button1_text, command=self.save_config)
        self.update_button1b.pack(side="right", padx=10)
        
        button2_text = macrodata.get("Button_2",self.tabClassName)
        if button2_text != "":
            self.update_button2a = ttk.Button(self.button_frame, text=button2_text, command=self.button2_command)
            self.update_button2a.pack(side="right", padx=10)
            self.update_button2b = ttk.Button(self.button_frame2, text=button2_text, command=self.button2_command)
            self.update_button2b.pack(side="right", padx=10)       
        #self.update_tree_button = ttk.Button(self.button_frame, text="Update Tree", command=self.update_tree)
        #self.update_tree_button.pack(side="left", padx=10)        
        #self.tree_frame = ttk.Frame(self.main_frame)

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
        #self.tree_frame.grid(row=3, column=0, pady=10, padx=10, sticky="nesw")
        self.button_frame2.grid(row=4, column=0,pady=10, padx=10)
        
        self.controller.update_variables_with_config_data(self.tabClassName)
        self.store_old_config()

        #self.save_config()

        # ----------------------------------------------------------------
        # Standardprocedures for every tabpage
        # ----------------------------------------------------------------

    def tabselected(self):
        logging.debug("Tabselected: %s",self.tabname)
        self.controller.set_statusmessage("")
        self.store_old_config()
    
    def tabunselected(self):
        logging.debug("Tabunselected: %s",self.tabname)
        
        if self.check_if_config_data_changed():
            logging.debug("Config_data changed - request save or cancel")
            answer = tk.messagebox.askyesnocancel ('Sie verlassen die Einstellungen','Die Einstellungen wurden verändert. Sollen die geänderten Einstellungen gesichert werden?',default='no')
            if answer == None:
                logging.debug("Config_data changed - answer: None")
                return # cancelation return to "ConfigurationOage"
            if answer:
                logging.debug("Config_data changed - answer: Yes")
                self.save_config()
            else:
                logging.debug("Config_data changed - answer: No")
       
    def cancel(self):
        self.save_config()

    def getConfigPageParams(self):
        pass
    
    def getConfigData(self, key,default=None):
        return self.controller.getConfigData(key,default=default)
    
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
        #try:
            #curItem = self.tree.focus()
            #curItem_value = self.tree.item(curItem)
        #except:
            #curItem_value = {}
        #selectedtrain=curItem_value.get("text","")
        param_values_dict = self.get_macroparam_var_values(self.tabClassName)
        self.setConfigDataDict(param_values_dict)
        self.store_old_config()
        self.controller.SaveConfigData()
        logging.debug("SaveConfig: %s - %s",self.tabname,repr(self.controller.ConfigData.data))
        
    def button2_command(self):
        pass

    def store_old_config(self):
        self.old_param_values_dict = self.get_macroparam_var_values(self.tabClassName)
    
    def check_if_config_data_changed(self):
        param_values_dict = self.get_macroparam_var_values(self.tabClassName)
        if self.old_param_values_dict != param_values_dict:
            logging.debug("Config-Data changed")
            return True
        return False