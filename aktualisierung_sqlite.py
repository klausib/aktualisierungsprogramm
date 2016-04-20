# -*- coding: utf-8 -*-
#!/usr/bin/python


##import sys
##sys.path.append('C:/Program Files/QGIS Wien/apps/Python27/Lib/site-packages')
import sqlite3, os, sys
import logging,string,shutil
import hilfsmodul
from hauptmodul import *
from indexabgleich import *
from osgeo import ogr, osr,gdal


def logroutine(log_error, text,flag):

    log_error.error(unicode(text),exc_info=flag)

###################################################################
#WICHTIG: Grundlegendes Verhalten der OGR/GDAl Lib wird so
#festgelegt und gilt für alle Teile des Programmes während der
#Laufzeit
###################################################################

gdal.UseExceptions()    # WICHTIG: Um GDAL/OGR Fehler als Laufzeitfehler abfangen
                        # und im Code behandeln zu können
gdal.SetConfigOption( "SQLITE_LIST_ALL_TABLES", "YES" ) #Sonst können keine geometrielosen Tabellen gefunden werden!!!
gdal.SetConfigOption( "PG_LIST_ALL_TABLES", "YES" ) #Sonst können keine geometrielosen Tabellen gefunden werden!!!



def sqliteaktual(db,cursor_sqlite,log_error,log_warning,log_abgelehnt,log_index_missing,log_ok,log_available,log_attrabgesch):

    try:
        #####################################################
        #   Aktualisierung Datenbank SQLITE                 #
        #####################################################

        #Die Auswahlabfrage ausführen
        cursor_sqlite.execute("select * from kopierliste_sqlite where aktualisierung = 'ja'")

        loeschliste = []
        errorliste = []

        #Alle passenden records auf einmal einlesen
        rows = cursor_sqlite.fetchall()
        if len(rows) > 0:
            row = rows[0]
        else:
            row = []


        #Marker setzen
        logroutine(log_abgelehnt,'---------Log SQLITE----------\r' ,False)
        logroutine(log_available,'---------Log SQLITE----------\r' ,False)
        logroutine(log_ok,'---------Log SQLITE----------\r' ,False)
        logroutine(log_index_missing,'---------Log SQLITE----------\r' ,False)
        logroutine(log_error,'---------Log SQLITE----------\r' ,False)
        logroutine(log_warning,'---------Log SQLITE----------\r' ,False)

        #Hauptschleife, alle records abarbeiten
        for row in rows:
            #print row["zieltyp"] + " " +  row["quellpfad"]  + " " +  row["zielpfad"]


            #dieser code ist zwar auch im Codesegment fürs Filesystem vorhanden,
            #aber ich finde es übersichtlicher ihn hier einfach nochmal zu verwenden anstatt
            #in ein Modul auszulagern

            inputpfad = str(os.path.dirname(row["quellpfad"]))
            outputpfad = str(os.path.dirname(row["zielpfad"]))
            inputname = str(os.path.basename(row["quellpfad"]))
            outputname = str(os.path.basename(row["quellpfad"]))
            output_sqlite = str(os.path.basename(row["zielpfad"]))

            if not os.path.exists(inputpfad + '/' + inputname):
                logroutine(log_available,"Nicht bereitgestellt - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
                continue
            if not os.path.exists(outputpfad + '/' + output_sqlite):
                drv = ogr.GetDriverByName('SQLite')
                sqliteOut = drv.CreateDataSource(outputpfad + '/' + output_sqlite,['SPATIALITE=YES'])
                logroutine(log_available,"Ausgangs SQLITE datenbank neu angelegt: - " + str(row["primindex"]) + " " + outputpfad + '/' + output_sqlite + '\r'  ,False)    #Warnung setzen aber weitermachen
                #continue


            #unsere drei zugelassen suffixe für Geodaten oder Tabellen
            if  (inputname.find('.csv') > -1):
                outputname_ohnesuffix = outputname.replace('.csv','')
                inputname_ohnesuffix = inputname.replace('.csv','')
            elif  (inputname.find('.dbf') > -1):
                outputname_ohnesuffix = outputname.replace('.dbf','')
                inputname_ohnesuffix = inputname.replace('.dbf','')
            elif  (inputname.find('.shp') > -1):
                outputname_ohnesuffix = outputname.replace('.shp','')
                inputname_ohnesuffix = inputname.replace('.shp','')
            elif  (inputname.find('.xlsx') > -1):
                outputname_ohnesuffix = outputname.replace('.xlsx','')
                inputname_ohnesuffix = inputname.replace('.xlsx','')

            else:
                if str(row["quelltyp"]) == 'datei':
                    outputname_ohnesuffix = ""
                    inputname_ohnesuffix = ""
                else:
                    logroutine(log_abgelehnt,"Dateityp nicht unterstuetzt - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + inputname)
                    continue    #Stop hier: nächster Datensatz in der Liste



##            ####################################################################################################
##            #Umkodieren falls notwendig (CP850 nach UTF8 damit Upload in DB's klappt)
##            #Dabei wird lediglich von CP850 nach UTF-8 umcodiert, und zwar das original Shape oder DBF.
##            #ACHTUNG: Beim kopieren versucht die OGR Bibliothek auch ein umcodieren und tut
##            #dies auch wenn sie kann! Allerdings, na ja ist das eine gute Idee
##            ####################################################################################################
##
##            if row['nach_utf8'] != 'nein':
##                if inputname.find('.shp') > -1:
##                    tmp_dbasename = inputname_ohnesuffix + '.dbf'
##                    if not hilfsmodul.umcodieren(inputpfad,tmp_dbasename,row['nach_utf8']):
##                        logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
##                elif inputname.find('.dbf') > -1:
##                    #hilfsmodul.umcodieren(inputpfad,inputname)
##                    if not hilfsmodul.umcodieren(inputpfad,tmp_dbasename,row['nach_utf8']):
##                        logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
##                elif inputname.find('.csv') > -1:
##                    #hilfsmodul.umcodieren(inputpfad,inputname)
##                    if not hilfsmodul.umcodieren(inputpfad,tmp_dbasename,row['nach_utf8']):
##                        logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname  + '\r' ,False)    #Warnung setzen aber weitermachen

            ####################################################################################################
            #Umkodieren falls notwendig (nach UTF8 damit Upload in DB's klappt)
            ####################################################################################################

            if row['nach_utf8'] != 'nein':  # es soll umcodiert werden -> mal schauen

                #ist es bereits im Laufe dieser Aktualisierung umcodiert worden?
                #das erkennen wir einfach am Suffix, Pech wenn jemand dieses schon verwendet...

                #if not inputname.find('_UTF8') > -1: # -> wir müssen umcoderien
                if  os.path.exists(inputpfad + '/' + inputname_ohnesuffix + '_UTF8' + os.path.splitext(inputname)[1]):  # UTF8 bereits vorhanden
                    inputname = inputname_ohnesuffix + '_UTF8' + os.path.splitext(inputname)[1]
                    loeschliste.append(inputpfad + '/' + inputname)
                    inputname_ohnesuffix = inputname_ohnesuffix + '_UTF8'       # das shape hat nun einen neuen Namen!
                else:    # -> wir müssen umcodieren

                    #Ein Vergleichsobjekt wird instanziert
                    #nur fürs Kopieren
                    dShape = Vergleich()

                    #das gesamte Inputshape umbenennen in neues Shape
                    if not dShape.kopieren_filebasis(inputpfad,inputname_ohnesuffix,inputpfad, inputname_ohnesuffix + '_UTF8',os.path.splitext(inputname)[1]):
                        logroutine(log_error,"Schwerer Fehler beim Umbenennen des original Shapes fuer die Umcodierung: - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                        errorliste.append(inputpfad + '/' + inputname)
                        continue    #Stop hier: nächster Datensatz in der Liste
                    else:   #umbenennen erfolgreich - löschen nicht vergessen -> löschliste
                        inputname = inputname_ohnesuffix + '_UTF8' + os.path.splitext(inputname)[1]
                        loeschliste.append(inputpfad + '/' + inputname)
                        inputname_ohnesuffix = inputname_ohnesuffix + '_UTF8'       # das shape hat nun einen neuen Namen!

                    if inputname.find('.shp') > -1:
                        tmp_dbasename = inputname_ohnesuffix + '.dbf'
                        if not hilfsmodul.umcodieren(inputpfad,tmp_dbasename,row['nach_utf8'],log_attrabgesch):
                            logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
                    elif inputname.find('.dbf') > -1:
                        #hilfsmodul.umcodieren(inputpfad,inputname)
                        if not hilfsmodul.umcodieren(inputpfad,inputname,row['nach_utf8'],log_attrabgesch):
                            logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
                    elif inputname.find('.csv') > -1:
                        #hilfsmodul.umcodieren(inputpfad,inputname)
                        if not hilfsmodul.umcodieren(inputpfad,inputname,row['nach_utf8'],log_attrabgesch):
                            logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname  + '\r' ,False)    #Warnung setzen aber weitermachen



            #ACHTUNG: Wenn eine Shapedatasource gewählt wird gibts zwei
            #Möglichkeiten: Das Datasource Objekt wird mit dem Kompletten Pfad
            #bis zum Shape gefüttert. ODER nur mit dem Verzeichnispfad. Dann können
            #alle Shapes in diesem Verzeichnis als Layer geladen werden!!
            #WICHTIG: UNBEDINGT kein / am Schluss, sonst gehts nicht!

                #öffnen des Eingangsdatensatzes:
            flag = ''
            if row["quelltyp"] == 'shape':  #öffnen eines Shapes
                dsIn = ogr.Open( inputpfad,True)    #Der Shapeworkspace: Flag True -> da brauch ich bereits Vollzugriff auf die Dateien!
                if dsIn == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsworkspace - " + str(row["primindex"]) + " " + inputpfad + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste
                lyrIn = dsIn.GetLayerByName(inputname_ohnesuffix)  #Als Layer das eigentliche Shape (ohne suffix)
                flag = 'shape'
            elif row["quelltyp"] == 'tabelle':  #Öffnen einer blanken Tabelle
                dsIn = ogr.Open( inputpfad + '/' + inputname,True)
                if dsIn == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsworkspace - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste
                lyrIn = dsIn.GetLayer()
                flag = 'tabelle'

            if lyrIn == None:   #hat auch nicht funktioniert!
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsdatensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

            #Nun das Ziel des Kopierprozesses
            #die SQLITE Datenbank
            sqliteOut = ogr.Open(outputpfad + '/' + output_sqlite, True)   #SQLIT Datasource Objekt der
            if sqliteOut == None:   #konnte nicht geöffnet werden
                logroutine(log_error,"Fehler beim Oeffnen der Ausgangs SQLITE Datenbank - " + str(row["primindex"]) + " " + outputpfad + '/' + output_sqlite + '\r' ,False)
                #errorliste.append(inputpfad + '/' + inputname)
                errorliste.append(inputpfad + '/' + outputname)
                continue    #Stop hier: nächster Datensatz in der Liste


            #prüfen ob der Ausgangsdatensatz vorhanden ist
            lyrSqliteOut = sqliteOut.GetLayerByName(outputname_ohnesuffix)
            if not lyrSqliteOut == None and row["ds_neu"] == 'ja':  #Wir haben den datensatz als neu definiert, d.h. ein
                sqliteOut.DeleteLayer(outputname_ohnesuffix)         #eventuell bestehender soll überschrieben werden


            if lyrSqliteOut == None and row["ds_neu"] == 'nein':
                #errorliste.append(inputpfad + '/' + inputname)
                errorliste.append(inputpfad + '/' + outputname)
                logroutine(log_abgelehnt,"Aktualisierung fehlgeschlagen - Datensatz im Ziel nicht vorhanden! - " + str(row["primindex"]) + " " + outputpfad + '/' + outputname + '\r' ,False)
                continue    #Stop hier: nächster Datensatz in der Liste



            ###### NEU ##############
            #Neuen Datensatz kopieren
            #########################
            if row["ds_neu"] == 'ja':



                #Ein Vergleichsobjekt wird instanziert
                #Es ist für kopieren, vergleich etc...
                dShape = Vergleich(lyrIn,dsIn)

                bezugssystem = (row["bezugssystem"])    #Das Soll Bezugssystem (statisch in der Kopiertabelle eingetragen)


                if dShape.verglRef(bezugssystem) == 2 and flag == 'shape':      #Bezugssystem mußte NEU zugewiesen werden
                    dsIn = ogr.Open( inputpfad,True)
                    lyrIn = dsIn.GetLayerByName(inputname_ohnesuffix)      #dann nach Zuweisen Bezugssystem neu instanzieren
                    dShape = Vergleich(lyrIn,dsIn)
                elif dShape.verglRef(bezugssystem) == 3 and flag == 'shape':    #Ein Fehler ist aufgetreten. Da stimmt was nicht, also abbrechen mit diesem Datensatz und den nächsten darannehmen
                    logroutine(log_error,"Fehler beim Zuweisen des Bezugssystems - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #zum nächsten Datensatz


                # ACHTUNG: Die Gross/Kleinschreibung des Shapes orientiert sich an dem String outputname in
                # der Steuertabelle: So wies dort drin ist wird der Shapename geschrieben
                # ACHTUNG: Die Gross/Kleinschreibung des Shapes orientiert sich an dem String outputname in
                # der Steuertabelle: So wies dort drin ist wird der Shapename geschrieben
                rueckgabe = dShape.kopieren(sqliteOut,lyrIn,outputname_ohnesuffix,row["zieltyp"])
                #if not dShape.kopieren(sqliteOut,lyrIn,outputname_ohnesuffix,row["zieltyp"]):    #outputname ist ja die sqlite Datei
                if not rueckgabe[0]:    #outputname ist ja die sqlite Datei
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + ' ' + str(rueckgabe[1]) + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop: Ab zum nächsten Datensatz


                #Püfen ob auch wirklich alle Feature übernommen wurden
                if lyrIn.GetFeatureCount() != sqliteOut.GetLayerByName(outputname_ohnesuffix).GetFeatureCount():
                    print str(lyrIn.GetFeatureCount()) + ' ' + str(sqliteOut.GetLayerByName(outputname_ohnesuffix).GetFeatureCount())
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + ' - Features fehlen' + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)

                    # Temp Tabelle löschen
                    query =    "Drop Table " + outputname_ohnesuffix
                    sqliteOut.ExecuteSQL(query)

                    continue    #Stop: Ab zum nächsten Datensatz



                #SPATIALITE Index aktualisieren:
                #ACHTUNG: Vorlage für den Index ist der Index beim Shapefile oder des DBASE File.
                #Der geometrische Index wird immer angelegt
                abgleich = indexabgleich(lyrIn,dsIn,sqliteOut.GetLayerByName(outputname_ohnesuffix),sqliteOut,True)
                ret_ind = abgleich.indexAbgl()
                if ret_ind == 4:
                    logroutine(log_index_missing,"Fehler beim Indizieren des des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)

                #nochmal zur Sicherheit die Endkontrolle, ob das Shape auch wirklich
                #kopiert wurde
                lyrOut = sqliteOut.GetLayerByName(outputname_ohnesuffix)  #Als Layer das eigentliche Shape (ohne suffix)
                #if lyrOut == None:
                if lyrOut == None or (lyrIn.GetFeatureCount() != lyrOut.GetFeatureCount()):
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - Endkontrolle Datensatz - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste
                else:
                    logroutine(log_ok, "Kopieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    #Alles OK, das Original kann in die Liste
                    #der zu löschenden Shapes aufgenommen werden
                    #print inputpfad + '/' + inputname
                    loeschliste.append(inputpfad + '/' + outputname)




                #Alles OK, das Original kann gelöscht werden

                #Die Objekte mit Referenz auf
                #die Dateien des Shapes müssen zuerst gelöscht werden
                #(sonst sind sie gelockt)
                lyrOut = None
                lyrSqliteOut = None
                dsOut = None
                lyrIn = None
                dsIn = None
                dShape = None
                abgleich = None

                #ACHTUNG: Im Produktivstatus unbedingt auskommentieren!!

                #Das Flag ds_neu von 'ja' nach 'nein' stellen
                primindex = row["primindex"]
                cursor_sqlite.execute("update kopierliste_sqlite set ds_neu = 'nein' where primindex = " + str(primindex) + "")
                db.commit()



            ###### AKTUALISIEREN ##############
            # Datensatz aktualisieren
            ###################################
            elif row["ds_neu"] == 'nein':

                #Ein Vergleichsobjekt wird instanziert
                #Es ist für kopieren, vergleich etc...
                dShape = Vergleich(lyrIn,dsIn,lyrSqliteOut,sqliteOut)


                #Gültigkeit der Attributtabelle
                #prüfen
                Attributliste = dShape.verglAttr(sqliteOut.GetDriver().GetName())
                if Attributliste.find("Fehler") >= 0:  #Das Stichwort Fehler wird zurückgegeben und wir brechen ab
                        logroutine(log_abgelehnt,"Fehler beim Vergleichen der Attribute - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + " " + Attributliste + '\r' ,False)
                        #errorliste.append(inputpfad + '/' + inputname)
                        errorliste.append(inputpfad + '/' + outputname)
                        continue    #zum nächsten Datensatz


                #Gültigkeit des Geometrietyps prüfen
                geom_Vergleich = dShape.verglGeom()
                if geom_Vergleich.find("Fehler") >= 0:  #Das Stichwort Fehler wird zurückgegeben und wir brechen ab
                    logroutine(log_abgelehnt,"Fehler beim Vergleichen des Geometrietyps - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #zum nächsten Datensatz


                #Das Bezugssystem muss natürlich auch passen!
                bezugssystem = (row["bezugssystem"])    #Das Soll Bezugssystem (statisch in der Kopiertabelle eingetragen)

                ref_ret = dShape.verglRef(bezugssystem)

                if ref_ret == 2 and flag == 'shape':      #Bezugssystem mußte NEU zugewiesen werden
                    dsIn = ogr.Open( inputpfad,True)
                    lyrIn = dsIn.GetLayerByName(inputname_ohnesuffix)      #dann nach Zuweisen Bezugssystem neu instanzieren
                    dShape = Vergleich(lyrIn,dsIn)
                elif ref_ret == 3 and flag == 'shape':    #Ein Fehler ist aufgetreten. Da stimmt was nicht, also abbrechen mit diesem Datensatz und den nächsten darannehmen
                    logroutine(log_error,"Fehler beim Zuweisen des Bezugssystems - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #zum nächsten Datensatz


                # ACHTUNG: Die Gross/Kleinschreibung des Shapes orientiert sich an dem String outputname in
                # der Steuertabelle: So wies dort drin ist wird der Shapename geschrieben
                rueckgabe = dShape.kopieren(sqliteOut,lyrIn,outputname_ohnesuffix + '_temp_aktual',row["zieltyp"])
                #if not dShape.kopieren(sqliteOut,lyrIn,outputname_ohnesuffix + '_temp_aktual',row["zieltyp"])[0]:   #outputname ist ja die sqlite Datei
                if not rueckgabe[0]:   #outputname ist ja die sqlite Datei
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + ' ' + str(rueckgabe[1]) + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop: Ab zum nächsten Datensatz


                #Püfen ob auch wirklich alle Feature übernommen wurden
                if lyrIn.GetFeatureCount() != sqliteOut.GetLayerByName(outputname_ohnesuffix + "_temp_aktual").GetFeatureCount():
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + ' - Features fehlen' + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)

                    # Temp Tabelle löschen
                    query =    "Drop Table " + outputname_ohnesuffix + "_temp_aktual"
                    sqliteOut.ExecuteSQL(query)

                    continue    #Stop: Ab zum nächsten Datensatz


                try:

                    #die Geometriespalte finden!
                    geometriespalte = ''
                    geometriespalte = lyrSqliteOut.GetGeometryColumn()  #gibt die geometriespalte zurück oder ''
                    query =    "DELETE from " + outputname_ohnesuffix
                    sqliteOut.ExecuteSQL(query)

                    # Autoincrement zurücksetzen
                    query =    "delete from sqlite_sequence where name=\'" + outputname_ohnesuffix + "\'"
                    sqliteOut.ExecuteSQL(query)

                    if not geometriespalte == '':   #wenn es keine gibt ist die variable ''
                        query =    "insert into " + outputname_ohnesuffix + " (" + geometriespalte + "," + Attributliste  + " ) select " +  geometriespalte   + "," + Attributliste + " from " + outputname_ohnesuffix + "_temp_aktual"
                        sqliteOut.ExecuteSQL(query)
                    else:
                        query =    "insert into " + outputname_ohnesuffix + " (" + Attributliste + " ) select " +  Attributliste + " from " + outputname_ohnesuffix + "_temp_aktual"
                        sqliteOut.ExecuteSQL(query)




                    query =    "Drop Table " + outputname_ohnesuffix + "_temp_aktual"
                    sqliteOut.ExecuteSQL(query)




                    #löschen des Geometrieeintrags. Wenn eine Geometrielose Tabelle, passiert einfach nichts!
                    query =    "delete from geometry_columns where f_table_name = '" + outputname_ohnesuffix + "_temp_aktual'"

                    sqliteOut.ExecuteSQL(query)
                    #logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    #Alles OK, das Original kann in die Liste
                    #der zu löschenden Shapes aufgenommen werden
                    loeschliste.append(inputpfad + '/' + outputname)
                except:
                    logroutine(log_error,"SQL Fehler in der Spatiallite DB " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Abbrechen und weiter zum nächsten Datensatz

                #SPATIALITE Index aktualisieren:
                #ACHTUNG: Vorlage für den Index ist ein Index beim Shapefile oder der DBASE File.
                #Der geometrische Index wird immer angelegt
                abgleich = indexabgleich(lyrIn,dsIn,sqliteOut.GetLayerByName(outputname_ohnesuffix),sqliteOut,False)
                ret_ind = abgleich.indexAbgl()

                if ret_ind == 4:
                    logroutine(log_index_missing,"Fehler beim Indizieren des des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)

                #nochmal zur Sicherheit die Endkontrolle, ob das Shape auch wirklich
                #kopiert wurde
                lyrOut = sqliteOut.GetLayerByName(outputname_ohnesuffix)  #Als Layer das eigentliche Shape (ohne suffix)
                if lyrOut == None or (lyrIn.GetFeatureCount() != lyrOut.GetFeatureCount()):
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - Endkontrolle Datensatz - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste
                else:
                    logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    #Alles OK, das Original kann in die Liste
                    #der zu löschenden Shapes aufgenommen werden
                    #print inputpfad + '/' + inputname
                    loeschliste.append(inputpfad + '/' + outputname)

                #Die Objekte mit Referenz auf
                #die Dateien des Shapes müssen zuerst gelöscht werden
                #(sonst sind sie gelockt)
                lyrOut = None
                dsOut = None
                lyrIn = None
                dsIn = None
                dShape = None
                abgleich = None
                sqliteOut = None
                lyrSqliteOut = None



            #sicherheitshalber das DB Objekt löschen
            # falls es noch existieren sollte
            if not sqliteOut == None:
                sqliteOut = None



        #Alles OK, das Oroginal kann gelöscht werden
        #ACHTUNG: Im Produktivstatus unbedingt auskommentieren!!

        return loeschliste, errorliste    #wir geben ein Tupel zurück


    except Exception as e:
        return [],[]


