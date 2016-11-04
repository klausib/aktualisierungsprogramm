# -*- coding: utf-8 -*-
#!/usr/bin/python


##import sys
##sys.path.append('C:/Program Files/QGIS Wien/apps/Python27/Lib/site-packages')
from osgeo import ogr, osr,gdal
import shutil, os, glob, string, sys




class Vergleich():
    def __init__(self,lyrIn=None,dsIn=None,lyrOut=None,dsOut=None):

        self.lyrOut = lyrOut
        self.lyrIn = lyrIn
        self.dsIn = dsIn
        self.dsOut = dsOut

        if not (dsIn == None or dsOut == None):
            self.featDefOut = self.lyrOut.GetLayerDefn()
            self.featDefIn = self.lyrIn.GetLayerDefn()


        self.depp = None

    ##################################################################
    #Bei Tabellen und Geodatensätzen wird deren Aufbau
    #beim Aktualisieren eines bestehenden Datensatzes
    #verglichen um Konsistenz im Datenmodell zu gewährleisten
    ##################################################################

    def verglAttr(self, driverName):

        try:
            AttrFlag = ''

            if self.featDefOut.GetFieldCount() <= self.featDefIn.GetFieldCount():
                index = 0
                while index < (self.featDefOut.GetFieldCount()):    #Das zu aktualisierende Shape ist die Referenz!

                    defOut = self.featDefOut.GetFieldDefn(index)

                    #die Reihenfolge der Attribute ist zwar egal, aber das Attributfeld
                    #muss auch im neuen datensatz gefunden werden
                    index_o = self.featDefIn.GetFieldIndex(defOut.GetNameRef())

                    #print str(defOut.GetNameRef()) + ' --- ' + str(self.lyrIn.GetName()) + ' ---' + self.lyrOut.GetName() + ' ----- ' + defOut.GetNameRef()
                    if index_o < 0: #schon mal schlecht, wird nicht gefunden
                        return 'Fehler - Feldnamen fehlen:  Ausgangsname: ' + defOut.GetNameRef()
                    defIn = self.featDefIn.GetFieldDefn(index_o)


                    #Prüfung für Shapefiles
                    if driverName == "ESRI Shapefile":

                        #Die jeweiligenFeldnamen
                        if index > 0:
                            AttrFlag = AttrFlag + "," + defIn.GetNameRef()
                        else:
                            AttrFlag = defIn.GetNameRef()

                        #Nun der Vergleich der Attributfelder
                        #Bei Fehler wird ein String mit dem Wort Fehler zurückgegeben
                        if not string.lower(defIn.GetNameRef()) == string.lower(defOut.GetNameRef()):
                            return   "Fehler Feldname:" + defIn.GetNameRef() + " = " + defOut.GetNameRef()
                        if not defIn.GetFieldTypeName(defIn.GetType()) == defOut.GetFieldTypeName(defOut.GetType()):
                            return "Fehler Feldtyp:" + defIn.GetFieldTypeName(defIn.GetType()) + " = " + defOut.GetFieldTypeName(defOut.GetType()) + " " + defIn.GetNameRef()
