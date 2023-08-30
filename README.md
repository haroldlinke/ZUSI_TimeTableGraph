# ZUSI_TimeTableGraph

Zusi ist eine stark vorbildorientierte, PC-basierte 3D-Eisenbahnfahrsimulation, mit dem Schwerpunkt auf dem virtuellen Fahren eines Zuges. Bei Zusi gibt es komplette Fahrplanszenarien mit u.U. mehreren 100 Zügen. Der Benutzer kann sich einen der Züge aussuchen und diesen manuell fahren oder auch vom Autopiloten fahren lassen und aus Lokführersicht zusehen. Details findet man unter http://www.zusi.de.

Ein Bildfahrplan ist eine grafische Darstellung einse Zugfahrplans für eine Strecke mit definierten Bahnhöfen in einem bestimmten Zeitraum.
Das ZUSI Bildfahrplanprogramm kann ZUSI-Fahrplanszenarien als Bildfahrplan darstellen.
Zur Erstellung eines Bildfahrplans geht man folgendermassen vor:
1. Auf die Seite <Bahnhof-Einstellungen> wechseln
2. Mit Hilfe des Buttons <ZUSI Fahrplandatei> einen ZUSI Fahrplan auswählen (Erweiterung .fpl
3. Um die Strecke und die Bahnhöfe zu definieren, wird ein ZUSI-Buchfahrplan verwendet. Dieser enthält für eine Strecke alle notwendigen Angaben.
4. Der ZUSI-Buchfahrplan kann aus der Streckenliste ausgewählt werden oder direkt als ZUSI Buchfahrplan-Datei (Erweiterung .timeline.xml)
5. Auf der Seite <Ansicht Einstellungen> kann die Grösse des Bildfahrplans in Pixel und der Zeitraum angegeben werden. Ausserdem ist es möglich beliebigen Zuggattungen eine Linen Farbe zuzuordnen.
6. Sind alle Angaben gemacht, kann auf der Seite <Bildfahrplan> der Bildfahrplan angezeigt werden. Je nach Komplexität des Fahrplans, kann die Anzeige etwas dauern.
  
  Installation:
  
1. Datei ZUSI_timetablegraph.zip herunterladen
2. ZUSI_timetablegraph.zip in einem beliebigen Verzeichnis entpacken
3. Es wird ein neuer Ordner ZUSI_timetablegraph erzeugt. Dieser Ordner enthält alle notwendigen Python-Dateien und eine Python3 Installation.
4. Programm starten mit anklicken von ZUSI_timetablegraph.exe


History of Changes:
V04.02: 
- Import Fahrtenschreiber (Beta)
V04.01:
new:
- schematic trackline
- show all ZFS
- support timeline > 0:00
corrected:
- multiple refresh possible
