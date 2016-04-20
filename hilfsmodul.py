# -*- coding: utf-8 -*-
#!/usr/bin/python


##import sys
##sys.path.append('C:/Program Files/QGIS Wien/apps/Python27/Lib/site-packages')
import os,sys
import string,shutil,glob, logging
from dbfpy.dbf import *



def logroutine(log_error, text,flag):

    log_error.error(unicode(text),exc_info=flag)



###########################################
#Diese Funktion nennt eine Shapedatei
#inkl. aller dazugehörenden Dateien auf
#Fileebene um
###########################################
#def shapeUmbenennen(pfadstring,dateistring,umb_suffix):
def shapeUmbenennen(pfadstring,dateistring,dateistring_alt):

    try:
        pfadstring = pfadstring + "/"


        if os.path.exists(pfadstring + dateistring_alt  + ".shp"):
            os.rename(pfadstring + dateistring_alt  +  ".shp", pfadstring + dateistring + ".shp")

        if os.path.exists(pfadstring + dateistring_alt  + ".shp.xml"):

            os.rename(pfadstring + dateistring_alt  + ".shp.xml", pfadstring + dateistring + ".shp.xml")
        if os.path.exists(pfadstring + dateistring_alt  + ".dbf"):

            os.rename(pfadstring + dateistring_alt  + ".dbf", pfadstring + dateistring + ".dbf")
        if os.path.exists(pfadstring + dateistring_alt  + ".sbn"):
            os.rename(pfadstring + dateistring_alt  +  ".sbn", pfadstring + dateistring + ".sbn")
        if os.path.exists(pfadstring + dateistring_alt  + ".sbx"):
            os.rename(pfadstring + dateistring_alt  +  ".sbx",pfadstring + dateistring + ".sbx")
        if os.path.exists(pfadstring + dateistring_alt  + ".fbn"):
            os.rename(pfadstring + dateistring_alt  +  ".fbn",pfadstring + dateistring + ".fbn")
        if os.path.exists(pfadstring + dateistring_alt  + ".fbx"):
            os.rename(pfadstring + dateistring_alt   + ".fbx",pfadstring + dateistring + ".fbx")
        if os.path.exists(pfadstring + dateistring_alt  + ".shx"):
            os.rename(pfadstring + dateistring_alt  + ".shx", pfadstring + dateistring + ".shx")
        if os.path.exists(pfadstring + dateistring_alt  + ".qix"):
            os.rename(pfadstring + dateistring_alt  +  ".qix",pfadstring + dateistring + ".qix")
        if os.path.exists(pfadstring + dateistring_alt  + ".prj"):
            os.rename(pfadstring + dateistring_alt  + ".prj",pfadstring + dateistring + ".prj")
        if os.path.exists(pfadstring + dateistring_alt  + ".ind"):
            os.rename(pfadstring + dateistring_alt  + ".ind",pfadstring + dateistring + ".ind")
        if os.path.exists(pfadstring + dateistring_alt  + ".idm"):
            os.rename(pfadstring + dateistring_alt  + ".idm",pfadstring + dateistring + ".idm")
        if os.path.exists(pfadstring + dateistring_alt  + ".ain"):
            os.rename(pfadstring + dateistring_alt  + ".ain",pfadstring + dateistring + ".ain")
        if os.path.exists(pfadstring + dateistring_alt  + ".aih"):
            os.rename(pfadstring + dateistring_alt  + ".aih",pfadstring + dateistring + ".aih")
        if os.path.exists(pfadstring + dateistring_alt  + ".ixs"):
            os.rename(pfadstring + dateistring_alt  + ".ixs",pfadstring + dateistring + ".ixs")
        if os.path.exists(pfadstring + dateistring_alt  + ".mxs"):
            os.rename(pfadstring + dateistring_alt  + ".mxs",pfadstring + dateistring + ".mxs")
        if os.path.exists(pfadstring + dateistring_alt  + ".xml"):
            os.rename(pfadstring + dateistring_alt  + ".xml",pfadstring + dateistring + ".xml")
        if os.path.exists(pfadstring + dateistring_alt  + ".cpg"):
            os.rename(pfadstring + dateistring_alt  + ".cpg",pfadstring + dateistring + ".cpg")

        #arcgis Attributindex Dateien
        #glob liefert eine liste mit Pfadnamen zurück
        atxes = glob.glob(pfadstring + dateistring_alt + ".*.atx")
        for atx in atxes:
            if os.path.exists(atx):
                #Wegen der gleichen Gross/Kleinschreibung wie in
                # outputname angegeben!!!!!!!!
                atx_suffix = os.path.splitext(atx)
                atx_suffix = os.path.splitext(atx_suffix[0])[1] + atx_suffix[1]
                os.rename(atx,pfadstring + dateistring  + atx_suffix)
                #print atx

        return True
    except:
        return False

