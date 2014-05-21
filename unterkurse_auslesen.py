#!/usr/bin/env python
# coding: utf8

import sys
import csv
import os

def finde_defizite(datei, notenskala):
    # Notenliste laden
    dateipfad, dateiname = os.path.split(datei)
    datei = csv.reader(open(datei),delimiter=';')

    noten=[] # beinhaltet die Notenübersicht aus der csv-Datei
    faecher={} # beinhaltet die Spaltennummer mit zug. Fach
    schueler=[] # beinhaltet alle Schüler, die jeweils eine Zeile in der cvs-Datei sind
    schueler_mit_unterkursen={} # nur für Schüler, die Unterkurse/Defizite aufweisen
    # Notenskalen (str, weil die Dateien so ausgelesen werden und sonst 'XX' mitgelesen würden)
    skala={'Noten':[str(i) for i in range(1,7)],'Punkte':[str(i) for i in range(0,16)]}
    defizit= {'Noten':range(5,7),'Punkte':range(0,5)}
    convert={'0':'6','1':'5-','2':'5','3':'5+','4':'4-','5':'5','6':'6'}

    # Eintragungen in der Datei werden in eine Liste geschrieben, 
    # jedes Element ist eine Zeile
    for eintrag in datei:
        noten.append(eintrag)

    # erstellt ein dict mit spaltennummer -> fach
    for i,fach in enumerate(noten[0]):
        #faecher[i]=fach.split(' ')[0]
        faecher[i]=fach

    # durchsucht jeden Schüler nach Defiziten und schreibt die Schüler
    # in ein dict mit (Name,Vorname) -> Liste mit Fach, Note
    for schueler in noten[2:]:			
        for i, note in enumerate(schueler[5:]): # die ersten 5 einträge sind nicht relevant
            if note in skala[notenskala] and int(note) in defizit[notenskala]:
                # Schueler erstmalig anlegen:
                if (schueler[0], schueler[1]) not in schueler_mit_unterkursen.keys():
                    schueler_mit_unterkursen[(schueler[0], schueler[1])] = [faecher[i+5] + ' ' + convert[note]]
                else:
                    schueler_mit_unterkursen[(schueler[0], schueler[1])].append(faecher[i+5] + ' ' + convert[note])

    # Ausgabedatei öffnen 
    datei_aus = csv.writer(open(os.path.join(dateipfad,os.path.splitext(dateiname)[0])+'_defizite.csv', 'wb'), delimiter=';')

    # Eintragen der Schüler in die Datei
    for schueler in sorted(schueler_mit_unterkursen.keys(), key=lambda schueler: schueler[0]):
        datei_aus.writerow([schueler[0],schueler[1]]+[kurs for kurs in schueler_mit_unterkursen[schueler]])

if __name__=="__main__":
    finde_defizite(sys.argv[1],sys.argv[2])




