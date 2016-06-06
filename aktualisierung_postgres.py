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



def postgresaktual(db,cursor_sqlite,log_error,log_warning,log_abgelehnt,log_index_missing,log_ok,log_available,log_attribgesch):

    try:
        #####################################################
        #   Aktualisierung Datenbank POSTGRES               #
        #####################################################

        loeschliste = []
        errorliste = []

        #Die Auswahlabfrage ausführen
        cursor_sqlite.execute("select * from kopierliste_postgres where aktualisierung = 'ja'")


        #Alle passenden records auf einmal einlesen
        rows = cursor_sqlite.fetchall()
        if len(rows) > 0:
            row = rows[0]
        else:
            row = []

        #Marker setzen
        logroutine(log_abgelehnt,'---------Log Postgres----------\r' ,False)
        logroutine(log_available,'---------Log Postgres----------\r' ,False)
        logroutine(log_ok,'---------Log Postgres----------\r' ,False)
        logroutine(log_index_missing,'---------Log Postgres----------\r' ,False)
        logroutine(log_error,'---------Log Postgres----------\r' ,False)
        logroutine(log_warning,'---------Log Postgres----------\r' ,False)



        #Hauptschleife, alle records abarbeiten
        for row in rows:
            #print row["zieltyp"] + " " +  row["quellpfad"]  + " " +  row["zielpfad"]


            #dieser code ist zwar auch im Codesegment fürs Filesystem vorhanden,
            #aber ich finde es übersichtlicher ihn hier einfach nochmal zu verwenden anstatt
            #in ein Modul auszulagern

            inputpfad = str(os.path.dirname(row["quellpfad"]))
            outputdb = str(row["zielpfad"])
            inputname = str(os.path.basename(row["quellpfad"]))
            outputname = str(os.path.basename(row["quellpfad"]))
            postgisOut = ogr.Open(outputdb) #ACHTUNG: Schema nicht vergessen!

            #conenction string PG: host=vnvfelfs2 dbname=vogis schemas=public user=postgres password=postgres


            if not os.path.exists(inputpfad + '/' + inputname):
                logroutine(log_available,"Nicht bereitgestellt - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
                continue    #nächster Datensatz
            #Nun das Ziel des Kopierprozesses
            #die Postgres DB Datenbank
            if postgisOut == None:
                logroutine(log_error,"Ausgangs POSTGRES Datenbank nicht gefunden: - " + str(row["primindex"]) + " " + outputdb + '\r'  ,False)    #Warnung setzen aber weitermachen
                errorliste.append(inputpfad + '/' + inputname)
                continue



            #unsere drei zugelassen suffixe für Geodaten oder Tabellen
            if  (inputname.find('.csv') > -1):
                outputname_ohnesuffix = inputname.replace('.csv','')
                inputname_ohnesuffix = inputname.replace('.csv','')
            elif  (inputname.find('.dbf') > -1):
                outputname_ohnesuffix = inputname.replace('.dbf','')
                inputname_ohnesuffix = inputname.replace('.dbf','')
            elif  (inputname.find('.shp') > -1):
                outputname_ohnesuffix = inputname.replace('.shp','')
                inputname_ohnesuffix = inputname.replace('.shp','')
            elif  (inputname.find('.xlsx') > -1):
                outputname_ohnesuffix = inputname.replace('.xlsx','')
                inputname_ohnesuffix = inputname.replace('.xlsx','')

            else:
                if str(row["quelltyp"]) == 'datei':
                    outputname_ohnesuffix = ""
                    inputname_ohnesuffix = ""
                else:
                    logroutine(log_abgelehnt,"Dateityp nicht unterstuetzt - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + inputname)
                    continue    #Stop hier: nächster Datensatz in der Liste



            # Umcodieren findet für den Postgres Fall direkt im Sub kopieren des Hauptmoduls statt.
            # Grund: Ist stabieler

##            ####################################################################################################
##            #Umkodieren falls notwendig (nach UTF8 damit Upload in DB's klappt)
##            ####################################################################################################
##
##            if row['nach_utf8'] != 'nein':  # es soll umcodiert werden -> mal schauen
##
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



##            ####################################################################################################
##            # Umkodieren falls notwendig (nach UTF8 damit Upload in DB's klappt)
##            ####################################################################################################
##
##            if row['nach_utf8'] != 'nein' and inputname.find('.shp') < 0:  # es soll umcodiert werden -> nur nicht für shapes
##
##                #ist es beriets im Laufe dieser Aktualisierung umcodiert worden?
##                #das erkennen wir einfach am Suffix, Pech wenn jemand dieses schon verwendet...
##
##                #if not inputname.find('_UTF8') > -1: # -> wir müssen umcoderien
##                if  os.path.exists(inputpfad + '/' + inputname_ohnesuffix + '_UTF8' + os.path.splitext(inputname)[1]):  # UTF8 bereits vorhanden
##                    inputname = inputname_ohnesuffix + '_UTF8' + os.path.splitext(inputname)[1]
##                    loeschliste.append(inputpfad + '/' + inputname)
##                    inputname_ohnesuffix = inputname_ohnesuffix + '_UTF8'       # das shape hat nun einen neuen Namen!
##                else:   # -> wir müssen umcodieren
##                    #Ein Vergleichsobjekt wird instanziert
##                    #nur fürs Kopieren
##
##                    dShape = Vergleich()
##                    # das gesamte Inputshape umbenennen in neues Shape
##                    if not dShape.kopieren_filebasis(inputpfad,inputname_ohnesuffix,inputpfad, inputname_ohnesuffix + '_UTF8',os.path.splitext(inputname)[1]):
##                        logroutine(log_error,"Schwerer Fehler beim Umbenennen des original Shapes fuer die Umcodierung: - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
##                        errorliste.append(inputpfad + '/' + inputname)
##                        continue    #Stop hier: nächster Datensatz in der Liste
##                    else:   #umbenennen erfolgreich - löschen nicht vergessen -> löschliste
##                        inputname = inputname_ohnesuffix + '_UTF8' + os.path.splitext(inputname)[1]
##                        loeschliste.append(inputpfad + '/' + inputname)
##                        inputname_ohnesuffix = inputname_ohnesuffix + '_UTF8'       # das shape hat nun einen neuen Namen!
##
##
##                    if inputname.find('.shp') > -1:
##                        pass
##                        tmp_dbasename = inputname_ohnesuffix + '.dbf'
##                        if not hilfsmodul.umcodieren(inputpfad,tmp_dbasename,row['nach_utf8'],log_attribgesch):
##                            logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
##                    elif inputname.find('.dbf') > -1:
##                        #hilfsmodul.umcodieren(inputpfad,inputname)
##                        if not hilfsmodul.umcodieren(inputpfad,inputname,row['nach_utf8'],log_attribgesch):
##                            logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
##                    elif inputname.find('.csv') > -1:
##                        #hilfsmodul.umcodieren(inputpfad,inputname)
##                        if not hilfsmodul.umcodieren(inputpfad,inputname,row['nach_utf8'],log_attribgesch):
##                            logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname  + '\r' ,False)    #Warnung setzen aber weitermachen
##
##
##
##
##
##
##
##
##
##
##
##            ####################################################################################################
##            # ENDE Modul umcodieren ############################################################################
##            ####################################################################################################



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

            #prüfen ob der Ausgangsdatensatz vorhanden ist
            lyrPostgisOut = postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix))
            if not lyrPostgisOut == None and row["ds_neu"] == 'ja':  #Wir haben den datensatz als neu definiert, d.h. ein
                if not postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix) + '_temp_alt') == None:
                    postgisOut.DeleteLayer(string.lower(outputname_ohnesuffix) + '_temp_alt')
                postgisOut.CopyLayer(lyrPostgisOut,string.lower(outputname_ohnesuffix) + '_temp_alt')
                postgisOut.DeleteLayer(string.lower(outputname_ohnesuffix))       #eventuell bestehender soll überschrieben werden

            if lyrPostgisOut == None and row["ds_neu"] == 'nein':
                logroutine(log_abgelehnt,"Aktualisierung fehlgeschlagen - Datensatz im Ziel nicht vorhanden! - " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                #errorliste.append(inputpfad + '/' + inputname)
                errorliste.append(inputpfad + '/' + outputname)
                continue    #Stop hier: nächster Datensatz in der Liste




            ###### NEU ##############
            #Neuen Datensatz kopieren
            #########################
            if row["ds_neu"] == 'ja':


                 # Schema extrahieren
                param_list = string.split(postgisOut.GetName())
                schema = ''

                for param in param_list:
                        if string.find(param,'schemas') >= 0:
                            schema = string.replace(param,'schemas=','')
                            #print schema
                        elif string.find(param,'Schemas=') >= 0:
                            schema = string.replace(param,'Schemas=','')
                            #print schema

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
                rueckgabe = dShape.kopieren(postgisOut,lyrIn,string.lower(outputname_ohnesuffix),row["zieltyp"],row['nach_utf8'])
                #if not dShape.kopieren(postgisOut,lyrIn,string.lower(outputname_ohnesuffix),row["zieltyp"]):    #outputname ist ja die sqlite Datei
                if not rueckgabe[0]:    #outputname ist ja die sqlite Datei
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + ' ' + str(rueckgabe[1]) + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)

                    # wenn möglich, zurückstellen
                    lyr_t = postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix) + '_temp_alt')
                    if not lyr_t == None:
                        postgisOut.CopyLayer(lyr_t, string.lower(outputname_ohnesuffix))
                        postgisOut.DeleteLayer(string.lower(outputname_ohnesuffix) + '_temp_alt')

                    continue    #Stop: Ab zum nächsten Datensatz

                #Püfen ob auch wirklich alle Feature übernommen wurden
                diff = lyrIn.GetFeatureCount() - postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix)).GetFeatureCount()
