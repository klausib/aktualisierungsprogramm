# -*- coding: utf-8 -*-
#!/usr/bin/python


##import sys
##sys.path.append('C:/Program Files/QGIS Wien/apps/Python27/Lib/site-packages')
import sqlite3, os, sys
import logging,string,shutil
import hilfsmodul
from hauptmodul import *
from aktualisierung_sqlite import *
from aktualisierung_postgres import *
from indexabgleich import *
from osgeo import ogr, osr,gdal
from datetime import *






def logroutine(log_error, text,flag):

    log_error.error(unicode(text),exc_info=flag)




#--------------------------------------------------------------------#
#---------------------main-------------------------------------------#


###################################################################
#WICHTIG: Grundlegendes Verhalten der OGR/GDAl Lib wird so
#festgelegt und gilt für alle Teile des Programmes während der
#Laufzeit
###################################################################

gdal.UseExceptions()    # WICHTIG: Um GDAL/OGR Fehler als Laufzeitfehler abfangen
                        # und im Code behandeln zu können
gdal.SetConfigOption( "SQLITE_LIST_ALL_TABLES", "YES" ) #Sonst können keine geometrielosen Tabellen gefunden werden!!!
gdal.SetConfigOption( "PG_LIST_ALL_TABLES", "YES" ) #Sonst können keine geometrielosen Tabellen gefunden werden!!!


#os.chdir('D:/datenaktualisierung/aktualisierungsprogramm')

#Das Fehler und Hinweislogging

Fehlertext = ""
log_error = logging.getLogger('log1')
log_warning = logging.getLogger('log2')
log_index_missing = logging.getLogger('log3')
log_ok = logging.getLogger('log4')
log_available = logging.getLogger('log5')
log_abgelehnt = logging.getLogger('log6')
log_attrabgesch = logging.getLogger('log7')


fh_error = logging.FileHandler('error.log','w','utf8')
fh_warning = logging.FileHandler('warning.log','w','utf8')
fh_index_missing= logging.FileHandler('index_warning.log','w','utf8')
fh_ok= logging.FileHandler('erfolgreich.log','w','utf8')
fh_av= logging.FileHandler('nicht_bereitgestellt.log','w','utf8')
fh_ab= logging.FileHandler('abgelehnt.log','w','utf8')
fh_attrabgesch= logging.FileHandler('attrabgesch.log','a','utf8')
form_error = logging.Formatter("%(asctime)s %(levelname)s %(message)s","%d.%m.%y-%H:%M")
form_ok = logging.Formatter("%(asctime)s %(message)s","%d.%m.%y-%H:%M")
fh_error.setFormatter(form_error)
fh_warning.setFormatter(form_error)
fh_index_missing.setFormatter(form_error)
fh_ok.setFormatter(form_ok)
fh_av.setFormatter(form_ok)
fh_ab.setFormatter(form_ok)
fh_attrabgesch.setFormatter(form_error)
#fh1 = logging.StreamHandler()
#fh2 = logging.FileHandler('seppl.log')

log_error.addHandler(fh_error)
log_error.setLevel(logging.ERROR)

log_warning.addHandler(fh_warning)
log_warning.setLevel(logging.WARNING)

log_index_missing.addHandler(fh_index_missing)
log_index_missing.setLevel(logging.WARNING)

log_ok.addHandler(fh_ok)
log_ok.setLevel(logging.INFO)

log_available.addHandler(fh_av)
log_available.setLevel(logging.INFO)

log_abgelehnt.addHandler(fh_ab)
log_abgelehnt.setLevel(logging.INFO)

log_attrabgesch.addHandler(fh_attrabgesch)
log_attrabgesch.setLevel(logging.ERROR)




