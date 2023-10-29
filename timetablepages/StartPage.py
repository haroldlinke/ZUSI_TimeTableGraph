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
from tkinter import ttk,messagebox
from tk_html_widgets import HTMLLabel
import urllib
#from timetablepages.configfile import ConfigFile
from locale import getdefaultlocale
import os
import time
import logging
from datetime import datetime
from scrolledFrame.ScrolledFrame import VerticalScrolledFrame,HorizontalScrolledFrame,ScrolledFrame

LARGE_FONT= ("Verdana", 12)
VERY_LARGE_FONT = ("Verdana", 14)
SMALL_FONT= ("Verdana", 8)

def check_for_existing_messages(mode=""):
    try:
        currURL = "http://www.hlinke.de/files/ZUSIBildFahrplanMessage.html"
        # Assign the open file to a variable
        webFile = urllib.request.urlopen(currURL)
        html_message = str(webFile.read())
    except:
        html_message = ""
    
    if mode !="":
        # check if there is a mode specific message available
        try:
            currURL = "http://www.hlinke.de/files/ZUSIBildFahrplanMessage_"+ mode+".html"
            # Assign the open file to a variable
            webFile = urllib.request.urlopen(currURL)
            # Read the file contents to a variable
            html_message = str(webFile.read())
        except:
            pass
        
    html_message = html_message[2:len(html_message)-1]
    return html_message

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        self.tabClassName = "StartPage"
        logging.debug("Init Page %s ",self.tabClassName)
        self.controller = controller
        macrodata = self.controller.MacroDef.data.get(self.tabClassName,{})
        if macrodata=={}:
            int_tabname = self.tabClassName+"_"+self.controller.arg_mode
            macrodata = self.controller.MacroDef.data.get(int_tabname,{})
        self.tabname = macrodata.get("MTabName",self.tabClassName)
        self.title = macrodata.get("Title",self.tabClassName)
        tk.Frame.__init__(self, parent)
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.frame=ttk.Frame(self,relief="ridge", borderwidth=1)
        self.scroll_main_frame = ScrolledFrame(self.frame)
        self.main_frame = ttk.Frame(self.scroll_main_frame.interior, relief="ridge", borderwidth=2)
        title_frame = ttk.Frame(self.main_frame, relief="ridge", borderwidth=1)
        label = ttk.Label(title_frame, text=self.title, font=LARGE_FONT)
        label.pack(padx=5,pady=(5,5))
        #config_frame = self.controller.create_macroparam_frame(self.main_frame,self.tabClassName, maxcolumns=4,startrow=1,style="CONFIGPage")

        text_frame = ttk.Frame(self.main_frame,relief="ridge", borderwidth=2)
        html_message=check_for_existing_messages(mode=controller.arg_mode_orig)
        html_label = HTMLLabel(text_frame,html=html_message,height=4,width=200,borderwidth=2,relief="ridge",)
        #text = macrodata.get("Ausführliche Beschreibung","")
        photo_filename = macrodata.get("Photo","")
        if photo_filename != "":
            try:
                logging.debug("Open Photo1 %s ",photo_filename)
                filedir = os.path.dirname(os.path.realpath(__file__))
                self.photofilepath = os.path.join(filedir, photo_filename)
                text1 = tk.Text(text_frame, bg=self.cget('bg'),relief="flat",width=200)
                logging.debug("Open Photo2 %s ",self.photofilepath)
                self.photo=tk.PhotoImage(file=self.photofilepath)
                text1.insert(tk.END,'\n')
                text1.image_create(tk.END, image=self.photo)
                logging.debug("Open Photo %s ",self.photofilepath)
            except BaseException as e:
                logging.debug("Photo-Error",self.photofilepath,e)
        else:
            text1 = tk.Text(text_frame, bg=self.cget('bg'),relief="flat",width=200)
        content = macrodata.get("Content",{})
        logging.debug("Open Content %s ",content)
        if content != {}:
            text_widget = tk.Text(text_frame,wrap=tk.WORD,bg=self.cget('bg'),relief="flat")
            text_scroll = tk.Scrollbar(text_frame, command=text_widget.yview)
            text_widget.configure(yscrollcommand=text_scroll.set)                    
            for titel,text in content.items():
                text_widget.tag_configure('bold_italics', font=('Verdana', 10, 'bold', 'italic'))
                text_widget.tag_configure('big', font=('Verdana', 14, 'bold'))
                text_widget.tag_configure('normal', font=('Verdana', 10, ))
                text_widget.insert(tk.END,"\n"+titel+"\n", 'big')
                text_widget.insert(tk.END, text, 'normal')
            text_widget.config(state=tk.DISABLED)
        else:
            text_widget = tk.Text(text_frame,wrap=tk.WORD,bg=self.cget('bg'),relief="flat")
            text_scroll = tk.Scrollbar(text_frame, command=text_widget.yview)            
        # --- placement
        # Tabframe => frame
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)                
        # Frame placement => scroll_main_frame
        self.frame.grid(row=0,column=0,sticky="ns")
        self.frame.grid_columnconfigure(0,weight=1)
        self.frame.grid_rowconfigure(0,weight=1)              
        # scroll_main_frame => scroll_main_frame.interior => main_frame
        self.scroll_main_frame.grid(row=0,column=0,sticky="nesw")
        self.scroll_main_frame.grid_columnconfigure(0,weight=1)
        self.scroll_main_frame.grid_rowconfigure(1,weight=1)
        self.scroll_main_frame.interior.grid_rowconfigure(0,weight=1)
        self.scroll_main_frame.interior.grid_columnconfigure(0,weight=1)
        
        # main_frame => title_frame, config_frame, text_frame
        self.main_frame.grid(row=0,column=0,sticky="nesw")
        self.main_frame.grid_columnconfigure(0,weight=1)
        self.main_frame.grid_rowconfigure(1,weight=1)         
        # place frames in main_frame
        title_frame.grid(row=0, column=0, pady=10, padx=10)
        #config_frame.grid(row=1, column=0, pady=10, padx=10)
        text_frame.grid(row=2,column=0,padx=10, pady=0,sticky="nesw")
        text_frame.grid_columnconfigure(1,weight=1)
        text_frame.grid_rowconfigure(1,weight=1)
        html_label.grid(row=0, column=0, pady=0, padx=10,sticky=("nesw"))
        text1.grid(row=1,column=0,sticky="nesw")
        text_widget.grid(row=2,column=0,sticky=("nesw"),padx=10,pady=10)
        text_scroll.grid(row=2,column=1,sticky=("ns"))                
       
    def cancel(self,_event=None):
        pass
        
    def tabselected(self):
        logging.debug("Tabselected: %s",self.tabname)
        #self.controller.currentTabClass = self.tabClassName
        logging.info(self.tabname)
        pass
    
    def tabunselected(self):
        logging.debug("Tabunselected: %s",self.tabname)
        pass
    
    def TabChanged(self,_event=None):
        pass    

    def getConfigData(self, key,default=None):
        return self.controller.getConfigData(key,default=default)
    
    def readConfigData(self):
        self.controller.readConfigData()
        
    def setConfigData(self,key, value):
        self.controller.setConfigData(key, value)

    def setParamData(self,key, value):
        self.controller.setParamData(key, value)

    def MenuUndo(self,_event=None):
        pass
    
    def MenuRedo(self,_event=None):
        pass
    
    def send_command_to_ARDUINO(self,command):
        pass

    def connect(self):
        pass

    def disconnect(self):
        pass