##                        if not defIn.GetWidth() == defOut.GetWidth():
##                            return "Fehler Feldbreite:" + str(defIn.GetWidth()) + " = " + str(defOut.GetWidth()) + " " + defIn.GetNameRef()
##                        if not defIn.GetPrecision() == defOut.GetPrecision():
##                            return "Fehler Feldgenauigkeit:" + str(defIn.GetPrecision()) + " = " +  str(defOut.GetPrecision()) + " " + defIn.GetNameRef()

                    #Prüfung für SQLite: Dort gibts keine Feldlänge oder Precision!
                    #Deshalb können diese auch beim Prüfen nicht unterschieden werden
                    #Weiters kann anscheinend auch keine Unterscheidung anhand des Feldtyps
                    #getroffen werden!
                    elif driverName =="SQLite":

                        #Die Feldnamen
                        if index > 0:
                            AttrFlag = AttrFlag + "," + defIn.GetNameRef().split(',',1)[0]
                        else:
                            AttrFlag = defIn.GetNameRef().split(',',1)[0]

                        #Nun der Vergleich der Attributfelder
                        if not string.lower(defIn.GetNameRef()) == string.lower(defOut.GetNameRef()):
                            return  "Fehler: Feldname nicht gleich" + defIn.GetNameRef() + " = " + defOut.GetNameRef()
                        if not defIn.GetFieldTypeName(defIn.GetType()) == defOut.GetFieldTypeName(defOut.GetType()):
                            return "Fehler Feldtyp:" +  defIn.GetFieldTypeName(defIn.GetType()) + " = " + defOut.GetFieldTypeName(defOut.GetType()) + " " + defIn.GetNameRef()+ " " + defOut.GetNameRef()

                    #Prüfung für Postgis:
                    elif driverName =="PostgreSQL":

                        #Die Feldnamen
                        if index > 0:
                            AttrFlag = AttrFlag + "," + "\"" +  defIn.GetNameRef() + "\""
                        else:
                            AttrFlag = "\"" + defIn.GetNameRef() + "\""

                        #Nun der Vergleich der Attributfelder
                        if not string.lower(defIn.GetNameRef()) == string.lower(defOut.GetNameRef()):
                            return   "Fehler Feldname:" + defIn.GetNameRef() + " = " + defOut.GetNameRef()
                        if not defIn.GetFieldTypeName(defIn.GetType()) == defOut.GetFieldTypeName(defOut.GetType()):
                            return "Fehler Feldtyp:" +  defIn.GetFieldTypeName(defIn.GetType()) + " = " + defOut.GetFieldTypeName(defOut.GetType()) + " " + defIn.GetNameRef()

                    index = index + 1

            else:
                AttrFlag = ("Fehler: Feldanzahl zu gering")

            return AttrFlag

        except Exception as e:
            print str(e)
            return "Fehler: Schwerer Fehler in Methode verglAttr"




    #Haben Ein- und Ausgang den gleichen Geometrietyp
    def verglGeom(self):


        if (self.lyrIn.GetGeomType() == self.lyrOut.GetGeomType()):
            return 'OK'
        #fall point/multipoint
        elif self.lyrIn.GetGeomType() == 1 and self.lyrOut.GetGeomType() == 4:
            return 'OK'
        elif self.lyrIn.GetGeomType() == 4 and self.lyrOut.GetGeomType() == 1:
            return 'OK'
        #fall line/multiline
        elif self.lyrIn.GetGeomType() == 2 and self.lyrOut.GetGeomType() == 5:
            return 'OK'
        elif self.lyrIn.GetGeomType() == 5 and self.lyrOut.GetGeomType() == 2:
            return 'OK'
        #fall polygon/multipolygon
        elif self.lyrIn.GetGeomType() == 3 and self.lyrOut.GetGeomType() == 6:
            return 'OK'
        elif self.lyrIn.GetGeomType() == 6 and self.lyrOut.GetGeomType() == 3:
            return 'OK'

        #fall point/multipoint mit M
        elif self.lyrIn.GetGeomType() == ogr.wkbPointM and self.lyrOut.GetGeomType() == ogr.wkbMultiPointM:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiPointM and self.lyrOut.GetGeomType() == ogr.wkbPointM:
            return 'OK'
        #fall line/multiline 3D
        elif self.lyrIn.GetGeomType() == ogr.wkbLineStringM and self.lyrOut.GetGeomType() == ogr.wkbMultiLineStringM:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiLineStringM and self.lyrOut.GetGeomType() == ogr.wkbLineStringM:
            return 'OK'
        #fall polygon/multipolygon 3D
        elif self.lyrIn.GetGeomType() == ogr.wkbPolygonM and self.lyrOut.GetGeomType() == ogr.wkbMultiPolygonM:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiPolygonM and self.lyrOut.GetGeomType() == ogr.wkbPolygonM:
            return 'OK'

        #fall point/multipoint 3D
        elif self.lyrIn.GetGeomType() == ogr.wkbPoint25D and self.lyrOut.GetGeomType() == ogr.wkbMultiPoint25D:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiPoint25D and self.lyrOut.GetGeomType() == ogr.wkbPoint25D:
            return 'OK'
        #fall line/multiline 3D
        elif self.lyrIn.GetGeomType() == ogr.wkbLineString25D and self.lyrOut.GetGeomType() == ogr.wkbMultiLineString25D:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiLineString25D and self.lyrOut.GetGeomType() == ogr.wkbLineString25D:
            return 'OK'
        #fall polygon/multipolygon 3D
        elif self.lyrIn.GetGeomType() == ogr.wkbPolygon25D and self.lyrOut.GetGeomType() == ogr.wkbMultiPolygon25D:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiPolygon25D and self.lyrOut.GetGeomType() == ogr.wkbPolygon25D:
            return 'OK'

        #fall point/multipoint 3D mit M
        elif self.lyrIn.GetGeomType() == ogr.wkbPointZM and self.lyrOut.GetGeomType() == ogr.wkbMultiPointZM:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiPointZM and self.lyrOut.GetGeomType() == ogr.wkbPointZM:
            return 'OK'
        #fall line/multiline 3D
        elif self.lyrIn.GetGeomType() == ogr.wkbLineStringZM and self.lyrOut.GetGeomType() == ogr.wkbMultiLineStringZM:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiLineStringZM and self.lyrOut.GetGeomType() == ogr.wkbLineStringZM:
            return 'OK'
        #fall polygon/multipolygon 3D
        elif self.lyrIn.GetGeomType() == ogr.wkbPolygonZM and self.lyrOut.GetGeomType() == ogr.wkbMultiPolygonZM:
            return 'OK'
        elif self.lyrIn.GetGeomType() == ogr.wkbMultiPolygonZM and self.lyrOut.GetGeomType() == ogr.wkbPolygonZM:
            return 'OK'
        else:
            return 'Fehler'

    #Haben Ein- und Ausgang das gleiche räumliche Bezugssystem und
    #wenn kein Bezugssystem definiert ist, wird das zugewiesen
    #welches in der Steuertabelle definiert ist
    #Ist der Datensatz neu, wird das Bezugssystem des Datensatzes (falls vorhanden)
    #mit dem Eintrag in der Steuertabelle verglichen
    def verglRef(self,bezugssystem):

        try:

            refIn = None
            refOut = None

            #Die Eingangs- und Ausgangsbezugssysteme
            if not self.lyrIn == None:
                refIn = self.lyrIn.GetSpatialRef()
            if not self.lyrOut == None:
                refOut = self.lyrOut.GetSpatialRef()

            #Das Standardbezugssystem laut Steuertabelle
            reffi = osr.SpatialReference()
            reffi.ImportFromEPSG(bezugssystem)

            inputname = self.lyrIn.GetName()
            inputpfad = self.dsIn.GetName() + "/"
            bezugssystem_txt = reffi.ExportToWkt() #gibt das Bezugssystem als Char zurück
            #self.depp = reffi.ExportToProj4() #gibt das Bezugssystem als Char zurück im Proj4 Format


            #Das Bezugssystem Ein- und Ausgang vergleichen
            if (not refIn == None) and (not refOut == None):
                if (refIn.ExportToWkt() == refOut.ExportToWkt()):
                    return 1

            #der Datensatz ist neu, ist das Bezugssystem
            #gleich dem in der Steuertabelle definierten
            elif not refIn == None:
                if refIn.ExportToWkt() == bezugssystem_txt:
                    return 1

            #Der Eingangsdatensatz hat kein Bezugssystem oder ein falsches(weil das oft vergessen wird)
            #es wird das in der Steuertabelle eingetragene Bezugssystem automatisch zugewiesen (dem Eingangsshape und
            #dadurch auch beim Kopierprozess den Ausgangsdaten in Datenbanken - nicht Shape)
            f = open (inputpfad + inputname + ".prj","w")
            # Die vogis Modifikation....
            bezugssystem_txt = bezugssystem_txt.replace('MGI','GCS_MGI')
            bezugssystem_txt = bezugssystem_txt.replace('GCS_MGI / Austria GK West','MGI_Austria_GK_West')
            bezugssystem_txt = bezugssystem_txt.replace('Militar_Geographische_Institute','D_MGI')
            #print bezugssystem_txt
            f.write(bezugssystem_txt)
            f.close()

            return 2

        except:
            return 3



    def grossKlein(self,inputname,outputname):
        if re.match(inputname,outputname):
            return True
        else:
            return False



    #Methode wird nur verwendet, wenn ein
    #neues Shape am Filesystem kopiert wird.
    #Liegen im Verzeichnis nämlich keine Shapes
    #ist das DataSource Objekt Null und die die
    #Methode kopieren kann nicht verwendet werden
    #def kopierenNachShape(self,driverin,dsIn,pfad):
    def kopieren_filebasis(self,inputpfad,inputname,outputpfad,outputname,suffix = None):

            #würde den ganzen workspace kopieren!!!
            #driverin.CopyDataSource(dsIn,pfad) #das eigentliche Kopieren
        try:
            inputpfad = inputpfad + "/"
            outputpfad = outputpfad + '/'

            if os.path.exists(inputpfad + inputname + ".shp"):
                shutil.copyfile(inputpfad + inputname + ".shp", outputpfad + outputname + ".shp")
            if os.path.exists(inputpfad + inputname + ".shp.xml"):
                shutil.copyfile(inputpfad + inputname + ".shp.xml",outputpfad + outputname + ".shp.xml")
            if os.path.exists(inputpfad + inputname + ".dbf"):
                shutil.copyfile(inputpfad + inputname + ".dbf", outputpfad + outputname + ".dbf")
            if os.path.exists(inputpfad + inputname + ".sbn"):
                shutil.copyfile(inputpfad + inputname + ".sbn",outputpfad + outputname + ".sbn")
            if os.path.exists(inputpfad + inputname + ".sbx"):
                shutil.copyfile(inputpfad + inputname + ".sbx", outputpfad + outputname + ".sbx")
            if os.path.exists(inputpfad + inputname + ".fbn"):
                shutil.copyfile(inputpfad + inputname + ".fbn", outputpfad + outputname + ".fbn")
            if os.path.exists(inputpfad + inputname + ".fbx"):
                shutil.copyfile(inputpfad + inputname + ".fbx", outputpfad + outputname + ".fbx")
            if os.path.exists(inputpfad + inputname + ".shx"):
                shutil.copyfile(inputpfad + inputname + ".shx", outputpfad + outputname + ".shx")
            if os.path.exists(inputpfad + inputname + ".qix"):
                shutil.copyfile(inputpfad + inputname + ".qix", outputpfad + outputname + ".qix")
            if os.path.exists(inputpfad + inputname + ".prj"):
                shutil.copyfile(inputpfad + inputname + ".prj", outputpfad + outputname + ".prj")
            if os.path.exists(inputpfad + inputname + ".ind"):
                shutil.copyfile(inputpfad + inputname + ".ind", outputpfad + outputname + ".ind")
            if os.path.exists(inputpfad + inputname + ".idm"):
                shutil.copyfile(inputpfad + inputname + ".idm", outputpfad + outputname + ".idm")
            if os.path.exists(inputpfad + inputname + ".ain"):
                shutil.copyfile(inputpfad + inputname + ".ain", outputpfad + outputname + ".ain")
            if os.path.exists(inputpfad + inputname + ".aih"):
                shutil.copyfile(inputpfad + inputname + ".aih", outputpfad + outputname + ".aih")
            if os.path.exists(inputpfad + inputname + ".ixs"):
                shutil.copyfile(inputpfad + inputname + ".ixs", outputpfad + outputname + ".ixs")
            if os.path.exists(inputpfad + inputname + ".mxs"):
                shutil.copyfile(inputpfad + inputname + ".mxs",outputpfad + outputname + ".mxs")
            if os.path.exists(inputpfad + inputname + ".xml"):
                shutil.copyfile(inputpfad + inputname + ".xml",outputpfad + outputname + ".xml")
            if os.path.exists(inputpfad + inputname + ".cpg"):
                shutil.copyfile(inputpfad + inputname + ".cpg", outputpfad + outputname + ".cpg")
            if os.path.exists(inputpfad + inputname + ".csv"):
                shutil.copyfile(inputpfad + inputname + ".csv", outputpfad + outputname + ".csv")

            #arcgis Attributindex Dateien
            #glob liefert eine liste mit Pfadnamen zurück
            # 1.PROBLEM: Sind quasi Doppelsuffix
            # 2.PROBLEM: Gross Kleinschreibung sollte einheitlich sein mit dem
            # anderen Kopierprozesse!!
            atxes = glob.glob(inputpfad + inputname  + ".*.atx")
            for atx in atxes:
                if os.path.exists(atx):

                    #Wegen der gleichen Gross/Kleinschreibung wie in
                    # outputname angegeben!!!!!!!!
                    atx_suffix = os.path.splitext(atx)
                    atx_suffix = os.path.splitext(atx_suffix[0])[1] + atx_suffix[1]

                    shutil.copyfile(atx, outputpfad + outputname + atx_suffix)

            return True

        #Beim Kopieren ist ein Fehler aufgetreten!
        except:
            return False

    def kopieren(self,dsOut,lyrIn,name,zieltyp,codierung=''):

        try:
            #srs = osr.SpatialReference()
            #srs.ImportFromEPSG( 31254 )

            ly = None   # unser zukünftiges Layerobjekt
            # lyrIn (das Eingangsshape) hat bereits eine SRS (original oder vom kopierprogramm vorher zugewiesen)
            # im Modul verglRef überprüft un bei Bedarf neu zugewiesen!
            srs = lyrIn.GetSpatialRef()

            if not dsOut == None:
                driverName = dsOut.GetDriver().GetName()
            else:
                if zieltyp == 'file':
                    driverName = "ESRI Shapefile"
                elif zieltyp == 'sqlite':
                    drivername = "SQLite"
                elif zieltyp == 'postgres':
                    driverName == "PostgreSQL"
                else:
                    raise Exception


            #Das Ziel des Kopierprozesses
            #wird anhand des Treibernamens identifiziert: ACHTUNG: Ist der Workspace
            #leer, dann ist dsOut None (z.B. kein Shape im Verzeichnis)
            if driverName == "ESRI Shapefile":
                ly = dsOut.CopyLayer(lyrIn,name)     #das Kopieren, unabhängig
                if ly == None:                       #vom OGR Treiber!


                    raise Exception

                #arcgis Attributindex Dateien
                #glob liefert eine liste mit Pfadnamen zurück
                # 1.PROBLEM: Sind quasi Doppelsuffix
                # 2.PROBLEM: Gross Kleinschreibung sollte einheitlich sein mit dem
                # anderen Kopierprozesse!!
                atxes = glob.glob(self.dsIn.GetName() + '/' + lyrIn.GetName()  + ".*.atx")
                for atx in atxes:
                    if os.path.exists(atx):

                        #Wegen der gleichen Gross/Kleinschreibung wie in
                        # outputname angegeben!!!!!!!!
                        atx_suffix = os.path.splitext(atx)
                        atx_suffix = os.path.splitext(atx_suffix[0])[1] + atx_suffix[1]

                        shutil.copyfile(atx, dsOut.GetName()  + '/' +  name + atx_suffix)



            elif driverName == "PostgreSQL" or driverName == "SQLite":


                #falls noch ein temp Layer existiert
                #(Beim Aktualisieren ist der name ja XXX_tmp_aktual!)
                if string.count(name,'temp_aktual') > 0:
                    if dsOut.GetLayerByName(name) > 0:
                        dsOut.DeleteLayer(name)


                # Create a memory OGR datasource to put results in. Von frank W. Die Doku ist einfach schwach
                # Deshalb wirds hier zu Dokumentationszwecken dringelassen:
                # Der Memory Layer ist deutlich performanter bei CreateFeature als wenn es direkt auf eine
                # Spatial Lite DB angewandt wird
                mem_drv = ogr.GetDriverByName( 'Memory' )
                mem_ds = mem_drv.CreateDataSource( 'out' )