################################################
#Umcodieren der Eingangstabelle, falls gewünscht
#geht nur bei DBF Dateien, also Tabellen aus
#Dbase und Shapes: die codierung
#kommt aus der Steuertabelle
################################################

def umcodieren(inputpfad,inputname,codierung,log_attribgesch):

    #codierung = 'latin1'
    try:
        #Umcodieren der CSV datei nach UTF8
        #falls notwendig
        if (inputname.find('.csv') > -1):
            f = open(inputpfad + "/" + inputname,'r+')
            data = f.read()
            #inhalt = data.decode('CP850')
            inhalt = data.decode(codierung) # Typ als String übergeben
            f.truncate(0)
            f.seek(0)
            f.write(inhalt.encode('UTF-8'))
            f.close()
        #Umcodieren der DBASE datei nach UTF8
        #falls notwendig
        elif (inputname.find('.dbf') > -1):
            #Dbase Objekt instanzieren
            db = Dbf(inputpfad + "/" + inputname)

            # gibts ein cpg file MUSS das genommen werden
            if os.path.exists(inputpfad + '/' + inputname.replace('.dbf','.cpg')):
                f = open(inputpfad + "/" + inputname.replace('.dbf','.cpg'),'r')
                codierung = f.read().split()    # sollte nur die codierung drinstehen, sicherheitshalber nehmen wir nur das erste wort


            # die Zeilen des DBFs durchgehen
            zeilen = 0
            for rec in db:
                recdic = rec.asDict()
                for rec2 in recdic: # die felder des record durchgehen
                    feldname = ""
                    dummy = ""

                    #Wenn ein Feld ein Stringtyp ist
                    #werden diese umcodiert
                    if type(recdic[rec2]) == str:
                        feldname = rec2

                        dummy = rec[feldname].decode(codierung) # in eine Bytestring umwnadeln: Die richtige Codierung muss bekannt sein
                        rec[feldname] = dummy.encode('utf8')    # dann nach UTF-8 codieren

                        # Länge des feldes aus den Felddefinitionen bestimmen.
                        # ACHTUNG: Beim Umcodieren von windows codepage (latin1 oder cp1252), in der alle Zeichen nur 1 Byte haben,
                        # nach UTF-8 (in der die Sonderzeichen 2 Byte oder mehr haben) wird natürlich der gesamte String größer.
                        # Da kann es sein, dass er nicht mehr in das DBASE Feld passt, und Zeichen abgeschnitten werden. Blöd ist nur,
                        # wenn das letzte Zeichen ein 2 Byte Zeichen ist, von dem die Hälfte wegkommt. Da entsteht ein Krakel, der
                        # nicht in die Datenbank kopiert werden kann.
                        for defi in db.fieldDefs:

                            if feldname  == defi.name:

                                if defi.length < len(rec[feldname] ):
                                    logroutine(log_attribgesch,'Attribut abgeschnitten: ' + inputpfad + '/' + inputname + ' Spalte: ' + feldname +  ' Zeile: ' + str(zeilen) + '\r' , False)
                                    rec[feldname] = rec[feldname][0:defi.length-1]  # wir müssen 1 Byte mehr abschneiden, da Ös etc. ja zwei Byte haben können, und theoretisch davon 1 Byte abgeschnitten werden könnte was einen Krakel als Resultat hat

                        rec.store() # Speichern nicht vergessen!
                zeilen = zeilen + 1
                del rec
            db.close()
            del db
        else:
            return False    #Falsche Datei?
        return True #Kein Fehler
    except:
        return False    #Es hat einen Fehler gegeben



