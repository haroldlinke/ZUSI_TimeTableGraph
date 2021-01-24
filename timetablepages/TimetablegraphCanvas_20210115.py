#!/usr/bin/env python3

from tkinter import Tk, Canvas, Frame, BOTH, font, filedialog

from xmltodict import parse

from datetime import datetime

import os

from PIL import Image, ImageGrab

"""
    * The left column has the layout information along with the station names next to the diagram box.
    * The column width is dynamic based on the width of the items.
    * Across the top, lined up with the diagram box, are the throttle lines.
    * The main section is the diagram box.
    * Across the bottom, lined up with the diagram box, is the hours section.
    * <pre>
    *       +--------- canvas -------------+
    *       | info    | throttle lines     |
    *       |         |+------------------+|
    *       | station ||                  ||
    *       | station || diagram box      ||
    *       | station ||                  ||
    *       |         |+------------------+|
    *       |         | hours              |
    *       +------------------------------+
    * </pre>
    * A normal train line will be "a-b-c-d-e" for a through train, or "a-b-c-b-a" for a turn.
    * <p>
    * A multi-segment train will be "a1-b1-c1-x2-y2-z2" where c is the junction. The
    * reverse will be "z2-y2-z2-c2-b1-a1".  Notice:  While c is in both segments, for
    * train stop purposes, the arrival "c" is used and the departure "c" is skipped.
    */
"""

import math

class Point:
        def __init__(self, x, y):
                self.x = x
                self.y = y

        def __add__(self, other: 'Vector'):
                return Vector(other.x + self.x, other.y + self.y)

        def __sub__(self, other):
                return Vector(self.x - other.x, self.y - other.y)

        def __iter__(self):
                yield self.x
                yield self.y

        def __str__(self):
                return f'{self.__class__.__name__}({self.x}, {self.y})'


class Vector:
        def __init__(self, x, y):
                self.x = x
                self.y = y

        def __add__(self, other):
                return Point(other.x + self.x, other.y + self.y)

        def __sub__(self, other):
                return Vector(other.x - self.x, other.y - self.y)

        def scale(self, scalar):
                return Vector(self.x * scalar, self.y * scalar)

        def normal(self):
                norm = self.norm()
                if norm == 0:
                        return Vector(self.x,self.y)
                else:
                        return Vector(self.x / norm, self.y / norm)

        def norm(self):
                return math.hypot(self.x, self.y)

        def perp(self):
                x, y = self.normal()
                return Vector(y, -x)

        def angle(self):
                return math.atan2(-self.y, self.x) * (180 / math.pi)

        def __iter__(self):
                yield self.x
                yield self.y

        def __str__(self):
                return f'{self.__class__.__name__}({self.x}, {self.y})'
        

class TimeTableGraphCommon():


