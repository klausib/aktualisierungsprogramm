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
                        return "Feldnamen fehlen: Eingansname: ".decode('utf8') + ' ' + defIn.GetNameRef() + ' Ausgangsname: ' + defOut.GetNameRef()
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

        except:
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

    def kopieren(self,dsOut,lyrIn,name,zieltyp):

        try:
            #srs = osr.SpatialReference()
            #srs.ImportFromEPSG( 31254 )


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


                if lyrIn.GetGeomType() == 100:   #Also keine Geometrie vorhanden

                    if driverName == "PostgreSQL":
                        ly = dsOut.CopyLayer(lyrIn,name, ['SPATIAL_INDEX=no','PRECISION=no','GEOMETRY_NAME=the_geom', 'LAUNDER=no'])
                    elif driverName == "SQLite":
                        ly = dsOut.CopyLayer(lyrIn,name, ['GEOMETRY_NAME=the_geom', 'LAUNDER=no'])

                elif driverName == "SQLite":

##                    # Create a memory OGR datasource to put results in. Von frank W. Die Doku ist einfach schwach
##                    # Deshalb wirds hier zu Dokumentationszwecken dringelassen:
##                    # Der Memory Layer ist deutlich performanter bei CreateFeature als wenn es direkt auf eine
##                    # Spatial Lite DB angewandt wird
##                    mem_drv = ogr.GetDriverByName( 'Memory' )
##                    mem_ds = mem_drv.CreateDataSource( 'out' )
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

                    dsOut.CopyLayer(memme,name,['SPATIAL_INDEX=no','PRECISION=no', 'GEOM_TYPE=geometry', 'GEOMETRY_NAME=the_geom', 'LAUNDER=no'])


                # Einen leeren Layer in der Postgis erzeugen
                # ACHTUNG: Beim Shape wird zwischen Linestring und Multilinestring etc.
                # nicht unterschieden, es können also in einem Shape beide Arten vorkommen!
                # Es muss deshalb per Default immer die Multi- Version erzeugt werden!
                elif driverName == "PostgreSQL":


##                    # Create a memory OGR datasource to put results in. Von frank W. Die Doku ist einfach schwach
##                    # Der Memory Layer ist deutlich performanter bei CreateFeature als wenn es direkt auf eine
##                    # reale Datenquelle angewandt wird
##                    mem_drv = ogr.GetDriverByName( 'Memory' )
##                    mem_ds = mem_drv.CreateDataSource( 'out' )


                    #Point oder Multipoint
                    if lyrIn.GetGeomType() == 1 or lyrIn.GetGeomType() == 4:
##                        # Einen neuen Layer in der datenbank erzeugen
##                        ly = dsOut.CreateLayer(name,srs,ogr.wkbMultiPoint,['SPATIAL_INDEX=no','PRECISION=no','GEOMETRY_NAME=the_geom', 'LAUNDER=no'])
##
##                        i = 0
##                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
##                        while i < feldanzahl:
##                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
##                            ly.CreateField(Fdefn)
##                            i = i+1

##                        # Create a memory OGR datasource to put results in. Von frank W. Die Doku ist einfach schwach
##                        # Der Memory Layer ist deutlich performanter bei CreateFeature als wenn es direkt auf eine
##                        # reale Datenquelle angewandt wird
##                        mem_drv = ogr.GetDriverByName( 'Memory' )
##                        mem_ds = mem_drv.CreateDataSource( 'out' )

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPoint)

                        i = 0
                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
                        while i < feldanzahl:
                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                            ly.CreateField(Fdefn)
                            i = i+1

                        # Der gesmate Layer muss neu geschrieben werden
                        # damit Probleme beim Laden in die Datenbank
                        # möglichst ausgeschlossen werden
                        for fea in lyrIn:

                            # Umwandeln der Geometrie in Multipoint
                            gemi = fea.GetGeometryRef()
                            gemi = ogr.ForceToMultiPoint(gemi)

                            fea_tmp = ogr.Feature(fea.GetDefnRef())

                            # gemoetrie einfügen (die geänderte)
                            fea_tmp.SetGeometry(gemi)

                            # sachinformation einfügen
                            i = 0
                            while i < feldanzahl:
                                fea_tmp.SetField(i,fea.GetField(i))
                                i = i+1

                            # ein neues (konvertiertes) Feature im Memory Layer erzeugen
                            fea_tmp.SetFID(-1)
                            ly.CreateFeature(fea_tmp)



                    #Line oder Multiline
                    elif lyrIn.GetGeomType() == 2 or lyrIn.GetGeomType() == 5:

