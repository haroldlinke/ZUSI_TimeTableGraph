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
from tkinter import ttk
#from timetablepages.configfile import ConfigFile
#from scrolledFrame.ScrolledFrame import VerticalScrolledFrame,HorizontalScrolledFrame,ScrolledFrame

#import re
#import math
#import os
#import sys
#import threading
#import queue
#import time
import logging
#import concurrent.futures
#import random
#import webbrowser
#from datetime import datetime
#import json
import timetablepages.TimetablegraphCanvas

VERSION ="V01.17 - 25.12.2019"
LARGE_FONT= ("Verdana", 12)
VERY_LARGE_FONT = ("Verdana", 14)
SMALL_FONT= ("Verdana", 8)


ThreadEvent = None
            
class TimeTablePage(tk.Frame):
    def __init__(self, parent, controller):
        self.tabClassName = "Bildfahrplan"
        tk.Frame.__init__(self,parent)
        self.controller = controller
        macrodata = self.controller.MacroDef.data.get(self.tabClassName,{})
        self.tabname = macrodata.get("MTabName",self.tabClassName)
        self.title = macrodata.get("Title",self.tabClassName)
        self.canvas_height = self.controller.canvas_height
        self.canvas_width = self.controller.canvas_width
        self.fpl_filename = ""
        self.xml_filename = ""
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.frame=ttk.Frame(self,relief="ridge", borderwidth=1)
        self.frame.grid_columnconfigure(0,weight=1)
        self.frame.grid_rowconfigure(0,weight=1)
        self.frame.grid(row=0,column=0,sticky="nesw")
        frame = ttk.Frame(self.frame)
        frame.grid(row=0,column=0,sticky="nesw")
        frame.grid_columnconfigure(0,weight=1)
        frame.grid_rowconfigure(0,weight=1)        
        self.canvas=tk.Canvas(frame,width=self.canvas_width,height=self.canvas_height,scrollregion=(0,0,self.canvas_width,self.canvas_height),bg="white")
        hbar=tk.Scrollbar(frame,orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM,fill=tk.X)
        hbar.config(command=self.canvas.xview)
        vbar=tk.Scrollbar(frame,orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT,fill=tk.Y)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(width=self.canvas_width,height=self.canvas_height)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side=tk.LEFT,expand=True,fill=tk.BOTH)
        self.timetable_main = timetablepages.TimetablegraphCanvas.Timetable_main(self.controller, self.canvas)
        self.canvas.bind("<MouseWheel>", self.scrollcanvas)
        self.controller.timetable_main = self.timetable_main
        
    def scrollcanvas(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def save_as_png(self, fileName):
        # save postscipt image 
        self.canvas.update()
        self.canvas.postscript(file = fileName + '.eps',colormode='color',width=self.canvas_width,height=self.canvas_height) 
        # use PIL to convert to PNG 
        img = Image.open(fileName + '.eps')
        try:

            img.save(fileName + '.png', 'png')
        except: 
            print("Error while generating png-file- Ghostscript not found")
            pass
        
    def create_train_type_to_color_dict(self):
        self.train_type_to_color_dict = {}
        config_traintype_to_color_dict = self.getConfigData("Bfp_TrainTypeColors")
        
        for i,value_dict in config_traintype_to_color_dict.items():
            print(repr(value_dict))
            traintype = value_dict.get("Bfp_TrainType","")
            traintypecolor = value_dict.get("Bfp_TrainTypeColor","black")
            if traintype != "":
                self.train_type_to_color_dict[traintype]=traintypecolor
        

    def tabselected(self):
        logging.debug("Tabselected: %s",self.tabname)
        #self.controller.currentTabClass = self.tabClassName
        logging.info(self.tabname)
        self.controller.set_statusmessage("Bildfahrplanerstellung gestartet - bitte etwas Geduld")
        self.controller.update()
        self.canvas_width = self.getConfigData("Bfp_width")
        self.canvas_height = self.getConfigData("Bfp_height")
        fpl_filename = self.getConfigData("Bfp_filename")
        xml_filename = self.getConfigData("Bfp_trainfilename")
        starthour = self.getConfigData("Bfp_start")
        duration = self.getConfigData("Bfp_duration")
        self.create_train_type_to_color_dict()
        self.timetable_main.set_zuggattung_to_color(self.train_type_to_color_dict)
        
        if fpl_filename == "":
            self.controller.set_statusmessage("Kein ZUSI Fahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> auswählen")
            return
        if xml_filename == "":
            self.controller.set_statusmessage("Kein ZUSI Buchfahrplann eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> auswählen")
            return
        if starthour == "":
            self.controller.set_statusmessage("Keine Startzeit für den Bildfahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> einstellen")
            return
        if duration == "":
            self.controller.set_statusmessage("Kein Zeitraum für den Bildfahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> einstellen")
            return        
        
        self.timetable_main.create_zusi_zug_liste(fpl_filename)
        
        if (fpl_filename != self.fpl_filename) or (self.xml_filename != xml_filename) or (self.starthour != starthour) or (self.duration != duration):
            self.xml_filename = xml_filename
            self.fpl_filename = fpl_filename
            self.starthour = starthour
            self.duration = duration
            self.timetable_main.redo_fpl_and_canvas(self.canvas_width,self.canvas_height,fpl_filename=fpl_filename,xml_filename=xml_filename,starthour=starthour,duration=duration)
        else:
            old_height =self.canvas.winfo_reqheight()
            old_width = self.canvas.winfo_reqwidth()
            
            #if (old_height-4 != self.canvas_height) or (old_width-4 != self.canvas_width):
            self.timetable_main.resize_canvas(self.canvas_width,self.canvas_height,starthour,duration)
    
    def tabunselected(self):
        logging.debug("Tabunselected: %s",self.tabname)
        pass 
    
    def _update_value(self,paramkey):
        logging.info("SerialMonitorPage - update_value: %s",paramkey)
        message = self.controller.get_macroparam_val(self.tabClassName, "SerialMonitorInput")+"\r\n" #self.input.get() +"\r\n"

    def getConfigData(self, key):
        return self.controller.getConfigData(key)
    
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