##                print str(lyrIn.GetFeatureCount())
##                print str(postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix)).GetFeatureCount())
##                exit(0)
                if abs(diff) > 0:
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + ' ' + str(abs(diff)) + ' - Features fehlen' + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)

##                    # Temp Tabelle löschen
##                    query =    "Drop Table " + string.lower(outputname_ohnesuffix)
##                    postgisOut.ExecuteSQL(query)

                    # wenn nötig, zurückstellen
                    lyr_t = postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix) + '_temp_alt')
                    if not lyr_t == None:
                        postgisOut.DeleteLayer(string.lower(outputname_ohnesuffix))
                        postgisOut.CopyLayer(lyr_t, string.lower(outputname_ohnesuffix))
                        postgisOut.DeleteLayer(string.lower(outputname_ohnesuffix) + '_temp_alt')



                    #löschen des Geometrieeintrags. Wenn eine Geometrielose Tabelle, passiert einfach nichts!
                    query =    "delete from geometry_columns where f_table_name = '" + string.lower(outputname_ohnesuffix)
                    postgisOut.ExecuteSQL(query)

                    continue    #Stop: Ab zum nächsten Datensatz

                #POSTGIS Index aktualisieren:
                #ACHTUNG: Vorlage für den Index ist der Index beim Shapefile oder des DBASE File.
                #Der geometrische Index wird immer angelegt
                abgleich = indexabgleich(lyrIn,dsIn,postgisOut.GetLayerByName(outputname_ohnesuffix),postgisOut,schema, True)
                ret_ind = abgleich.indexAbgl()
                if ret_ind == 4:
                    logroutine(log_index_missing,"Fehler beim Indizieren des des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)

                #nochmal zur Sicherheit die Endkontrolle, ob das Shape auch wirklich
                #kopiert wurde
                lyrPostgisOut = postgisOut.GetLayerByName(outputname_ohnesuffix)  #Als Layer das eigentliche Shape (ohne suffix)
                if lyrPostgisOut == None or (lyrIn.GetFeatureCount() != lyrPostgisOut.GetFeatureCount()):
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - Endkontrolle Datensatz - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                else:
                    logroutine(log_ok, "Kopieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    #Alles OK, das Original kann in die Liste
                    #der zu löschenden Shapes aufgenommen werden
                     # wenn möglich, zurückstellen
                    if not postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix) + '_temp_alt') == None:
                        postgisOut.DeleteLayer(string.lower(outputname_ohnesuffix) + '_temp_alt')

                    loeschliste.append(inputpfad + '/' + outputname)


                #Die Objekte mit Referenz auf
                #die Dateien des Shapes müssen zuerst gelöscht werden
                #(sonst sind sie gelockt)
                lyrPostgisOut = None
                postgisOut = None
                lyrIn = None
                dsIn = None
                dShape = None
                abgleich = None


                #Das Flag ds_neu von 'ja' nach 'nein' stellen
                primindex = row["primindex"]
                cursor_sqlite.execute("update kopierliste_postgres set ds_neu = 'nein' where primindex = " + str(primindex) + "")
                db.commit()



            ###### AKTUALISIEREN ##############
            # Datensatz aktualisieren
            ###################################
            elif row["ds_neu"] == 'nein':


                #Ein Vergleichsobjekt wird instanziert
                #Es ist für kopieren, vergleich etc...
                dShape = Vergleich(lyrIn,dsIn,lyrPostgisOut,postgisOut)


                #Gültigkeit der Attributtabelle
                #prüfen
                Attributliste = dShape.verglAttr(postgisOut.GetDriver().GetName())
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
                rueckgabe = dShape.kopieren(postgisOut,lyrIn,string.lower(outputname_ohnesuffix) + '_temp_aktual',row["zieltyp"],row['nach_utf8'])
                #if not dShape.kopieren(postgisOut,lyrIn,string.lower(outputname_ohnesuffix) + '_temp_aktual',row["zieltyp"]):   #outputname ist ja die sqlite Datei
                if not rueckgabe[0]:   #outputname ist ja die sqlite Datei
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + ' ' + str(rueckgabe[1]) + '\r',False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop: Ab zum nächsten Datensatz


