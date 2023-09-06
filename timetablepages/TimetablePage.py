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
import os
import logging
import timetablepages.TimetablegraphCanvas
try:
    
    from PIL import Image, EpsImagePlugin
except:
    pass

LARGE_FONT= ("Verdana", 12)
VERY_LARGE_FONT = ("Verdana", 14)
SMALL_FONT= ("Verdana", 8)

class TimeTablePage(tk.Frame):
    def __init__(self, parent, controller):
        self.tabClassName = "TimeTablePage"
        self.canvas=None
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
        self.cv_frame=None
        self.define_key_bindings()
        self.canvas = self.create_canvas()
        self.timetable_main = timetablepages.TimetablegraphCanvas.Timetable_main(self.controller, self.canvas, self)
        self.scalefactorunit = 0.95
        self.controller.total_scalefactor = 1
        self.old_scalefactor = 1
        self.controller.timetable_main = self.timetable_main
        self.firstcall = True
        #self.canvas_bindings()
        self.block_Canvas_movement_flag = False
        self.canvas_init = True
        
 
    def create_canvas(self):
        if self.cv_frame:
            #self.cv_frame.destroy()
            pass
        else:
            self.cv_frame = ttk.Frame(self.frame)
        self.cv_frame.grid(row=0,column=0,sticky="nesw")
        self.cv_frame.grid_columnconfigure(0,weight=1)
        self.cv_frame.grid_rowconfigure(0,weight=1)
        if self.canvas and self.canvas != None:
            canvas = self.canvas
        else:
            canvas=tk.Canvas(self.cv_frame,width=self.canvas_width,height=self.canvas_height,scrollregion=(0,0,self.canvas_width,self.canvas_height),bg="white")
            hbar=tk.Scrollbar(self.cv_frame,orient=tk.HORIZONTAL)
            hbar.pack(side=tk.BOTTOM,fill=tk.X)
            hbar.config(command=canvas.xview)
            vbar=tk.Scrollbar(self.cv_frame,orient=tk.VERTICAL)
            vbar.pack(side=tk.RIGHT,fill=tk.Y)
            vbar.config(command=canvas.yview)
            canvas.config(width=self.canvas_width,height=self.canvas_height)
            canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
            canvas.pack(side=tk.LEFT,expand=True,fill=tk.BOTH)
        self.canvas = canvas
        self.canvas_bindings()
        return canvas
        
    def define_key_bindings(self):
        
        self.key_to_method_dict = { "onRestoreZoom"     : self.onRestoreZoom,
                                    "onMoveCanvasUp"    : self.onMoveCanvasUp,
                                    "onMoveCanvasDown"  : self.onMoveCanvasDown,
                                    "onMoveCanvasLeft"  : self.onMoveCanvasLeft, 
                                    "onMoveCanvasRight" : self.onMoveCanvasRight,
                                    "onZoomIn"          : self.onZoomIn,
                                    "onZoomOut"         : self.onZoomOut,
                                    "onRefreshCanvas"   : self.onRefreshCanvas
                                   }            
        
    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        if self.block_Canvas_movement_flag:
            return
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        if self.block_Canvas_movement_flag:
            return        
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        
    def onCtrlMouseWheel(self, event):
        scale = 1.0
        if event.delta == -120:
            scale *= self.scalefactorunit
        if event.delta == 120:
            scale /= self.scalefactorunit
        self.resize(event, scale)
    
    def onAltMouseWheel(self, event):
        pass
    
    def onMouseWheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def onMoveCanvasUp(self, event):
        if event.keysym == "Up":
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(-1, "pages")
    
    def onMoveCanvasDown(self, event):
        if event.keysym == "Down":
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(1, "pages")
    
    def onZoomIn(self, event):
        scale = self.scalefactorunit
        self.resize(event, scale)
    
    def onZoomOut(self, event):
        scale = 1.0/self.scalefactorunit
        self.resize(event, scale)
    
    def onMoveCanvasLeft(self, event):
        self.canvas.xview_scroll(-1, "units")
    
    def onMoveCanvasRight(self, event):
        self.canvas.xview_scroll(1, "units")
    
    #def onPrior(self, event):
    #    self.canvas.xview_scroll(1, "pages")
    
    #def onNext(self, event):
    #    self.canvas.xview_scroll(-1, "pages")
    
    def onShiftMouseWheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        
    def onRefreshCanvas(self, event):
        self.timetable_main.regenerate_canvas()
    
    def onRestoreZoom(self, event):
        if round(self.controller.total_scalefactor,4)!=1:
            self.old_scalefactor = self.controller.total_scalefactor
            #self.canvas_old_x, self.canavs_old_y = self.canvas.coords("all")
            #print(self.canvas_old_x, self.canavs_old_y)
            #self.canvas_old_x, self.canavs_old_y, x2, y2 = self.canvas.bbox("all")
            #print(self.canvas_old_x, self.canavs_old_y)
            self.resize(event, 1/self.controller.total_scalefactor)
            self.controller.total_scalefactor = 1
        else:
            self.resize(event, self.old_scalefactor)
            self.old_scalefactor = 1
            #self.canvas.move("all",self.canvas_old_x, self.canavs_old_y)
            #self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        #self.resize(event, 1/self.total_scalefactor)
        #self.total_scalefactor = 1
   
    def scale_objects(self, scale):
        self.canvas.scale('all', 0, 0, scale, scale)
        
    def scale_canvas_arround_object(self, scale, objectid):
        if False: #objectid != -1:
            object_coords = self.canvas.coords(objectid)
            self.scaleshift_x0 = object_coords[0]
            self.scaleshift_y0 = object_coords[1]
        else:
            self.scaleshift_x0 = 0
            self.scaleshift_y0 = 0
        self.canvas.scale('all', self.scaleshift_x0, self.scaleshift_y0, scale, scale)        
        
    def resize(self, event, scale):
        self.controller.total_scalefactor *= scale
        if self.controller.total_scalefactor > 1:
            self.canvas.itemconfigure("Background",fill="",outline="")
        else:
            self.canvas.itemconfigure("Background",fill="white",outline="")
        if event == None:
            x=0
            y=0
        else:
            x = 0 #self.canvas.canvasx(event.x)
            y = 0 #self.canvas.canvasy(event.y)
        #objectid = self.timetable_main.timetable.tt_canvas_cvobject
        #self.scale_canvas_arround_object(scale, objectid)
        self.canvas.scale('all', x, y, scale, scale)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
                
    def block_Canvas_movement(self,flag):
        self.block_Canvas_movement_flag = flag
        
    def canvas_bindings(self):
        self.canvas.bind('<Shift-ButtonPress-1>', self.move_from)
        self.canvas.bind('<Shift-B1-Motion>', self.move_to)
        self.canvas.bind("<Control-MouseWheel>", self.onCtrlMouseWheel, add="+")
        self.canvas.bind("<Alt-MouseWheel>", self.onAltMouseWheel, add="+")
        self.canvas.bind("<MouseWheel>", self.onMouseWheel, add="+")
        self.canvas.bind("<Shift-MouseWheel>", self.onShiftMouseWheel, add="+")
        for action,method in self.key_to_method_dict.items():
            key_str = self.controller.get_key_for_action(action)
            self.canvas.bind(key_str,method)
        return
    
    def canvas_unbind(self):
        self.canvas.unbind('<Shift-ButtonPress-1>')
        self.canvas.unbind('<Shift-B1-Motion>')
        self.canvas.unbind("<Control-MouseWheel>")
        self.canvas.unbind("<Alt-MouseWheel>")
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Shift-MouseWheel>")
        for action,method in self.key_to_method_dict.items():
            key_str = self.controller.get_key_for_action(action)
            self.canvas.unbind(key_str)
        return    

    def save_as_pdf(self, fileName):
        # save postscipt image 
        self.canvas.update()
        self.canvas.postscript(file = fileName + 'tmp.eps',colormode='color',width=self.canvas_width,height=self.canvas_height) 
        EpsImagePlugin.gs_windows_binary =  self.controller.ghostscript_path  #r"D:\data\doc\GitHub\ZUSI_TimeTableGraph\gs9.53.3\bin\gswin32c.exe"  #r'C:\Program Files (x86)\gs\gs9.53.3\bin\gswin32c'
        logging.debug("Ghostscriptpath: %s", self.controller.ghostscript_path)
        img = Image.open(fileName + 'tmp.eps')
        try:
            img.load(scale=8)
            size = img.size
            img.save(fileName,"pdf",resolution=300)
        except BaseException as e:
            logging.debug("Error while generating pdf-file\n %s",e)
            self.controller.set_statusmessage("Error while generating pdf-file\n" + str(e))
        
    def save_as_eps(self, fileName):
        # save postscipt image 
        self.canvas.update()
        self.canvas.postscript(file = fileName,colormode='color',width=self.canvas_width,height=self.canvas_height)
        
    def save_as_image(self, fileName):
        # save postscipt image 
        self.canvas.update()
        tmp_filename = fileName + '.tmp.eps'
        self.canvas.postscript(file = tmp_filename,colormode='color',width=self.canvas_width,height=self.canvas_height)
        EpsImagePlugin.gs_windows_binary =  self.controller.ghostscript_path  #r"D:\data\doc\GitHub\ZUSI_TimeTableGraph\gs9.53.3\bin\gswin32c.exe"  #r'C:\Program Files (x86)\gs\gs9.53.3\bin\gswin32c'
        img = Image.open(tmp_filename)
        try:
            #max_size = 178956970
            #imagesize = self.canvas_width * self.canvas_height*32
            #if imagesize > max_size:
            #    print("Error")
            img.load(scale=8)
            size = img.size
            img.save(fileName)
        except BaseException as e:
            logging.debug("Error while generating image-file\n %s",e)
            self.controller.set_statusmessage("Error while generating image-file\n" + str(e))
            pass
            
    def import_Fahrtenschreiber(self, fileNames):
        logging.info("import_Fahrtenschreiber - %s \n",fileNames)
        try:
            for fileName in fileNames:
                
                try:
                    self.timetable_main.import_one_Fahrtenschreiber(fileName)
                except BaseException as e:
                    logging.debug("import_one_Fahrtenschreiber - Fehler: %s \n %s",fileName,e)
                    self.controller.set_statusmessage("Fehler beim Importieren von \n" + fileName)
                    
            self.controller.set_statusmessage("Import der Fahrtenschreiber beendet")
            logging.info("import_Fahrtenschreiber beendet")

        except BaseException as e:
            logging.debug("import_Fahrtenschreiber - Fehler %s \n %s",fileNames,e)
            self.controller.set_statusmessage("Fehler beim Import")
       
    def edit_export_to_all_trn(self):
        self.timetable_main.edit_export_to_all_trn()
        
    def create_train_type_to_color_dict(self):
        self.train_type_prop_dict = {}
        self.train_type_to_width_dict = {}
        config_traintype_prop_dict = self.getConfigData("Bfp_TrainTypeProp")
        config_traintype_prop_default_dict = self.getConfigData("Bfp_TrainTypePropDefault",default={})
        if config_traintype_prop_default_dict:
            config_traintype_prop_default_dict["0"]["Bfp_TrainType"]="*"
        else:
            config_traintype_prop_default_dict["0"]={"Bfp_TrainType": "*",
                                                     "Bfp_TrainTypeColor": "black",
                                                     "Bfp_TrainTypeWidth": 1,
                                                     "Bfp_TrainTypeLabel": "Alle Segmente",
                                                     "Bfp_TrainTypeLabel_No": 0,
                                                     "Bfp_TrainTypeLabelSize": 10,
                                                     "Bfp_TrainTypeLineDashed": ""
                                                     }
        if config_traintype_prop_dict == None:
            config_traintype_prop_dict = config_traintype_prop_default_dict
        else:
            config_traintype_prop_dict[999]=config_traintype_prop_default_dict["0"]
        for i,value_dict in config_traintype_prop_dict.items():
            #print(repr(value_dict))
            traintype = value_dict.get("Bfp_TrainType","")
            #traintypecolor = value_dict.get("Bfp_TrainTypeColor","black")
            #traintypewidth = value_dict.get("Bfp_TrainTypeWidth","4")
            if traintype != "":
                traintype=traintype.replace(" ","")
                traintypelist = traintype.split(",")
                for traintype in traintypelist:
                    self.train_type_prop_dict[traintype]=value_dict

    def tabselected(self):
        try:
            if self.cancel_pagechange:
                self.cancel_pagechange = True
        except:
            self.cancel_pagechange = False
        if self.cancel_pagechange:
            self.pagechange_canceled = True
        else:
            self.pagechange_canceled = False
            logging.debug("Tabselected: %s",self.tabname)
            #self.controller.currentTabClass = self.tabClassName
            logging.info(self.tabname)
            self.controller.update()
            self.canvas_width = self.getConfigData("Bfp_width")
            self.canvas_height = self.getConfigData("Bfp_height")
            logging.debug("Timetablepage - tabselected - Canvas_height %s, width %s",self.canvas_height,self.canvas_width)
            fpl_filename = self.getConfigData("Bfp_filename")
            xml_filename = self.getConfigData("Bfp_trainfilename")
            starthour = self.getConfigData("Bfp_start")
            duration = self.getConfigData("Bfp_duration")
            self.create_train_type_to_color_dict()
            self.timetable_main.set_traintype_prop(self.train_type_prop_dict)
            self.controller.allow_TRN_files = self.controller.getConfigData("SCP_AllowTRN",default="")
            if fpl_filename == "":
                self.controller.set_statusmessage("Kein ZUSI Fahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> auswählen")
                return
            else:
                if not os.path.isfile(fpl_filename):
                    self.controller.set_statusmessage("ZUSI Fahrplan <"+ fpl_filename + "> nicht gefunden. Bitte auf der Seite <Fahrplan und Strecke-Einstellungen> richtig einstellen")
                    return                    
            if xml_filename == "":
                self.controller.set_statusmessage("Kein ZUSI Buchfahrplann eingestellt. Bitte auf der Seite <Fahrplan und Strecke-Einstellungen> auswählen")
                return
            else:
                if not os.path.isfile(xml_filename):
                    self.controller.set_statusmessage("ZUSI Buchfahrplan <"+ xml_filename + "> nicht gefunden. Bitte auf der Seite <Fahrplan und Strecke-Einstellungen> richtig einstellen")
                    return                      
            if starthour == "" or starthour==None:
                self.controller.set_statusmessage("Keine Startzeit für den Bildfahrplan eingestellt. Bitte auf der Seite <Fahrplan und Strecke-Einstellungen> einstellen")
                return
            if duration == "" or duration==None:
                self.controller.set_statusmessage("Kein Zeitraum für den Bildfahrplan eingestellt. Bitte auf der Seite <Fahrplan und Strecke-Einstellungen> einstellen")
                return        
            self.timetable_main.create_zusi_zug_liste(fpl_filename)
            if self.controller.check_if_config_data_changed() or self.firstcall:
                self.controller.set_statusmessage("Bildfahrplanerstellung gestartet - bitte etwas Geduld")
                self.firstcall = False
                self.xml_filename = xml_filename
                self.fpl_filename = fpl_filename
                self.starthour = starthour
                self.duration = duration
                self.timetable_main.redo_fpl_and_canvas(self.canvas_width,self.canvas_height,fpl_filename=fpl_filename,xml_filename=xml_filename,starthour=starthour,duration=duration)
            else:
                self.controller.set_statusmessage(" ")
                self.controller.timetable_activ = True
        self.canvas_bindings()
        self.cancel_pagechange = False
    
    def tabunselected(self):
        if self.pagechange_canceled:
            self.pagechange_canceled = False
        else:
            logging.debug("Tabunselected: %s",self.tabname)
            try:
                if self.timetable_main.timetable.test_trainline_data_changed_flag():
                    answer = tk.messagebox.askyesnocancel ('Sie verlassen den Bildfahrplan','Der Fahrplan wurde verändert. Sie sollten die Änderungen vor dem Verlassen speichern. Wollen Sie zurück zum Bildfahrplan, und die Änderungen speichern?',default='yes')
                    if answer == None:
                        self.cancel_pagechange = True
                        self.controller.showFramebyName("TimeTablePage")               
                    if answer:
                        self.cancel_pagechange = True
                        self.controller.showFramebyName("TimeTablePage")
                    else:
                        pass
                pass
            except:
                pass
    
    def save_schedule_data(self):
        
        pass
    
    def _update_value(self,paramkey):
        logging.info("SerialMonitorPage - update_value: %s",paramkey)
        message = self.controller.get_macroparam_val(self.tabClassName, "SerialMonitorInput")+"\r\n" #self.input.get() +"\r\n"

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