###########################################
#Diese Funktion löscht eine Shapedatei
#inkl. aller dazugehörenden Dateien auf
#Fileebene
###########################################
def shapeLoeschen(pfadstring,dateistring):

    try:
        pfadstring = pfadstring + "/"

        if os.path.exists(pfadstring + dateistring + ".shp"):
            os.remove(pfadstring + dateistring + ".shp")
        if os.path.exists(pfadstring + dateistring + ".shp.xml"):
            os.remove(pfadstring + dateistring + ".shp.xml")
        if os.path.exists(pfadstring + dateistring + ".dbf"):
            os.remove(pfadstring + dateistring + ".dbf")
        if os.path.exists(pfadstring + dateistring + ".sbn"):
            os.remove(pfadstring + dateistring + ".sbn")
        if os.path.exists(pfadstring + dateistring + ".sbx"):
            os.remove(pfadstring + dateistring + ".sbx")
        if os.path.exists(pfadstring + dateistring + ".fbn"):
            os.remove(pfadstring + dateistring + ".fbn")
        if os.path.exists(pfadstring + dateistring + ".fbx"):
            os.remove(pfadstring + dateistring + ".fbx")
        if os.path.exists(pfadstring + dateistring + ".shx"):
            os.remove(pfadstring + dateistring + ".shx")
        if os.path.exists(pfadstring + dateistring + ".qix"):
            os.remove(pfadstring + dateistring + ".qix")
        if os.path.exists(pfadstring + dateistring + ".prj"):
            os.remove(pfadstring + dateistring + ".prj")
        if os.path.exists(pfadstring + dateistring + ".ind"):
            os.remove(pfadstring + dateistring + ".ind")
        if os.path.exists(pfadstring + dateistring + ".idm"):
            os.remove(pfadstring + dateistring + ".idm")
        if os.path.exists(pfadstring + dateistring + ".ain"):
            os.remove(pfadstring + dateistring + ".ain")
        if os.path.exists(pfadstring + dateistring + ".aih"):
            os.remove(pfadstring + dateistring + ".aih")
        if os.path.exists(pfadstring + dateistring + ".ixs"):
            os.remove(pfadstring + dateistring + ".ixs")
        if os.path.exists(pfadstring + dateistring + ".mxs"):
            os.remove(pfadstring + dateistring + ".mxs")
        if os.path.exists(pfadstring + dateistring + ".xml"):
            os.remove(pfadstring + dateistring + ".xml")
        if os.path.exists(pfadstring + dateistring + ".cpg"):
            os.remove(pfadstring + dateistring + ".cpg")


        #arcgis Attributindex Dateien
        #glob liefert eine liste mit Pfadnamen zurück
        atxes = glob.glob(pfadstring + dateistring  + ".*.atx")
        for atx in atxes:
            if os.path.exists(atx):
                os.remove(atx)
                #print atx
        return True

    except:
        return False



###########################################
#Diese Funktion löscht eine Datei
#inkl. aller dazugehörenden Dateien auf
#Fileebene
###########################################
def dateiLoeschen(pfadstring,dateistring):

    try:
        pfadstring = pfadstring + "/"

        #normale dateien
        if os.path.exists(pfadstring + dateistring):
            os.remove(pfadstring + dateistring)


        #nun noch zwei ausnahmen, weil ja im Windows die Suffix die dateien trennt
        #müssen wir das so machen, weill mit * würden vielleicht auch pdf oder andere mitgelöscht

        #dbase indexdateien
        if (dateistring.find('.dbf') > -1):

            if os.path.exists(pfadstring + '/' + dateistring.replace('.dbf','.idm')):
                os.remove(pfadstring + dateistring.replace('.dbf','.idm'))
            if os.path.exists(pfadstring + '/' + dateistring.replace('.dbf','.ind')):
                os.remove(pfadstring + dateistring.replace('.dbf','.ind'))

        #csv templatedatei
        if (dateistring.find('.csv') > -1):

            if os.path.exists(pfadstring + '/' + dateistring.replace('.csv','.csvt')):
                os.remove(pfadstring + dateistring.replace('.csv','.csvt'))



        return True


    except:
        return False



#WIRD nicht verwendet
def formale_pruefung(inputpfad,outputpfad,ds_neu):


    try:
        fehlertext = ''
        dir_eingang = os.path.dirname(inputpfad)
        datei_eingang = os.path.basename(inputpfad)


        if not datei_eingang == datei_ausgang:
            fehlertext = ' Ein- und Ausgangsdatei haben unterschiedliche Namen'

        if os.access(inputpfad, os.F_OK and os.R_OK and os.W_OK):
            f = 3


        if alt_neu == 'nein':
            dir_ausgang = os.path.dirname(outputpfad)
            datei_ausgang = os.path.basename(outputpfad)



        print 'Depp'
        if os.access(pfad, os.F_OK and os.R_OK and os.W_OK):
            return True
        else:
            return False

    except:
        return 'Fehler in Routine formale_pruefung'