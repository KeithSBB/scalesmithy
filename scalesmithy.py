'''
Created on Nov 10, 2024

@author: keith
'''
import argparse
import copy
import json
import logging
import random

from collections import deque
from enum import Enum
from math import sin, cos, pi

from PyQt6.QtCore import (QSize, Qt, QPoint, QSettings, QRegularExpression, QUrl, QTimer)
from PyQt6.QtGui import QAction, QIcon, QPainter, QRegularExpressionValidator
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QMessageBox, QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QRadioButton, \
    QComboBox, QWidgetAction, QCheckBox, QGridLayout, QHBoxLayout, QPushButton, QButtonGroup, \
    QGroupBox, QLineEdit, QTextBrowser, QFileDialog, QListWidget, QListWidgetItem

import mido
import argparse

parser = argparse.ArgumentParser(
        prog='Scale smithy',
        description='Musical Scale analysis Application',
        epilog='-by Keith Smith')
parser.add_argument("-loglevel", nargs=1,
                    default=["INFO"], help="Enter INFO, DEBUG, WARNING, CRITICAL, or ERROR ")

args = parser.parse_args()

logging.basicConfig(level=args.loglevel[0], handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

from musicalclasses import Scale, Chorder, StradellaBass, ChordLevel, ChordSymbol, MidiPattern
from utils import drawText, drawCircle, Pos, Brushes, Pens, CircleGraphicsItem


class RootPosition(Enum):
    R9 = 180
    R12 = -90
    R3 = 0
    R6 = 90


class ScaleSelectDlg(QDialog):
    def __init__(self, parent, prompt, scales, cfScales={}):
        '''
        ScaleSelectDlg is used when saving and loading scales.  When saving scales pass the current
        dict of scales via the scales argument and leave cfScales empty.  When loading scales pass the
        scales from the file via scales and the current scales vis cfScales.
        :param parent:
        :param scales:
        :param cfScales:
        '''
        super().__init__( parent)
        self.setWindowTitle("Scale Family Selection")
        layout = QVBoxLayout()
        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(QLabel(prompt))

        self.list_widget = QListWidget()

        self.scales = scales
        self.cfScales = cfScales

        for akey in self.scales:
            item = QListWidgetItem(akey)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            if akey in self.cfScales:
                item.setForeground(Brushes().red)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget )
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def getSelectedScales(self):
        filteredScales = {}
        for indx in range(self.list_widget.count()):
            if self.list_widget.item(indx).checkState() == Qt.CheckState.Checked:
                sname = self.list_widget.item(indx).text()
                filteredScales[sname] = self.scales[sname]
        return filteredScales


    def accept(self):
        self.done(1)

