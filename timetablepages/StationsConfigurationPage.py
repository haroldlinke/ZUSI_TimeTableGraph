#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#         TimetableGraph
#
# * Version: 0.01
# * Author: Harold Linke
# * Date: January 12th, 2021
# * Copyright: Harold Linke 2021
# *
# *
# ***************************************************************************

import tkinter as tk
from tkinter import ttk,font
from scrolledFrame.ScrolledFrame import ScrolledFrame
import uuid
import logging
from timetablepages.DefaultConstants import STD_FONT
from timetablepages.DefaultConstants import LARGE_FONT

page_link = None

# ----------------------------------------------------------------
# Class ConfigurationPage
# ----------------------------------------------------------------

class StationsConfigurationPage(tk.Frame):

    def __init__(self, parent, controller):
        self.controller = controller
        self.arduino_portlist = {}
        tk.Frame.__init__(self,parent)
        self.tabClassName = "StationsConfigurationPage"
        macrodata = self.controller.MacroDef.data.get(self.tabClassName,{})
        self.tabname = macrodata.get("MTabName",self.tabClassName)
        self.title = macrodata.get("Title",self.tabClassName)
        page_link = self
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
        self.std_font = font.Font(font=STD_FONT)
        self.generic_methods = {"TreeView": self.treeview}
        config_frame = self.controller.create_macroparam_frame(self.main_frame,self.tabClassName, maxcolumns=1,startrow =10,style="CONFIGPage",generic_methods=self.generic_methods)  

        # --- Buttons
        self.button_frame = ttk.Frame(self.main_frame)
        button1_text = macrodata.get("Button_1",self.tabClassName)
        
        self.update_button = ttk.Button(self.button_frame, text=button1_text, command=self.save_config)
        self.update_button.pack(side="right", padx=10)
        #update treeview, when value in FPL-filename changed
        paramvar = self.controller.macroparams_var[self.tabClassName]["Bfp_filename"]
        paramvar.trace('w',self.bfpl_filename_updated)        
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

        macroparams = macrodata.get("Params",[])
        
        for paramkey in macroparams:
            paramconfig_dict = self.controller.MacroParamDef.data.get(paramkey,{})
            param_type = paramconfig_dict.get("Type","")
            if param_type == "Multipleparams":
                mparamlist = paramconfig_dict.get("MultipleParams",[])
                mp_repeat  = paramconfig_dict.get("Repeat","")
                if mp_repeat == "":
                    for mparamkey in mparamlist:
                        configdatakey = self.controller.getConfigDatakey(mparamkey)
                        value = self.getConfigData(configdatakey)
                        self.controller.set_macroparam_val(self.tabClassName, mparamkey, value)
                else:
                    # get the repeated multipleparams rep_mparamkey=macro.mparamkey.index (e.g. ConfigDataPage.Z21Data.0
                    for i in range(int(mp_repeat)):
                        for mparamkey in mparamlist:
                            configdatakey = self.controller.getConfigDatakey(mparamkey)
                            value = self.controller.getConfigData_multiple(configdatakey,paramkey,i)
                            mp_macro = self.tabClassName+"." + paramkey + "." + str(i)
                            self.controller.set_macroparam_val(mp_macro, mparamkey, value)
            else:
                configdatakey = self.controller.getConfigDatakey(paramkey)
                value = self.getConfigData(configdatakey)
                self.controller.set_macroparam_val(self.tabClassName, paramkey, value)

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
    
    def get_macroparam_var_val(self,paramkey,macro=""):
        if macro == "":
            macro=self.tabClassName
        return self.controller.get_macroparam_val(macro,paramkey)        

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
        
    def bfpl_filename_updated(self, *args):
        self.update_tree()        
    
    def update_tree(self):
        self.tree=self.create_zusi_zug_treeframe(self.tree_frame)
        logging.debug("SaveConfig: %s - %s",self.tabname,repr(self.controller.ConfigData.data))

    def treeview(self,parent_frame, marco,macroparams):
        #self.save_config()
        self.tree=self.create_zusi_zug_treeframe(parent_frame)
        self.tree_frame = parent_frame
        

    def store_old_config(self):
        self.old_param_values_dict = self.get_macroparam_var_values(self.tabClassName)
    
    def check_if_config_data_changed(self):
        param_values_dict = self.get_macroparam_var_values(self.tabClassName)
        if self.old_param_values_dict != param_values_dict:
            return True
        return False

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
                    #value = value.replace(' ', '_')
                    value = value.replace('[', '')
                    value = value.replace(']', '')
                    value = value.replace(" '", '')
                    value = value.replace("'", '')
                    value = value.replace(' ', '_')
                    value_width = self.std_font.measure(value+"      ")
                    self.max_value_width = max(value_width, self.max_value_width)
                    pass
                Tree.insert(Parent, 'end', uid, text=key, value=value)
                
    def selectItem(self,a):
        curItem = self.tree.focus()
        selectedItem_dict = self.tree.item(curItem)
        if selectedItem_dict != {}:
            value=selectedItem_dict.get("values","")
            if value != "": # station list selected
                trainname = selectedItem_dict.get("text","")
                xml_filename = self.Bfp_xmlfilenamelist.get(trainname)
                
                if xml_filename != "":
                    self.controller.set_string_variable(xml_filename,paramkey="Bfp_trainfilename", macrokey=self.tabClassName)
    
    def create_zusi_zug_treeframe(self,parent):
        # Setup Data
        self.max_value_width = 0
        self.max_key_width = 0
        fpl_filename = self.get_macroparam_var_val("Bfp_filename")
        #self.getConfigData("Bfp_filename")
        # Setup the Frames
        TreeFrame = ttk.Frame(parent, padding="3")
        TreeFrame.grid(row=0, column=0, sticky=tk.NSEW)

        # Setup the Tree
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
                