##                #Püfen ob auch wirklich alle Feature übernommen wurden
##                diff = lyrIn.GetFeatureCount() -  postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix + "_temp_aktual")).GetFeatureCount()
##                if abs(diff) > 0:
##                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + ' ' + str(abs(diff)) + ' - Features fehlen' + '\r' ,False)
##                    #errorliste.append(inputpfad + '/' + inputname)
##                    errorliste.append(inputpfad + '/' + outputname)
##                    print 'hierrrrr'
##                    # Temp Tabelle löschen
##                    query =    "BEGIN;drop table " + string.lower(schema + '.' + outputname_ohnesuffix) + "_temp_aktual;COMMIT;"
##                    print 'query=' + str(query)
##                    postgisOut.ExecuteSQL(query)
##                    print 'dort'
##
##                    #löschen des Geometrieeintrags. Wenn eine Geometrielose Tabelle, passiert einfach nichts!
##                    query =    "delete from geometry_columns where f_table_name = '" + string.lower(outputname_ohnesuffix) + "_temp_aktual'"
##                    postgisOut.ExecuteSQL(query)
##
##                    continue    #Stop: Ab zum nächsten Datensatz

                try:
                    # Schema extrahieren
                    param_list = string.split(postgisOut.GetName())
                    schema = ''

                    for param in param_list:
                            if string.find(param,'schemas') >= 0:
                                schema = string.replace(param,'schemas=','')
                                #print schema
                            elif string.find(param,'Schemas=') >= 0:
                                schema = string.replace(param,'Schemas=','')
                                #print schema

                    #die Geometriespalte finden!
                    geometriespalte = ''
                    geometriespalte = lyrPostgisOut.GetGeometryColumn()  #gibt die Geometriespalte zurück oder ''


                    #Püfen ob auch wirklich alle Feature übernommen wurden
                    diff = lyrIn.GetFeatureCount() -  postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix + "_temp_aktual")).GetFeatureCount()
                    if abs(diff) > 0:
                        logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + ' ' + str(abs(diff)) + ' - Features fehlen' + '\r' ,False)
                        #errorliste.append(inputpfad + '/' + inputname)
                        errorliste.append(inputpfad + '/' + outputname)
                        # Temp Tabelle löschen
                        query =    "BEGIN;drop table " + string.lower(schema + '.' + outputname_ohnesuffix) + "_temp_aktual;COMMIT;"
                        postgisOut.ExecuteSQL(query)


                        #löschen des Geometrieeintrags. Wenn eine Geometrielose Tabelle, passiert einfach nichts!
                        query =    "delete from geometry_columns where f_table_name = '" + string.lower(outputname_ohnesuffix) + "_temp_aktual'"
                        postgisOut.ExecuteSQL(query)
                        continue    #Stop: Ab zum nächsten Datensatz




                    if not geometriespalte == '':   # wenn es keine gibt ist die variable ''
                        query = "alter sequence " + string.lower(schema + '.' + outputname_ohnesuffix) + "_ogc_fid_seq restart with 1"
                        postgisOut.ExecuteSQL(query)
                        query = "BEGIN;DELETE from " + string.lower(schema + '.' + outputname_ohnesuffix) + ";insert into " + string.lower(schema + '.' + outputname_ohnesuffix) + " (" + string.lower(Attributliste) + ",\"" + string.lower(geometriespalte) + "\" ) select " + string.lower(Attributliste) + ",\"" + string.lower(geometriespalte) + "\" from " + string.lower(schema + '.' + outputname_ohnesuffix) + "_temp_aktual;COMMIT;"
                        postgisOut.ExecuteSQL(query)
                    else:
                        query = "alter sequence " + string.lower(schema + '.' + outputname_ohnesuffix) + "_ogc_fid_seq restart with 1"
                        postgisOut.ExecuteSQL(query)
                        query = "BEGIN;DELETE from " + string.lower(schema + '.' + outputname_ohnesuffix) + ";insert into " + string.lower(schema + '.' + outputname_ohnesuffix) + " (" + string.lower(Attributliste) + ")  select " + string.lower(Attributliste) + " from " + string.lower(schema + '.' + outputname_ohnesuffix) + "_temp_aktual;COMMIT;"
                        postgisOut.ExecuteSQL(query)

                    # Temp Tabelle löschen
                    query =    "BEGIN;drop table " + string.lower(schema + '.' + outputname_ohnesuffix) + "_temp_aktual;COMMIT;"
                    postgisOut.ExecuteSQL(query)

                    #löschen des Geometrieeintrags. Wenn eine Geometrielose Tabelle, passiert einfach nichts!
                    query =    "delete from geometry_columns where f_table_name = '" + string.lower(schema + '.' + outputname_ohnesuffix) + "_temp_aktual'"
                    postgisOut.ExecuteSQL(query)


                    #logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    #Alles OK, das Original kann in die Liste
                    #der zu löschenden Shapes aufgenommen werden
                    loeschliste.append(inputpfad + '/' + outputname)

                except:

                    logroutine(log_error,"SQL Fehler in der Postgis DB " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    #errorliste.append(inputpfad + '/' + inputname)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Abbrechen und weiter zum nächsten Datensatz

                #POSTGIS Index aktualisieren:
                #ACHTUNG: Vorlage für den Index ist der Index beim Shapefile oder des DBASE File.
                #Der geometrische Index wird immer angelegt

                abgleich = indexabgleich(lyrIn,dsIn,postgisOut.GetLayerByName(outputname_ohnesuffix),postgisOut, schema, False)
                ret_ind = abgleich.indexAbgl()

                if ret_ind == 4:
                    logroutine(log_index_missing,"Fehler beim Indizieren des des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)


                #####################################################################################
                #nochmal zur Sicherheit die Endkontrolle
                #####################################################################################
                lyrOut = postgisOut.GetLayerByName(string.lower(outputname_ohnesuffix))  #Als Layer das eigentliche Shape (ohne suffix)
                if lyrOut == None or (lyrIn.GetFeatureCount() != lyrOut.GetFeatureCount()):
                    logroutine(log_error,"Fehler beim Aktualisieren des Datensatzes - Endkontrolle Datensatz - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste
                else:
                    logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    #Alles OK, das Original kann in die Liste
                    #der zu löschenden Shapes aufgenommen werden
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
                postgisOut = None
                lyrPostgisOut = None


        return loeschliste, errorliste    #wir geben ein Tupel zurück

    except Exception as e:
        print str(e)
        return [],[]