class MidiSettingsDlg(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("MIDI Settings")

        layout = QVBoxLayout()
        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout.addWidget(QLabel('Select the MIDI output port'))
        hlayout = QHBoxLayout()

        self.outputPortsbox = QComboBox()
        self.refeshPorts()

        self.outputPortsbox.currentTextChanged.connect(self.newPort)
        hlayout.addWidget(self.outputPortsbox)

        refreshbtn = QPushButton("Refesh Ports")
        refreshbtn.clicked.connect(self.refeshPorts)
        hlayout.addWidget(refreshbtn)
        layout.addLayout(hlayout)

        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(QLabel("Select which midi program (instrument) to use:"))

        standard_midi_programs = [  "Acoustic Grand Piano",
                                    "Bright Acoustic Piano",
                                    "Electric Grand Piano",
                                    "Honky-tonk Piano",
                                    "Electric Piano 1",
                                    "Electric Piano 2",
                                    "Harpsichord",
                                    "Clavi",
                                    "Celesta",
                                    "Glockenspiel",
                                    "Music Box",
                                    "Vibraphone",
                                    "Marimba",
                                    "Xylophone",
                                    "Tubular Bells",
                                    "Dulcimer",
                                    "Drawbar Organ",
                                    "Percussive Organ",
                                    "Rock Organ",
                                    "Church Organ",
                                    "Reed Organ",
                                    "Accordion",
                                    "Harmonica",
                                    "Tango Accordion",
                                    "Acoustic Guitar (nylon)",
                                    "Acoustic Guitar (steel)",
                                    "Electric Guitar (jazz)",
                                    "Electric Guitar (clean)",
                                    "Electric Guitar (muted)",
                                    "Overdriven Guitar",
                                    "Distortion Guitar",
                                    "Guitar harmonics",
                                    "Acoustic Bass",
                                    "Electric Bass (finger)",
                                    "Electric Bass (pick)",
                                    "Fretless Bass",
                                    "Slap Bass 1",
                                    "Slap Bass 2",
                                    "Synth Bass 1",
                                    "Synth Bass 2",
                                    "Violin",
                                    "Viola",
                                    "Cello",
                                    "Contrabass",
                                    "Tremolo Strings",
                                    "Pizzicato Strings",
                                    "Orchestral Harp",
                                    "Timpani",
                                    "String Ensemble 1",
                                    "String Ensemble 2",
                                    "SynthStrings 1",
                                    "SynthStrings 2",
                                    "Choir Aahs",
                                    "Voice Oohs",
                                    "Synth Voice",
                                    "Orchestra Hit",
                                    "Trumpet",
                                    "Trombone",
                                    "Tuba",
                                    "Muted Trumpet",
                                    "French Horn",
                                    "Brass Section",
                                    "SynthBrass 1",
                                    "SynthBrass 2",
                                    "Soprano Sax",
                                    "Alto Sax",
                                    "Tenor Sax",
                                    "Baritone Sax",
                                    "Oboe",
                                    "English Horn",
                                    "Bassoon",
                                    "Clarinet",
                                    "Piccolo",
                                    "Flute",
                                    "Recorder",
                                    "Pan Flute",
                                    "Blown Bottle",
                                    "Shakuhachi",
                                    "Whistle",
                                    "Ocarina",
                                    "Lead 1 (square)",
                                    "Lead 2 (sawtooth)",
                                    "Lead 3 (calliope)",
                                    "Lead 4 (chiff)",
                                    "Lead 5 (charang)",
                                    "Lead 6 (voice)",
                                    "Lead 7 (fifths)",
                                    "Lead 8 (bass + lead)",
                                    "Pad 1 (new age)",
                                    "Pad 2 (warm)",
                                    "Pad 3 (polysynth)",
                                    "Pad 4 (choir)",
                                    "Pad 5 (bowed)",
                                    "Pad 6 (metallic)",
                                    "Pad 7 (halo)",
                                    "Pad 8 (sweep)",
                                    "FX 1 (rain)",
                                    "FX 2 (soundtrack)",
                                    "FX 3 (crystal)",
                                    "FX 4 (atmosphere)",
                                    "FX 5 (brightness)",
                                    "FX 6 (goblins)",
                                    "FX 7 (echoes)",
                                    "FX 8 (sci-fi)",
                                    "Sitar",
                                    "Banjo",
                                    "Shamisen",
                                    "Koto",
                                    "Kalimba",
                                    "Bag pipe",
                                    "Fiddle",
                                    "Shanai",
                                    "Tinkle Bell",
                                    "Agogo",
                                    "Steel Drums",
                                    "Woodblock",
                                    "Taiko Drum",
                                    "Melodic Tom",
                                    "Synth Drum",
                                    "Reverse Cymbal",
                                    "Guitar Fret Noise",
                                    "Breath Noise",
                                    "Seashore",
                                    "Bird Tweet",
                                    "Telephone Ring",
                                    "Helicopter",
                                    "Applause",
                                    "Gunshot"
                                ]

        self.programBox = QComboBox()
        self.programBox.addItems(standard_midi_programs)
        self.programBox.setCurrentIndex(self.parent().midiProgNum)
        self.programBox.currentTextChanged.connect(self.progChange)
        hlayout1.addWidget(self.programBox)

        layout.addLayout(hlayout1)

        hlayout2 = QHBoxLayout()
        numOctLbl = QLabel('Select the number of octaves to play: ')
        hlayout2.addWidget(numOctLbl)

        self.numOctavesBox = QComboBox()
        self.numOctavesBox.addItems(['1', '2'])
        self.numOctavesBox.setCurrentText(str(self.parent().midiNumOctaves))
        self.numOctavesBox.currentTextChanged.connect(self.newNumOct)
        hlayout2.addWidget(self.numOctavesBox)
        layout.addLayout(hlayout2)

        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(QLabel('Tempo to play notes at bpm: '))

        self.tempoBox = QLineEdit()
        self.tempoBox.setText(str(self.parent().midiTempo))
        validator = QRegularExpressionValidator(QRegularExpression(r"[0-9]+"))
        self.tempoBox.setValidator(validator)
        self.tempoBox.textChanged.connect(self.newTempo)
        hlayout3.addWidget(self.tempoBox)
        layout.addLayout(hlayout3)

        patBtns = QButtonGroup()
        patBtns.setExclusive(False)
        patGrpBox = QGroupBox("MIDI Scale Play Patterns")

        patGrpBox.clicked.connect(self.newPattern)
        glayout = QGridLayout()

        self.linUpChkbox = QCheckBox('linear up')
        self.linUpChkbox.setChecked(MidiPattern.LINEAR_UP in self.parentWidget().midiPattern)
        self.linUpChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.linUpChkbox, 0, 0)

        self.linDwnChkbox = QCheckBox('linear down')
        self.linDwnChkbox.setChecked(MidiPattern.LINEAR_DOWN in self.parentWidget().midiPattern)
        self.linDwnChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.linDwnChkbox, 1, 0)

        self.patUpChkbox = QCheckBox('Pattern up')
        self.patUpChkbox.setChecked(MidiPattern.PATTERN_UP in self.parentWidget().midiPattern)
        self.patUpChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.patUpChkbox, 0, 1)

        self.patDwnChkbox = QCheckBox('Pattern down')
        self.patDwnChkbox.setChecked(MidiPattern.PATTERN_DOWN in self.parentWidget().midiPattern)
        self.patDwnChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.patDwnChkbox, 1, 1)

        self.arpUpChkbox = QCheckBox('Arpagio up')
        self.arpUpChkbox.setChecked(MidiPattern.ARPEGGIO_UP in self.parentWidget().midiPattern)
        self.arpUpChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.arpUpChkbox, 0,2)

        self.arpDwnChkbox = QCheckBox('Arpagio down')
        self.arpDwnChkbox.setChecked(MidiPattern.ARPEGGIO_DOWN in self.parentWidget().midiPattern)
        self.arpDwnChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.arpDwnChkbox, 1, 2)

        patGrpBox.setLayout(glayout)

        layout.addWidget(patGrpBox)

        plyBtn = QPushButton('Play Scale')
        plyBtn.clicked.connect(self.parent().playSynth)

        layout.addWidget(plyBtn)

        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def progChange(self):
        self.parent().midiProgNum = self.programBox.currentIndex()

    def refeshPorts(self):
        self.output_ports = mido.get_output_names()
        self.outputPortsbox.clear()
        self.outputPortsbox.addItems(self.output_ports)
        self.outputPortsbox.setCurrentText(self.parent().midiPortName)

    def newTempo(self):
        self.parent().midiTempo = int(self.tempoBox.text())

    def newPattern(self):
        print('new pattern!!!!!')
        pattern = MidiPattern.NONE
        if self.linUpChkbox.isChecked():
            pattern |= MidiPattern.LINEAR_UP
        if self.linDwnChkbox.isChecked():
            pattern |= MidiPattern.LINEAR_DOWN
        if self.patUpChkbox.isChecked():
            pattern |= MidiPattern.PATTERN_UP
        if self.patDwnChkbox.isChecked():
            pattern |= MidiPattern.PATTERN_DOWN
        if self.arpUpChkbox.isChecked():
            pattern |= MidiPattern.ARPEGGIO_UP
        if self.arpDwnChkbox.isChecked():
            pattern |= MidiPattern.ARPEGGIO_DOWN

        if pattern == MidiPattern.NONE:
            pattern = MidiPattern.LINEAR_UP
        logger.debug(pattern)
        self.parentWidget().midiPattern = pattern

    def newNumOct(self):
        self.parent().midiNumOctaves = int(self.numOctavesBox.currentText())



    def newPort(self):
        self.parent().midiPortName = self.outputPortsbox.currentText()

    def accept(self):
        self.done(1)


