#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------
# Dateiname: klausurplan_erzeugen.py
# Version: 0.1
# Funktion: Wandelt die eingegeben CVS-Datei in eine lesbare um
# Autor: Boris Pohler
# Datum der letzten Änderung: 18.2.2011
# umgeschrieben zum Einbinden in helferlein
# -------------------------------------------------

#TODO: Zuordnung der Kurse noch auf die Jgst beziehen.

import os
import sys
import time
import codecs
from kurse_einlesen import kurse_einlesen
reload(sys)
sys.setdefaultencoding('utf-8')

def konvertiere(datei):
    dateipfad, dateiname = os.path.split(datei)
    wochentag_dict={'Mon':'Mo','Tue':'Di','Wed':'Mi','Thu':'Do','Fri':'Fr','Sat':'Sa','Sun':'So'}
    zuordnung = kurse_einlesen()
    #print zuordnung.keys()
    klausuren=[]

    #liste füllen
    # daten haben die struktur Datum;Von;Bis;Name;Text;Kurs;Studt;Lehrer;Räume;Klassen
    with codecs.open(datei,'r','iso-8859-1') as zeilen:
        for zeile in zeilen:
            liste = zeile.split(';')  # trennt nach Semikolon und liefert eine Liste
            liste[8]=liste[8][:4] # nimmt nur die ersten 4 Zeichen der Raumbelegung
            liste[7]=liste[7].split(' - ') # trennt die einzelnen Aufsichten in eine Liste auf
            del liste[3],liste[5]
            #print liste
            klausuren.append(liste) # fügt die Klausur der Liste hinzu
        del klausuren[0] # löscht die Kopfzeile aus der Vorlage

    # hier wird eine zeile als liste übergeben und umgewandelt
    # daten haben die struktur Datum;Von;Bis;Text;Kurs;Lehrer;Räume;Klassen
    def zeileUmwandeln(datum0,liste):
        #print liste
        datum1 = liste[0]
        kurs = liste[4]
        klasse = liste[7][:3]  #Sonst wird das Steuerzeichen \n mitgenommen
        #print klasse, type(klasse)
        wochentag = wochentag_dict[time.strftime("%a",time.strptime(datum1,"%d.%m.%Y"))] #gibt den wochentag von datum1 aus
        # Achtung, in dem Orginal-Skript wurde noch das dict wochentag_dict benötigt
        if liste[5][0][:3]=='GVS':
            fachlehrer ='GVS'
        elif liste[5][0]=='':
            fachlehrer = 'NN'
        else:
            #alte Version ohne direkte Zuordnung (erste Aufsicht wurde genommen, schlecht)
            #fachlehrer = liste[5][0]
            # neue Version (dict mit zuordnung stufe -> kurs -> lehrer
            #print kurs, klasse, zuordnung[klasse]
            if kurs in zuordnung[klasse]:
                #print "Kurs gefunden"
                #print kurs, zuordnung[klasse][kurs]
                fachlehrer = zuordnung[klasse][kurs]
            else:
                print kurs, "nicht gefunden"
                fachlehrer = liste[5][0]
        stundeA = int(liste[1])
        stundeE = int(liste[2])
        #kurs = liste[4]
        aufsichten = ''
        if fachlehrer == 'GVS' or fachlehrer == 'NN':
            aufsichten=';;;;;;'
        else: 
            for i in range(1,stundeA):
                aufsichten = aufsichten+';'
            for lehrer in liste[5]:
                aufsichten = aufsichten+lehrer+';'
            for i in range(1,7-stundeE):
                aufsichten = aufsichten+';'
        if liste[6] == '':
            raum = 'NN'
        else:
            raum = liste[6]
        stufe = liste[7]
        bemerkungen = liste[3]
        if datum0 == datum1:
            return ';;'+kurs+';'+ fachlehrer +';'+raum+';'+aufsichten+';'+stufe
        else:
            return wochentag+';'+ datum1 +';'+kurs+';'+fachlehrer+';'+raum+';'+aufsichten+bemerkungen+';'+stufe

    #ausgabe in eine neue csv-Datei
    with codecs.open(os.path.join(dateipfad,os.path.splitext(dateiname)[0])+'_konvertiert.csv','w','iso-8859-1') as outfile:
        datum = ''
        # Kopfzeilen
        outfile.write('Klausurplan;;;;;;;;;;;;\n')
        outfile.write('Wochentag;Datum;Kurs;Fachl.;Raum;Aufsicht in Stunde;;;;;;Bemerkungen;Klassen\n')
        outfile.write(';;;;;1;2;3;4;5;6;;\n')
        # Klausuren
        for klausur in klausuren:
            #print datum, klausur[0]
            #print zeileUmwandeln(datum,klausur)
            outfile.write(zeileUmwandeln(datum,klausur))
            datum = klausur[0]

if __name__=="__main__":
    konvertiere(sys.argv[1])