##                        # Einen neuen Layer in der datenbank erzeugen
##                        ly = dsOut.CreateLayer(name,srs,ogr.wkbMultiLineString,['SPATIAL_INDEX=no','PRECISION=no','GEOMETRY_NAME=the_geom', 'LAUNDER=no'])
##
##                        i = 0
##                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
##                        while i < feldanzahl:
##                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
##                            ly.CreateField(Fdefn)
##                            i = i+1


##                        # Create a memory OGR datasource to put results in. Von frank W. Die Doku ist einfach schwach
##                        # Der Memory Layer ist deutlich performanter bei CreateFeature als wenn es direkt auf eine
##                        # reale Datenquelle angewandt wird
##                        mem_drv = ogr.GetDriverByName( 'Memory' )
##                        mem_ds = mem_drv.CreateDataSource( 'out' )

                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiLineString)
                        i = 0
                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
                        while i < feldanzahl:
                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                            ly.CreateField(Fdefn)
                            i = i+1

                        # Der gesmate Layer muss neu geschrieben werden
                        # damit Probleme beim Laden in die Datenbank
                        # möglichst ausgeschlossen werden
                        for fea in lyrIn:

                            # Umwandeln der Geometrie in Multilinestring
                            gemi = fea.GetGeometryRef()
                            gemi = ogr.ForceToMultiLineString(gemi)

                            fea_tmp = ogr.Feature(fea.GetDefnRef())

                            # gemoetrie einfügen (die geänderte)
                            fea_tmp.SetGeometry(gemi)

                            # sachinformation einfügen
                            i = 0
                            while i < feldanzahl:
                                fea_tmp.SetField(i,fea.GetField(i))
                                i = i+1

                            # ein neues (konvertiertes) Feature im Memory Layer erzeugen
                            fea_tmp.SetFID(-1)
                            ly.CreateFeature(fea_tmp)


                    #Polygon oder Multipolygon
                    elif lyrIn.GetGeomType() == 3 or lyrIn.GetGeomType() == 6:


##                        # Einen neuen Layer in der datenbank erzeugen
##                        ly = dsOut.CreateLayer(name,srs,ogr.wkbMultiPolygon,['SPATIAL_INDEX=no','PRECISION=yes','GEOMETRY_NAME=the_geom', 'LAUNDER=yes'])
##
##                        i = 0
##                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
##                        while i < feldanzahl:
##                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
##                            ly.CreateField(Fdefn)
##                            i = i+1