##                if lyrIn.GetGeomType() == 100 and driverName == "SQLite":   #Also keine Geometrie vorhanden

##                    if driverName == "PostgreSQL":
##                        ly = dsOut.CopyLayer(lyrIn,name, ['SPATIAL_INDEX=no','PRECISION=no','GEOMETRY_NAME=the_geom', 'LAUNDER=no'])
##                    elif driverName == "SQLite":
##                        ly = dsOut.CopyLayer(lyrIn,name, ['GEOMETRY_NAME=the_geom', 'LAUNDER=no'])



                if driverName == "SQLite":

                    if lyrIn.GetGeomType() == 100:  # also KEINE Geometrie Tabelle
                        ly = dsOut.CopyLayer(lyrIn,name, ['GEOMETRY_NAME=the_geom', 'LAUNDER=no'])
                    else:
                        memme = mem_ds.CreateLayer(name,srs,lyrIn.GetGeomType())

                        i = 0
                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
                        while i < feldanzahl:
                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                            memme.CreateField(Fdefn)
                            i = i+1

                        # Unbedingt die Geometrie vereinheitlichen, im Shape ist das anscheinend
                        # nicht immer sauber und würde sonst nicht in die DB übernommen werden!!!
                        # Mehr Unterscheidungen (der Geometrie) gibt es derzeit noch nicht, also Single point oder line
                        for fea in lyrIn:

                            # None kann vom Shape weg vorkommen, deshalb die Prüfung
                            # Gibts ein Feature ohne Geometrie (das kann beim Shape vorkommen), wirds
                            # ignoriert.
                            if not fea.GetGeometryRef() == None:
                                gemi = fea.GetGeometryRef().Clone()
                            else:
                                next

                            if lyrIn.GetGeomType() == ogr.wkbMultiPoint:
                                gemi = ogr.ForceToMultiPoint(gemi)
                            elif lyrIn.GetGeomType() == ogr.wkbMultiLineString:
                                gemi = ogr.ForceToMultiLineString(gemi)
                            elif lyrIn.GetGeomType() == ogr.wkbMultiPolygon:
                                gemi = ogr.ForceToMultiPolygon(gemi)
                            elif lyrIn.GetGeomType() == ogr.wkbPolygon:
                                gemi = ogr.ForceToPolygon(gemi)
                            else:
                                gemi = gemi.Clone()

                            fea.SetGeometry(gemi)
                            memme.CreateFeature(fea)
                        if memme == None:
                            raise Exception

                        dsOut.CopyLayer(memme,name,['SPATIAL_INDEX=no', 'GEOM_TYPE=geometry', 'GEOMETRY_NAME=the_geom', 'LAUNDER=no'])


                # Einen leeren Layer in der Postgis erzeugen
                # ACHTUNG: Beim Shape wird zwischen Linestring und Multilinestring etc.
                # nicht unterschieden, es können also in einem Shape beide Arten vorkommen!
                # Es muss deshalb per Default immer die Multi- Version erzeugt werden!
                elif driverName == "PostgreSQL":



                    if lyrIn.GetGeomType() == 100: # Keine Geometrie
                        ly = mem_ds.CreateLayer(name,None,ogr.wkbNone)

                        i = 0

                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
                        while i < feldanzahl:
                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                            Fdefn.SetName(string.lower(Fdefn.GetName()))
                            ly.CreateField(Fdefn)
                            i = i+1

                        # Der gesmate Layer muss neu geschrieben werden
                        # damit Probleme beim Laden in die Datenbank
                        # möglichst ausgeschlossen werden
                        for fea in lyrIn:


                            fea_tmp = ogr.Feature(fea.GetDefnRef())


                            # sachinformation einfügen

                            i = 0
                            while i < feldanzahl:
                                if not fea.GetField(i) == None:

                                    if fea.GetFieldDefnRef(i).GetType() == 4:   # Textfeld
                                            if codierung == 'nein' or '':
                                                fea_tmp.SetField(i,fea.GetFieldAsString(i))
                                            else:   # bei Bedarf umcodieren
                                                kasperle = fea.GetFieldAsString(i).decode(codierung,'replace').encode('utf8','replace')
                                                fea_tmp.SetField(i,kasperle)
                                    else:   # numerisches Feld
                                        fea_tmp.SetField(i,fea.GetField(i))
                                i = i+1


                            # ein neues (konvertiertes) Feature im Memory Layer erzeugen
                            fea_tmp.SetFID(-1)
                            ly.CreateFeature(fea_tmp)


                     #########################################
                    # Alle Formen von Punktgeometrien
                    #########################################

                    #Point oder Multipoint
                    elif lyrIn.GetGeomType() == ogr.wkbPoint or lyrIn.GetGeomType() == ogr.wkbMultiPoint:

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPoint)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiPoint,'point', lyrIn,codierung,ly):
                            ly = None

                    #Point oder Multipoint mit M
                    elif lyrIn.GetGeomType() == ogr.wkbPointM or lyrIn.GetGeomType() == ogr.wkbMultiPointM:

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPointM)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiPointM,'point', lyrIn,codierung,ly):
                            ly = None

                    #Point oder Multipoint 3D mit M
                    elif lyrIn.GetGeomType() == ogr.wkbPointZM or lyrIn.GetGeomType() == ogr.wkbMultiPointZM:

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPointZM)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiPointZM,'point', lyrIn,codierung,ly):
                            ly = None

                    #Point oder Multipoint 3D
                    elif lyrIn.GetGeomType() == ogr.wkbPoint25D or lyrIn.GetGeomType() == ogr.wkbMultiPoint25D:

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPoint25D)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiPoint25D,'point', lyrIn,codierung,ly):
                            ly = None




                    #########################################
                    # Alle Formen von Liniengeometrien
                    #########################################

                    # Line oder Multiline
                    elif lyrIn.GetGeomType() == ogr.wkbLineString or lyrIn.GetGeomType() == ogr.wkbMultiLineString:

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiLineString)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiLineString,'line', lyrIn,codierung,ly):
                            ly = None

                    # Line oder Multiline mit M
                    elif lyrIn.GetGeomType() == ogr.wkbLineStringM or lyrIn.GetGeomType() == ogr.wkbMultiLineStringM:
                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiLineStringM)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not self.__create_and_populate_layer(name, srs, ogr.wkbMultiLineStringM,'line', lyrIn,codierung,ly):
                            ly = None

                    # Line oder Multiline 3D mit M
                    elif lyrIn.GetGeomType() == ogr.wkbLineStringZM or lyrIn.GetGeomType() == ogr.wkbMultiLineStringZM:
                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiLineStringZM)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiLineStringZM,'line', lyrIn,codierung,ly):
                            ly = None

                    # Linien mit 3D
                    elif lyrIn.GetGeomType() == ogr.wkbMultiLineString25D  or lyrIn.GetGeomType() == ogr.wkbLineString25D :


                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiLineString25D)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiLineString25D,'line', lyrIn,codierung,ly):
                            ly = None


                    #########################################
                    # Alle Formen von Polygongeometrien
                    #########################################

                    #Polygon oder Multipolygon
                    elif lyrIn.GetGeomType() == ogr. wkbPolygon or lyrIn.GetGeomType() == ogr.wkbMultiPolygon:

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPolygon)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiPolygon,'polygon', lyrIn,codierung,ly):
                            ly = None

                    #Polygon oder Multipolygon mit M
                    elif lyrIn.GetGeomType() == ogr. wkbPolygonM or lyrIn.GetGeomType() == ogr.wkbMultiPolygonM:

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPolygonM)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiPolygonM,'polygon', lyrIn,codierung,ly):
                            ly = None

                    #Polygon oder Multipolygon 3D mit M
                    elif lyrIn.GetGeomType() == ogr. wkbPolygonZM or lyrIn.GetGeomType() == ogr.wkbMultiPolygonZM:

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPolygonZM)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiPolygonZM,'polygon', lyrIn,codierung,ly):
                            ly = None

                    # Polygone mit 3D
                    elif lyrIn.GetGeomType() == ogr.wkbMultiPolygon25D  or lyrIn.GetGeomType() == ogr.wkbPolygon25D :

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPolygon25D)
                        # ACHTUNG: return hat mit dem im sub erzeugten Layer Objekt nicht funktioniert (crash)
                        # dh wird das Lyerobjekt ly bereits vorher erzeugt und im Sub (Pointer!) verändert.
                        # zurückgegeben wird nur das fehlerstatement
                        if not  self.__create_and_populate_layer(name, srs, ogr.wkbMultiPolygon25D,'polygon', lyrIn,codierung,ly):
                            ly = None

                    # alles andere
                    else:
                        dsOut.CopyLayer(lyrIn,name,['SPATIAL_INDEX=no','PRECISION=NO','GEOM_TYPE=geometry', 'GEOMETRY_NAME=the_geom', 'LAUNDER=yes'])


                    # Fertig: der Memorylayer mit dem gesäuberten Inhalt des Shapes kann in die Datenbank kopiert werden
                    if not ly == None:
                        dsOut.CopyLayer(ly,name,['SPATIAL_INDEX=no','PRECISION=NO','GEOM_TYPE=geometry', 'GEOMETRY_NAME=the_geom', 'LAUNDER=yes'])
                    else:
                        return [False,'Geometrietyp nicht unterstuetzt oder Layer Nachbesserung fehlgeschlagen']

            return [True]



        # Wir geben die Exception auch mit zurück - damit die fehlermeldung informativer ist!
        except Exception as e:
            print str(e)
            return [False,e]



    #################################
    # Der Postgis-Featureverwurstler...
    #################################
    def __create_and_populate_layer(self,name, srs, ogr_type, geom_type, lyrIn,codierung,ly_tmp):

        try:
            i = 0
            feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
            while i < feldanzahl:
                Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                Fdefn.SetName(string.lower(Fdefn.GetName()))
                ly_tmp.CreateField(Fdefn)
                i = i+1

            # Der gesmate Layer muss neu geschrieben werden
            # damit Probleme beim Laden in die Datenbank
            # möglichst ausgeschlossen werden
            for fea in lyrIn:

                # Umwandeln der Geometrie in ein MultiLinestring
                gemi = fea.GetGeometryRef()

                if geom_type == 'point':
                    gemi = ogr.ForceToMultiPoint(gemi)
                if geom_type == 'line':
                    gemi = ogr.ForceToMultiLineString(gemi)
                if geom_type == 'polygon':
                    gemi = ogr.ForceToMultiPolygon(gemi)

                fea_tmp = ogr.Feature(fea.GetDefnRef())

                # gemoetrie einfügen (die geänderte)
                fea_tmp.SetGeometry(gemi)

                # sachinformation einfügen

                i = 0
                while i < feldanzahl:
                    if not fea.GetField(i) == None:

                        if fea.GetFieldDefnRef(i).GetType() == 4:   # Textfeld
                                if codierung == 'nein' or '':
                                    fea_tmp.SetField(i,fea.GetFieldAsString(i))
                                else:   # bei Bedarf umcodieren
                                    kasperle = fea.GetFieldAsString(i).decode(codierung,'replace').encode('utf8','replace')
                                    fea_tmp.SetField(i,kasperle)
                        else:   # numerisches Feld
                            fea_tmp.SetField(i,fea.GetField(i))
                    i = i+1


                # ein neues (konvertiertes) Feature im Memory Layer erzeugen
                fea_tmp.SetFID(-1)
                ly_tmp.CreateFeature(fea_tmp)

            #Layer erfolgreich erstellt
            return True


        # Layer nicht erfolgreich erstellt!
        except:
            return False



