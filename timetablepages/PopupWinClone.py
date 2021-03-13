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
from timetablepages.ZUSI_fpn_class import ZUSI_fpn
from timetablepages.ZUSI_trn_class import ZUSI_trn
import xml.etree.ElementTree as ET
import os
import logging
from timetablepages.DefaultConstants import LARGE_FONT

class popup_win_clone(tk.Frame):

    def __init__(self, parent, controller, trn_filename, fpn_filename):
        #def popup_win_clone(trn_filename,controller):
        tk.Frame.__init__(self,parent)
        self.controller = controller
        self.controller.popup_active = True
        self.pageName = "PopupWinClone"
        macrodata = controller.MacroDef.data.get(self.pageName,{})
        self.tabname = macrodata.get("MTabName",self.pageName)
        title = macrodata.get("Title",self.pageName)
        self.fpn_filename = fpn_filename
        
        self.win = tk.Toplevel()
        self.win.wm_title(title)
    
        self.win.grid_columnconfigure(0,weight=1)
        self.win.grid_rowconfigure(0,weight=1)
        main_frame = ttk.Frame(self.win, relief="ridge", borderwidth=2)
        main_frame.grid_columnconfigure(0,weight=1)
        main_frame.grid_rowconfigure(2,weight=1) 
        title_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
        label = ttk.Label(title_frame, text=title, font=LARGE_FONT)
        label.pack(padx=5,pady=(5,5))
        config_frame = controller.create_macroparam_frame(main_frame,self.pageName, maxcolumns=1,startrow =10,style="CONFIGPage",generic_methods={})  
        # --- Buttons
        button_frame = ttk.Frame(main_frame)
        button1_text = macrodata.get("Button_1",self.pageName)
        update_button = ttk.Button(button_frame, text=button1_text, command=self.clone_trnfile)
        update_button.pack(side="right", padx=10)
    
        # scroll_main_frame
        main_frame.grid(row=0,column=0)
        # main_frame        
        title_frame.grid(row=0, column=0, pady=10, padx=10)
        button_frame.grid(row=1, column=0,pady=10, padx=10)
        config_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nesw")
        #self.tree_frame.grid(row=3, column=0, pady=10, padx=10, sticky="nesw")
        
        controller.set_macroparam_val(self.pageName, "PWC_train_filename", trn_filename)
        #main_frame.set_focus()
    
    def clone_trnfile(self):
        trn_filepathname = self.controller.get_macroparam_val(self.pageName,"PWC_train_filename")
        new_trn_traintype = self.controller.get_macroparam_val(self.pageName,"PWC_TrainType")
        new_trn_trainnumbers = self.controller.get_macroparam_val(self.pageName,"PWC_TrainNumbers")
        new_trn_deltatime = int(self.controller.get_macroparam_val(self.pageName,"PWC_DeltaTime"))
        new_trn_trainnumbers_list = new_trn_trainnumbers.split(",")
        
        self.fpn_xmlfile = ZUSI_fpn(self.fpn_filename,self.controller)
        self.fpn_xmlfile.read_fpn_file_as_xml()
        self.fpn_xmlfile.write_fpn_file_from_xml(self.fpn_filename+".bak")
        
        for new_trn_trainnumber in new_trn_trainnumbers_list:
            if new_trn_trainnumber != "":
                new_trn_filepathname=self.execute_clone(trn_filepathname,new_trn_traintype,new_trn_trainnumber,new_trn_deltatime)
                new_trn_deltatime += new_trn_deltatime
                self.fpn_xmlfile.add_fpn_zug_entry(new_trn_filepathname)
        self.fpn_xmlfile.write_fpn_file_from_xml(self.fpn_filename)
        self.win.destroy()
        self.controller.timetable_main.canvas.focus_set()
        self.controller.popup_active=False
        self.controller.set_statusmessage("Datei klonen erfolgreich: "+trn_filepathname)
        self.controller.timetable_main.regenerate_canvas()        
        
    def execute_clone(self,trn_filepathname,new_trn_traintype,new_trn_trainnumber,new_trn_deltatime):
        logging.debug("Execute Clone %s %s %s %s", trn_filepathname,new_trn_traintype,new_trn_trainnumber,new_trn_deltatime)
        
        #copy org-trn-file to new-trn-filename
        trn_dirName = os.path.dirname(trn_filepathname)
        new_trn_filename = new_trn_traintype + new_trn_trainnumber+".trn"
        new_trn_filepathname = os.path.join(trn_dirName,new_trn_filename)

        trn_xmlfile = ZUSI_trn(trn_filepathname,self.controller)
        trn_xmlfile.read_trn_file_as_xml()
        trn_xmlfile.update_time_entries(new_trn_deltatime)
        trn_xmlfile.update_train_entry(new_trn_traintype, new_trn_trainnumber)
        trn_xmlfile.write_trn_file_from_xml(new_trn_filepathname)
        
        return new_trn_filepathname
        
        
         
        