class PrefEditorDlg(QDialog):
    def __init__(self, parent=None, chordLevel=ChordLevel.OFF, chordSymbol=ChordSymbol.RAW, rootPos=RootPosition.R9):
        super().__init__(parent)

        if isinstance(chordLevel, ChordLevel):
            self.chordLevel = chordLevel
        else:
            self.chordLevel = ChordLevel.OFF

        if isinstance(chordSymbol, ChordSymbol):
            self.chordSymbol = chordSymbol
        else:
            self.chordSymbol = ChordSymbol.RAW

        if isinstance(rootPos, RootPosition):
            self.rootPos = rootPos
        else:
            self.rootPos = RootPosition.R9

        self.setWindowTitle("Preferences")

        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        rplabel = QLabel('Select the root position\n by clock hour')
        self.rootPosbox = QComboBox()
        self.rootPosbox.addItems(['9', '12', '3', '6'])

        if self.rootPos == RootPosition.R9:
            self.rootPosbox.setCurrentIndex(0)
        elif self.rootPos == RootPosition.R12:
            self.rootPosbox.setCurrentIndex(1)
        elif self.rootPos == RootPosition.R3:
            self.rootPosbox.setCurrentIndex(2)
        elif self.rootPos == RootPosition.R6:
            self.rootPosbox.setCurrentIndex(3)
        else:
            Exception("Root Position Value Error")

        layout = QVBoxLayout()


        # Chord preferences
        chrdlayout = QHBoxLayout()
        cdGrpBox = QGroupBox("Chord Display")
        cdlayout = QVBoxLayout()

        self.b1 = QRadioButton("No chords displayed")
        if self.chordLevel == ChordLevel.OFF:
            self.b1.setChecked(True)
        cdlayout.addWidget(self.b1)

        self.b2 = QRadioButton("Basic Accordion chords")
        if self.chordLevel == ChordLevel.BASIC_ACCORD:
            self.b2.setChecked(True)
        cdlayout.addWidget(self.b2)

        self.b3 = QRadioButton("Advanced Accordion chords")
        if self.chordLevel == ChordLevel.ADV_ACCORD:
            self.b3.setChecked(True)
        cdlayout.addWidget(self.b3)

        self.b4 = QRadioButton("All chords")
        if self.chordLevel == ChordLevel.ALL:
            self.b4.setChecked(True)
        cdlayout.addWidget(self.b4)

        cdGrpBox.setLayout(cdlayout)
        chrdlayout.addWidget(cdGrpBox)

        csGrpBox = QGroupBox("Chord Symbology")
        cslayout = QVBoxLayout()
        self.b21 = QRadioButton("no translation")
        if self.chordSymbol == ChordSymbol.RAW:
            self.b21.setChecked(True)
        cslayout.addWidget(self.b21)

        self.b22 = QRadioButton("Common : maj, min, dim, 7, aug")
        if self.chordSymbol == ChordSymbol.COMMON:
            self.b22.setChecked(True)
        cslayout.addWidget(self.b22)

        self.b23 = QRadioButton("Jazz: Δ,-, +, 7 ")
        if self.chordSymbol == ChordSymbol.JAZZ:
            self.b23.setChecked(True)
        cslayout.addWidget(self.b23)
        csGrpBox.setLayout(cslayout)
        chrdlayout.addWidget(csGrpBox)

        layout.addLayout(chrdlayout)

        layout.addWidget(rplabel)
        layout.addWidget(self.rootPosbox)

        self.showBassChkBox = QCheckBox("Show Stradella Bass", self)
        self.showBassChkBox.setChecked(parent.showStradella)
        layout.addWidget(self.showBassChkBox)

        self.setLayout(layout)
        self.setWindowTitle("Preferences")

        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def accept(self):
        # Get the form data and process it
        if self.b1.isChecked():
            self.chordLevel = ChordLevel.OFF
        elif self.b2.isChecked():
            self.chordLevel = ChordLevel.BASIC_ACCORD
        elif self.b3.isChecked():
            self.chordLevel = ChordLevel.ADV_ACCORD
        elif self.b4.isChecked():
            self.chordLevel = ChordLevel.ALL
        else:
            Exception("Chord Level accept value error")

        if self.b21.isChecked():
            self.chordSymbol = ChordSymbol.RAW
        elif self.b22.isChecked():
            self.chordSymbol = ChordSymbol.COMMON
        elif self.b23.isChecked():
            self.chordSymbol = ChordSymbol.JAZZ
        else:
            Exception("Chord symbology preference accept error")

        if self.rootPosbox.currentIndex() == 0:
            self.rootPos = RootPosition.R9
        elif self.rootPosbox.currentIndex() == 1:
            self.rootPos = RootPosition.R12
        elif self.rootPosbox.currentIndex() == 2:
            self.rootPos = RootPosition.R3
        elif self.rootPosbox.currentIndex() == 3:
            self.rootPos = RootPosition.R6
        else:
            Exception("Root Position accept value error")

        # Close the dialog with accepted status
        # self.accept() #QDialog.accepted)
        self.done(1)

class FindScaleDlg(QDialog):
    '''
    Dialog asks for unknown slace notes and returns name of scale family, mode and key

    '''

    def __init__(self, knownScales, parent=None):
        super().__init__(parent)
        self.knownScales = knownScales
        self.ukintervals = None
        self.found = False
        self.key = ""
        self.scalefamily = 'unknown'
        self.mode = 'unknown'
        layout = QVBoxLayout()
        toplabel = QLabel('Enter the notes (starting with root) in capital letters \nseparated by spaces or commas.  Follow flats \nwith "b" and sharps with "#" Ex: C D# E Gb Bb ...')
        layout.addWidget(toplabel)
        hlayout1 = QHBoxLayout()
        findbtn = QPushButton("Find")
        findbtn.clicked.connect(self.find)
        hlayout1.addWidget(findbtn)
        self.noteEditBox = QLineEdit()
        hlayout1.addWidget(self.noteEditBox)
        layout.addLayout(hlayout1)
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(QLabel("Key:"))
        self.keylabel = QLabel("")
        hlayout2.addWidget(self.keylabel)
        layout.addLayout(hlayout2)
        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(QLabel("Scale Family:"))
        self.scaleFamlabel = QLabel("")
        hlayout3.addWidget(self.scaleFamlabel)
        layout.addLayout(hlayout3)
        hlayout4 = QHBoxLayout()
        hlayout4.addWidget(QLabel("Mode:"))
        self.modelabel = QLabel("")
        hlayout4.addWidget(self.modelabel)
        layout.addLayout(hlayout4)
        hlayout5 = QHBoxLayout()
        setscalebtn = QPushButton("Set to this scale")
        setscalebtn.clicked.connect(self.accept)
        hlayout5.addWidget(setscalebtn)
        exitbtn = QPushButton("Exit")
        exitbtn.clicked.connect(self.reject)
        hlayout5.addWidget(exitbtn)
        layout.addLayout(hlayout5)
        self.setLayout(layout)

    def find(self):
        # First note is assumed key
        chromScale = {'A':0, 'A#':1, 'Bb':1, 'B':2, 'C':3, 'C#':4, 'Db:4':4, 'D':5, 'D#':6, 'Eb':6, 'E':7, 'F':8,
                        'F#':9, 'Gb':9, 'G':10, 'G#':11, 'Ab':11}
        notes = self.noteEditBox.text().split()
        self.key = notes[0]
        self.keylabel.setText(self.key)
        noteNumbers = [(chromScale[akey] - chromScale[notes[0]]) for akey in notes]
        for indx,anum in enumerate(noteNumbers):
            if anum < 0:
                noteNumbers[indx] = 12 + anum

        noteNumbers.sort()
        noteNumbers.append(12)
        logger.debug(noteNumbers)
        #get intervals
        keycpos = chromScale[notes[0]]
        self.ukintervals = deque([h-l for h,l in zip(noteNumbers[1:], noteNumbers[:-1])])
        logger.debug(self.ukintervals)
        self.found = False
        for self.scalefamily in self.knownScales:
            intervals = deque(self.knownScales[self.scalefamily][0])
            if len(intervals) != len(self.ukintervals):
                #print(f"{scalefamily} has a different number of notes")
                continue

            modes = self.knownScales[self.scalefamily][1]
            for midx, self.mode in enumerate(modes):
                rotIntvls = intervals.copy()
                rotIntvls.rotate(-midx)
                #rotIntvls.appendleft(0)
                logger.debug(f"{self.ukintervals} == {rotIntvls} ?")
                if self.ukintervals == rotIntvls:
                    logger.info(self.scalefamily)
                    logger.info(self.mode)
                    self.found = True
                    break;
            if self.found:
                break
        if self.found:
            self.scaleFamlabel.setText(self.scalefamily)
            self.modelabel.setText(self.mode)
        else:
            self.scaleFamlabel.setText("Not Found")
            self.modelabel.setText("Not Found")

