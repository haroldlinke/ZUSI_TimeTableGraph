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
from tkinter import ttk,font
from scrolledFrame.ScrolledFrame import ScrolledFrame
import uuid
import logging
from timetablepages.DefaultConstants import STD_FONT, LARGE_FONT
from timetablepages.ConfigPageTemplate import ConfigPagetemplate
page_link = None

# ----------------------------------------------------------------
# Class ConfigurationPage
# ----------------------------------------------------------------

class StationsConfigurationPage(ConfigPagetemplate):

    def __init__(self, parent, controller):
        self.tabClassName = "StationsConfigurationPage"
        self.generic_methods = {"TreeView": self.treeview}
        self.std_font = font.Font(font=STD_FONT)
        page_link = self
        self.tree = None
        super().__init__(parent, controller, self.tabClassName, generic_methods=self.generic_methods)
        self.controller = controller
        #update treeview, when value in FPL-filename changed
        paramvar = self.controller.macroparams_var[self.tabClassName]["Bfp_filename"]
        paramvar.trace('w',self.bfpl_filename_updated)
        paramvar = self.controller.macroparams_var[self.tabClassName]["Bfp_trainfilename"]
        paramvar.trace('w',self.xml_filename_updated)
        self.controller.update_variables_with_config_data(self.tabClassName)
        return

    def get_macroparam_var_val(self,paramkey,macro=""):
        if macro == "":
            macro=self.tabClassName
        return self.controller.get_macroparam_val(macro,paramkey)            
    
    def bfpl_filename_updated(self, *args):
        self.update_tree()
        
    def xml_filename_updated(self, *args):
        #self.update_tree()
        self.controller.get_stationlist_for_station_chooser()
        pass
    
    def update_tree(self):
        self.tree=self.create_zusi_zug_treeframe(self.tree_frame)
        logging.debug("SaveConfig: %s - %s",self.tabname,repr(self.controller.ConfigData.data))
        station_list = []
        self.controller.set_macroparam_val(StationsConfigurationPage, "StationChooser", station_list)

    def treeview(self,parent_frame, marco,macroparams):
        self.tree_frame = parent_frame
        self.tree=self.create_zusi_zug_treeframe(self.tree_frame)

    def JSONTree(self, Tree, Parent, Dictionary):
        for key in Dictionary :
            uid = uuid.uuid4()
            if isinstance(Dictionary[key], dict):
                Tree.insert(Parent, 'end', uid, text=key)
                key_width = self.std_font.measure(key+"      ")
                self.max_key_width = max(key_width, self.max_key_width)                
                self.JSONTree(Tree, uid, Dictionary[key])
            elif isinstance(Dictionary[key], list):
                Tree.insert(Parent, 'end', uid, text=key + '[]')
                key_width = self.std_font.measure(key+"      ")
                self.max_key_width = max(key_width, self.max_key_width)                          
                self.JSONTree(Tree,uid,dict([(i, x) for i, x in enumerate(Dictionary[key])]))
            else:
                value = Dictionary[key]
                if isinstance(value, str):
                    value = value.replace('[', '')
                    value = value.replace(']', '')
                    value = value.replace(" '", '')
                    value = value.replace("'", '')
                    value = value.replace(' ', '_')
                    value_width = self.std_font.measure(value+"      ")
                    self.max_value_width = max(value_width, self.max_value_width)
                Tree.insert(Parent, 'end', uid, text=key, value=value)
                
    def selectItem(self,a):
        curItem = self.tree.focus()
        selectedItem_dict = self.tree.item(curItem)
        if selectedItem_dict != {}:
            stationlist=selectedItem_dict.get("values","")
            if stationlist != "": # station list selected
                trainname = selectedItem_dict.get("text","")
                xml_filename = self.Bfp_xmlfilenamelist.get(trainname)
                if xml_filename != "":
                    self.controller.set_string_variable(xml_filename,paramkey="Bfp_trainfilename", macrokey=self.tabClassName)
                    #startStationparamvar = self.controller.macroparams_var["StationsConfigurationPage"]["StartStation"]
                    #stationlist_list=stationlist[0].split(",")
                    #startStationparamvar["value"]=stationlist_list
                    #startStationparamvar.set(stationlist_list[0])
                    #endStationparamvar = self.controller.macroparams_var["StationsConfigurationPage"]["EndStation"]
                    #endStationparamvar["value"]=stationlist_list
                    #endStationparamvar.set(stationlist_list[len(stationlist_list)-1])
                    self.controller.get_stationlist_for_station_chooser()
                else:
                    self.controller.set_statusmessage("No <.timetable.xml> file found for "+trainname)
    
    def create_zusi_zug_treeframe(self,parent):
        # Setup Data
        self.max_value_width = 0
        self.max_key_width = 0
        fpl_filename = self.get_macroparam_var_val("Bfp_filename")
        # Setup the Frames
        TreeFrame = ttk.Frame(parent, padding="3")
        TreeFrame.grid(row=0, column=0, sticky=tk.NSEW)
        # Setup the Tree
        #if self.tree == None:
        self.tree = ScrollableTV(TreeFrame, height=20, columns=("value")) #ttk.Treeview(TreeFrame, columns=('Values'))
        style = ttk.Style()
        style.configure("Treeview", font=STD_FONT)
        self.tree.heading("value", text="Strecken-Bahnhöfe", anchor="w")
        #tree.column("#0", width=200, stretch=False)
        #tree.column("value", minwidth=2500, width=1000, stretch=True)
        self.tree.grid(padx=8, pady=(8,0),sticky="nesw")
        if fpl_filename == "":
            return            
        if self.controller.timetable_main:
            Data_main =self.controller.timetable_main.create_zusi_zug_liste(fpl_filename)
        self.Bfp_xmlfilenamelist = Data_main.get("XML_Filenamelist",{})
        Data = Data_main.get("Trainlist",{})
        Data_sorted = dict(sorted(Data.items()))            
        self.JSONTree(self.tree, '', Data_sorted)
        TreeFrame.grid_columnconfigure(0,weight=1)
        TreeFrame.grid_rowconfigure(0,weight=1)
        verscrlbar = ttk.Scrollbar(TreeFrame,  
                                   orient =tk.VERTICAL,  
                                   command = self.tree.yview)
        verscrlbar.grid(row=0,column=1,sticky="ns") 
        # Configuring treeview 
        self.tree.configure(xscrollcommand = verscrlbar.set)             
        horscrlbar = ttk.Scrollbar(TreeFrame,  
                                   orient =tk.HORIZONTAL,  
                                   command = self.tree.xview)
        horscrlbar.grid(row=1,column=0,sticky="we",padx=8, pady=(0,8)) 
        # Configuring treeview 
        self.tree.configure(xscrollcommand = horscrlbar.set)
        self.tree.column("#0", width=self.max_key_width, stretch=False)
        self.tree.column("value",minwidth=self.max_value_width,width=1000,stretch=True)
        self.tree.bind('<Double-1>', self.selectItem)
        return self.tree

        # subclass treeview for the convenience of overriding the column method
class ScrollableTV(ttk.Treeview):
        def __init__(self, master, **kw):
            super().__init__(master, **kw)
            self.columns=[]
        # column now records the name and details of each column in the TV just before they're added
        def column(self, column, **kw):
            if column not in [column[0] for column in self.columns]:
                self.columns.append((column, kw))
            super().column(column, **kw)
        
def bfpl_filename_updated(*args):
        #tk.messagebox.showinfo("entry callback", "You changed the entry %s" % str(args))
        page_link.update_tree()
                