#     * Initialize the data used by paint() and supporting methods when the
#     * panel is displayed.
#     * @param segmentId The segment to be displayed.  For multiple segment
#     * layouts separate graphs are required.
#     * @param scheduleId The schedule to be used for this graph.
#     * @param showTrainTimes When true, include the minutes portion of the
#     * train times at each station.
#     * @param height Display height
#     * @param width Display width
#     * @param displayType (not currently used)
#     */


        def __init__(self, controller, showTrainTimes, height, width):
                self.controller = controller
                self.showTrainTimes = showTrainTimes
                self.ZugGattung_to_Color = { "D" : "red",
                                             "E" : "blue"}
                self.trainTypeList = [] #["D","E"]
                
                # init timetable with dummy data
                self.timetable_dict = {"Schedule":
                                        {"Name": "Testschedule",
                                         "StartHour": 12,
                                         "Duration" : 7,
                                         "Stations":
                                         {0:
                                               {"StationName" : "Station0",
                                                "Distance"    : 0,
                                                "data"        : "Data1"
                                               },
                                          1:
                                               {"StationName": "Station1",
                                                "Distance"   : 10,
                                                "data"       : "Data2"
                                               },
                                          2:
                                               {"StationName": "Station2",
                                                "Distance"   : 30,
                                                "data"       : "Data2"
                                               },
                                          3:
                                               {"StationName": "Station3",
                                                "Distance"   : 60,
                                                "data"       : "Data2"
                                               },
                                          4:
                                               {"StationName": "Station4",
                                                "Distance"   : 100,
                                                "data"       : "Data2"
                                               },                                   
                                          },                                 
                                         "Trains":
                                         {1: 
                                          {"TrainName":"Train1",
                                           "Color" : "red",
                                           "Stops" : 
                                           {0:
                                            {"StationIdx" : 0,
                                             "ArriveTime" : 10,
                                             "DepartTime" : 15,
                                             "Direction"  : "down"
                                             },
                                            1:
                                            {"StationIdx" : 1,
                                              "ArriveTime": 60,
                                              "DepartTime": 65,
                                              "Direction" : "down"
                                              },
                                            2:
                                            {"StationIdx" : 2,
                                              "ArriveTime": 90,
                                              "DepartTime": 120,
                                              "Direction" : "down"
                                              },
                                            3:
                                            {"StationIdx" : 3,
                                              "ArriveTime": 150,
                                              "DepartTime": 160,
                                              "Direction" : "down"
                                              },
                                            4:
                                            {"StationIdx" : 4,
                                              "ArriveTime": 200,
                                              "DepartTime": 240,
                                              "Direction" : "down"
                                              }                                     
                                             }
                                            },
                                          2:
                                          {"TrainName":"Train2",
                                           "Color" : "blue",
                                           "Stops" : 
                                           {0:
                                            {"StationIdx" : 0,
                                             "ArriveTime"    : 60,
                                             "DepartTime"  : 65,
                                             "Direction"  : "down"
                                             },
                                            1:
                                            {"StationIdx" : 1,
                                              "ArriveTime": 70,
                                              "DepartTime" : 75,
                                              "Direction" : "down"
                                        }
                                       }
                                      }
                                    }
                                  }
                                }                
                                
                #segment_dict = self.dataMgr.get("Segment",{})
                #self.segment = segment_dict.get(self.segmentId,None)
                #self.layout = self.dataMgr.getLayout(self.segment.getLaYoutId)
                #self.throttles = self.layout.getThrottles()
                self.schedule_dict = self.timetable_dict.get("Schedule",{})
                
                self.schedule = self.schedule_dict # .get(self.scheduleId,None)                
                
                self.startHour = self.schedule_dict.get("StartHour",0)
                self.duration  = self.schedule_dict.get("Duration",0)
                self.stations  = self.schedule_dict.get("Stations",{})   # getStations(self.scheduleId, True)
                self.startTime_min = self.startHour * 60
                self.stationIdx_max = 0
                self.trains    = self.schedule_dict.get("Trains",{}) # self.trains = self.dataMgr.getTrains(self.scheduleId,0,True)
                self.trainIdx_max = 0
                self.dimHeight = height
                self.dimWidth  = width

                self.stdFont = font.Font(family="SANS_SERIF", size=10)  #new Font(Font.SANS_SERIF, Font.PLAIN, 10);
                self.smallFont = font.Font(family="SANS_SERIF", size=8) # new Font(Font.SANS_SERIF, Font.PLAIN, 8);
                self.gridstroke = 0.5 # new BasicStroke(0.5f);
                self.stroke = 2.0 #new BasicStroke(2.0f);

                self.segmentId = 0
                self.scheduleId = 0

                self.stops = [] #List<Stop> self.stops;

                #// ------------ global variables ------------
                self.stationGrid = {0: 0.01 } # HashMap<Integer, Double> self.stationGrid = new HashMap<>();
                self.hourMap = {0: 0.01} # HashMap<Integer, Double> self.hourMap = new HashMap<>();
                self.hourgrid = [] # ArrayList<Double> self.hourGrid = new ArrayList<>();
                self.infoColWidth = 0;
                self.hourOffset = 0;
                self.graphHeight = 0;
                self.graphWidth = 0;
                self.graphTop = 0;
                self.graphBottom = 0;
                self.graphLeft = 0;
                self.graphRight = 0;
                self.g2 = None # Graphics2D self.g2;
                self.pf = 0 #PageFormat self.pf;

                #    // ------------ train variables ------------
                self.textLocation = [(0,0,5,5)]
                                                      # ArrayList<Rectangle2D> self.textLocation = new ArrayList<>();

                #    // Train
                self.trainName = "" #String self.trainName;
                self.trainThrottle = 0
                self.trainColor = 0 # Color self.trainColor;
                self.trainLine = [] # Path2D self.trainLine;

                #    // Stop
                self.stopCnt = 0
                self.stopIdx = 0
                self.arriveTime = 0
                self.departTime = 0

                #// Stop processing
                self.maxDistance = 0.0
                self.direction = ""
                #//     int self.baseTime;
                self.firstStop = False
                self.lastStop = False

                self.firstX = 0.0
                self.lastX = 0.0

                self.sizeMinute = 0.0
                self.throttleX = 0.0

        def doPaint (self,g): #public void doPaint(Graphics g) {
                self.g2 = g
                #self._g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                self.stationGrid  = {} # clear();
                self.hourGrid     = [] #.clear();
                self.textLocation = [] # .clear();

                #//         Dimension dim = getSize();
                #//         double dimHeight = self.pf.getImageableHeight();
                #//         double dimWidth = self.pf.getImageableWidth() * 2;
                #//         double dimHeight = self.dimHeight;
                #//         double dimWidth = self.dimWidth;
                
                #// Get the height of the throttle section and set the graph top
                self.graphTop = 70.0;
                #if (self._layout.getThrottles() > 4):
                #        self.graphTop = self.layout.getThrottles() * 15.0
        
                self.graphHeight = self.dimHeight - self.graphTop - 30.0;
                self.graphBottom = self.graphTop + self.graphHeight;

                #// Draw the left column components
                self.drawInfoSection();
                self.drawStationSection();

                #// Set the horizontal graph dimensions based on the width of the left column
                self.graphLeft = self.infoColWidth + 50.0
                self.graphWidth = self.dimWidth - self.infoColWidth - 65.0
                self.graphRight = self.graphLeft + self.graphWidth

                self.drawHours();
                self.drawThrottleNumbers();
                self.drawGraphGrid();
                self.drawTrains();
                self.save_as_png(self.g2,"test_zusi")


        def drawInfoSection(self):
                # // Info section
                #self.g2.setFont(self.stdFont);
                #self.g2.setColor(Color.BLACK);
                #layoutName = "Layout" #String.format("%s %s", Bundle.getMessage("LabelLayoutName"), self.layout.getLayoutName());  #
                #segmentName = "Segment" #String.format("%s %s", Bundle.getMessage("LabelSegmentName"), self.segment.getSegmentName());  #
                scheduleName = self.schedule_dict.get("Name","")
                #effDate = "effdate" # String.format("%s %s", Bundle.getMessage("LabelEffDate"), self.schedule.getEffDate());  #
        
                #self.infoColWidth = max(self.infoColWidth, self.stdFont.measure(layoutName)) # Math.max(self.infoColWidth, self.g2.getFontMetrics().stringWidth(layoutName));
                #self.infoColWidth = max(self.infoColWidth, self.stdFont.measure(scheduleName));
                #self.infoColWidth = max(self.infoColWidth, self.stdFont.measure(effDate));
        
                #self.g2.create_text(10, 20, text=layoutName, font=self.stdFont, anchor="nw");
                #self.g2.create_text(10, 40, text=segmentName, font=self.stdFont, anchor="nw");
                self.g2.create_text(10, 40, text=scheduleName, font=self.stdFont, anchor="nw");
                #self.g2.create_text(10, 80, text=effDate, font=self.stdFont, anchor="nw");

        def drawStationSection(self):
                stationIdx_last = len(self.stations)-1
                self.maxDistance = self.stations[stationIdx_last].get("Distance",0)
                self.stationGrid = {}
                for stationIdx in self.stations:
                        station = self.stations.get(stationIdx,{})
                        stationName = station.get("StationName","")
                        self.infoColWidth = max(self.infoColWidth, self.stdFont.measure(stationName) + 5)
                        distance = station.get("Distance")
                        stationY = ((self.graphHeight - 50) / self.maxDistance) * distance + self.graphTop + 30  #// calculate the Y offset
                        self.g2.create_text(15.0, stationY, text=stationName, font=self.stdFont, anchor="w")
                        self.stationGrid[stationIdx] = stationY

        def drawHours(self):
                currentHour = self.startHour
                hourWidth = self.graphWidth / (self.duration)
                self.hourOffset = hourWidth / 2
                #self.g2.setFont(self.stdFont)
                #self.g2.setColor(Color.BLACK)
                self.hourgrid = []
                
                for i in range(0, self.duration+1):
                        hourString = str(currentHour)+":00"
                        hourX = (hourWidth * i) + self.hourOffset + self.graphLeft;
                        hOffset = self.stdFont.measure(hourString) / 2 # hOffset = self.g2.getFontMetrics().stringWidth(hourString) / 2;
                        self.g2.create_text(hourX - hOffset, self.graphBottom + 20, text = hourString, anchor="w")
                        self.g2.create_text(hourX - hOffset, self.graphTop - 8, text = hourString, anchor="w")
                        self.hourMap[currentHour] = hourX
                        
                        self.hourGrid.append(hourX);
                        if (i == 0):
                                self.firstX = hourX - hOffset;
                        
                        if (i == self.duration):
                                self.lastX = hourX - hOffset;
                        
                        currentHour+= 1
                        if (currentHour > 23):
                                currentHour -= 24;

        def drawThrottleNumbers(self):
                #self.g2.setFont(self.smallFont);
                #self.g2.setColor(Color.BLACK);
                #for i in range(1, self.throttles):
                #        self.g2.create_text(self.graphLeft, i * 14, text=str(i), font = self.smallFont);
                pass
                
            
        def drawGraphGrid(self):
                # Print the graph box
                self.g2.create_rectangle(self.graphLeft, self.graphTop, self.graphLeft+self.graphWidth, self.graphTop + self.graphHeight)
        
                # Print the grid lines
                for y in self.stationGrid.values():
                        self.g2.create_line(self.graphLeft, y, self.graphRight, y, width=2, fill="gray")
                for x in self.hourGrid:
                        self.g2.create_line(x, self.graphTop, x, self.graphBottom, width=2, fill="gray");