class ScaleEditorDlg(QDialog):
    '''
    Scale editor displays a scale as three data items: scale name, scale intervals (in semitones), scale modes
    The editor alows you to load, save, create new, scales.   Scales are stored in the scaletool config file
    the number of notes needs to be set somewhere and this value would change the number of table cols
    '''

    def __init__(self, currentEditMode, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Scale Editor")

        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout = QVBoxLayout()
        if currentEditMode:
            self.selNotes = parent.getSelectedNotes()
            glayout = QGridLayout()
            message = QLabel('enter new scale name and names for each mode')
            layout.addWidget(message)
            self.sname = QLineEdit()
            self.modes = []
            glayout.addWidget(QLabel('Scale Name:'), 0, 0)
            glayout.addWidget(self.sname, 0, 1)
            for mode in range(len(self.selNotes)):
                glayout.addWidget(QLabel(f'Mode {mode + 1} Name:'), mode + 1, 0)
                self.modes.append(QLineEdit())
                glayout.addWidget(self.modes[-1], mode + 1, 1)

            layout.addLayout(glayout)
        else:
            message = QLabel("Select notes by clicking on them.  When done select scale edit from menu again")
            layout.addWidget(message)
            self.currentscale = QCheckBox('start with current scale')
            layout.addWidget(self.currentscale)

        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class AboutDlg(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle("Scale Smithy")
        self.label1 = QLabel("Scale Smithy v0.1")
        self.label2 = QLabel(f"Location of config file:\n {parent.settings.fileName()}")
        self.button = QPushButton("Close")
        self. button.clicked.connect(self.accept)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.label2)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

class DocsDig(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Documentation")

        self.layout = QVBoxLayout()
        self.backward_button = QPushButton("<")
        self.forward_button = QPushButton(">")

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.backward_button)
        hlayout.addWidget(self.forward_button)
        hlayout.addStretch()
        self.layout.addLayout(hlayout)

        self.label = QLabel("Table of Contents")
        self.tb = QTextBrowser(minimumWidth=800, minimumHeight=600)
        self.tb.document().setDefaultStyleSheet(
            'body {color: #333; font-size: 14px;} '
            'h2 {background: #CCF; color: #443;} '
            'h1 {background: #001133; color: white;} '
        )

        # TextBrowser background is a widget style, not a document style
        self.tb.setStyleSheet('background-color: #EEF;')

        iurl = QUrl('help/index.md')
        self.tb.setSource(iurl)
        self.tb.setSearchPaths(['help'])
        # with open('index.md', 'r') as fh:
        #     self.tb.insertHtml(fh.read())

        self.tb.setAcceptRichText(True)
        self.tb.setOpenExternalLinks(True)
        self.button = QPushButton("Close")
        self.button.clicked.connect(self.accept)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.tb)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
        self.backward_button.clicked.connect(self.tb.backward)
        self.forward_button.clicked.connect(self.tb.forward)

    # def addDocs(self):
    #     self.tb.append("Ths is a <b>test</b>")

class FaqDlg(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FAQ")
        self.label = QLabel("Here we go")
        self.tb = QTextBrowser(minimumWidth=800, minimumHeight=600)
        self.tb.document().setDefaultStyleSheet(
                'body {color: #333; font-size: 14px;} '
                'h2 {background: #CCF; color: #443;} '
                'h1 {background: #001133; color: white;} '
        )

        # TextBrowser background is a widget style, not a document style
        self.tb.setStyleSheet('background-color: #EEF;')
        iurl = QUrl('help/faq.md')
        self.tb.setSource(iurl)
        self.tb.setAcceptRichText(True)
        self.tb.setOpenExternalLinks(True)
        self.button = QPushButton("Close")
        self.button.clicked.connect(self.accept)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.tb)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

