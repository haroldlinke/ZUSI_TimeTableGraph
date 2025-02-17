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
import threading
import queue
import time
import struct
import socket
import logging

ThreadEvent_ZUSI = None

# ----------------------------------------------------------------
# Class ZUSI_TCP
# ----------------------------------------------------------------
class ZUSI_TCP():

    def __init__(self, TCP_IP_Adress, TCP_Port_Adress, controller):
        logging.debug("Init ZUSI_fpn: %s : %s ",TCP_IP_Adress,TCP_Port_Adress)
        self._controller = controller
        if TCP_IP_Adress == "":
            self._TCP_IP_Adress = "127.0.0.1"
        else:
            self._TCP_IP_Adress = TCP_IP_Adress
        if TCP_Port_Adress == "":
            self._TCP_Port_Adress = "1436"
        else:
            self._TCP_Port_Adress = TCP_Port_Adress
        self._callback_dict = {}
        #self.queue = queue.Queue()
        self._queue_ZUSI = queue.Queue()
        self._connected_to_ZUSI_server = False
        self._ZUSI_server_connected = False
        
    def open_connection(self,TCP_IP_Adress="127.0.0.1", TCP_Port_Adress="1436",callback=None):
        self._TCP_IP_Adress = TCP_IP_Adress
        self._TCP_Port_Adress = TCP_Port_Adress
        self.connection_status_callback = callback
        logging.debug("open connection to ZUSI Server: %s : %s ",self._TCP_IP_Adress,self._TCP_Port_Adress)
        if self.connection_status_callback:
            self.connection_status_callback(status="Connecting",message="open connection to ZUSI Server: " + self._TCP_IP_Adress + self._TCP_Port_Adress)
        return self._start_process_ZUSI()
        
    def close_connection (self):
        if self._ZUSI_server_connected:
            logging.debug("close connection to ZUSI Server: %s : %s ",self._TCP_IP_Adress,self._TCP_Port_Adress)
            self._stop_process_ZUSI()
            self._socket.close()
            self._ZUSI_server_connected = False
            self._connected_to_ZUSI_server = False
        
    def start_ZUSI_train(self,trainnumber,fpn_filename=""):
        self.send_msg = bytearray()
        if fpn_filename=="":
            self._addKnotenAnfang(0x0002) # <Kn>    // Client-Anwendung 02
            self._addKnotenAnfang(0x010B) # <Kn>    // Befehl CONTROL
            self._addKnotenAnfang(0x0006) # <Kn>    // Zug starten
            self._addTextAtribut(0x01, trainnumber)  # Zugnummer
            self._addKnotenEnde()
            self._addKnotenEnde()
            self._addKnotenEnde()
        else:
            self._addKnotenAnfang(0x0002) # <Kn>    // Client-Anwendung 02
            self._addKnotenAnfang(0x010B) # <Kn>    // Befehl CONTROL
            self._addKnotenAnfang(0x0003) # <Kn>    // Zug starten
            self._addTextAtribut(0x01, fpn_filename) # Fahrplandateiname
            self._addTextAtribut(0x02, trainnumber)  # Zugnummer
            self._addKnotenEnde()
            self._addKnotenEnde()
            self._addKnotenEnde()
        try:
            self._socket.sendall(self.send_msg)
            return True
        except:
            self.close_connection()
            return False

    def addcallbackforNeededFunctions(self, knoten, attribute_list, callback_function,valuetype="Single"):
        """assign a callback function and valuetype to a ZUSI function
        
        Arguments:
        knoten -- node number as defined in the ZUSI doc for Fahrpultdaten
        attribute_list -- list of attributes for whih the callback_function should be called e.g. (16,17,18)
        callback_function -- function that should be called when ZUSI sends a message for one of the attributes listed in attribute_list
        
              the callback_function has following arguments: 
                             
                             event_dict -- dictionaire with the keywords: 
                                  "Attribute"  -- attribute_id that was send from ZUSI
                                  "Value"      -- value that was send by ZUSI in the valuetype as specified in valuetype
                                  
                            example: def callback_time(event_dict): 
                                         attribute_id = event_dict["Attribute"]
                                         value = event_dict["Value"]
                                         # do something with the data
        
        Keyword arguments
        value_type -- type of the value submited to the callback function
            Byte: 1 byte 0...255
            ShortInt: 1 byte -128...127
            Word: 2 byte 0...65535
            SmallInt: 2 byte -32768..32767
            Integer: 4 byte -2147483648...2147483647
            Cardinal: 4 byte 0...4294967295
            Single: 4 byte 1,5E-45...3,4E38
            Double: 8 byte 5,0E-324...1,7E308
            String: X byte Ein byte pro Ziffer/Buchstabe
            Datei: X byte Serialisierte Datei
        """
        logging.debug("addNeededFunctions: %s : %s", attribute_list, repr(callback_function))
        knoten_dict = self._callback_dict.get(knoten,{})
        if knoten_dict == {}:
            self._callback_dict[knoten]=knoten_dict
        for attribute in attribute_list:
            knoten_dict[attribute] = {"cb_function":callback_function,
                                      "valuetype"  : valuetype}
            
    def sendNeededData(self):
        self.send_msg = bytearray()
        self._addKnotenAnfang(0x0002) # <Kn>    // Client-Anwendung 02
        self._addKnotenAnfang(0x0003) # <Kn>    // Befehl NEEDED_DATA
        for knoten,knoten_dict in self._callback_dict.items():
            self._addKnotenAnfang(knoten)
            for attribute in knoten_dict.keys():
                self._addAtributonly(attribute)
            self._addKnotenEnde()
        self._addKnotenEnde()
        self._addKnotenEnde()
        self._socket.sendall(self.send_msg)
        
    def getConnectionStatus(self):
        return self._ZUSI_server_connected
    
    def cancel(self):
        self._stop_process_ZUSI()    
         
    def _addKnotenAnfang(self, knoten):
        self.send_msg.extend((0x00, 0x00, 0x00, 0x00))
        self.send_msg.extend(struct.pack('<h',knoten))
        
    def _addKnotenEnde(self):
        self.send_msg.extend((0xFF, 0xFF, 0xFF, 0xFF))
        
    def _addAtribut(self, atid, atribut):
        self.send_msg.extend((0x04, 0x00, 0x00, 0x00))
        self.send_msg.extend(struct.pack('<h',atid))
        self.send_msg.extend(struct.pack('<h',atribut))
        
    def _addTextAtribut(self, atid, text):
        pass
        text_len = len(text) + 2
        self.send_msg.append(text_len & 0x000000ff)
        self.send_msg.append((text_len & 0x0000ff00) >> 8)
        self.send_msg.append((text_len & 0x00ff0000) >> 16)
        self.send_msg.append((text_len & 0xff000000) >> 24)
        self.send_msg.append(atid & 0x00ff)
        self.send_msg.append((atid & 0xff00) >> 8)
        self.send_msg.extend(text.encode('latin-1'))

    def _addAtributonly(self, atribut):
        self.send_msg.extend((0x04, 0x00, 0x00, 0x00, 0x01, 0x00))
        self.send_msg.append(atribut)
        self.send_msg.append(0x00)
        
    def _readZUSIInput(self, data):
        # This function is used to isolate a zusi telegram.
        # If we can find an entire one, we cut it for decoding, and leave the rest, to be appended to new data.
        nodesChanged = False
        nodeCount = 0
        packetLength = 0
        self._nodelayer = 0
        self._incommingData.extend(data)      # Add arrived data to be parsed
        i = 0
        while i < (len(self._incommingData)-3):
            packetLength = self._readIntegerInRawAtPos(i); # Get length of according zusi docu 11.3.1.1
            if packetLength == 0: # 0x0000 means node begin
                nodesChanged = True;
                nodeCount += 1
                i = i + 6
            elif packetLength == -1:    # 0xffff (= -1) means node end
                nodesChanged = True
                nodeCount -= 1
                i = i + 4
            else:
                i = i + packetLength + 4
            if (nodesChanged and nodeCount == 0):
                self._ZusiCommand = self._incommingData[0:i]
                self._incommingData = self._incommingData[i:]
                self._AnalyseZUSICommand()
                nodesChanged = False
            if nodeCount > 6:
                self._incommingData = bytearray() # something went wrong Notbremse!!
                break

    def _readIntegerInRawAtPos(self,pos):
        try:
            
            if len(self._incommingData)>=pos+3:
                data = struct.unpack("<l",self._incommingData[pos:pos+4])
            else:
                logging.debug("Error _readIntegerInRawAtPos: ",repr(self._incommingData))
                return 0
            return data[0]
        except:
            return 0
        
    def _readIntegerAtPos(self, pos):
        data = struct.unpack("<l",self._ZusiCommand[pos:pos+4])        
        return data[0]
        
    def _readIdAtPos(self, pos):
        data = struct.unpack("<H",self._ZusiCommand[pos:pos+2])               
        return data[0]
        
    def _AnalyseZUSICommand(self):
        packetLength = 0
        self.atributeId = 0
        self.nodeIds = [0] *6
        i = 0
        while i < (len(self._ZusiCommand)-3):
            packetLength = self._readIntegerAtPos(i);
            if packetLength == 0: # Länge = 0 kennzeichnet den Knoten im Unterschied zum Attribut
                self.nodeIds[self._nodelayer] = self._readIdAtPos(i+4) # ID zur Codierung der Funktion des Knotens (Word)
                self._nodelayer += 1
                i = i + 6
            elif packetLength == -1: #Kennzeichnung des Knoten-Endes
                self._nodelayer -= 1
                i = i + 4
            else:
                self.atributeId = self._readIdAtPos(i+4) # ID zur Codierung der Funktion des Attributs (Word)
                self.nodeIds[self._nodelayer] = self.atributeId
                self.attributeData = self._ZusiCommand[i+6:i+6+packetLength-2]
                if (self.nodeIds[0] == 0x0002): # "Client-Anwendung 02"
                    self._zusiDecoderFahrpult()
                else:
                    self._zusiDecoderSecondaryInfos()
                i = i + packetLength + 4
        
    def _zusiDecoderFahrpult(self):
        knoten_dict = self._callback_dict.get(self.nodeIds[1],{})
        if knoten_dict == {}:
            return
        else:
            callback_dict = knoten_dict.get(self.nodeIds[2],{})
            callback = callback_dict.get("cb_function",None)
            valuetype = callback_dict.get("valuetype","")
            if callback:
                event={}
                event["Attribute"] = self.nodeIds[2]
                if valuetype == "Single":
                    event["Value"] = struct.unpack("<f",self.attributeData)[0] # 4-byte float
                elif valuetype == "Double":
                        event["Value"] = struct.unpack("<d",self.attributeData)[0] # 4-byte float                    
                elif valuetype == "String":
                    event["Value"] = str(self.attributeData,"UTF-8") # String
                elif valuetype == "Byte":
                    event["Value"] = struct.unpack("B",self.attributeData)[0] # 1-byte integer
                elif valuetype == "Word":
                    event["Value"] = struct.unpack("<H",self.attributeData)[0] # 2-byte integer
                elif valuetype == "Integer":
                    event["Value"] = struct.unpack("<i",self.attributeData)[0] # 4-byte integer
                elif valuetype == "Cardinal":
                    event["Value"] = struct.unpack("<I",self.attributeData)[0] # 4-byte integer                
                elif valuetype == "SmallInt":
                    event["Value"] = struct.unpack("<h",self.attributeData)[0] # 2-byte integer
                elif valuetype == "ShortInt":
                    event["Value"] = struct.unpack("b",self.attributeData)[0] # 2-byte integer
                elif valuetype == "Datei":
                    event["Value"] = self.attributeData # serialisierte Datei
                callback(event)
        return
                    
    def _zusiDecoderSecondaryInfos(self):
        #// Verbindung
        if (self.nodeIds[0] == 0x0001) and (self.nodeIds[1] == 0x0002):
            if (self.nodeIds[2]) == 0x0001:
                logging.debug("Zusi-Version: " + str(self.attributeData,"UTF-8"))
                self.ZUSI_version = str(self.attributeData,"UTF-8")
                return
            elif (self.nodeIds[2]) == 0x0002:
                logging.debug("Zusi-Verbindungsinfo: " + str(self.attributeData,"UTF-8"))
                self.ZUSI_Verbindungsinfo = str(self.attributeData,"UTF-8")
                return
        if ((self.nodeIds[0] == 0x0001) and (self.nodeIds[1] == 0x0002) and (self.nodeIds[2] == 0x0003)):
            if self.attributeData[0] == 0:
                logging.debug("Der Client wurde akzeptiert")
                self._ZUSI_server_connected = True
                if self.connection_status_callback:
                    self.connection_status_callback(status="Connected",message="Connection to ZUSI Server: " + self.ZUSI_version + self.ZUSI_Verbindungsinfo)                        
                
            pass

    def _process_ZUSI_TCP(self):
        if self._queue_ZUSI:
            while self._queue_ZUSI.qsize():
                #logging.debug("process_serial: While loop")
                try:
                    readtext = self._queue_ZUSI.get()
                    self._readZUSIInput(readtext)
                except IOError:
                    pass

        if self._connected_to_ZUSI_server:
            self._controller.after(100, self._process_ZUSI_TCP)
        else:
            pass

    def _start_process_ZUSI(self):
        global ThreadEvent_ZUSI
        # Datagram (udp) socket
        msg = ""
        self._incommingData = bytearray()
        self._connected_to_ZUSI_server = False
        try :
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            logging.debug ('Socket created: Host' + hostname + " IP-adress " + ip_address)
        except (socket.error, msg) :
            logging.debug ('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            if self.connection_status_callback:
                self.connection_status_callback(status="Not Connected",message='Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])              
            return False
        self.send_msg = bytearray()
        self._addKnotenAnfang(0x0001)  #<Kn>  Verbindungsaufbau
        self._addKnotenAnfang(0x0001)  #<Kn>  Befehl HELLO
        self._addAtribut(0x01, 0x02) # Protokoll-Version
        self._addAtribut(0x02, 0x02) # Client-Typ: [1: Zusi| 2: Fahrpult]
        self._addTextAtribut(0x03, "TimeTableGraph")
        self._addTextAtribut(0x04, "2.0.8")
        self._addKnotenEnde()
        self._addKnotenEnde()
        # connect and send "Hello" to ZUSI
        try:
            self._socket.connect((self._TCP_IP_Adress,int(self._TCP_Port_Adress)))
            self._socket.sendall(self.send_msg)
        except BaseException as e:
            if self.connection_status_callback:
                self.connection_status_callback(status="Not Connected",message='Failed to create socket. Error Code : ' + str(e))              
            logging.debug ('Connect failed. Error Code : %s',str(e))
            return False
        self._connected_to_ZUSI_server = True
        ThreadEvent_ZUSI = threading.Event()
        ThreadEvent_ZUSI.set()
        time.sleep(2)
        ThreadEvent_ZUSI.clear()
        self.thread = ZUSIThread(self._queue_ZUSI,self._socket,self)
        self.thread.start()
        self._process_ZUSI_TCP()
        logging.debug ('Socket bind complete')
        return True
        
    def _stop_process_ZUSI(self):
        global ThreadEvent_ZUSI
        self._connected_to_ZUSI_server = False
        if ThreadEvent_ZUSI:
            ThreadEvent_ZUSI.set()
        time.sleep(1)
        try:
            self._socket.close()
        except:
            pass
            logging.debug("Error closing socket") 
   
class ZUSIThread(threading.Thread):
    def __init__(self, p_queue, p_socket,mainpage):
        threading.Thread.__init__(self)
        self._queue_ZUSI = p_queue
        self._socket = p_socket
        self._mainpage = mainpage

    def run(self):
        logging.debug("ZUSIThread started")
        if self._socket:
            #now keep talking with the client
            while not ThreadEvent_ZUSI.is_set() and self._socket:
                self._socket.settimeout(3)
                try:
                    data = self._socket.recv(1024)
                except (socket.timeout,ConnectionResetError):
                    continue                
                except BaseException as e: 
                    logging.debug("ZUSI-Thread %s",str(e))
                    self._mainpage.close_connection()
                    break
                try:
                    if len(data)>0:
                        self._queue_ZUSI.put(data)
                except:
                    pass
        logging.debug("ZUSI Thread received event. Exiting")
   
    
    
 