#    /**
#    * Create the train line for each train with labels.  Include times if
#     * selected.
#     * <p>
#     * All defined trains their stops are processed.  If a stop has a station
#     * in the segment, it is included.  Most trains only use a single segment.
#     */
        def drawTrains(self):
                #//         self.baseTime = self.startHour * 60;
                self.sizeMinute = self.graphWidth / ((self.duration) * 60);
                self.throttleX = 0;
                for trainidx in self.trains:
                        train = self.trains.get(trainidx,{})
                        
                        self.trainType = train.get("TrainType","X-Deko")
                        
                        self.trainName = self.trainType + train.get("TrainName","0000")
                      
                        if (self.trainTypeList != [] and not self.trainType in self.trainTypeList):
                                break
                        #self.trainThrottle = train.getThrottle();
                        #typeColor = self.dataMgr.getTrainType(train.getTypeId()).getTypeColor();
                        self.trainColor = train.get("Color","black")
                        self.trainLine = []
            
                        activeSeg = False
            
                        self.stops = train.get("Stops",{});
                        self.stopCnt = len(self.stops);
                        self.firstStop = True;
                        self.lastStop = False;
                        self.prevStop = None
            
                        for self.stopIdx,stop_dict in self.stops.items():
                                
                                self.arriveTime = stop_dict.get("ArriveTime",0)
                                self.departTime = stop_dict.get("DepartTime",0)
                                #self.direction = stop_dict.get("Direction","down")
                                self.stopStation  = stop_dict
                                stopSegmentId = self.segmentId # stopStation.getSegmentId();
                                if (self.stopIdx > 0): self.firstStop = False;
                                if (self.stopIdx == self.stopCnt - 1): self.lastStop = True;
                                                                                
                                if (not activeSeg):
                                        if (stopSegmentId != self.segmentId):
                                                continue
                    
                                        activeSeg = True
                                        self.setBegin(self.stopStation)
                                        if (self.lastStop):
                                                #// One stop route or only one stop in current segment
                                                self.setEnd(self.stopStation, False);
                                                break;
                                        continue;
                                        
                
                                #// activeSeg always true here
                                if stopSegmentId != self.segmentId:
                                                #// No longer in active segment, do the end process
                                                self.setEnd(self.stopStation, True);
                                                activeSeg = False;
                                                continue;
                                else:
                                                self.drawLine(self.stopStation);
                                                if (self.lastStop):
                                                                #// At the end, do the end process
                                                                self.setEnd(self.stopStation, False);
                                                                break;

