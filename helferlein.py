#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Importe
import sys
import os
import codecs
import pickle
import sip
from PyQt4.QtGui import QPrinter, QTextDocument
from PyQt4.QtSql import (QSqlDatabase, QSqlQuery, QSqlQueryModel)
from PyQt4 import Qt, QtGui, QtCore, uic

from unterkurse_auslesen import finde_defizite
from klausurplan_erzeugen import konvertiere

#sip.setapi('QDate', 2)
import time

reload(sys)
sys.setdefaultencoding('utf-8')


# Klassen für die Dialoge:
class Dialog_Tabelle(QtGui.QWidget):
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.ui = uic.loadUi("ui_dialog_tabelle.ui")
        self.ui.show()

    def drucken(self):  # für später
        printer = QPrinter()
        printer.setPaperSize(QPrinter.A5)

        doc = QTextDocument('Ich bin ein Text.')
        doc.print_(printer)

class Dialog_Schueler_Anlegen(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self,parent)
        self.ui = uic.loadUi("ui_dialog_schueler_anlegen.ui")


# Klasse für das Hauptfenster
class Helferlein(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        # Oberfläche abbilden:      
        self.ui = uic.loadUi("ui_helferlein.ui")
        self.ui.setWindowIcon(QtGui.QIcon('helferlein.png'))
        #self.db = QSqlDatabase.addDatabase("QMYSQL")
        self.db = QSqlDatabase.addDatabase("QSQLITE3")
        self.db.setHostName("localhost")
        self.db.setDatabaseName("helferlein")
        self.user = "root"
        self.password = "*****"
        if self.db.open(self.user, self.password):
            print "DB Verbindung"
            #self.init_db()
        else:
            print "Verbindung konnte nicht hergestellt werden"
        self.sql_model_namensliste = QSqlQueryModel(self)
        self.sql_model_fehlzeiten = QSqlQueryModel(self)
        self.ui.tableView_schuelernamen.setModel(self.sql_model_namensliste)
        self.ui.tableView_fehlzeiten.setModel(self.sql_model_fehlzeiten)


        # Argumente übergeben
        if len(sys.argv) > 1:
            self.filename = sys.argv[1]
            f = open(self.filename,'rb')
   	    self.schuelerliste = pickle.load(f)
            f.close()
            for schueler in self.schuelerliste.values():
                self.ui.listWidget.addItem(schueler.name + ', ' + schueler.vorname)
                self.ui.listWidget.sortItems(0)
        else:
            self.filename = ''
            self.schuelerliste = {}

        # Grundeinstellungen:
        self.ui.dateEdit.setDate(QtCore.QDate.currentDate())
        self.ui.dateEdit_2.setDate(QtCore.QDate.currentDate())
        self.ui.dateEdit_3.setDate(QtCore.QDate.currentDate())
        self.ui.dateEdit_4.setDate(QtCore.QDate.currentDate())
        self.ui.comboBox_stufenwahl.currentIndexChanged.connect(self.stufenwahl)
        self.ui.show()

        # Connects:
        # Menü
        self.ui.actionStufe_importieren.triggered.connect(self.stufe_importieren)
        self.ui.action_ffnen.triggered.connect(self.datei_oeffnen)
        self.ui.actionSpeichern.triggered.connect(self.datei_speichern)
        self.ui.actionSpeichern_unter.triggered.connect(self.datei_speichern_unter)
        self.ui.actionSch_ler_l_schen.triggered.connect(self.schueler_loeschen)
        self.ui.actionSch_ler_hinzuf_gen.triggered.connect(self.schueler_anlegen)    
        self.ui.actionKrankmeldungen.triggered.connect(self.zeige_krankmeldungen)
        self.ui.actionBeurlaubungen.triggered.connect(self.zeige_beurlaubungen)
        self.ui.actionKlausur_Attest.triggered.connect(self.zeige_klausur_attest)
        self.ui.actionDefizite_suchen.triggered.connect(self.suche_defizite)
        self.ui.actionKlausurplan_konvertieren.triggered.connect(self.klausurplan_konvertieren)

        self.ui.tableView_schuelernamen.activated.connect(self.schueler_auswahl)
        self.ui.tableView_schuelernamen.clicked.connect(self.schueler_auswahl)
        self.ui.lineEdit.textChanged.connect(self.suche)
        self.ui.pushButton_7.clicked.connect(self.heutiges_datum_setzen)
        
        # Krankmeldungen
        self.ui.pushButton.clicked.connect(self.krankmeldung_speichern)
        self.ui.lineEdit_2.returnPressed.connect(self.krankmeldung_speichern)
        self.ui.pushButton_4.clicked.connect(self.eintrag_loeschen_krank)
        self.ui.tableView_fehlzeiten.clicked.connect(self.krankmeldung_aufrufen)

        # Beurlaubungen
        self.ui.pushButton_2.clicked.connect(self.beurlaubung_speichern)
        self.ui.lineEdit_3.returnPressed.connect(self.beurlaubung_speichern)
        self.ui.pushButton_5.clicked.connect(self.eintrag_loeschen_beurlaubung)
        self.ui.tableWidget_2.cellClicked.connect(self.beurlaubung_aufrufen)

        # Bemerkungen
        self.ui.pushButton_3.clicked.connect(self.bemerkung_speichern)
        #self.ui.lineEdit_4.returnPressed.connect(self.bemerkung_speichern)
        self.ui.pushButton_6.clicked.connect(self.eintrag_loeschen_bemerkung)
        self.ui.tableWidget_3.cellClicked.connect(self.bemerkung_aufrufen)

        self.ui.calendarWidget.selectionChanged.connect(self.datum_geaendert)

        #self.ui.tableWidget.cellChanged.connect(self.zeile_geaendert_krank)

    # DB-Methoden ###############################################################

    def init_db(self):
        print "here"
        sql_query = QSqlQuery('''SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA 
                                 WHERE SCHEMA_NAME = 'helferlein';''', self.db)
        size = sql_query.size()
        print size
        if size == 0:
            print "db anlegen"
            sql_query = QSqlQuery("CREATE DATABASE helferlein;", self.db)
            print "tabelle schueler anlegen"
            sql_query = QSqlQuery('''CREATE TABLE SCHUELER (
               id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
               Name CHAR(100),
               Vorname CHAR(100),
               Stufe CHAR(2));''', self.db)
            print "tabelle fehlzeit anlegen"
            sql_query.prepare('''CREATE TABLE FEHLZEIT (
               id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
               schueler_id INT,
               Grund CHAR(100),
               Beginn CHAR(10),
               Ende CHAR(10),
               Stunden INT,
               ist_Beurlaubung INT,
               Attest INT,
               klausur_verpasst INT,
               Schuljahr CHAR(10));''')
            sql_query.exec_()            
       
    def create_db(self):
        self.db.setDatabaseName(FILENAME_DB)
        ok = self.db.open()
        if ok:
            sql_query = QSqlQuery()
            

    # Menü-Methoden:
    def stufe_importieren(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, u'CVS-Datei öffnen','.')
        namens_liste = [[col.strip() for col in row.split(";")] 
                   for row in codecs.open(filename, encoding="iso-8859-15")]
        sql_query = QSqlQuery()
        sql_query.prepare('''INSERT INTO SCHUELER(NAME, VORNAME, STUFE)
                                 VALUES(:name,:vorname,:stufe)''')
        for name, vorname, stufe in namens_liste:          
            sql_query.bindValue(':name',name)
            sql_query.bindValue(':vorname', vorname)
            sql_query.bindValue(':stufe', stufe)
            sql_query.exec_()

    def datei_oeffnen(self):
        self.filename = QtGui.QFileDialog.getOpenFileName(self, u'Datei öffnen','.')
        f = open(self.filename,'rb')
   	self.schuelerliste = pickle.load(f)
        f.close()

        self.ui.listWidget.clear()
        for schueler in self.schuelerliste.values():
            self.ui.listWidget.addItem(schueler.name + ', ' + schueler.vorname)
        self.ui.listWidget.sortItems(0)

    def datei_speichern(self):
        f = open(self.filename,'wb')
   	pickle.dump(self.schuelerliste,f)
        f.close()

    def datei_speichern_unter(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, u'Namen der Datei angeben','.')
        f = open(filename,'wb')
   	pickle.dump(self.schuelerliste,f)
        f.close()

    def schueler_loeschen(self):
        if self.ui.label_3.text():
            name, vorname = self.ui.label_3.text().split(', ')
            reply = QtGui.QMessageBox.question(self, "Achtung!",
                         "Soll %s, %s wirklich gelöscht werden?" % (name,vorname),
                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                del self.schuelerliste[(vorname,name)]
                self.ui.listWidget.clear()
                for schueler in self.schuelerliste.values():
                    self.ui.listWidget.addItem(schueler.name + ', ' + schueler.vorname)
                    self.ui.listWidget.sortItems(0)
                self.datei_speichern()
                self.ui.label_3.setText("")
                self.ui.label_10.setText("")
                self.ui.label_16.setText("")

        else: 
             MESSAGE = u"<p>Bitte erst einen Schüler aus der Liste auswählen</p>"
             reply = QtGui.QMessageBox.information(self,
                "Achtung!", MESSAGE)
            
    def schueler_anlegen(self):
        dialog_anlegen = Dialog_Schueler_Anlegen(self)
        dialog_anlegen.ui.setWindowTitle(u'Schüler/in hinzufügen')
        if dialog_anlegen.ui.exec_() == 1:
            name = dialog_anlegen.ui.lineEdit_name.text()
            vorname = dialog_anlegen.ui.lineEdit_vorname.text()              
            stufe = dialog_anlegen.ui.spinBox_stufe.value() 
            schueler = Schueler(vorname, name, stufe)
            if schueler not in self.schuelerliste:
                self.schuelerliste[(vorname, name)] = schueler
                self.ui.listWidget.clear()
                for schueler in self.schuelerliste.values():
                    self.ui.listWidget.addItem(schueler.name + ', ' + schueler.vorname)
                    self.ui.listWidget.sortItems(0)
                self.datei_speichern()
                self.ui.label_3.setText("")
                self.ui.label_10.setText("")
                self.ui.label_16.setText("")
            
  
    # Fenster-Methoden:
    def stufenwahl(self, index):
        print "stufenwahl", index
        query = '''SELECT id, Name, Vorname FROM SCHUELER 
                   WHERE Stufe='{}' ORDER BY Name;'''.\
                   format(self.ui.comboBox_stufenwahl.itemText(index))
        print query
        sql_query = QSqlQuery(query)
        self.sql_model_namensliste.setQuery(sql_query)
        sql_query.exec_()
        self.ui.tableView_schuelernamen.hideColumn(0) #don't show id

    def schueler_auswahl(self, index):
        self.schueler_id = index.sibling(index.row(),0).data().toString()
        name = index.sibling(index.row(),1).data().toString()
        vorname = index.sibling(index.row(),2).data().toString()
        self.ui.label_3.setText(u'{}, {}'.format(name, vorname))
        self.ui.label_10.setText(u'{}, {}'.format(name, vorname))
        self.ui.label_16.setText(u'{}, {}'.format(name, vorname))
        self.tabelle_krank_aktualisieren()

    def heutiges_datum_setzen(self):
        self.ui.calendarWidget.setSelectedDate(QtCore.QDate.currentDate())    

    def tabelle_krank_aktualisieren(self):
        query_string = '''SELECT id, Beginn, Ende, Attest, klausur_verpasst
                          as Klausur, Grund FROM FEHLZEIT 
                          WHERE FEHLZEIT.schueler_id={} AND ist_beurlaubung = '0';
                       '''.format(self.schueler_id)
        print query_string
        sql_query = QSqlQuery(query_string)
        self.sql_model_fehlzeiten.setQuery(sql_query)
        self.ui.tableView_fehlzeiten.hideColumn(0) #don't show id
        sql_query.exec_()
        self.ui.tableView_fehlzeiten.resizeColumnsToContents()
        self.ui.tableView_fehlzeiten.horizontalHeader().setStretchLastSection(True)

    def tabelle_beurlaubung_aktualisieren(self,schueler):
        self.ui.tableWidget_2.setRowCount(len(schueler.beurlaubungen.keys()))
        zeile = 0
        for eintrag in sorted(schueler.beurlaubungen.keys(),reverse=True):
            liste = schueler.beurlaubungen[eintrag]
            liste0 = [eintrag.toString("dd.MM.yyyy"), 
                      liste[0].toString("dd.MM.yyyy"),
                      str(liste[1]), 
                      liste[2]]
            for spalte in range(4):
               item = QtGui.QTableWidgetItem(liste0[spalte])
               self.ui.tableWidget_2.setItem(zeile, spalte, item);
            zeile += 1
        self.ui.tableWidget_2.resizeColumnsToContents()
        self.ui.tableWidget_2.horizontalHeader().setStretchLastSection(True)

    def tabelle_bemerkung_aktualisieren(self,schueler):
        self.ui.tableWidget_3.setRowCount(len(schueler.bemerkungen.keys()))
        zeile = 0
        for eintrag in sorted(schueler.bemerkungen.keys(),reverse=True):
            aktennotiz = ('ja' if schueler.bemerkungen[eintrag][1] else 'nein')
            bemerkung = schueler.bemerkungen[eintrag][0] 
            liste0 = [eintrag.toString("dd.MM.yyyy"),aktennotiz, bemerkung]
            for spalte in range(3):
               item = QtGui.QTableWidgetItem(liste0[spalte])
               self.ui.tableWidget_3.setItem(zeile, spalte, item);
            zeile += 1
        self.ui.tableWidget_3.resizeColumnsToContents()
        self.ui.tableWidget_3.horizontalHeader().setStretchLastSection(True)
        self.ui.plainTextEdit.clear()
        
    def ui_zuruecksetzen(self):
        self.ui.lineEdit.clear()
        self.ui.lineEdit_2.clear()
        self.ui.lineEdit_3.clear()
        #self.ui.lineEdit_4.clear()
        self.ui.plainTextEdit.clear()
        self.ui.checkBox.setChecked(False)
        self.ui.checkBox_2.setChecked(False)
        self.ui.checkBox_3.setChecked(False)
        self.ui.spinBox.setValue(0)
        self.ui.calendarWidget.setSelectedDate(QtCore.QDate.currentDate())
    
    def suche(self,text):
        self.ui.listWidget.clear()
        for schueler in self.schuelerliste:
            if schueler[0].contains(text,0) or schueler[1].contains(text,0):
                s = self.schuelerliste[schueler]
                self.ui.listWidget.addItem(s.name + ', ' + s.vorname)
        self.ui.listWidget.sortItems(0)

    def datum_geaendert(self):
        datum_aktuell = self.ui.calendarWidget.selectedDate()
        self.ui.dateEdit.setDate(datum_aktuell)
        self.ui.dateEdit_2.setDate(datum_aktuell)
        self.ui.dateEdit_3.setDate(datum_aktuell)
        self.ui.dateEdit_4.setDate(datum_aktuell)

    def krankmeldung_speichern(self):
        self.schuljahr = '2013/14'
        datum_von = self.ui.dateEdit.date().toString("dd.MM.yyyy")
        datum_bis = self.ui.dateEdit_2.date().toString("dd.MM.yyyy")
        grund = (unicode(self.ui.lineEdit_2.text()) if self.ui.lineEdit_2.text() else u'-')
        attest = (u'ja' if self.ui.checkBox.isChecked() else u'nein')
        klausur = (u'ja' if self.ui.checkBox_2.isChecked() else u'nein')
        sql_query = QSqlQuery()
        query_string = '''INSERT INTO FEHLZEIT (schueler_id, Grund, Beginn, 
                             Ende, Attest, klausur_verpasst, ist_beurlaubung, schuljahr)
                             VALUES({},'{}','{}','{}','{}','{}','0','{}');'''.format(self.schueler_id,
                             grund, datum_von, datum_bis, attest, klausur, self.schuljahr)
        #print query_string
        sql_query.prepare(query_string)
        sql_query.exec_()
        self.ui_zuruecksetzen()
        self.tabelle_krank_aktualisieren()

    def eintrag_loeschen_krank(self):
        selected_items = self.ui.tableView_fehlzeiten.selectionModel().selection().indexes()
        if selected_items:
            index = selected_items[0]
            zeile = index.row()
            fehlzeit_id = index.sibling(zeile,0).data().toString()
            reply = QtGui.QMessageBox.question(self, "Achtung!",
                         u"Soll die markierte Zeile wirklich gelöscht werden?",
                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                print "Zeile löschen", fehlzeit_id
                sql_query = QSqlQuery('''DELETE FROM FEHLZEIT
                                         WHERE id = {}'''.format(fehlzeit_id))
                sql_query.exec_()
                self.tabelle_krank_aktualisieren()
        else:
            QtGui.QMessageBox.information(self, "Achtung!", "Bitte erst eine Zeile markieren!")

    def krankmeldung_aufrufen(self,index):
        zeile = index.row()
        sql_record = self.sql_model_fehlzeiten.record(zeile) 
        beginn = sql_record.value('Beginn').toString()
        ende = sql_record.value('Ende').toString()
        attest = sql_record.value('Attest').toString() == 'ja'
        klausur = sql_record.value('Klausur').toString() == 'ja'
        grund = sql_record.value('Grund').toString()
        self.ui.dateEdit.setDate(QtCore.QDate.fromString(beginn,"dd.MM.yyyy"))
        self.ui.dateEdit_2.setDate(QtCore.QDate.fromString(ende,"dd.MM.yyyy"))
        self.ui.checkBox.setChecked(attest)
        self.ui.checkBox_2.setChecked(klausur)
        self.ui.lineEdit_2.setText(grund)

    def beurlaubung_speichern(self):
        name, vorname = self.ui.label_10.text().split(', ')
        schueler = self.schuelerliste[(vorname,name)]
        datum_von = self.ui.dateEdit_3.date()
        datum_bis = self.ui.dateEdit_4.date()
        grund = (self.ui.lineEdit_3.text() if self.ui.lineEdit_3.text() else u'-')
        anzahl_stunden = self.ui.spinBox.value()
        schueler.beurlaubungen[datum_von]=[datum_bis,anzahl_stunden,grund]
        self.ui_zuruecksetzen()
        self.tabelle_beurlaubung_aktualisieren()
        self.datei_speichern()

    def beurlaubung_aufrufen(self,zeile,spalte):
        self.ui.dateEdit_3.setDate(QtCore.QDate.fromString(self.ui.tableWidget_2.item(zeile,0).text(),"dd.MM.yyyy"))
        self.ui.dateEdit_4.setDate(QtCore.QDate.fromString(self.ui.tableWidget_2.item(zeile,1).text(),"dd.MM.yyyy"))
        self.ui.spinBox.setValue(int(self.ui.tableWidget_2.item(zeile,2).text()))
        self.ui.lineEdit_3.setText(self.ui.tableWidget_2.item(zeile,3).text())

    def bemerkung_speichern(self):
        name, vorname = self.ui.label_16.text().split(', ')
        schueler = self.schuelerliste[(vorname,name)]
        datum = self.ui.calendarWidget.selectedDate()
        bemerkung = self.ui.plainTextEdit.document().toPlainText()
        if not bemerkung:
           QtGui.QMessageBox.information(self,u"Achtung!", u"Bitte erst eine Bemerkung eingeben!")
        else:
            schueler.bemerkungen[datum]=[bemerkung,self.ui.checkBox_3.isChecked()]
            self.tabelle_bemerkung_aktualisieren(schueler)
            self.datei_speichern()
            if self.ui.checkBox_3.isChecked():
                printer = QtGui.QPrinter()
                printer.setPaperSize(QtGui.QPrinter.A4)
                kopfzeile = u'Aktennotiz von ' + vorname + ' ' + name + u' am ' + datum.toString("dd.MM.yyyy") + ':\n\n'
                #kopfzeile = u'<b>Aktennotiz von ' + vorname + ' ' + name + u' am ' + datum.toString("dd.MM.yyyy") + ':</b><br /><br />'
                doc = QtGui.QTextDocument(kopfzeile + bemerkung)
                #doc.setHtml(kopfzeile + bemerkung)
                doc.print_(printer)
            self.ui_zuruecksetzen()

    def bemerkung_aufrufen(self,zeile,spalte):
        #print zeile, spalte
        self.ui.calendarWidget.setSelectedDate(QtCore.QDate.fromString(self.ui.tableWidget_3.item(zeile,0).text(),"dd.MM.yyyy"))
        self.ui.plainTextEdit.setPlainText(self.ui.tableWidget_3.item(zeile,2).text())
        if self.ui.tableWidget_3.item(zeile,1).text()=='ja':
            self.ui.checkBox_3.setChecked(True)
        else:
            self.ui.checkBox_3.setChecked(False)
            

    def eintrag_loeschen_beurlaubung(self):
        name, vorname = self.ui.label_10.text().split(', ')
        schueler = self.schuelerliste[(vorname,name)]
        i, ok = QtGui.QInputDialog.getInteger(self,
                u"Zeile löschen", u"Welche Zeile soll gelöscht werden?",1,1 ,len(schueler.beurlaubungen.keys()), 1)
        if ok:
            datum = QtCore.QDate.fromString(self.ui.tableWidget_2.item(i-1,0).text(),"dd.MM.yyyy")
            del schueler.beurlaubungen[datum]
            self.tabelle_beurlaubung_aktualisieren(schueler)
            self.datei_speichern()

    def eintrag_loeschen_bemerkung(self):
        name, vorname = self.ui.label_16.text().split(', ')
        schueler = self.schuelerliste[(vorname,name)]
        i, ok = QtGui.QInputDialog.getInteger(self,
                u"Zeile löschen", u"Welche Zeile soll gelöscht werden?",1,1 ,len(schueler.bemerkungen.keys()), 1)
        if ok:
            datum = QtCore.QDate.fromString(self.ui.tableWidget_3.item(i-1,0).text(),"dd.MM.yyyy")
            del schueler.bemerkungen[datum]
            self.tabelle_bemerkung_aktualisieren(schueler)
            self.datei_speichern()

    def zeile_geaendert_krank(self,zeile,spalte):
        print self.ui.tableWidget.item(zeile,spalte).text()
        if self.ui.tableWidget.item(zeile,spalte).text() != '':
            name, vorname = self.ui.label_3.text().split(', ')
            schueler = self.schuelerliste[(vorname,name)]
            datum = QtCore.QDate.fromString(self.ui.tableWidget.item(zeile,0).text(),"dd.MM.yyyy")
            datum_bis = QtCore.QDate.fromString(self.ui.tableWidget.item(zeile,1).text(),"dd.MM.yyyy")
            attest = self.ui.tableWidget.item(zeile,2).text()
            grund = self.ui.tableWidget.item(zeile,3).text()
            schueler.krankmeldungen[datum]=[datum_bis,attest,grund]
            self.datei_speichern()

    #Statistiken
    def zeige_krankmeldungen(self):
        dialog_krank = Dialog_Tabelle(self)
        dialog_krank.ui.setWindowTitle(u'Krankmeldungen')
        dialog_krank.ui.tableWidget.setRowCount(len(self.schuelerliste))
        dialog_krank.ui.tableWidget.setColumnCount(2)
        dialog_krank.ui.tableWidget.setHorizontalHeaderLabels([u'Name, Vorname',u'Tage krank'])
  
        schueler_krank = []
        for schueler in self.schuelerliste.values():
            tage = 0
            for datum in schueler.krankmeldungen.keys():
                tage += datum.daysTo(schueler.krankmeldungen[datum][0])+1
            schueler_krank.append([schueler.name+ ', ' + schueler.vorname,str(tage)])

        zeile = 0
        for eintrag in sorted(schueler_krank, key= lambda schueler : int(schueler[1]), reverse=True):
            for spalte in range(2):
               item = QtGui.QTableWidgetItem(eintrag[spalte])
               if spalte == 1:
                   item.setTextAlignment(4)
               dialog_krank.ui.tableWidget.setItem(zeile, spalte, item);
            zeile += 1
        dialog_krank.ui.tableWidget.resizeColumnsToContents()
        dialog_krank.ui.tableWidget.resizeRowsToContents() 
        dialog_krank.ui.tableWidget.horizontalHeader().setStretchLastSection(True)
        

    def zeige_beurlaubungen(self):
        dialog_krank = Dialog_Tabelle(self)
        dialog_krank.ui.setWindowTitle(u'Beurlaubungen')
        dialog_krank.ui.tableWidget.setRowCount(len(self.schuelerliste))
        dialog_krank.ui.tableWidget.setColumnCount(2)
        dialog_krank.ui.tableWidget.setHorizontalHeaderLabels([u'Name, Vorname',u'Stunden beurlaubt'])

        schueler_beurlaubt = []
        for schueler in self.schuelerliste.values():
            stunden = 0
            for datum in schueler.beurlaubungen:
                stunden += schueler.beurlaubungen[datum][1]
            schueler_beurlaubt.append([schueler.name+ ', ' + schueler.vorname,str(stunden)])

        zeile = 0
        for eintrag in sorted(schueler_beurlaubt, key= lambda schueler : int(schueler[1]), reverse=True):
            for spalte in range(2):
               item = QtGui.QTableWidgetItem(eintrag[spalte])
               if spalte == 1:
                   item.setTextAlignment(4)
               dialog_krank.ui.tableWidget.setItem(zeile, spalte, item);
            zeile += 1
        dialog_krank.ui.tableWidget.resizeColumnsToContents()


    def zeige_klausur_attest(self):
        dialog_krank = Dialog_Tabelle(self)
        dialog_krank.ui.setWindowTitle(u'versäumte Klausuren')
        dialog_krank.ui.tableWidget.setRowCount(len(self.schuelerliste))
        dialog_krank.ui.tableWidget.setColumnCount(3)    

    def suche_defizite(self):
        MESSAGE = u"<p>Die Eingabedatei muss im CSV-Format (als Trennzeichen Komma) vorliegen.</p>" \
            u"<p>Die Ausgabedatei wird in demselben Verzeichnis erzeugt, wo die Eingabedatei liegt.\
                 Sie hat den gleichen Namen mit dem Zusatz '_defizite'.\<p>Sollte etwas nicht funktionieren, frag Boris ;).</p>"
        reply = QtGui.QMessageBox.information(self,
                "Achtung!", MESSAGE)
        if reply == QtGui.QMessageBox.Ok:
            items = ("Noten", "Punkte")
            item, ok = QtGui.QInputDialog.getItem(self, "Abfrage",
                                                   "Wie sind die Noten eingeben?\nAls...", items, 0, False)
            if ok and item:
                print item
                csv_ein = QtGui.QFileDialog.getOpenFileName(self, u'CSV-Datei öffnen','.')
                if csv_ein:
                    finde_defizite(str(csv_ein), str(item))

    def klausurplan_konvertieren(self):
        MESSAGE = u"<p>Die Eingabedatei muss im CSV-Format vorliegen\
                  Es dürfen keine Kommata in den Bemerkungen vorkommen!</p>"\
             u"<p>Die Ausgabedatei wird in demselben Verzeichnis erzeugt, wo die Eingabedatei liegt.\
                  Sie hat den gleichen Namen mit dem Zusatz '_konvertiert'.\
                  Es öffnet sich nun ein Fenster, wo man die Eingabedatei auswählen kann.</p>"\
            u"<p>Sollte etwas nicht funktionieren, frag Boris ;).</p>"
        reply = QtGui.QMessageBox.information(self,
                "Achtung!", MESSAGE)
        if reply == QtGui.QMessageBox.Ok:
            csv_ein = QtGui.QFileDialog.getOpenFileName(self, u'CSV-Datei öffnen','.')
            if csv_ein:
                konvertiere(str(csv_ein))



# Starten des Programms
if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    helferlein = Helferlein()
    sys.exit(app.exec_())