class ContactDlg(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contact Info")
        self.label = QLabel("keith@github.com")
        self.button = QPushButton("Close")
        self.button.clicked.connect(self.accept)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()

        #logging.basicConfig(level=args.loglevel[0])

        logger.info('Scale Smithy Started.  The configuration file being used is:')
        self.settings = QSettings("santabayanian", "ScaleSmithy")
        logger.info(self.settings.fileName())
        priScaleName, priScaleMode, priScaleKey, refScaleName, refScaleMode, refScaleKey = self.readSettings()
        self.setStyleSheet("QMainWindow { border: 1px solid black; }")
        self.angOffset = float(self.rootPos.value)

        self.chromeCircleGraphics = []
        self.scalegraphics = []
        self.refScalegraphics = []
        self.scaleEditMode = False

        # set app  window size and title
        self.setWindowTitle("Scale Smithy")

        # scale and mode titles
        self.scaleFamilyGI = None
        self.modeGI = None

        # set the graphics scene size and the app window size
        self.scene = QGraphicsScene(-400, -500, 800, 1000)
        self.view = QGraphicsView(self.scene)

        self.chorder = Chorder(self.scene, self.chordSymbology, self.chordNameLevel)

        if len(self.scales) == 0:
            self.scales = self.defaultScales()

        self.primaryScale = Scale(priScaleName, self.scales[priScaleName], self.scene)
        self.primaryScale.mode = priScaleMode
        self.primaryScale.key = priScaleKey

        if not refScaleName:
            self.refScale = None
        else:
            self.refScale = Scale(refScaleName, self.scales[refScaleName], self.scene)
            self.refScale.mode = refScaleMode
            self.refScale.key = refScaleKey



        # setup menu
        menu = self.menuBar()
        #File Menu
        file_menu = menu.addMenu("&File")

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)

        load_action = QAction("Load", self)
        load_action.triggered.connect(self.load)
        file_menu.addAction(load_action)

        print_action = QAction( "Print", self)
        print_action.triggered.connect(self.print)
        file_menu.addAction(print_action)

        createIMG_action = QAction(QIcon("bug.png"), "Save &Image", self)
        createIMG_action.triggered.connect(self.image)
        file_menu.addAction(createIMG_action)

        # Edit Menu
        edit_menu = menu.addMenu("&Edit")
        cpyedit = QAction("Copy", self)
        cpyedit.triggered.connect(self.copy)
        edit_menu.addAction(cpyedit)
        fscEdit = QAction("Find Scale", self)
        fscEdit.triggered.connect(self.findScale)
        edit_menu.addAction(fscEdit)
        scEdit = QAction("Scale Family Editor", self)
        scEdit.triggered.connect(self.scaleEdit)
        edit_menu.addAction(scEdit)
        scDel = QAction("Delete Scale Family", self)
        scDel.triggered.connect(self.scaleDelete)
        edit_menu.addAction(scDel)
        scRst = QAction("Restore Default Scale Families", self)
        scRst.triggered.connect(self.scaleRestore)
        edit_menu.addAction(scRst)
        pref_action = QAction("Preferences", self)
        pref_action.triggered.connect(self.prefEdit)
        edit_menu.addAction(pref_action)

        #Scale Family
        self.scale_Menu = menu.addMenu("&Scale Family")
        self.buildScaleMenu()
        self.mode_menu = menu.addMenu("&Mode")
        self.buildModeMenu()
        self.key_menu = menu.addMenu("&Key")
        self.buildKeyMenu()

        refScaleMenu = menu.addMenu("Ref-scale")

        setRef_action = QAction("Set Ref", self)
        setRef_action.triggered.connect(self.setRef)
        refScaleMenu.addAction(setRef_action)
        clearRef_action = QAction("Clear Ref", self)
        clearRef_action.triggered.connect(self.clearRef)
        refScaleMenu.addAction(clearRef_action)
        swapRef_action = QAction("Swap Ref <-> Primary", self)
        swapRef_action.triggered.connect(self.swapRef)
        refScaleMenu.addAction(swapRef_action)
        autoran_action = QAction("Toggle Random Run", self)
        autoran_action.triggered.connect(self.randomrun)
        refScaleMenu.addAction((autoran_action))

        #Midi Menu
        midiMenu = menu.addMenu("MIDI")
        play_action = QAction("Play To Port", self)
        play_action.triggered.connect(self.playSynth)
        midiMenu.addAction(play_action)
        midiSettings_action = QAction('MIDI Settings', self)
        midiSettings_action.triggered.connect(self.midiSettings)
        midiMenu.addAction(midiSettings_action)


        # Help menu
        helpmenu = menu.addMenu("Help")
        aboutmenu = QAction("About", self)
        aboutmenu.triggered.connect(self.about)
        helpmenu.addAction(aboutmenu)
        docmenu = QAction("Documentation", self)
        docmenu.triggered.connect(self.documentation)
        helpmenu.addAction((docmenu))
        faqmenu = QAction("FAQ", self)
        faqmenu.triggered.connect(self.faq)
        helpmenu.addAction((faqmenu))
        contactmenu = QAction("Contact", self)
        contactmenu.triggered.connect(self.contact)
        helpmenu.addAction((contactmenu))



        #DRAWING TOOLS

        # Creation of drawing tools
        # Brushes for fills
        self.brush = Brushes()
        # Pens for lines
        self.pen = Pens()

        #Qtimer for random run
        self.timer = QTimer(self, timeout=self.update_ran)

        self.stradella =  StradellaBass(self.scene, self.pen)

        # draw chromatic circle and stradella layout 
        self.drawChromCircle()
        self.stradella.draw_Stradella(0, 420,
                                      self.primaryScale.noteSemitonePositions,
                                      self.showStradella)

        # Add the view to the window and draw the scale.  Also draw reference scale if it exists
        self.setCentralWidget(self.view)
        self.drawScale()

    def defaultScales(self):
        '''
        This overwrites all custom scales to the following factory set:
        '''
        scales = {     "Diatonic": [[2, 2, 1, 2, 2, 2, 1],
                                    ['Ionian - Major', 'Dorian', 'Phrygain', 'Lydian', 'Mixolydian',
                                     'Aeolian - Natural Minor', 'Locrian']],
                       "Ascending Melodic Minor": [[2, 1, 2, 2, 2, 2, 1],
                                                   ['Dorian #7', 'Phrygain #6', 'Lydian #5', 'Mixolydian #4',
                                                    'Aeolian #3', 'Locrian #2', 'Ionian #1 - The Altered Scale']],
                       "Harmonic Minor": [[2, 1, 2, 2, 1, 3, 1],
                                          ['Aeolian #7', 'Locrian #6', 'Ionian #5', 'Dorian #4', 'Phrygain #3',
                                           'Lydian #2', 'Mixolydian #1 - Super Locrian']],
                       "Harmonic Major": [[2, 2, 1, 2, 1, 3, 1],
                                          ['Ionian b6', 'Dorian b5', 'Phrygain b4', 'Lydian b3', 'Mixolydian b2',
                                           'Aeolian b1', 'Locrian b7']],
                       "Diminished": [[2, 1, 2, 1, 2, 1, 2, 1], ['Diminished', 'Inverted Diminished']],
                       "Whole Tone": [[2, 2, 2, 2, 2, 2], ['Whole Tone']],
                       "Augmented": [[3, 1, 3, 1, 3, 1], ['Augmented', 'Inverted Augmented']],
                       "Double Harmonic Major": [[1, 3, 1, 2, 1, 3, 1],
                                                 ['Bizantine', 'Lydian #2 #6', 'Ultraphrygain', 'Hungarian Minor',
                                                  'Oriental', 'Ionian ♯2 ♯5', 'Locrian bb3 bb7']],
                       "Eight step scale": [[2, 3, 1, 1, 2, 1, 1, 1],
                                            ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']]}
        return scales

    def writeSettings(self):
        "writes settings to config file ($HOME/.config/santabayanian/scaleTool.conf"
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("showStradella", self.showStradella)
        self.settings.endGroup()
        self.settings.beginGroup("chromCir")
        self.settings.setValue("rootpos", self.rootPos)
        self.settings.endGroup()
        self.settings.beginGroup("chords")
        self.settings.setValue("chordNameLevel", self.chordNameLevel)
        self.settings.setValue("chordsymbology", self.chordSymbology)
        self.settings.endGroup()
        self.settings.beginGroup("scale")
        self.settings.setValue("CurrentScale", self.primaryScale.name)
        self.settings.setValue("CurrentMode", self.primaryScale.mode)
        self.settings.setValue("CurrentKey", self.primaryScale.key)
        if not self.refScale:
            self.settings.setValue("RefScale", '')
            self.settings.setValue("RefMode", '')
            self.settings.setValue("RefKey", '')
        else:
            self.settings.setValue("RefScale", self.refScale.name)
            self.settings.setValue("RefMode", self.refScale.mode)
            self.settings.setValue("RefKey", self.refScale.key)
        self.settings.beginWriteArray("scales")
        for i, akey in enumerate(self.scales):
            self.settings.setArrayIndex(i)
            self.settings.setValue("scaleName", akey)
            self.settings.setValue("intervals", json.dumps(self.scales[akey][0]))
            self.settings.setValue("modes", json.dumps(self.scales[akey][1]))

        self.settings.endArray()
        self.settings.endGroup()

        self.settings.beginGroup('midi')
        self.settings.setValue("midiPortName", self.midiPortName )
        self.settings.setValue("midiNumOctaves", self.midiNumOctaves)
        self.settings.setValue("midiProgNum", self.midiProgNum)
        self.settings.setValue("midiTempo", self.midiTempo)
        self.settings.setValue("midiPattern", self.midiPattern)
        self.settings.endGroup()

    def readSettings(self):
        "read settings from config file ($HOME/.config/santabayanian/scaleTool.conf"
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size", QSize(800, 1000)))
        self.move(self.settings.value("pos", QPoint(200, 200)))
        self.showStradella = ("true" == self.settings.value("showStradella", True))
        self.settings.endGroup()
        self.settings.beginGroup("chromCir")
        try:
            self.rootPos = RootPosition(int(self.settings.value("rootpos", RootPosition.R9)))
        except:
            self.rootPos = RootPosition.R9
        self.settings.endGroup()
        self.settings.beginGroup("chords")
        # try:
        self.chordNameLevel = self.settings.value("chordNameLevel", ChordLevel.OFF)
        self.chordSymbology = self.settings.value("chordsymbology", ChordSymbol.RAW)
        # except:
        #   self.chordNameLevel = ChordLevel.OFF
        self.settings.endGroup()
        self.settings.beginGroup("scale")
        primaryScaleName = self.settings.value("CurrentScale", "Diatonic")
        if primaryScaleName == 'Unknown':
            primaryScaleName = "Diatonic"
        primaryScaleMode = self.settings.value("CurrentMode", 'Ionian - Major')
        primaryScaleKey = self.settings.value("CurrentKey", 'none')
        refScaleName = self.settings.value("RefScale", None)
        refScaleMode = self.settings.value("RefMode", None)
        refScaleKey = self.settings.value("RefKey", None)
        numScales = self.settings.beginReadArray("scales")
        self.scales = {}
        for i in range(numScales):
            self.settings.setArrayIndex(i)
            name = self.settings.value("scaleName")
            modes = json.loads(self.settings.value("modes"))
            intervals = json.loads(self.settings.value("intervals"))
            self.scales[name] = [intervals, modes]

        self.settings.endArray()
        self.settings.endGroup()

        self.settings.beginGroup('midi')
        self.midiPortName = self.settings.value("midiPortName", 'unknown')
        self.midiNumOctaves = int(self.settings.value("midiNumOctaves", 1))
        self.midiProgNum = int(self.settings.value("midiProgNum", 0))
        self.midiTempo = int(self.settings.value("midiTempo", 120))
        self.midiPattern = self.settings.value("midiPattern", MidiPattern.NONE)
        self.settings.endGroup()
        return [primaryScaleName, primaryScaleMode, primaryScaleKey, refScaleName, refScaleMode, refScaleKey]

    def closeEvent(self, event):
        "When main window closes write current setting to conf file"
        self.writeSettings()
        event.accept()

    def save(self):
        fileNameInfo = QFileDialog.getSaveFileName(self, "Save Scales", "~", "JSON Files (*.json)")
        if fileNameInfo[0][-5:] != ".json":
            fileName = fileNameInfo[0] + ".json"
        else:
            fileName = fileNameInfo[0]

        dlg = ScaleSelectDlg(self, "Select which scales to save to file", self.scales)
        if dlg.exec():
            with open(fileName, "w") as fp:
                json.dump(dlg.getSelectedScales(), fp)

    def load(self):
        fileNameInfo = QFileDialog.getOpenFileName(self, "Load Scales", "", "JSON Files (*.json)")
        if len(fileNameInfo[0]) > 0:
            with open(fileNameInfo[0], "r") as fp:
                ldscales = json.load(fp)
            dlg = ScaleSelectDlg(self, ("Select which scales to load from file.\n" +
                                     "Red indicates a conflict that will \n" +
                                     "overwrite an existing scale"), ldscales, self.scales)
            if dlg.exec():
                chosenscales = dlg.getSelectedScales()
                logger.debug(chosenscales )
                for akey in chosenscales:
                    self.scales[akey] = chosenscales[akey]
                self.scale_Menu.clear()
                self.buildScaleMenu()
            else:
                logger.debug("Canceled")

    def findScale(self):
        dlg = FindScaleDlg(self.scales)
        if dlg.exec():
            logger.debug("set to this scale")
            self.primaryScale.deleteGraphicItems()
            if dlg.found:
                scaleName = dlg.scalefamily
                self.primaryScale = Scale(dlg.scalefamily, self.scales[ dlg.scalefamily], self.scene)
                self.buildModeMenu()
            else:
                logger.debug(dlg.ukintervals)
                self.primaryScale = Scale("Unknown", [dlg.ukintervals, ["unkn", "unkn"]], self.scene)

            self.primaryScale.key = dlg.key
            self.drawScale()
            self.drawTitle()

        else:
            logger.info("Cancel")

    def scaleEdit(self):

        dlg = ScaleEditorDlg(self.scaleEditMode, self)
        if dlg.exec():
            logger.debug("Scale Edit Success!")
            sindx = []
            if not self.scaleEditMode:
                # set up edit mode
                for acir in self.chromeCircleGraphics:
                    if isinstance(acir, CircleGraphicsItem):
                        acir.setSelectable(True)
                        if acir.noteId in self.primaryScale.sindx and dlg.currentscale.isChecked():
                            acir.setSelectedState(True)
                self.primaryScale.deleteGraphicItems()
            else:
                # finish capturing new scale
                genModes = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
                scaleName = dlg.sname.text()
                if len(scaleName) > 0:
                    modeNames = []
                    for midx, anEditBox in enumerate(dlg.modes):
                        aModeName = anEditBox.text()
                        if len(aModeName) == 0:
                            modeNames.append(genModes[midx])
                        else:
                            modeNames.append(aModeName)
                    logger.debug(scaleName)
                    logger.debug(modeNames)
                    logger.debug(dlg.selNotes)

                    for acir in self.chromeCircleGraphics:
                        if isinstance(acir, CircleGraphicsItem):
                            acir.setSelectedState(False)
                            acir.setSelectable(False)

                    dlg.selNotes.append(12)
                    newIntvls = [(dlg.selNotes[i + 1] - dlg.selNotes[i]) for i in range(len(dlg.selNotes) - 1)]

                    self.scales[scaleName] = [newIntvls, modeNames]
                    self.scale_Menu.clear()
                    self.buildScaleMenu()

                else:
                    Exception('Missing scale name')

            self.scaleEditMode = not self.scaleEditMode
        else:
            logger.debug("Cancel!")
            self.scaleEditMode = False
            for acir in self.chromeCircleGraphics:
                if isinstance(acir, CircleGraphicsItem):
                    acir.setSelectedState(False)
                    acir.setSelectable(False)

            self.drawScale()

    def scaleDelete(self):
        msgBox = QMessageBox()
        msgBox.setText("Clicking on OK will delete the current outer scale family and delete it from the list of available scales.  This is irreversible.  Are you sure you want to delete the current scale?")
        msgBox.setWindowTitle("Edit->Delete Scale")
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        result = msgBox.exec()
        if result == QMessageBox.StandardButton.Ok:
            print("OK button clicked")
            self.primaryScale.deleteGraphicItems()
            del self.scales[self.primaryScale.name]
            self.scale_Menu.clear()
            self.buildScaleMenu()

        elif result == QMessageBox.StandardButton.Cancel:
            print("Cancel button clicked")

    def scaleRestore(self):
        msgBox = QMessageBox()
        msgBox.setText(
            "<p><b>Reset to default scale set</b>: Will replace all scale families with the default set.  This will delete all custom scales </p>"
            "<p><b>Restore default scales</b>: Will restore just the defaut scales leaving any custom named scales alone</p>"
            "<p><b>Cancel</b>: Will exit and do nothing </p>")
        msgBox.setWindowTitle("Edit->Restore Default Scales")
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.addButton("Reset to default scale set", QMessageBox.ButtonRole.ResetRole)
        msgBox.addButton("Restore default scales", QMessageBox.ButtonRole.ActionRole)
        msgBox.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        result = msgBox.exec()
        if result == 0:
            print("reset")
            self.scales = self.defaultScales()
            self.scale_Menu.clear()
            self.buildScaleMenu()
        elif result == 1:
            print("restore defaults")
            defScale = self.defaultScales()
            for ascale in defScale:
                self.scales[ascale] = defScale[ascale]
            self.scale_Menu.clear()
            self.buildScaleMenu()
        elif result == 2:
            print("cancel")
        else:
            print(result)

    def prefEdit(self):
        dlg = PrefEditorDlg(self, self.chordNameLevel, self.chordSymbology, self.rootPos)
        if dlg.exec():
            self.chordNameLevel = dlg.chordLevel
            self.chordSymbology = dlg.chordSymbol
            self.chorder.symbology = self.chordSymbology
            self.rootPos = dlg.rootPos
            self.angOffset = float(self.rootPos.value)
            self.showStradella = dlg.showBassChkBox.isChecked()
            self.stradella.draw_Stradella(0, 420, self.showStradella)
            self.drawTitle()
            self.drawChromCircle()
            self.drawScale()

        else:
            print("Cancel!")

    def midiSettings(self):
        dlg = MidiSettingsDlg(self)
        if dlg.exec():
            print('success')

    def clearRef(self):
        if self.refScale:
            self.refScale.deleteGraphicItems()
            self.refScale = None

    def setRef(self):
        self.clearRef()
        print("setRef called")
        refScaleName = copy.deepcopy(self.primaryScale.name)
        refScaleMode = copy.deepcopy(self.primaryScale.mode)
        refScaleKey = copy.deepcopy(self.primaryScale.key)
        self.refScale = Scale(refScaleName, self.scales[refScaleName], self.scene)
        self.refScale.mode = refScaleMode
        self.refScale.key = refScaleKey
        self.drawRefScale()

    def swapRef(self):
        tmp = self.primaryScale
        self.primaryScale = copy.copy(self.refScale)
        self.refScale = tmp
        self.drawScale()
        self.drawTitle()

    def buildScaleMenu(self):
        '''builds the scale menu and actions from self.scales.
        scale entries are sorted first by the default set and then by custom scales
        in order added'''
        defaultKeys = self.defaultScales().keys()
        currentKeys = self.scales.keys()
        sortedKeys = []
        for aKey in defaultKeys:
            if aKey in currentKeys:
                sortedKeys.append(aKey)
        for aKey in currentKeys:
            if aKey not in defaultKeys:
                sortedKeys.append(aKey)

        for ascale in sortedKeys:
            anAction = QAction(ascale, self)
            self.scale_Menu.addAction(anAction)
            anAction.triggered.connect(self.setScale)

    def buildModeMenu(self):
        "builds the mode menu for the current scale - executed every time a different scale family is selected"
        self.mode_menu.clear()
        self.currentMode = None
        for amode in self.primaryScale.modes:
            if not self.currentMode:
                self.currentMode = amode
            anAction = QAction(amode, self)
            self.mode_menu.addAction(anAction)
            anAction.triggered.connect(self.setMode)
        self.drawTitle()

    def buildKeyMenu(self):
        "builds the scale menu and actions from self.scales"
        for akey in Scale.allKeys:
            anAction = QWidgetAction(self)
            aLbl = QLabel(akey)
            aLbl.setStyleSheet("font-size: 12pt;")
            anAction.setDefaultWidget(aLbl)

            self.key_menu.addAction(anAction)
            anAction.triggered.connect(self.setKey)

    def setScale(self):
        # self.currentScale = self.sender().text()
        self.primaryScale.deleteGraphicItems()
        key = self.primaryScale.key
        self.primaryScale = Scale(self.sender().text(), self.scales[self.sender().text()], self.scene)
        self.primaryScale.key = key
        self.buildModeMenu()
        self.drawScale()  # print(self.currentScale)

    def setMode(self):
        self.currentMode = self.sender().text()
        self.primaryScale.mode = self.sender().text()
        self.drawTitle()
        self.drawScale()  # print(self.currentMode)

    def setKey(self):
        self.primaryScale.key = self.sender().defaultWidget().text()
        # print(self.currentKey)
        self.drawScale()

    def about(self):
        about_dialog = AboutDlg(self)
        about_dialog.exec()

    def documentation(self):
        docs_dialog = DocsDig()
        docs_dialog.exec()

    def faq(self):
        faq_dialog = FaqDlg()
        faq_dialog.exec()

    def contact(self):
        cont_dialog = ContactDlg()
        cont_dialog.exec()


    def drawTitle(self):
        if not self.scaleFamilyGI:
            self.scaleFamilyGI = drawText(self.scene, [-380, -460], f"Family: {self.primaryScale.name}", size=20,
                                          position=Pos.RIGHT_CENTER)
        else:
            self.scaleFamilyGI.setPlainText(f"Family: {self.primaryScale.name}")

        if not self.modeGI:
            self.modeGI = drawText(self.scene, [-380, -420], f"Mode: {self.primaryScale.mode}", size=20,
                                   position=Pos.RIGHT_CENTER)
        else:
            self.modeGI.setPlainText(f"Mode: {self.primaryScale.mode}")

        self.chorder.drawChordKey(300, -440)

    def drawChromCircle(self, cx=0, cy=0, dia=600, pen=None):
        "this method draws the chromatic circle with intervals identified"
        if not pen:
            pen = self.pen.black

        for anItem in self.chromeCircleGraphics:
            self.scene.removeItem(anItem)
            del anItem
        self.chromeCircleGraphics = []

        r = dia / 2
        rt = r + 10  # radial offset for adding text outside circle
        ndia = 20  # note diameter

        intervals = ["Root", "min 2nd", "Maj 2nd", "min 3rd", "Maj 3rd", "Perfect\n 4th", "Tritone", "Perfect\n 5th",
                     "Min 6th", "Maj 6th", "min 7th", "Maj 7th"]

        drawCircle(self.scene, cx, cy, dia, pen)
        for indx, ang in enumerate([i * 30 for i in range(12)]):
            rad = pi * (ang + self.angOffset) / 180
            x = cx + r * cos(rad)
            y = cy + r * sin(rad)
            tx = cx + rt * cos(rad)
            ty = cy + rt * sin(rad)
            self.chromeCircleGraphics.append(
                    drawCircle(self.scene, x, y, ndia, self.pen.black, self.brush.white, noteId=indx,
                               acceptMousebuttons=self.scaleEditMode))
            self.chromeCircleGraphics.append(drawText(self.scene, [tx, ty], intervals[indx],
                                                      size=12, position=Pos.RADIAL_OUT, refPt=[cx, cy]))

    def getSelectedNotes(self):
        selnotes = []
        for anItem in self.chromeCircleGraphics:
            if isinstance(anItem, CircleGraphicsItem):
                if anItem.isSelected:
                    selnotes.append(anItem.noteId)
        return selnotes

    def unselectedAllNotes(self):
        for anItem in self.chromeCircleGraphics:
            if isinstance(anItem, CircleGraphicsItem):
                if anItem.isSelected:
                    anItem.setSelectedState(False)



    def drawScale(self):

        x0 = 0
        y0 = 0
        rmax = 300
        angOffset = self.angOffset
        pen = self.pen.black
        self.primaryScale.drawScale(x0, y0, rmax, angOffset, pen, self.chordNameLevel, self.chorder)
        self.stradella.draw_Stradella(0, 420,
                                      self.primaryScale.noteSemitonePositions,
                                      self.showStradella)

        if self.refScale:
            self.drawRefScale()

    def drawRefScale(self):
        # check that a key is selected
        if not self.primaryScale.key:
            dialog = QMessageBox(parent=self, text="You must select a key first")
            dialog.setWindowTitle("Message")
            ret = dialog.exec()  # Stores the return value for the button pressed
            return

        x0 = 0
        y0 = 0
        rmax = 200
        angOffset = self.angOffset
        pen = self.pen.red
        self.refScale.drawScale(x0, y0, rmax, angOffset, pen, self.chordNameLevel, self.chorder, alignNote=self.primaryScale.key)

    def print(self):
        print("create imgae called")

        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            #pixmap = QPixmap(self.view.viewport().size())
            painter = QPainter(printer)
            #self.view.render(painter)
            #painter.drawPixmap(0, 0, pixmap)
            self.scene.render(painter)
            painter.end()

            # Print the pixmap  # pixmap.print_(printer)

    def image(self):
        fileNameInfo = QFileDialog.getSaveFileName(self, "Save Image File", "", "png, jpeg, bmp")
        if len(fileNameInfo[0]) > 0:
            pixmap = self.grab()
            clipboard = QApplication.instance().clipboard()
            pixmap.save(fileNameInfo[0], fileNameInfo[1])

    def copy(self):
        pixmap = self.grab()
        clipboard = QApplication.instance().clipboard()
        clipboard.setPixmap(pixmap)

    def playSynth(self):
        '''
        Plays the scale on fluid synth
        :return:
        '''
        self.primaryScale.playScale(self.midiPortName, self.midiProgNum, self.midiTempo, self.midiNumOctaves, self.midiPattern)

    def randomrun(self):
        # setRef
        #   randomly choose a key,  scale family and mode
        # set primary to this new scaleinfo
        # repeat ...
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(1000)  #


    def update_ran(self):
        self.setRef()

        newsf = random.choice(list(self.scales.keys()))
        newScale = Scale(newsf, self.scales[newsf], self.scene)
        newMode = random.choice(newScale.modes)
        newScale.mode = newMode
        newKey = random.choice(Scale.allKeys[1:])
        newScale.key = newKey
        self.primaryScale.deleteGraphicItems()
        self.primaryScale = newScale

        self.drawScale()

        self.drawTitle()






if __name__ == '__main__':

    # You need one (and only one) QApplication instance per application.
    # Pass in sys.argv to allow command line arguments for your app.
    # If you know you won't use command line arguments QApplication([]) works too.
    app = QApplication([])

    # Create a Qt widget, which will be our window.

    window = MainWindow(args)
    window.show()  # IMPORTANT!!!!! Windows are hidden by default.

    # Start the event loop.
    app.exec()

    # Your application won't reach here until you exit and the event  # loop has stopped.