try:


    #Öffnen der Steuertabelle
    #Sqlite DB mit der Kopierliste öffnen
    #Die Steuertabelle einlesen
    Fehlertext = "Steuertabelle nicht gefunden"
    #db  = sqlite3.connect("kopierlistee.sqlite")

    if os.path.exists('kopierliste.sqlite'):
        db  = sqlite3.connect("kopierliste.sqlite")

    else:
        #log_error.error('Steuertabelle nicht gefunden')
        logroutine(log_error,"Fehler: Oeffnen der Steuertabelle fehlgeschlagen\r",False)
        raise SystemExit
        #raise Exception



    db.row_factory = sqlite3.Row    #für den Zugriff auf die einzelnen Spalten mit dem Spaltennamen
    #Den Datenbankkursor instanzieren
    assert db != None, "Steuertabelle: Datenbankobjekt ist None"   #Datenbankobjekt ist nicht erzeugt worden: Assertion Fehler wird ausgelöst
    cursor_sqlite = db.cursor()


    loeschliste = []
    errorliste = []
    loeschliste_tmp = []
    loeschliste_tmp_stat = []
    errorliste_tmp = []




    ###############################################
    ###############################################
    # Aktualisieren der SQLITE Datenbank
    ##############################################
    ##############################################


    #loeschliste = sqliteaktual(db,cursor_sqlite,log_error,log_warning,log_abgelehnt,log_index_missing,log_ok,log_available)
    a,b = sqliteaktual(db,cursor_sqlite,log_error,log_warning,log_abgelehnt,log_index_missing,log_ok,log_available,log_attrabgesch)

    if len (a) > 0:
        loeschliste = a
    if len (b) > 0:
        errorliste = b



    ##############################################
    ##############################################
    # Aktualisieren der POSTGRES Datenbank
    ##############################################
    ##############################################

    #if not loeschliste == None:
        #loeschliste.extend(postgresaktual(db,cursor_sqlite,log_error,log_warning,log_abgelehnt,log_index_missing,log_ok,log_available))
    c,d = postgresaktual(db,cursor_sqlite,log_error,log_warning,log_abgelehnt,log_index_missing,log_ok,log_available,log_attrabgesch)

    if len (c) > 0:
        if len(loeschliste) > 0:
            loeschliste.extend(c)
        else:
            loeschliste = c


    if len (d) > 0:
        if len(errorliste) > 0:
            errorliste.extend(d)
        else:
            errorliste = d






    #####################################################
    #####################################################
    #   Daten am Filesystem                             #
    #####################################################
    #####################################################

    #Die Auswahlabfrage ausführen
    cursor_sqlite.execute("select * from kopierliste_file where aktualisierung = 'ja'")

    #Alle passenden records auf einmal einlesen
    rows = cursor_sqlite.fetchall()
    if len(rows) > 0:
        row = rows[0]
    else:
        row = []

    #Marker setzen
    logroutine(log_abgelehnt,'---------Log Filesystem----------\r' ,False)
    logroutine(log_available,'---------Log Filesystem----------\r' ,False)
    logroutine(log_ok,'---------Log Filesystem----------\r' ,False)
    logroutine(log_index_missing,'---------Log Filesystem----------\r' ,False)
    logroutine(log_error,'---------Log Filesystem----------\r' ,False)
    logroutine(log_warning,'---------Log Filesystem----------\r' ,False)


    #Hauptschleife, alle records abarbeiten
    #das bedeutet alle zu aktualisierenden
    #Shapes, Tabellen, Dateien
    for row in rows:

        inputpfad = string.strip(str(os.path.dirname(row["quellpfad"])))
        outputpfad = string.strip(str(os.path.dirname(row["zielpfad"])))
        inputname = string.strip(str(os.path.basename(row["quellpfad"])))
        outputname = string.strip(str(os.path.basename(row["quellpfad"])))    # MÜSSEN GLEICH sein!!!!!!!!

        if not os.path.exists(inputpfad + '/' + inputname):
            logroutine(log_available,"Nicht bereitgestellt - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)    #Warnung setzen aber weitermachen
            continue


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
                logroutine(log_abgelehnt,"Dateityp nicht unterstuetzt - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r',False)
                errorliste.append(inputpfad + '/' + inputname)


##        ####################################################################################################
##        #Umkodieren falls notwendig (CP850 nach UTF8 damit Upload in DB's klappt)
##        #Dabei wird lediglich von CP850 nach UTF-8 umcodiert, und zwar das original Shape oder DBF.
##        #ACHTUNG: Beim kopieren versucht die OGR Bibliothek auch ein umcodieren und tut
##        #dies auch wenn sie kann! Allerdings, na ja ist das eine gute Idee
##        ####################################################################################################
##
##        if row['nach_utf8'] != 'nein':
##            if inputname.find('.shp') > -1:
##                tmp_dbasename = inputname_ohnesuffix + '.dbf'
##                if not hilfsmodul.umcodieren(inputpfad,tmp_dbasename,row['nach_utf8']):
##                    logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r'  ,False)    #Warnung setzen aber weitermachen
##            elif inputname.find('.dbf') > -1:
##                #hilfsmodul.umcodieren(inputpfad,inputname)
##                if not hilfsmodul.umcodieren(inputpfad,tmp_dbasename,row['nach_utf8']):
##                    logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname  + '\r' ,False)    #Warnung setzen aber weitermachen
##            elif inputname.find('.csv') > -1:
##                #hilfsmodul.umcodieren(inputpfad,inputname)
##                if not hilfsmodul.umcodieren(inputpfad,tmp_dbasenamerow['nach_utf8']):
##                    logroutine(log_warning,"Fehler beim Umcodieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname  + '\r' ,False)    #Warnung setzen aber weitermachen

        ####################################################################################################
        #Umkodieren falls notwendig (nach UTF8 damit Upload in DB's klappt)
        ####################################################################################################

        if row['nach_utf8'] != 'nein':  # es soll nicht umcodiert werden -> mal schauen

            #ist es beriets im Laufe dieser Aktualisierung umcodiert worden?
            #das erkennen wir einfach am Suffix, Pech wenn jemand dieses schon verwendet...

            #if not inputname.find('_UTF8') > -1: # -> wir müssen umcoderien
            if  os.path.exists(inputpfad + '/' + inputname_ohnesuffix + '_UTF8' + os.path.splitext(inputname)[1]):  # UTF8 bereits vorhanden
                inputname = inputname_ohnesuffix + '_UTF8' + os.path.splitext(inputname)[1]
                loeschliste.append(inputpfad + '/' + inputname)
                inputname_ohnesuffix = inputname_ohnesuffix + '_UTF8'       # das shape hat nun einen neuen Namen!
            else:   # -> wir müssen umcodieren
                #Ein Vergleichsobjekt wird instanziert
                #nur fürs Kopieren
                dShape = Vergleich()

                if not inputname.find('_UTF8') > -1: # -> wir müssen umcoderien

                    #Ein Vergleichsobjekt wird instanziert
                    #nur fürs Kopieren
                    dShape = Vergleich()

                # das gesamte Inputshape umbenennen in neues Shape
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



        ###### NEU ##############
        #Neuen Datensatz kopieren
        #########################
        if row["ds_neu"] == 'ja':


            ############ SHAPE ##################
            # Das Kopieren eines neuen Shapes

            if row["quelltyp"] == 'shape':

                bezugssystem = (row["bezugssystem"])    #Das Soll Bezugssystem (statisch in der Kopiertabelle eingetragen)


                #ACHTUNG: Wenn eine Shapedatasource gewählt wird gibts zwei
                #Möglichkeiten: Das Datasource Objekt wird mit dem Kompletten Pfad
                #bis zum Shape gefüttert. ODER nur mit dem Verzeichnispfad. Dann können
                #alle Shapes in diesem Verzeichnis als Layer geladen werden!!
                #WICHTIG: UNBEDINGT kein / am Schluss, sonst gehts nicht!

                #öffnen des Shapdatensatzes:
                dsIn = ogr.Open( inputpfad,True)    #Der Shapeworkspace: Flag True -> da brauch ich bereits Vollzugriff auf die Dateien!
                if dsIn == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsworkspace - " + str(row["primindex"]) + " " + inputpfad + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                lyrIn = dsIn.GetLayerByName(inputname_ohnesuffix)  #Als Layer das eigentliche Shape (ohne suffix)

                if lyrIn == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsdatensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                #Ein Vergleichsobjekt wird instanziert
                #Es ist für kopieren, vergleichen etc...
                dShape = Vergleich(lyrIn,dsIn)


                #Bezugssystem des Eingangsshapes prüfen
                ref_ret =  dShape.verglRef(bezugssystem)

                if  ref_ret == 2:   #Bezugssystem mußte NEU zugewiesen werden
                    dsIn = ogr.Open(inputpfad,True)
                    lyrIn = dsIn.GetLayerByName(inputname_ohnesuffix)       #Als Layer das eigentliche Shape (ohne suffix) dann müssen neu instanzieren damit beim Kopieren auf DB's
                    dShape = Vergleich(lyrIn,dsIn)                          #das Bezugssystem mitgenommen wird
                elif ref_ret == 3:  #Ein Fehler ist aufgetreten. Da stimmt was nicht, also abbrechen mit diesem Datensatz und den nächsten darannehmen
                    logroutine(log_error,"Fehler beim Zuweisen des Bezugssystems - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #zum nächsten Datensatz



                #ACHTUNG: Die Gross/Kleinschreibung des Shapes orientiert sich an dem String outputname in
                # der Steuertabelle: So wies dort drin ist wird der Shapename geschrieben
                if not dShape.kopieren_filebasis(inputpfad,inputname_ohnesuffix,outputpfad,outputname_ohnesuffix):
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop: Ab zum nächsten Datensatz


                #SHAPE Index aktualisieren. Zur Sicherheit, falls kein neuer Index
                #erzeugt wurde und noch der alte Index beim Shape liegt. Ansonsten wäre es
                #natürlich nicht notwendig
                #Den gerade kopierten Datensatz nochmal öffnen für den Indexabgleich

                dsOut =  ogr.Open( outputpfad,True) #Der Shapeworkspace: Ausgang -> ACHTUNG wenn leer ist dsOut = None
                abgleich = indexabgleich(lyrIn,dsIn,dsOut.GetLayerByName(outputname_ohnesuffix),dsOut,True)
                ret_ind = abgleich.indexAbgl()
                if ret_ind == 4:
                    logroutine(log_index_missing,"Fehler beim Indizieren des des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                if ret_ind == 3:
                    logroutine(log_index_missing,"Fehlender Datenbankindex für Attribute - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                if ret_ind == 2:
                    logroutine(log_index_missing,"Falscher Datentyp für die Indizierung - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)



                #nochmal zur Sicherheit prüfen ob der Datensatz auch wirklich angekommen ist
                dsOut = ogr.Open( outputpfad,True)    #Der Shapeworkspace: Eingang
                if dsOut == None:
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - Endkontrolle Workspace " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                lyrOut = dsOut.GetLayerByName(outputname_ohnesuffix)  #Als Layer das eigentliche Shape (ohne suffix)

                if lyrOut == None:
                    logroutine(log_error,"Fehler beim Kopieren des Datensatzes - Endkontrolle Datensatz - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste


                #Die Objekte mit Referenz auf
                #die Dateien des Shapes müssen zuerst gelöscht werden
                #(sonst sind sie gelockt)
                lyrOut = None
                dsOut = None
                lyrIn = None
                dsIn = None
                dShape = None
                abgleich = None


                #Wenns bis hierher geht, paßt alles, deshalb Quelldatensatz löschen
                #if hilfsmodul.shapeLoeschen(inputpfad,inputname_ohnesuffix):
                cursor_sqlite.execute("update kopierliste_file set datum_aktual = \'" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\' where primindex = " + str(row["primindex"]) + "")
                db.commit()
                logroutine(log_ok, "Kopieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r',False)
                loeschliste.append(inputpfad + '/' + outputname)
                #else:
                    #logroutine(log_warning,"Fehler beim Loeschen des Datensatzes - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                    #logroutine(log_ok, "Kopieren erfolgreich - loeschen fehlgeschlagen " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                    #loeschliste.append(inputpfad + '/' + inputname)


            ########## DATEI #############
            #Das Kopieren einer neuen Datei... ist am Einfachsten
            elif row["quelltyp"] == 'datei':


                if os.path.exists(inputpfad + '/' + inputname):

                    try:
                        shutil.copyfile(inputpfad + '/' + inputname, outputpfad + '/' + outputname)
                        #if hilfsmodul.dateiLoeschen(inputpfad,inputname):
                        cursor_sqlite.execute("update kopierliste_file set datum_aktual = \'" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\' where primindex = " + str(row["primindex"]) + "")
                        db.commit()
                        logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                        loeschliste.append(inputpfad + '/' + outputname)
                        #else:
                            #logroutine(log_warning,"Fehler beim Loeschen des Datensatzes - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                            #logroutine(log_ok, "Kopieren erfolgreich - loeschen fehlgeschlagen " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                            #loeschliste.append(inputpfad + '/' + inputname)
                    except:
                        logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                        errorliste.append(inputpfad + '/' + outputname)
                        continue    #Nächster Datensatz

                else:
                    logroutine(log_error,"Fehler beim Zugriff auf den Datensatz - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop: Nächster Datensatz


            ########### TABELLE ############
            #Das Kopieren einer neuen Tabelle
            elif row["quelltyp"] == 'tabelle':

                if os.path.exists(inputpfad + '/' + inputname):
                    try:
                        shutil.copyfile(inputpfad + '/' + inputname, outputpfad + '/' + outputname)
                         #Beim CSV auch noch die CSVT Datei kopieren
                        if (inputname.find('.csv') > -1) and os.path.exists(inputpfad + '/' + inputname + 't'):
                            shutil.copyfile(inputpfad + '/' + inputname + 't', outputpfad + '/' + outputname + 't')

                        if (inputname.find('.dbf') > -1) and os.path.exists(inputpfad + '/' + inputname.replace('.dbf','.idm')):    #attributiver Index
                            #Beim DBF einen eventuell vorhandenen Index anlegen                                                     #der DBF Datei
                            #Layer/datasource In/Out müssen dazu instanziert werden
                            dsOut =  ogr.Open( outputpfad + '/' + outputname,True)
                            lyrOut = dsOut.GetLayer()
                            dsIn = ogr.Open(inputpfad + '/' + inputname,True)
                            lyrIn = dsIn.GetLayer()
                            abgleich = indexabgleich(lyrIn,dsIn,lyrOut,dsOut,True)
                            if not abgleich.indexAbgl() == 1:
                                logroutine(log_warning,"Fehler beim Indexerzeugen - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                        #if hilfsmodul.dateiLoeschen(inputpfad,inputname):
                        cursor_sqlite.execute("update kopierliste_file set datum_aktual = \'" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\' where primindex = " + str(row["primindex"]) + "")
                        db.commit()
                        logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                        loeschliste.append(inputpfad + '/' + outputname)
                        #else:
                            #logroutine(log_warning,"Fehler beim Loeschen des Datensatzes - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                            #logroutine(log_ok, "Kopieren erfolgreich - loeschen fehlgeschlagen " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                            #loeschliste.append(inputpfad + '/' + inputname)
                    except:
                        logroutine(log_error,"Fehler beim Kopieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                        errorliste.append(inputpfad + '/' + outputname)
                        continue    #Stop: Nächster Datensatz

                else:
                    logroutine(log_error,"Fehler - Datensatz nicht gefunden: " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop: Nächster Datensatz


            #Das Flag ds_neu von 'ja' nach 'nein' stellen
            primindex = row["primindex"]
            cursor_sqlite.execute("update kopierliste_file set ds_neu = 'nein' where primindex = " + str(primindex) + "")
            db.commit()




        ###### AKTUALISIEREN ##############
        # Datensatz aktualisieren
        ###################################
        elif row["ds_neu"] == 'nein':


            ############ SHAPE ##################
            # Das Aktualisieren eines Shapes
            if row["quelltyp"] == 'shape':


                bezugssystem = (row["bezugssystem"])

                #ACHTUNG: Wenn eine Shapedatasource gewählt wird gibts zwei
                #Möglichkeiten: Das Datasource Objekt wird mit dem Kompletten Pfad
                #bis zum Shape gefüttert. ODER nur mit dem Verzeichnispfad. Dann können
                #alle Shapes in diesem Verzeichnis als Layer geladen werden!!
                #WICHTIG: UNBEDINGT kein / am Schluss, sonst gehts nicht!

                #öffnen des Input-Shapdatensatzes:
                dsIn = ogr.Open( inputpfad,True)    #Der Shapeworkspace: Flag True -> da brauch ich bereits Vollzugriff auf die Dateien!
                if dsIn == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsworkspace - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputpfad + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                lyrIn = dsIn.GetLayerByName(inputname_ohnesuffix)  #Als Layer das eigentliche Shape (ohne suffix)

                if lyrIn == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsdatensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + inputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste



                #öffnen des Output-Shapdatensatzes:
                dsOut = ogr.Open( outputpfad,True)    #Der Shapeworkspace: Flag True -> da brauch ich bereits Vollzugriff auf die Dateien!
                if dsOut == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Zielworkspace - " + str(row["primindex"]) + " "  + outputpfad + '/' + outputpfad + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                lyrOut = dsOut.GetLayerByName(outputname_ohnesuffix)  #Als Layer das eigentliche Shape (ohne suffix)

                if lyrOut == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Zieldatensatzes - " + str(row["primindex"]) + " "  + outputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste



                # Das Treiberobjekt
                drvOut = dsOut.GetDriver()
                drvIn = dsIn.GetDriver()

                #Das Vergleichsobjekt und die
                #notwendigen Vergleiche
                dShape = Vergleich(lyrIn,dsIn,lyrOut,dsOut)

                ref_ret = dShape.verglRef(bezugssystem) #gibt 1 zurück wenn nichts zu tun ist

                if  ref_ret == 2:   #Bezugssystem mußte NEU zugewiesen werden
                    dsIn = ogr.Open(inputpfad,True)
                    lyrIn = dsIn.GetLayerByName(inputname_ohnesuffix)       #Als Layer das eigentliche Shape (ohne suffix) dann müssen neu instanzieren damit beim Kopieren auf DB's
                    dShape = Vergleich(lyrIn,dsIn,lyrOut,dsOut)             #das Bezugssystem mitgenommen wird
                elif ref_ret == 3:  #Ein Fehler ist aufgetreten. Da stimmt was nicht, also abbrechen mit diesem Datensatz und den nächsten darannehmen
                    logroutine(log_abgelehnt,"Fehler beim Vergleich der Attributtabelle - " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #zum nächsten Datensatz



                #Gültigkeit der Attributtabelle
                #prüfen
                Attributliste = dShape.verglAttr(dsOut.GetDriver().GetName())   #Gibt einen String zurück:
                                                                                #Bei Problemen enthält er "Fehler:"


                if Attributliste.find("Fehler") >= 0:  #Das Stichwort Fehler wird zurückgegeben und wir brechen ab
                    logroutine(log_abgelehnt,"Fehler beim Vergleichen der Attribute - " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + " " + Attributliste.decode('utf8') + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #zum nächsten Datensatz


                #Gültigkeit des Geometrietyps prüfen
                geom_Vergleich = dShape.verglGeom()
                if geom_Vergleich.find("Fehler") >= 0:  #Das Stichwort Fehler wird zurückgegeben und wir brechen ab
                    logroutine(log_abgelehnt,"Fehler beim Vergleichen des Geometrietyps - " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #zum nächsten Datensatz


                #wenn wir bis hierher kommen, dann können wir mit
                #dem Kopieren beginnen:
                #Aufruf der Kopiermethode. Egal
                #welche Datenquelle/Treiber im Hintergrund steht,
                #der Layer wird mit dem gleich Aufruf kopiert.
                try:

                    #ACHTUNG: Die Gross/Kleinschreibung des Shapes orientiert sich an dem String outputname in
                    # der Steuertabelle: So wies dort drin ist wird der Shapename geschrieben
                    if not dShape.kopieren_filebasis(inputpfad,inputname_ohnesuffix,outputpfad,outputname_ohnesuffix+ '_temp_aktual'):
                    #zuerst neues Shape in Tempnamen kopieren
                    #if not dShape.kopieren(dsOut,lyrIn,outputname_ohnesuffix + '_temp_aktual',row["zieltyp"]):
                        logroutine(log_error,"Fehler beim Aktualisieren - " + str(row["primindex"]) + " " + outputname + '\r' ,False)
                        errorliste.append(inputpfad + '/' + outputname)
                        continue
                    shutil.copyfile(inputpfad + '/' + inputname_ohnesuffix + '.prj',outputpfad + '/' + outputname_ohnesuffix  + '_temp_aktual.prj')    #dann noch das prj File kopieren (damit format wie auf datenbank, nur zur Konsistenz)

                    #neu initialisieren, sonst spinnts
                    dsOut =  ogr.Open( outputpfad,True) #Der Shapeworkspace: Ausgang -> ACHTUNG wenn leer ist dsOut = None
                    #lyrOut = dsOut.GetLayerByName(outputname_ohnesuffix + '_temp_aktual')   #Als Layer das eigentliche Shape (ohne suffix)

                    #SHAPE Index aktualisieren
                    #bzw. an das bestehende Shape anpassen
                    abgleich = indexabgleich(lyrIn,dsIn,dsOut.GetLayerByName(outputname_ohnesuffix + '_temp_aktual'),dsOut,False)
                    ret_ind = abgleich.indexAbgl()
                    if ret_ind == 4:
                        logroutine(log_index_missing,"Fehler beim Indizieren des Datensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    if ret_ind == 3:
                        logroutine(log_index_missing,"Fehlender Datenbankindex für Attribute - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    if ret_ind == 2:
                        logroutine(log_index_missing,"Falscher Datentyp fuer die Indizierung - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)


                    #Die Objekte mit Referenz auf
                    #die Dateien des Shapes müssen zuerst gelöscht werden
                    #(sonst sind sie gelockt)
                    lyrOut = None
                    dsOut = None
                    lyrIn = None
                    dsIn = None
                    dShape = None
                    abgleich = None


                    #das original umbenennen
                    #bevor das neue Shape den richtigen Namen bekommt!
                    if not hilfsmodul.shapeUmbenennen(outputpfad,outputname_ohnesuffix + '_temp_original',outputname_ohnesuffix):
                        #das umbenennen des original ist fehlgeschlagen
                        logroutine(log_warning,"Fehler beim Umbenennen des original Shapes: - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)

                        #eventuelle dateien des shapes die entstanden sein könnten rückbenennen!
                        if not hilfsmodul.shapeUmbenennen(outputpfad,outputname_ohnesuffix,outputname_ohnesuffix + '_temp_original'):
                            logroutine(log_warning,"Schwerer Fehler beim Rueckbenennen des original Shapes: - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)

                        #das neue tempfile muss geloescht werden
                        #wir lassen das alte
                        if not hilfsmodul.shapeLoeschen(outputpfad,outputname_ohnesuffix + '_temp_aktual'):
                            logroutine(log_warning,"Weiterer Fehler beim Loeschen des temp Shapes: - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '_temp_original' + '\r' ,False)


                        logroutine(log_error,"Schwerer Fehler beim Aktualisieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                        errorliste.append(inputpfad + '/' + outputname)
                        continue    #stop und weiter zum Nächsten Shape

                    #umbenennen des original war erfolgreich
                    #nun dem neuen Shape den richtigen namen geben
                    if not hilfsmodul.shapeUmbenennen(outputpfad,outputname_ohnesuffix, outputname_ohnesuffix + '_temp_aktual'):
                        logroutine(log_error,"Fehler beim Umbenennen des neuen Shapes: - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '_temp_original' + '\r' ,False)
                        errorliste.append(inputpfad + '/' + outputname)

                        #dann halt das original wieder herstellen
                        if not hilfsmodul.shapeUmbenennen(outputpfad,outputname_ohnesuffix,outputname_ohnesuffix + '_temp_original'):
                            #wenns da zusätzlich noch ein Problem gibt, abbrechen
                            logroutine(log_error,"Schwerer Fehler beim Aktualisieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                            errorliste.append(inputpfad + '/' + outputname)
                            continue    #stop und weiter zum Nächsten Shape


                    #Uff, alles hat geklappt, nun das alte (umbenannte) loeschen

                    if hilfsmodul.shapeLoeschen(outputpfad,outputname_ohnesuffix + '_temp_original'):

                        #if hilfsmodul.shapeLoeschen(inputpfad,inputname_ohnesuffix):
                        cursor_sqlite.execute("update kopierliste_file set datum_aktual = \'" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\' where primindex = " + str(row["primindex"]) + "")
                        db.commit()
                        logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                        loeschliste.append(inputpfad + '/' + outputname)
                        #else:
                            #logroutine(log_warning,"Fehler beim Loeschen des Datensatzes - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                            #logroutine(log_ok, "Aktualisieren erfolgreich - loeschen fehlgeschlagen " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                            #loeschliste.append(inputpfad + '/' + inputname)
                    else:
                        logroutine(log_error,"Fehler beim Aktualisieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                        errorliste.append(inputpfad + '/' + outputname)
                        continue


                except: #Allgemeine Ausnahme
                    logroutine(log_error,"Fehler beim Aktualisieren - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue





            ########## DATEI #############
            # Das Aktualisieren einer Datei ... wieder am Einfachsten!
            elif row["quelltyp"] == 'datei':

                try:
                    if os.path.exists(outputpfad + '/' + outputname):
                        shutil.copyfile(inputpfad + '/' + inputname, outputpfad + '/' + outputname)
                        #if hilfsmodul.dateiLoeschen(inputpfad,inputname):
                        cursor_sqlite.execute("update kopierliste_file set datum_aktual = \'" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\' where primindex = " + str(row["primindex"]) + "")
                        db.commit()
                        logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                        loeschliste.append(inputpfad + '/' + outputname)
                        #else:
                            #logroutine(log_warning,"Fehler beim Loeschen des Datensatzes - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                            #logroutine(log_ok, "Aktualisieren erfolgreich - loeschen fehlgeschlagen " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                            #loeschliste.append(inputpfad + '/' + inputname)
                        #Nun die Quelldatei loeschen
                    else:
                        logroutine(log_error, "Aktualisieren fehlgeschlagen " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                        errorliste.append(inputpfad + '/' + outputname)
                except:
                    logroutine(log_error, "Aktualisieren fehlgeschlagen " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                #egal ob Bestand oder nicht, es wird einfach kopiert und die Alte überschreiben. Prüfen eienr Datei (z.B. JPEG) ist nicht möglich


            ########### TABELLE ############
            # Das Aktualisieren einer Tabelle
            elif row["quelltyp"] == 'tabelle':


                #öffnen der inputdatei
                dsIn =  ogr.Open( inputpfad + '/' + inputname,True)  #Bei Tabellen braucht die OGR hier das Suffix
                if dsIn == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsworkspace - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                lyrIn = dsIn.GetLayer()   #und dann kann man so den Layer instanzieren

                if lyrIn == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Eingangsdatensatzes - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste


                 #öffnen der Outputdatei
                dsOut =  ogr.Open( outputpfad + '/' + outputname,True)  #Bei Tabellen braucht die OGR hier das Suffix
                if dsOut == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Zielworkspace - " + str(row["primindex"]) + " " + outputpfad + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                lyrOut = dsOut.GetLayer()   #und dann kann man so den Layer instanzieren

                if lyrOut == None:
                    logroutine(log_error,"Fehler beim Oeffnen des Zieldatensatzes - " + str(row["primindex"]) + " "  + outputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #Stop hier: nächster Datensatz in der Liste

                #Das Vergleichsobjekt und die
                #notwendigen Vergleiche
                dShape = Vergleich(lyrIn,dsIn,lyrOut,dsOut)


                #Gültigkeit der Attributtabelle
                #prüfen
                Attributliste = dShape.verglAttr(dsOut.GetDriver().GetName())   #Gibt einen String zurück:
                                                                                #Bei Problemen enthält er "Fehler:"

                if Attributliste.find("Fehler") >= 0:  #Das Stichwort Fehler wird zurückgegeben und wir brechen ab
                    logroutine(log_abgelehnt,"Fehler beim Vergleichen der Attribute - " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + " " + Attributliste.decode('utf8') + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue    #zum nächsten Datensatz

                try:
                    #Tabelle wie Datei am Filesystem kopieren
                    #dShape.kopierenNachShape(dsIn.GetDriver(),dsIn,outputpfad)
                    shutil.copyfile(inputpfad + '/' + inputname, outputpfad + '/' + outputname) #egal ob Bestand oder nicht, es wird einfach kopiert

                    #Beim DBASE die Indexdateien löschen (werden ja neu angelegt)
                    if  (inputname.find('.dbf') > -1):
                        if os.path.exists(outputpfad + '/' + outputname_ohnesuffix + '.idm'):
                            os.remove(outputpfad + '/' + outputname_ohnesuffix + '.idm')
                        if os.path.exists(outputpfad + '/' + outputname_ohnesuffix + '.ind'):
                            os.remove(outputpfad + '/' +outputname_ohnesuffix + '.ind')

                    #Beim csv auch noch die CSVT datei kopieren
                    if  (inputname.find('.csv') > -1) and os.path.exists(inputpfad + '/' + inputname + 't'):
                        shutil.copyfile(inputpfad + '/' + inputname + 't', outputpfad + '/' + outputname + 't')

                    dsOut =  ogr.Open( outputpfad + '/' + outputname,True) # hier nochmal instanzieren!

                    if (inputname.find('.dbf') > -1) and os.path.exists(inputpfad + '/' + inputname.replace('.dbf','.idm')):    #attributiver Index
                        #Beim DBF einen eventuell vorhandenen Index anlegen                                                     #der DBF Datei
                        #Layer/datasource In/Out müssen dazu instanziert werden
                        abgleich = indexabgleich(lyrIn,dsIn,dsOut.GetLayer(),dsOut,False)

                        if not abgleich.indexAbgl() == 1:
                            logroutine(log_warning,"Fehler beim Indexerzeugen - " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)

                    #Die Objekte mit Referenz auf
                    #die Dateien des Shapes müssen zuerst gelöscht werden
                    #(sonst sind sie gelockt)
                    lyrOut = None
                    dsOut = None
                    lyrIn = None
                    dsIn = None
                    dShape = None
                    abgleich = None

                    #if hilfsmodul.dateiLoeschen(inputpfad,inputname):
                    cursor_sqlite.execute("update kopierliste_file set datum_aktual = \'" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\' where primindex = " + str(row["primindex"]) + "")
                    db.commit()
                    logroutine(log_ok, "Aktualisieren erfolgreich " + str(row["primindex"]) + " " + inputpfad + '/' + outputname + '\r' ,False)
                    loeschliste.append(inputpfad + '/' + outputname)
                    #else:
                        #logroutine(log_warning,"Fehler beim Loeschen des Datensatzes - " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                        #logroutine(log_ok, "Aktualisieren erfolgreich - loeschen fehlgeschlagen " + str(row["primindex"]) + " " + inputpfad + '/' + inputname + '\r' ,False)
                        #loeschliste.append(inputpfad + '/' + inputname)
                    #Nun die Quelldatei loeschen
                except:
                    logroutine(log_error, "Aktualisieren fehlgeschlagen " + str(row["primindex"]) + " "  + inputpfad + '/' + outputname + '\r' ,False)
                    errorliste.append(inputpfad + '/' + outputname)
                    continue




    #Cursorobjekt Steuertabelle schliessen
    cursor_sqlite.close()
    #Datenbankverbindung Steuertabelle schliessen
    db.close()


    #Die Objekte mit Referenz auf
    #die Dateien des Shapes müssen zuerst gelöscht werden
    #(sonst sind sie gelockt)
    lyrOut = None
    dsOut = None
    lyrIn = None
    dsIn = None
    dShape = None
    abgleich = None






    #doppelte Einträge entfernen
    if len (loeschliste) > 0:
        loeschliste_tmp = list(set(loeschliste))
        loeschliste_tmp_stat = list(set(loeschliste))
    if len (errorliste) > 0:
        errorliste_tmp = list(set(errorliste))


    #da mehrfacheinträge bei den Quelldateien möglich sind (file, sqlite und postgres haben gleiche Quelle!)
    #muss überprüft werden ob bei allen das Shape erfolgreich kopiert wurde, d.h. einträge in der Löschliste
    #dürfen NICHT in der Fehlerliste vorkommen!


    for quelle in loeschliste_tmp_stat:
        #print 'quelle = ' + quelle
        for fehler in errorliste_tmp:
            #print 'fehler = ' + fehler
            if fehler.find(quelle) > -1:
                loeschliste_tmp.remove(quelle)   #aus der löschliste entfernen
                break   #nächster Eintrag für Quelle

    #print loeschliste_tmp



    #nun noch nicht gelöschte Originaldateien der Datenbankaktualisierungen
    #löschen (eine Shape kann ja mehrmals vorkommen file, sqlite, postgis)
    for pfad in loeschliste_tmp:
        if  (pfad.find('.shp') > -1):
            if not hilfsmodul.shapeLoeschen(str(os.path.dirname(pfad)),str(os.path.basename(pfad)).replace('.shp','')):
                logroutine(log_warning,'-------------------------------------------------------------------------------------\r' ,False)
                logroutine(log_warning,"Fehler beim Loeschen des Datensatzes  - " + pfad +'\r' ,False)
                #logroutine(log_ok, "Aktualisieren erfolgreich - loeschen fehlgeschlagen - " + pfad +'\r' ,False)
        else:
            if not hilfsmodul.dateiLoeschen(str(os.path.dirname(pfad)),str(os.path.basename(pfad))):
                logroutine(log_warning,'-------------------------------------------------------------------------------------\r' ,False)
                logroutine(log_warning,"Fehler beim Loeschen des Datensatzes - " + pfad +'\r' ,False)
                #logroutine(log_ok, "Aktualisieren erfolgreich - loeschen fehlgeschlagen - " + pfad +'\r' ,False)

    # Abschlussnachricht
    logroutine(log_ok, 'Aktualisierungprozess Ende' ,False)


#Programmabbruch wird durch diese
#Exception durchgeführt
except SystemExit:
    logroutine(log_error, 'Fehler in der Programmausfuehrung - Abbruch notwendig' + '\r' ,True)
    sys.exit()

except AssertionError:
    logroutine(log_error, 'Negative Bedingung - Abbruch notwendig' + '\r' ,True)
    sys.exit()

except Exception as e:
    logroutine(log_error,str(e) + '\r' ,True)
    sys.exit()