#    /**
#        * Draw a train name on the graph.
#        * <p>
#        * The base location is provided by x and y.  justify is used to offset
#        * the x axis.  invert is used to flip the y offsets.
#        * @param x The x coordinate.
#        * @param y The y coordinate.
#        * @param justify "Center" moves the string left half of the distance.  "Right"
#        * moves the string left the full width of the string.
#        * @param invert If true, the y coordinate offset is flipped.
#        * @param throttle If true, a throttle line item.
#        */
        def drawTrainName( self, x,  y,  justify,  invert,  throttle):
                
                textbox_x= self.stdFont.measure(self.trainName)
                #// Position train name
                if justify =="Center": # 
                        x = x - textbox_x /2
                else:
                        if justify == "Right": 
                                x = x - textbox_x
        
                if (invert):
                        if (self.direction== "down" or throttle):
                                y = y - 7 #20
                        else:
                                y = y + 13 # 20  
                else:
                        if (self.direction== "down" or throttle):
                                y = y + 13
                        else:
                                y = y - 7                    

                textRect = (
                        x,
                        y,
                        textbox_x,
                        10
                        )
                textRect = self.adjustText(textRect)
                x = textRect[0] # textRect.getX();
                #self.g2.create_rectangle(x,y,x+textbox_x,y+12,fill="white")
                trainName_objid = self.g2.create_text(x , y, activefill="red",text = self.trainName, anchor = "w") #anchor="nw")
                self.controller.ToolTip_canvas(self.g2, trainName_objid, text="Zug: "+self.trainName, key=self.trainName,button_1=True)
                self.textLocation.append(textRect)


