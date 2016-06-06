# -*- coding: utf-8 -*-
#!/usr/bin/python

import sys,glob,os,sqlite3
from osgeo import ogr, osr,gdal
import string,shutil
from dbfpy.dbf import *
from xml.dom.minidom import *

class indexabgleich():
    def __init__(self,lyrIn,dsIn,lyrOut,dsOut, schema = 'public', neu = True):

        #instanzvariablen
        self.lyrOut = lyrOut
        self.lyrIn = lyrIn
        self.dsIn = dsIn
        self.dsOut = dsOut
        self.neu = neu
        self.schema = schema




    ################################################################################
    #Die Klasse hat nur eine, aber dafür eine aufwendige, Methode
    #Sie aktualisiert die attributiven und räumlichen Indices sowohl für
    #Tabellen als auch Geodaten vom Format Shape/DBASE, SQLITE,POSTGIS
    ################################################################################
    def indexAbgl(self):


        try:
            if not self.dsIn.GetDriver().GetName() == "ESRI Shapefile": # gilt Für Shapes und Dbase Dateien
                return 2                                                # andere Eingangsdateien werden nich behandelt


            #######################################################################
            # RÄUMLICHER INDEX
            #einen räumlichen Index brauchen wir auf jeden Fall, wenn
            #es sich um einen Geometrie Layer handelt wird dieser IMMER angelegt
            #ohne zu fragen, egal ob Datensatz neu oder nur Aktualisierung
            #####################################################################

            if not (self.lyrIn.GetGeomType() == 100):     #100 beduetet geometrielos, dh. Eingangsdatensatz ist nur Tabelle
                #Shape
                if self.dsOut.GetDriver().GetName() == "ESRI Shapefile":
                    #print str(self.dsOut())
                    #print str(self.lyrOut())

                    self.dsOut.ExecuteSQL('create spatial index on ' + self.lyrOut.GetName())

                #Layer in Postgis
                if self.dsOut.GetDriver().GetName() == "PostgreSQL":

                    geometriespalte = self.lyrOut.GetGeometryColumn()

                    # die query schaut nach, ob ein Index auf das Geometriefeld besteht
                    query = 'select * from pg_indexes where tablename = \'' + self.lyrOut.GetName() + '\' and schemaname = \'' + self.schema + '\' and indexdef like \'%'  + geometriespalte + '%\''
                    erg = self.dsOut.ExecuteSQL(query)
                    recs = erg.GetFeatureCount()  # Gibt ein Layer Objekt zurück, dass die Anzahl der Records enthält

                    if not (recs > 0):  #Indexeintrag wird gefunden, wenn recs > 0 d.h. es gibt einen Index auf Geometriespalte (= räuml. Index)
                        #print 'Index POSTGIS fehlt'
                        query ='create index idx_' + geometriespalte + '_' + self.lyrOut.GetName() + ' on ' + self.schema + '.' + self.lyrOut.GetName() + ' using gist (' "\"" + geometriespalte + "\"" ')'
                        self.dsOut.ExecuteSQL(query)  #Es gibt schon einen raeumlichen Index, der halt nicht passt es wird 0 (String) zurückgegeben

                    else:
                        #print 'Index POSTGIS vorhanden'
                        query = 'reindex table '  + self.schema + '.' +  self.lyrOut.GetName()
                        self.dsOut.ExecuteSQL(query)

                #Spatialite
                #(legt den räumlichen Index nicht als "normalen" Index an,
                #sondern bildet ein Konstrukt von Triggern und Tabellen für den räumlichen Index)
                if self.dsOut.GetDriver().GetName() == "SQLite": #SQLITE
                    geometriespalte = self.lyrOut.GetGeometryColumn()

                    query = 'select CheckSpatialIndex(\'' + self.lyrOut.GetName() + '\',\'' + geometriespalte + '\')'
                    d = self.dsOut.ExecuteSQL(query)
                    f = d.GetNextFeature().GetFieldAsInteger(0)

                    if f == 1: #Die Query liefert als Feldwert des Features 1 zurück wenn Index vorhanden
                        self.dsOut.ReleaseResultSet(d)  #sonst DB blockiert!!!
                        query = 'select RecoverSpatialIndex(\'' + self.lyrOut.GetName() + '\',\'' + geometriespalte + '\')'
                        s = self.dsOut.ExecuteSQL(query)
                        self.dsOut.ReleaseResultSet(s)  #sonst DB blockiert!!!
                    elif f == 0: #Die Query liefert als Feldwert des Features 0 zurück wenn Index fehlt
                        self.dsOut.ReleaseResultSet(d)  #sonst DB blockiert!!!
                        query = 'select CreateSpatialIndex(\'' + self.lyrOut.GetName() + '\',\'' + geometriespalte + '\')'
                        s = self.dsOut.ExecuteSQL(query)
                        self.dsOut.ReleaseResultSet(s)  #sonst DB blockiert!!!
                    #else:
                        #print 'Fehler bei Indexerstellung'



            ##################################################################
            #  ATTRIBUTIVER INDEX                                            #
            ##################################################################

            if self.neu:   #Neuer Datensatz wird hochgeladen

                #der Pfad zum attributiven Index File der Shape Datei
                if not (self.lyrIn.GetGeomType() == 100):  #100 beduetet geometrielos
                    indexfileIn = self.dsIn.GetName() + "/" + self.lyrIn.GetName() + ".idm"

                #der Pfad zum attributiven Indexfile einer DBASE Datei
                else:
                    indexfileIn = self.dsIn.GetName().replace('.dbf','') + ".idm"



                #hat das Eingangsfile (egal ob Shape oder nur DBF)
                #einen attributiven Index?
                FlaggeIn = False

                try:
                    file = open(indexfileIn)
                    xml = file.read()
                    din = parseString(xml)
                    file.close()
                    FlaggeIn = True #Eingangsfile hat attributiven Index
                except IOError:
                   FlaggeIn = False #Eingangsfile hat keinen attributiven Index



                idx = []
                if FlaggeIn:    #Eingangsshape hat attributive Indices
                                #Diese werden nun als Vorlage für den neuen Layer verwendet!

                    feldnamenIn = din.getElementsByTagName("FieldName") #Diese Node im XNL enhält die Spaltenname mit Index!
                    for feldname in feldnamenIn:
                        idx.append(feldname.firstChild.data)


                    #Der Ziellayer ist ein Shape
                    if self.dsOut.GetDriver().GetName() == "ESRI Shapefile":
                        for indi in idx:
                            query = str('create index on ' + self.lyrOut.GetName() + ' using ' + indi + '')
                            self.dsOut.ExecuteSQL(query)

                    #Der Ziellayer ist Spatialite
                    elif self.dsOut.GetDriver().GetName() == "SQLite":
                        for indi in idx:
                            query = str('create index idx_' + indi + '_' + self.lyrOut.GetName() + ' on ' + self.lyrOut.GetName() + ' (' "\"" + indi + "\"" ')') #ACHTUNG: Gross Kleinschreibung bei postgres!
                            self.dsOut.ExecuteSQL(query)

                    #Der Ziellayer ist Postgis
                    elif self.dsOut.GetDriver().GetName() == "PostgreSQL":
                        for indi in idx:
                            query = str('create index idx_' + indi + '_' + self.lyrOut.GetName() + ' on ' + self.schema + '.' + self.lyrOut.GetName() + ' using btree (' "\"" + indi + "\"" ')') #ACHTUNG: Gross Kleinschreibung bei postgres!
                            self.dsOut.ExecuteSQL(query)




            else:   #Bestehender Datensatz wird aktualisiert

                #der Pfad zu den attributiven Index Files der Shape Dateien (In/Out)
                if not (self.lyrIn.GetGeomType() == 100):  #100 beduetet geometrielos
                    indexfileIn = self.dsIn.GetName() + "/" + self.lyrIn.GetName() + ".idm"
                    indexfileOut = self.dsOut.GetName() + "/" + self.lyrOut.GetName() + ".idm"

                #der Pfad zu den attributiven index Files des DBASE Dateien (In/Out)
                else:
                    indexfileIn = self.dsIn.GetName().replace('.dbf','') + ".idm"
                    indexfileOut = self.dsOut.GetName().replace('.dbf','') + ".idm"



                #hat das Eingangsfile (egal ob Shape oder nur DBF)
                #einen attributiven Index?
                FlaggeIn = False
                try:
                    file = open(indexfileIn)
                    xml = file.read()
                    din = parseString(xml)
                    file.close()
                    FlaggeIn = True #Eingangsfile hat attributiven Index
                except IOError:
                   FlaggeIn = False #Eingangsfile hat keinen attributiven Index


                #hat das Ziel (egal ob Shape oder DBF oder Postgres oder SQLITE)
                #einen attributiven Index?
                FlaggeOut = False
                if self.dsOut.GetDriver().GetName() == "ESRI Shapefile": #Shape oder DBF
                    try:
                        file = open(indexfileOut)
                        xml = file.read()
                        dout = parseString(xml)
                        file.close()
                        FlaggeOut = True #Ausgangsfile hat attributiven Index
                    except IOError:
                        FlaggeOut = False #Ausgangsfile hat keinen attributiven Index



                if self.dsOut.GetDriver().GetName() == "PostgreSQL":    # Postgres - ACHTUNG: OGR gibt bei geometrielosen Tabellen None bei GEt FeatureCoutn zurück
                                                                        # deshalb immer reindex!
                    query = 'select * from pg_indexes where tablename = \''   + self.lyrOut.GetName() + '\' and schemaname = \''   + self.schema + '\''   #Hier werden die Indices dokumentiert
                    erg = self.dsOut.ExecuteSQL(query)
                    #print str(erg.GetFeatureCount())
                    if erg.GetFeatureCount > 0:
                        #print 'dort'                                                                                                                                                #Findet die query nichts ist das Objekt None
                        FlaggeOut = True        #Ausgangstabelle hat Index
                    else:
                        FlaggeOut = False


                if self.dsOut.GetDriver().GetName() == "SQLite": #SQLIT
                    if self.dsOut.ExecuteSQL('pragma index_list (' + self.lyrOut.GetName() + ')').GetFeatureCount() > 0:    #Hier werden die Indices dokumentiert
                                                                                                                    #Findet die query nichts ist das Objekt None
                        FlaggeOut = True        #Ausgangstabelle hat Index
                    else:
                        FlaggeOut = False



                #Eingangsshape hat attributiven Index
                #Ist die primär Vorlage für die Indices des zu aktualisierenden Layer verwendet!
                idx = []

                if FlaggeIn:
                    feldnamenIn = din.getElementsByTagName("FieldName")
                    for feldname in feldnamenIn:
                        idx.append(feldname.firstChild.data)

                #Eingangsshape hat keinen attributiven Index, dafür aber das Ausgangsshape
                #Ist nun die Vorlage für die Indices des zu aktualisierenden Layers!
                elif FlaggeOut and self.dsOut.GetDriver().GetName() == "ESRI Shapefile":    #Eingangsshape hat KEINE attributive Indices
                                                                                            #Es werden die am Ziellayer bestehenden aktualisiert
                                                                                            #Nur bei Shapes!
                    feldnamenOut = dout.getElementsByTagName("FieldName")
                    for feldname in feldnamenOut:
                        idx.append(feldname.firstChild.data)


                #So, nun wissen wir was für Indices anzulegen sind
                #also kanns losgehen

                #Attributive Indices für Shape oder DBF Datei
                #Wird einfach für das aktualisierte Shape oder
                #die DBASE Tabelle neu geschrieben
                if self.dsOut.GetDriver().GetName() == "ESRI Shapefile":
                    for indi in idx:
                        query = str('create index on ' + self.lyrOut.GetName() + ' using ' + indi + '')
                        self.dsOut.ExecuteSQL(query)

                #Attributive Indices für Sqlite
                #ACHTUNG: Im Unterschied zum File wird IMMER nur
                #der Datenbankindex neu gebildet. Da dieser gegebenenfalls
                #komplexer sein kann als beim Shape/DBASE File ist das so besser
                #Wenn kein Index in der Datenbank vorhanden wird ein Hinweis rausgegeben
                #diesen anzulegen
                elif self.dsOut.GetDriver().GetName() == "SQLite" and FlaggeOut:    #Wenn Index auf DB gilt dieser
                    if FlaggeOut:
                        query = 'reindex ' + self.lyrOut.GetName()
                        self.dsOut.ExecuteSQL(query)
                    else:
                        return 3



                #Attributive Indices für Postgres
                #ACHTUNG: Im Unterschied zum File wird IMMER nur
                #der Datenbankindex neu gebildet. Da dieser gegebenenfalls
                #komplexer sein kann als beim Shape/DBASE File ist das so besser
                #Wenn kein Index in der Datenbank vorhanden wird ein Hinweis rausgegeben
                #diesen anzulegen
                elif self.dsOut.GetDriver().GetName() == "PostgreSQL":    #Wenn Index auf DB gilt dieser
                    if FlaggeOut:
                        query = 'reindex table ' + self.schema + '.' + self.lyrOut.GetName()
                        self.dsOut.ExecuteSQL(query)
                    else:
                        return 3


            #Alles in Ordnung!!
            return 1

        except Exception as e:
            print str(e)

            return 4    #komplett danebengegangen