##                        # Create a memory OGR datasource to put results in. Von frank W. Die Doku ist einfach schwach
##                        # Der Memory Layer ist deutlich performanter bei CreateFeature als wenn es direkt auf eine
##                        # reale Datenquelle angewandt wird
##                        mem_drv = ogr.GetDriverByName( 'Memory' )
##                        mem_ds = mem_drv.CreateDataSource( 'out' )
                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPolygon)

                        i = 0
                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
                        while i < feldanzahl:
                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                            ly.CreateField(Fdefn)
                            i = i+1

                        # Der gesmate Layer muss neu geschrieben werden
                        # damit Probleme beim Laden in die Datenbank
                        # möglichst ausgeschlossen werden
                        for fea in lyrIn:

                            # Umwandeln der Geometrie in ein Multipolygon
                            gemi = fea.GetGeometryRef()
                            gemi = ogr.ForceToMultiPolygon(gemi)

                            fea_tmp = ogr.Feature(fea.GetDefnRef())

                            # gemoetrie einfügen (die geänderte)
                            fea_tmp.SetGeometry(gemi)

                            # Sachinformation einfügen
                            i = 0
                            while i < feldanzahl:
                                fea_tmp.SetField(i,fea.GetField(i))
                                i = i+1

                            # ein neues (konvertiertes) Feature im Memory Layer erzeugen
                            fea_tmp.SetFID(-1)
                            error = ly.CreateFeature(fea_tmp)

                    # Punkte mit 3D
                    elif lyrIn.GetGeomType() == ogr.wkbMultiPoint25D   or lyrIn.GetGeomType() == ogr.wkbPoint25D  :


                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPoint25D)

                        i = 0
                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
                        while i < feldanzahl:
                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                            ly.CreateField(Fdefn)
                            i = i+1

                        # Der gesmate Layer muss neu geschrieben werden
                        # damit Probleme beim Laden in die Datenbank
                        # möglichst ausgeschlossen werden
                        for fea in lyrIn:

                            # Umwandeln der Geometrie in ein MultiLinestring
                            gemi = fea.GetGeometryRef()
                            gemi = ogr.ForceToMultiPoint(gemi)

                            fea_tmp = ogr.Feature(fea.GetDefnRef())

                            # gemoetrie einfügen (die geänderte)
                            fea_tmp.SetGeometry(gemi)

                            # Sachinformation einfügen
                            i = 0
                            while i < feldanzahl:
                                fea_tmp.SetField(i,fea.GetField(i))
                                i = i+1

                            # ein neues (konvertiertes) Feature im Memory Layer erzeugen
                            fea_tmp.SetFID(-1)
                            ly.CreateFeature(fea_tmp)

                    # Linien mit 3D
                    elif lyrIn.GetGeomType() == ogr.wkbMultiLineString25D  or lyrIn.GetGeomType() == ogr.wkbLineString25D :


                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiLineString25D)

                        i = 0
                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
                        while i < feldanzahl:
                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                            ly.CreateField(Fdefn)
                            i = i+1

                        # Der gesmate Layer muss neu geschrieben werden
                        # damit Probleme beim Laden in die Datenbank
                        # möglichst ausgeschlossen werden
                        for fea in lyrIn:

                            # Umwandeln der Geometrie in ein MultiLinestring
                            gemi = fea.GetGeometryRef()
                            gemi = ogr.ForceToMultiLineString(gemi)

                            fea_tmp = ogr.Feature(fea.GetDefnRef())

                            # gemoetrie einfügen (die geänderte)
                            fea_tmp.SetGeometry(gemi)

                            # Sachinformation einfügen
                            i = 0
                            while i < feldanzahl:
                                fea_tmp.SetField(i,fea.GetField(i))
                                i = i+1

                            # ein neues (konvertiertes) Feature im Memory Layer erzeugen
                            fea_tmp.SetFID(-1)
                            ly.CreateFeature(fea_tmp)

                    # Polygone mit 3D
                    elif lyrIn.GetGeomType() == ogr.wkbMultiPolygon25D  or lyrIn.GetGeomType() == ogr.wkbPolygon25D :


                        ly = mem_ds.CreateLayer(name,srs,ogr.wkbMultiPolygon25D)

                        i = 0
                        feldanzahl = lyrIn.GetLayerDefn().GetFieldCount()
                        while i < feldanzahl:
                            Fdefn = lyrIn.GetLayerDefn().GetFieldDefn(i)
                            ly.CreateField(Fdefn)
                            i = i+1

                        # Der gesmate Layer muss neu geschrieben werden
                        # damit Probleme beim Laden in die Datenbank
                        # möglichst ausgeschlossen werden
                        for fea in lyrIn:

                            # Umwandeln der Geometrie in ein MultiLinestring
                            gemi = fea.GetGeometryRef()
                            gemi = ogr.ForceToMultiPolygon(gemi)

                            fea_tmp = ogr.Feature(fea.GetDefnRef())

                            # gemoetrie einfügen (die geänderte)
                            fea_tmp.SetGeometry(gemi)

                            # Sachinformation einfügen
                            i = 0
                            while i < feldanzahl:
                                fea_tmp.SetField(i,fea.GetField(i))
                                i = i+1

                            # ein neues (konvertiertes) Feature im Memory Layer erzeugen
                            fea_tmp.SetFID(-1)
                            ly.CreateFeature(fea_tmp)

                    # Fertig: der Memorylayer mit dem gesäuberten Inhalt des Shapes kann in die Datenbank kopiert werden
                    dsOut.CopyLayer(ly,name,['SPATIAL_INDEX=no','PRECISION=no','GEOM_TYPE=geometry', 'GEOMETRY_NAME=the_geom', 'LAUNDER=no'])


            return [True]

        # Wir geben die Exception auch mit zurück - damit die fehlermeldung informativer ist!
        except Exception as e:
            #print str(e)
            return [False,e]