#    /**
#        * Draw the minutes value on the graph if enabled.
#        * @param time The time in total minutes.  Converted to remainder minutes.
#        * @param mode Used to set the x and y offsets based on type of time.
#        * @param x The base x coordinate.
#        * @param y The base y coordinate.
#        */
        def drawTrainTime(self, time,  mode,  x,  y):
                if (not self.showTrainTimes):
                        return;
                
                if not (time in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                        return                
                
                minutes = str(time % 60).format("%02d")
                textbox_x = self.stdFont.measure(minutes)
                if mode ==  "begin" :
                        if (self.direction== "down"):
                                x = x + 2
                                y = y + 10
                        else:
                                x = x + 2  #
                                y = y - 1   # 10  
                elif mode == "arrive":
                        if (self.direction== "down"):
                                x = x - 12     # +2
                                y = y - 10 # #####2
                        else:
                                x = x - 12
                                y = y + 20
                elif mode == "depart":
                        if (self.direction== "down"):
                                x = x + 2
                                y = y + 10
                        else:
                                x = x + 2
                                y = y - 20   
                elif mode == "end":
                        x = x
                        y = y
                        
                else:
                        return;
                
                textRect = (
                        x,
                        y,
                        textbox_x,
                        10
                        )
                #textRect = self.adjustText(textRect)
                #x = textRect[0] # textRect.getX();
        
                #self.g2.setFont(self.stdFont);
                #s self.g2.setColor(Color.GRAY);
                #self.g2.create_rectangle(textRect[0],textRect[1],textRect[0]+textbox_x,textRect[1]+12,fill="white")
                trainTime_objid = self.g2.create_text(x , y, text = minutes, anchor="w")
                self.controller.ToolTip_canvas(self.g2, trainTime_objid, text="Zug: "+self.trainName, key=self.trainName,button_1=True)
                #self.g2.drawString(self.trainName, x, y);
                self.textLocation.append(textRect)                

#    /**
#        * Move text that overlaps existing text.
#        * @param textRect The proposed text rectangle.
#        * @return The resulting rectangle
#        */
        def adjustText(self, textRect):
                xLoc = textRect[0] 
                yLoc = textRect[1] 
                xLen = textRect[2] 
        
                wrkX = xLoc;
                chgX = False;

                for workRect in self.textLocation:
                        if workRect[1] == yLoc:
                                xMin = workRect[0]
                                xMax = xMin + workRect[3]
                
                                if (xLoc > xMin and xLoc < xMax):
                                        wrkX = xMax + 2;
                                        chgX = True;
                                
                
                                if (xLoc + xLen > xMin and xLoc + xLen < xMax):
                                        wrkX = xMin - xLen -2;
                                        chgX = True;
                if (chgX):
                        textRect = (
                                wrkX,
                                yLoc,
                                textRect[2], 
                                textRect[3]
                                )
                return textRect

#    
#    Determine direction of travel on the graph: up or down
#    
        def setDirection(self):
                        
                if (self.stopCnt == 1):
                        # Single stop train, default to down
                        self.direction = "down";  #
                        return;
                
        
                stop = self.stops.get(self.stopIdx);
                currStation_Idx = stop.get("Station_Idx",0)
                currStation = self.stations.get(currStation_Idx)
                currkm = currStation.get("Distance")
        
                if (self.firstStop):
                        #// For the first stop, use the next stop to set the direction
                        nextStation_Idx = self.stops.get(self.stopIdx + 1).get("StationIdx")
                        nextStation = self.stations.get(nextStation_Idx)
                        if nextStation.get("Distance") > currkm:
                                self.direction = "down" 
                        else :  
                                self.direction = "up"
                        return
                    
                prevStation_Idx = self.stops.get(self.stopIdx - 1).get("StationIdx")
                prevStation = self.stations.get(prevStation_Idx)
                #prevStation = self.dataMgr.getStation(self.stops.get(self.stopIdx - 1).getStationId());
                if (self.lastStop):
                        #// For the last stop, use the previous stop to set the direction
                        #// Last stop may also be only stop after segment change; if so wait for next "if"
                        #if (prevStation.get(SegmentId() == self.segmentId):
                        #self.direction = (prevStation.getDistance() < currDistance) ? "down" : "up";  
                        if prevStation.get("Distance") < currkm:
                                self.direction = "down" 
                        else :  
                                self.direction = "up"                                
                        return;
            
                #// For all other stops in the active segment, use the next stop.
                if (not self.lastStop):
                        nextStation_Idx = self.stops.get(self.stopIdx + 1).get("StationIdx")
                        nextStation = self.stations.get(nextStation_Idx)                        
                        #if (nextStation.getSegmentId() == self.segmentId):
                        if (nextStation.get("Distance") > currkm):
                                self.direction = "down"
                        else: 
                                self.direction = "up";  
                        return;
                
        
        
                #// At this point, don't change anything.
            

#    /**
#        * Set the starting point for the self.trainLine path.
#        * The normal case will be the first stop (aka start) for the train.
#        * <p>
#        * The other case is a multi-segment train.  The first stop in the current
#        * segment will be the station AFTER the junction.  That means the start
#        * will actually be at the junction station.
#        * @param stop The current stop.
#        */
        def setBegin(self, stop):
                segmentChange = False;

                if self.stopIdx > 0:
                        #// Begin after segment change
                        segmentChange = True;
                        prevStop = self.stops.get(self.stopIdx - 1,{})
                        prevStation = self.stations(prevStop.getStationId());
                        prevName = prevStation.getStationName();                        
                        
                        #// Find matching station in the current segment for the last station in the other segment
                        for segStation in self.stations:
                                if (segStation.getStationName() == prevName):
                                        #// x is based on previous depart time, y is based on corresponding station position
                                        x = self.calculateX(prevStop.getDepartTime());
                                        y = self.stationGrid.get(segStation.getStationId());
                                        self.trainLine.extend([x, y])
                                        self.throttleX = x;  #// save for drawing the throttle line at setEnd
                    
                                        self.setDirection();
                                        #self.drawTrainName(x, y, "Center", True, False);  #
                                        self.drawTrainTime(prevStop.getDepartTime(), "begin", x, y);  #
                                        break
                if not (self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                        return                
                x = self.calculateX(stop.get("ArriveTime"))
                y = self.stationGrid.get(stop.get("StationIdx",0))
        
                if (segmentChange):
                        self.trainLine.extend([x, y])
                        self.setDirection();
                        self.drawTrainTime(stop.get("ArriveTime"), "arrive", x, y);  #
                else:
                        self.trainLine = [x, y]
                        self.throttleX = x;  #// save for drawing the throttle line at setEnd
            
                        self.setDirection();
                        #self.drawTrainName(x, y, "Center", True, False);  #
                        self.drawTrainTime(stop.get("ArriveTime"), "begin", x, y);  #
                    
        
                #// Check for stop duration before depart
                if (self.duration > 0):
                        x = self.calculateX(self.stopStation.get("DepartTime",0))
                        self.trainLine.extend([x, y])
                        self.drawTrainTime(self.stopStation.get("DepartTime",0), "depart", x, y);  #// NOI18

#    /**
#        * Extend the train line with additional stops.
#        * @param stop The current stop.
#        */
        def drawLine(self, stop):
                if not (self.departTime in range(self.startTime_min,self.startTime_min + self.duration * 60) or self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                        return
                x = self.calculateX(self.arriveTime);
                y = self.stationGrid.get(stop.get("StationIdx"));
                self.trainLine.extend([x, y])
                self.drawTrainTime(self.arriveTime, "arrive", x, y);  #
                if len(self.trainLine)>3:
                        self.draw_trainName_parallel(self.trainName, self.trainLine[-4],self.trainLine[-3],x, y)                
        
                self.setDirection();
                #// Check for duration after arrive
                if (self.departTime - self.arriveTime) > 0 :
                        if not (self.departTime in range(self.startTime_min,self.startTime_min + self.duration * 60) or self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                                return                        
                        x = self.calculateX(self.departTime);
                        self.trainLine.extend([x, y])
                        self.drawTrainTime(self.departTime, "depart", x, y);  #

#    /**
#        * Finish the train line, draw it, the train name and the throttle line if used.
#        * @param stop The current stop.
#        * @param endSegment final segment
#        */
        def setEnd(self, stop, endSegment):
                skipLine = False;
                if self.trainLine == []:
                        return
                if (len(self.stops) == 1 or endSegment):
                        x = self.trainLine[-2]
                        y = self.trainLine[-1]
                        skipLine = True
                        #self.drawTrainName(x, y, "Center", False, False) 
                else:
                        if (self.arriveTime in range(self.startTime_min,self.startTime_min + self.duration * 60)):
                                x = self.calculateX(self.arriveTime)
                                y = self.stationGrid.get(stop.get("StationIdx"))
                                #self.drawTrainName(x, y, "Center", False, False)
                        else:
                                x = self.trainLine[-2]
                                y = self.trainLine[-1]
                                skipLine = True
                                self.drawTrainName(x, y, "Center", False, False)
                if (not skipLine):
                        self.trainLine.extend([x, y])
                
                train_line_objid = self.g2.create_line(self.trainLine,fill=self.trainColor,width=4,activewidth=8)
                self.controller.ToolTip_canvas(self.g2, train_line_objid, text="Zug: "+self.trainName, key=self.trainName,button_1=True)
                
#            /**
#                * Convert the time value, 0 - 1439 to the x graph position.
#                * @param time The time value.
#                * @return the x value.
#                */
        def calculateX(self, time):
                if (time < 0): time = 0;
                if (time > 1439): time = 1439;
        
                hour = int(time / 60)
                min = int(time % 60)
        
                return self.hourMap.get(hour,self.firstX) + (min * self.sizeMinute)
        
        
        def draw_trainName_parallel(self,trainName,x0,y0,x1,y1):
                p0, p1 = Point(x0,y0), Point(x1,y1)
                segment = p1 - p0
                mid_point = segment.scale(0.5) + p0
               
                offset = segment.perp().scale(10)
                # canvas.create_line(*mid_point, *(mid_point+offset))
        
                txt = self.g2.create_text(*(offset + mid_point), text=trainName)
                if y0 != y1:
                        angle = segment.angle()
                        self.g2.itemconfig(txt, angle=angle)                

        def enter_station(self,stationName, distance):
                
                for stationIdx in self.stations:
                        station_data = self.stations.get(stationIdx)
                        if station_data.get("StationName") == stationName:
                                return
                
                self.stations[self.stationIdx_max] = {"StationName": stationName, "Distance": distance}
                self.stationIdx_max +=1
                
                return self.stationIdx_max - 1
                
        def enter_train_data(self,ZugNummer,ZugGattung,Zuglauf):
                
                color = self.ZugGattung_to_Color.get(ZugGattung,"black")
                
                self.trains[self.trainIdx_max] = {"TrainName": ZugNummer,
                                                  "TrainType": ZugGattung,
                                                  "Trainline": Zuglauf,
                                                  "Color"    : color,
                                                  "Stops"    : {}
                                                   }
                self.trainIdx_max += 1
                
                return self.trainIdx_max-1
        
        def search_station(self, stationName):
                for stationIdx in self.stations:
                        station_data = self.stations.get(stationIdx)
                        if station_data.get("StationName") == stationName:
                                return stationIdx
                
                return -1
                
                
        
        def enter_train_stop(self, train_idx, trainstop_idx,FplName,FplAnk_min,FplAbf_min):
                
                train_dict = self.trains.get(train_idx)
                
                trainstops = train_dict.get("Stops")
                
                station_idx = self.search_station(FplName)
                
                if FplAnk_min == 0:
                        FplAnk_min = FplAbf_min
                        
                arriveTime = FplAnk_min
                departTime = FplAbf_min
                trainstops[trainstop_idx] = {"StationIdx" : station_idx,
                                             "ArriveTime" : arriveTime,
                                             "DepartTime" : departTime,
                                             "Direction"  : "down"
                                             }
                
                return trainstop_idx + 1
        
        def convert_zusi_tt_to_timetable_train_x(self, zusi_tt, define_stations=False):
                        

                Zusi_dict = zusi_tt.get("Zusi")
                Buchfahrplan_dict = Zusi_dict.get("Buchfahrplan")
                kmStart = float(Buchfahrplan_dict.get("@kmStart","0.00"))
                ZugNummer = Buchfahrplan_dict.get("@Nummer")
                ZugGattung = Buchfahrplan_dict.get("@Gattung")
                if ZugGattung == "X-Deko":
                        return
                Zuglauf = Buchfahrplan_dict.get("@Zuglauf")
                Datei_fpn_dict = Buchfahrplan_dict.get("Datei_fpn")
                fpn_dateiname = Datei_fpn_dict.get("@Dateiname")
                self.schedule_dict["Name"] = fpn_dateiname
                train_idx = self.enter_train_data(ZugNummer,ZugGattung,Zuglauf)
                train_stop_idx = 0
                FplZeile_list = Buchfahrplan_dict.get("FplZeile")
                for FplZeile_dict in FplZeile_list:
                        try:
                                FplAbf_dict_list = FplZeile_dict.get("FplAbf")
                        except:
                                FplAbf_dict_list = None
                        if FplAbf_dict_list:
                                try:
                                        FplAbf = FplAbf_dict_list.get("@Abf")
                                except:
                                        FplAbf_dict = FplAbf_dict_list[0]
                                        FplAbf = FplAbf_dict.get("@Abf")
                                
                                FplAbf_obj = datetime.strptime(FplAbf, '%Y-%m-%d %H:%M:%S')
                                FplAbf_min = FplAbf_obj.hour * 60 + FplAbf_obj.minute
                                FplAnk_dict_list = FplZeile_dict.get("FplAnk")
                                if FplAnk_dict_list:
                                        try:
                                                FplAnk = FplAnk_dict_list.get("@Ank")
                                        except:
                                                FplAnk_dict = FplAnk_dict_list[0]
                                                FplAnk = FplAnk_dict.get("@Ank")
                                        FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                                        FplAnk_min = FplAnk_obj.hour * 60 + FplAnk_obj.minute
                                else:
                                        
                                        FplAnk_min = 0
                                FplName_dict = FplZeile_dict.get("FplName")
                                FplName = FplName_dict.get("@FplNameText","---")
                                Fplkm_dict_list = FplZeile_dict.get("Fplkm")
                                
                                if Fplkm_dict_list:
                                        
                                        try: # Fplkm_dict_list is a dict
                                                Fplkm = float(Fplkm_dict_list.get("@km"))
                                        except: # Fplkm_dict_list is a list
                                                Fplkm_dict = Fplkm_dict_list[0]
                                                Fplkm = float(Fplkm_dict.get("@km"))
                                else:
                                        Fplkm = 0.0
                                
                                Fpldistance = abs(kmStart - Fplkm)
                                
                                #FplAnk_obj = datetime.strptime(FplAnk, '%Y-%m-%d %H:%M:%S')
                                
                                #print(FplName,"-",Fplkm,"-",FplAnk_min,"-",FplAbf_min,"-",Fpldistance)
                                
                                if define_stations:
                                        station_idx = self.enter_station(FplName,Fpldistance)
                                else:
                                        station_idx = self.search_station(FplName)
                                        if station_idx != -1:
                                                train_stop_idx = self.enter_train_stop(train_idx, train_stop_idx, FplName,FplAnk_min,FplAbf_min)
                return
        
        def save_as_png(self, canvas, fileName):
                # save postscipt image 
                canvas.update()
                canvas.postscript(file = fileName + '.eps',colormode='color') 
                # use PIL to convert to PNG 
                img = Image.open(fileName + '.eps')
                try:
                        
                        img.save(fileName + '.png', 'png')
                except: 
                        print("Error while generating png-file- Ghostscript not found")
                        pass

class Example(Frame):

        def __init__(self,controller,canvas):
                super().__init__()
                self.controller = controller
                self.zusi_master_timetable_dict = {}
                self.canvas = canvas
        
                self.initUI()
                
        def open_zusi_trn_file(self, trn_filepathname):
                
                with open(trn_filepathname,mode="r",encoding="utf-8") as fd:
                        xml_text = fd.read()
                        trn_dict = parse(xml_text)
                        
                trn_filepath, trn_filename = os.path.split(trn_filepathname)
                
                trn_zusi_dict = trn_dict.get("Zusi")
                trn_zug_dict = trn_zusi_dict.get("Zug")
                Buchfahrplan_dict = trn_zug_dict.get("BuchfahrplanRohDatei")
                if Buchfahrplan_dict:
                        
                        Bfpl_Dateiname = Buchfahrplan_dict.get("@Dateiname")
                        
                        Bfpl_file_path, Bfpl_file_name = os.path.split(Bfpl_Dateiname)
                        
                        Bfpl_filepathname = os.path.join(trn_filepath,Bfpl_file_name)
                        
                        with open(Bfpl_filepathname,mode="r",encoding="utf-8") as fd:
                                xml_text = fd.read()
                                Bfpl_timetable_dict = parse(xml_text)
        
                                #enter train-timetable
                                self.timetable.convert_zusi_tt_to_timetable_train_x(Bfpl_timetable_dict)                
                
                
        def open_zusi_master_schedule(self):
                fpl_filename = r"D:\Zusi3\_ZusiData\Timetables\Deutschland\Ruhrtalbahn\Hagen-Kassel_Fahrplan1981_12Uhr-19Uhr.fpn"
                #fpl_filename = filedialog.askopenfilename(title="Select Zusi Master Schedule",filetypes=(("Zusi-Master-Fahrplan","*.fpn"),("all files","*.*")))
                                
                if fpl_filename == "": return
                
                fpl_path, fpl_file = os.path.split(fpl_filename)
        
                print('Input File, %s.' % fpl_filename)
                with open(fpl_filename,mode="r",encoding="utf-8") as fd:
                        xml_text = fd.read()
                        self.zusi_master_timetable_dict = parse(xml_text)
                zusi_dict = self.zusi_master_timetable_dict.get("Zusi")        
                fahrplan_dict = zusi_dict.get("Fahrplan")       
                zug_list = fahrplan_dict.get("Zug")
                
                for zug in zug_list:
                        datei_dict = zug.get("Datei")
                        trn_filename = datei_dict.get("@Dateiname")
                        trn_filename_comp = trn_filename.split("\\")
                        trn_file_and_path = os.path.join(fpl_path,trn_filename_comp[-2],trn_filename_comp[-1])
                        
                        self.open_zusi_trn_file(trn_file_and_path)

    
        def initUI(self):
    
                #self.master.title("Timetable")
                #self.pack(fill=BOTH, expand=1)
        
                #canvas = Canvas(self)
                #canvas.create_line(15, 25, 200, 25)
                #canvas.create_line(300, 35, 300, 200, dash=(4, 2))
                #canvas.create_line(55, 85, 155, 85, 105, 180, 55, 85)
                canvas = self.canvas
                showTrainTimes = True
                height =self.canvas.winfo_reqheight()
                width = self.canvas.winfo_reqwidth()
                

                xml_filename = r"D:\Zusi3\_ZusiData\Timetables\Deutschland\Ruhrtalbahn\Hagen-Kassel_Fahrplan1981_12Uhr-19Uhr\D843.timetable.xml"
                #xml_filename = filedialog.askopenfilename(title="ZUSI Zugfahrplan",filetypes=(("Timetable","*.xml"),("all files","*.*")))
                                
                if xml_filename == "": return
        
                print('Input File master train timetable, %s.' % xml_filename)
                with open(xml_filename,mode="r",encoding="utf-8") as fd:
                        xml_text = fd.read()
                        zusi_timetable_dict = parse(xml_text)

                self.timetable = TimeTableGraphCommon(self.controller, showTrainTimes, height, width)
                #define stops via selected train-timetable
                self.timetable.convert_zusi_tt_to_timetable_train_x(zusi_timetable_dict,define_stations=True)
                
                self.open_zusi_master_schedule()

                self.timetable.doPaint(canvas)
                
                #self.timetable.save_as_png(canvas, xml_filename)
        
                #canvas.pack(fill=BOTH, expand=1)
