'''
Created on Nov 10, 2024

@author: keith
'''
import math
import copy
import json
import time
import re
import logging
from collections import deque
from enum import Enum, property, Flag, auto
from math import sin, cos, pi, radians, sqrt

from PyQt6.QtCore import QSize, Qt, QPoint, QPointF, QSettings, QLineF, QRegularExpression, QUrl
from PyQt6.QtGui import QAction, QIcon, QBrush, QPen, QFont, QPainter, QPixmap, QRegularExpressionValidator, QColor
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, \
    QGraphicsTextItem, QGraphicsLineItem, QMessageBox, QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QRadioButton, \
    QComboBox, QWidgetAction, QCheckBox, QLineEdit, QGridLayout, QHBoxLayout, QPushButton, QButtonGroup, \
    QGroupBox, QLineEdit, QGraphicsRectItem, QTextBrowser, QFileDialog, QListWidget, QListWidgetItem

import mido

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


sharp = '<sup>#</sup>'
flat = '<sup>♭</sup>'

class Pos(Enum):
    LEFT_CENTER = 1
    CENTER = 2
    RIGHT_CENTER = 3
    RADIAL_IN = 4
    RADIAL_OUT = 5

class MidiPattern(Flag):
    # supports: opts = MidiPattern.LINEAR_UP | MidiPattern.LINEAR_DOWN; MidiPattern.PATTERN_UP in opts
    NONE = auto()
    LINEAR_UP = auto()
    LINEAR_DOWN = auto()
    PATTERN_UP = auto()
    PATTERN_DOWN = auto()
    ARPEGGIO_UP = auto()
    ARPEGGIO_DOWN = auto()


class RootPosition(Enum):
    R9 = 180
    R12 = -90
    R3 = 0
    R6 = 90


class ChordLevel(Enum):
    OFF = 0
    BASIC_ACCORD = 1
    ADV_ACCORD = 2
    ALL = 3

class ChordSymbol(Enum):
    RAW = 0
    JAZZ = 1
    COMMON = 2


class Brushes:
    def __init__(self):
        self.none = QBrush(Qt.BrushStyle.NoBrush)
        self.white = QBrush(Qt.GlobalColor.white)
        self.black = QBrush(Qt.GlobalColor.black)
        self.red = QBrush(Qt.GlobalColor.red)
        self.blue = QBrush(Qt.GlobalColor.blue)
        self.green = QBrush(Qt.GlobalColor.green)


class Pens:
    def __init__(self):
        self.black = QPen(Qt.GlobalColor.black)
        self.black.setWidth(3)
        self.red = QPen(Qt.GlobalColor.red)
        self.red.setWidth(3)
        self.blue = QPen(Qt.GlobalColor.blue)
        self.blue.setWidth(3)
        self.green = QPen(Qt.GlobalColor.green)
        self.green.setWidth(3)

def Cumulative(lists):
    cu_list = []
    length = len(lists)
    cu_list = [sum(lists[0:x:1]) for x in range(0, length + 1)]
    return cu_list[1:]

def drawText(scene, pt, text, size=10, position=Pos.CENTER, refPt=[0,0], tcolor=Qt.GlobalColor.black, txtWidth=None):
    ''' drawText draws text relative to the position of the bounding box.  x, y define where that
    boundary box position will be located.
    '''
    font = QFont('[bold]')
    # print(QFontInfo(font).family())
    font.setPointSize(size)
    strItem = QGraphicsTextItem()
    #strItem.setToolTip("This is the hover text")

    strItem.setDefaultTextColor(tcolor)
    strItem.setFont(font)

    if text[:3] == '<p>':
        strItem.setHtml(text)
    else:
        strItem.setPlainText(text)

    fm = strItem.font()

    if txtWidth is not None:
        if txtWidth > 0:
            strItem.setTextWidth(txtWidth)
        else:
            #Resize to Squarish shape  - This helps with radial positioning
            w = strItem.boundingRect().width()
            h = strItem.boundingRect().height()
            s = sqrt(w * h)
            strItem.setTextWidth(s)


    xoffset = 0
    yoffset = 0


    if position == Pos.CENTER:
        xoffset = strItem.boundingRect().center().x()
        yoffset = strItem.boundingRect().center().y()
    elif position == Pos.LEFT_CENTER:
        xoffset = strItem.boundingRect().bottomRight().x()
        yoffset = strItem.boundingRect().center().y()
    elif position == Pos.RIGHT_CENTER:
        xoffset = 0
        yoffset = strItem.boundingRect().center().y()
    elif position == Pos.RADIAL_IN:
        # For radial in the bounding Rect is used to position the text so that the
        # rect fits within the centered at refPt circle at point pt on the circle
        bby = math.fabs((strItem.boundingRect().center().y() - strItem.boundingRect().bottomRight().y()))
        bbx = math.fabs((strItem.boundingRect().center().x() - strItem.boundingRect().bottomRight().x()))
        logger.debug(f"***** bbx = {bbx}, bby = {bby}")
        bbang = math.atan(math.fabs(bby / bbx))
        dx = pt[0] - refPt[0]
        dy = pt[1] - refPt[1]
        ang = math.atan2(dy, dx)

        cang = math.atan(math.fabs(dy/dx))

        logger.debug(f"cnag = {math.degrees(cang)} while bbang = {math.degrees(bbang)}")
        if cang > bbang:
            if cang > math.radians(89):
                rbb = bby
            else:
                rbb = bby / math.sin(cang)
        else:
            if cang < math.radians(1):
                rbb = bbx
            else:
                rbb = bbx / math.cos(cang)

        logger.debug((f" rbb = {rbb}, angle = {math.degrees(ang)}"))
        xoffset =  rbb*math.cos(ang) + strItem.boundingRect().center().x()
        yoffset =  rbb*math.sin(ang) + strItem.boundingRect().center().y()
        logger.debug(f"x: {xoffset} is applied to {pt[0]}")
        logger.debug(f"y: {yoffset} is applied to {pt[1]}")

    elif position == Pos.RADIAL_OUT:
        # For radial out the bounding Rect is used to position the text so that the
        # rect fits outside the centered at refPt circle at point pt on the circle
        # ==================
        #  once resized to squarish shape the following data is availble:
        # pt = [x, y]  is the coordinate to position the text around.
        # refPt is the center of the circular object that the text is not to overlap with
        # strItem.boundingRect().center() is the text bounding box center x, y coordinates
        # strItem.boundingRect().bottomRight() is as it says the x coord if width/2, y is height/2
        # Goal: Position text so that some point on its bounding box includes pt.
        # The bounding box center, pt and refPt form a straight line.
        # Approach:
        #          1. Determine which bounding box edge contains pt
        #          2.
        logger.debug(f"Center point = {refPt}")
        logger.debug(pt)

        bby = math.fabs((strItem.boundingRect().center().y() - strItem.boundingRect().bottomRight().y()))
        bbx = math.fabs((strItem.boundingRect().center().x() - strItem.boundingRect().bottomRight().x()))
        logger.debug(f"***** bbx = {bbx}, bby = {bby}")
        bbang = math.atan(math.fabs(bby / bbx))

        #rpt = sqrt((pt[0] - refPt[0]) ** 2 + (pt[1] - refPt[1]) ** 2) #Radius of reference circle
        #logger.debug(f"Point passed to draw radius = {rpt}")

        dx = pt[0] - refPt[0]
        dy = pt[1] - refPt[1]
        ang = math.atan2(dy, dx)

        cang = math.atan(math.fabs(dy/dx))

        logger.debug(f"cnag = {math.degrees(cang)} while bbang = {math.degrees(bbang)}")
        if cang > bbang:
            if cang > math.radians(89):
                rbb = bby
            else:
                rbb = bby / math.sin(cang)
        else:
            if cang < math.radians(1):
                rbb = bbx
            else:
                rbb = bbx / math.cos(cang)

        logger.debug((f" rbb = {rbb}, angle = {math.degrees(ang)}"))
        xoffset =  -rbb*math.cos(ang) + strItem.boundingRect().center().x()
        yoffset =  -rbb*math.sin(ang) + strItem.boundingRect().center().y()
        logger.debug(f"x: {xoffset} is applied to {pt[0]}")
        logger.debug(f"y: {yoffset} is applied to {pt[1]}")


    newx = pt[0] - xoffset
    newy = pt[1] - yoffset

    strItem.setPos(QPointF(newx, newy))

    scene.addItem(strItem)

    rect = strItem.boundingRect()

    if txtWidth == -1:
        rectItem = QGraphicsRectItem(rect)
        rectItem.setPos(strItem.pos())
        scene.addItem(rectItem)

    return strItem


def drawCircle(scene, cx, cy, d, pen, brush=None, noteId=None, acceptMousebuttons=False):
    x = cx - d / 2
    y = cy - d / 2
    # x, y w h  (x,y are the lower left corner)
    ellipse = CircleGraphicsItem(x, y, d, noteId=noteId, acceptMousebuttons=acceptMousebuttons)
    ellipse.setPen(pen)
    if brush:
        ellipse.setBrush(brush)
    scene.addItem(ellipse)
    return ellipse


def drawLine(scene, x1, y1, x2, y2, pen=None):
    if not pen:
        pen = Pens.black

    # Define start and end points
    start = QPointF(x1, y1)
    end = QPointF(x2, y2)
    aline = QLineF(start, end)

    # Draw the line
    alineItem = QGraphicsLineItem(aline)
    alineItem.setPen(pen)
    scene.addItem(alineItem)
    return alineItem

class ScaleSelect(QDialog):
    def __init__(self, parent, prompt, scales, cfScales={}):
        '''
        ScaleSelect is used when saving and loading scales.  When saving scales pass the current
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

class MidiSettings(QDialog):
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
        self.linUpChkbox.setChecked(MidiPattern.LINEAR_UP in  self.parentWidget().midiPattern)
        self.linUpChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.linUpChkbox, 0, 0)

        self.linDwnChkbox = QCheckBox('linear down')
        self.linDwnChkbox.setChecked(MidiPattern.LINEAR_DOWN in  self.parentWidget().midiPattern)
        self.linDwnChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.linDwnChkbox, 1, 0)

        self.patUpChkbox = QCheckBox('Pattern up')
        self.patUpChkbox.setChecked(MidiPattern.PATTERN_UP in  self.parentWidget().midiPattern)
        self.patUpChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.patUpChkbox, 0, 1)

        self.patDwnChkbox = QCheckBox('Pattern down')
        self.patDwnChkbox.setChecked(MidiPattern.PATTERN_DOWN in  self.parentWidget().midiPattern)
        self.patDwnChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.patDwnChkbox, 1, 1)

        self.arpUpChkbox = QCheckBox('Arpagio up')
        self.arpUpChkbox.setChecked(MidiPattern.ARPEGGIO_UP in  self.parentWidget().midiPattern)
        self.arpUpChkbox.toggled.connect(self.newPattern)
        glayout.addWidget(self.arpUpChkbox, 0,2)

        self.arpDwnChkbox = QCheckBox('Arpagio down')
        self.arpDwnChkbox.setChecked(MidiPattern.ARPEGGIO_DOWN in  self.parentWidget().midiPattern)
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


class PrefEditor(QDialog):
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

class FindScale(QDialog):
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











class ScaleEditor(QDialog):
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


class CircleGraphicsItem(QGraphicsEllipseItem):
    def __init__(self, x, y, d, noteId=None, acceptMousebuttons=False, parent=None):
        super().__init__(x, y, d, d, parent)
        self.setAcceptHoverEvents(False)
        self.brushes = Brushes()
        self.noteId = noteId
        self.setSelectable(acceptMousebuttons)
        self.isSelected = False

    def setSelectable(self, state):
        if state:
            self.setAcceptedMouseButtons(Qt.MouseButton.AllButtons)
        else:
            self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def setSelectedState(self, state):
        if state:
            self.setBrush(self.brushes.green)
            self.isSelected = True
        else:
            self.setBrush(self.brushes.white)
            self.isSelected = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print("Left mouse button pressed on item")
            currentBrush = self.brush()
            if currentBrush.color() == Qt.GlobalColor.white:
                self.setBrush(self.brushes.green)
                self.isSelected = True
            else:
                self.setBrush(self.brushes.white)
                self.isSelected = False
        elif event.button() == Qt.MouseButton.RightButton:
            print("Right mouse button pressed on item")
        else:
            print("Middle mouse button pressed on item")

        # Call the default implementation to propagate the event
        super().mousePressEvent(event)


class Scale:
    '''
    The scale class encapsulates all data and methods for a particular scale family with 
    variable mode and key signature.
    '''
    allKeys = ["None", "C", "C" + sharp + '/D' + flat, "D", "D" + sharp + "/E" + flat, "E", "F",
               "F" + sharp + "/G" + flat, "G", "G" + sharp + "/A" + flat, "A", "A" + sharp + "/B" + flat, "B"]


    def __init__(self, name, scaleDef, scene):
        self.name = name
        logger.info(f"Scale created: {name}")
        logger.debug(scaleDef)
        self.modes = scaleDef[1]
        self.intervals = deque(scaleDef[0])
        self.modeIndx = 0
        self.scene = scene
        self._key = None
        self.GetNotePositions()
        self.ReorderNoteNames()
        self.graphicItems = []
        self.noteMidiNum = dict(zip(Scale.allKeys, [0, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71]))

    @property
    def mode(self):
        return self.modes[self.modeIndx]

    @mode.setter
    def mode(self, amode):
        try:
            self.modeIndx = self.modes.index(amode)
        except:
            logger.warn('Bad mode recalled')
        self.GetNotePositions()
        self.ReorderNoteNames()
        self.deleteGraphicItems()

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, newKey):
        if newKey == 'None':
            self._key = None
        else:
            self._key = newKey
        self.ReorderNoteNames()
        self.deleteGraphicItems()

    def GetNotes(self):
        return self.notes

    def NotePositions(self):
        return self.sindx

    def GetNotePositions(self):
        rotIntvls = self.intervals.copy()
        rotIntvls.rotate(-self.modeIndx)
        rotIntvls.appendleft(0)
        self.sindx = Cumulative(list(rotIntvls))
        logger.debug(f" scale index = {self.sindx}")

    def ReorderNoteNames(self):
        """Given the root note the 12 notes are reordered starting with the root note.
        Note that the first item in Scale.keys is 'none' that is why Scale.keys[1:] is
        used below as it starts with 'C'  """
        if self._key == "none" or not self._key:
            # no note was selected for the root, relative scale members will be shown with roman numerals
            self.notes = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'][:len(self.intervals)]
        else:
            # construct a chromatic list of 12 notes starting with the root
            offset = Scale.allKeys[1:].index(self._key)
            self.notes = [Scale.allKeys[1:][(i + offset) % len(Scale.allKeys[1:])] for i, x in
                          enumerate(Scale.allKeys[1:])]
            self.notes = [self.notes[i] for i in self.sindx[:-1]]





    def drawScale(self, x0, y0, rmax, angOffset, pen, chordLevel, chorder, alignNote=None):
        '''
        This method draws the scale centered at x0, y0 with a maximumradius of rmax,
        an angular offset (root position), QPen to use (color, etc), chordlevel to display (simple, all, etc.),
        and if the scale should be realigned to some other root position reference note. (None for primary, 
        primary root note for reference scale)
        '''
        # delete current scale graphics
        self.deleteGraphicItems()

        if alignNote:
            self.graphicItems.append(
                drawText(self.scene, [x0, y0 - 10], self.name, 14, position=Pos.CENTER, tcolor=pen.color()))
            self.graphicItems.append(
                drawText(self.scene, [x0, y0 + 10], self.mode, 14, position=Pos.CENTER, tcolor=pen.color()))
            semitoneDelta = Scale.allKeys.index(self._key) - Scale.allKeys.index(alignNote)
        else:
            semitoneDelta = 0

        start = (rmax * cos(radians(angOffset + (semitoneDelta * 30))),
                 rmax * sin(radians(angOffset + (semitoneDelta * 30))))
        pts = []

        chordNames, hoverText = chorder.getChordNames(self.sindx, self.notes, self.intervals, level=chordLevel)
        for scaleDeg, i in enumerate(self.sindx):
            a = radians(angOffset + (i + semitoneDelta) * 30)
            r = rmax
            x = r * cos(a)
            y = r * sin(a)

            rt = r * 1.12
            xt = rt * cos(a)
            yt = rt * sin(a)
            # print(f"Scale degree = {scaleDeg}, chromatic index = {i}")

            if i < 12:
                noteName = self.notes[scaleDeg]
                chName= chordNames[scaleDeg]
                gitem = drawText(self.scene, [0.85 * (xt + x0), 0.85 * (yt + y0)], chName, size=14, txtWidth=0,
                                 position=Pos.RADIAL_IN, refPt=[x0, y0], tcolor=pen.color())
                gitem.setToolTip(hoverText[scaleDeg])
                self.graphicItems.append(gitem)

            pts.append((x, y))
            self.graphicItems.append(drawCircle(self.scene, x + x0, y + y0, 10, pen))
            if scaleDeg == 0 and alignNote:
                self.graphicItems.append(drawCircle(self.scene, x + x0, y + y0, 16, pen))

        for pt in pts:
            stop = pt
            self.graphicItems.append(
                drawLine(self.scene, start[0] + x0, start[1] + y0, stop[0] + x0, stop[1] + y0, pen=pen))

            start = stop

    def deleteGraphicItems(self):
        logger.debug(f'deleting scale {len(self.graphicItems)} items')
        for anItem in self.graphicItems:
            # print(anItem)
            self.scene.removeItem(anItem)
            del anItem
        self.graphicItems = []

    def playNote(self, port, midiNote, duration):
        # Send MIDI message (e.g., note on)
        logger.debug(midiNote)
        msg = mido.Message('note_on', note=midiNote, velocity=127)
        port.send(msg)
        time.sleep(duration)
        # Send MIDI message (e.g., note off)
        msg = mido.Message('note_off', note=midiNote, velocity=0)
        port.send(msg)


    def playScale(self, midiPortName, progNum, tempo, octaves, scalePatterns):
        # Initialize MIDI output
        try:
            port = mido.open_output(midiPortName)  # Replace with the correct port name
        except:
            msgBox = QMessageBox()
            msgBox.setText("You must select a valid MIDI device's input port from Midi settings")
            msgBox.setWindowTitle("MIDI Port ERROR")
            msgBox.setIcon(QMessageBox.Icon.Critical)
            msgBox.setStandardButtons(QMessageBox.StandardButton.Ok )

            result = msgBox.exec()
            return

        # Set the program change message
        program_change = mido.Message('program_change', program=progNum, channel=0,
                                      time=10)  # Change to instrument 12 on channel 0
        port.send(program_change)

        noteDuration = 60 / tempo
        octaveOffsets = [0, 12, 24]

        # make assending semitone offsets from key
        keyNum = self.noteMidiNum[self.key]
        noteNumberSequence = [keyNum + st + octOff for octOff in octaveOffsets for st in self.sindx[:-1] ]
        noteNumberSequence.append(keyNum + 12 + octaveOffsets[-1])
        #print(noteNumberSequence)
        #print(scalePatterns)

        numOfNotesToPlay = ((len(self.sindx) - 1)* octaves ) + 1

        reversedNoteNumberSequence = list(reversed(noteNumberSequence))
        logger.debug(reversedNoteNumberSequence)
        revIndxToStartFrom = len(reversedNoteNumberSequence ) - numOfNotesToPlay

        if MidiPattern.LINEAR_UP in scalePatterns:
            for anote in noteNumberSequence[:numOfNotesToPlay]:
                self.playNote(port, anote, noteDuration)

        if MidiPattern.LINEAR_DOWN in scalePatterns:
            for anote in reversedNoteNumberSequence[revIndxToStartFrom:]:
                self.playNote(port, anote, noteDuration)

        if MidiPattern.PATTERN_UP in scalePatterns:
            for indx, anote in enumerate(noteNumberSequence[:numOfNotesToPlay]):
                self.playNote(port, anote, noteDuration)
                if indx < numOfNotesToPlay - 1:
                    self.playNote(port, noteNumberSequence[indx+1], noteDuration)
                    self.playNote(port, noteNumberSequence[indx+2], noteDuration)

        if MidiPattern.PATTERN_DOWN in scalePatterns:
            for indx,anote in enumerate(reversedNoteNumberSequence[revIndxToStartFrom:]):
                self.playNote(port, reversedNoteNumberSequence[revIndxToStartFrom+indx - 2], noteDuration)
                self.playNote(port, reversedNoteNumberSequence[revIndxToStartFrom+indx - 1], noteDuration)
                self.playNote(port, anote, noteDuration)

        if MidiPattern.ARPEGGIO_UP in scalePatterns:
            for indx, anote in enumerate(noteNumberSequence[:numOfNotesToPlay]):
                self.playNote(port, anote, noteDuration)
                self.playNote(port, noteNumberSequence[indx + 2], noteDuration)
                self.playNote(port, noteNumberSequence[indx + 4], noteDuration)

        if MidiPattern.ARPEGGIO_DOWN in scalePatterns:
            for indx, anote in enumerate(reversedNoteNumberSequence[revIndxToStartFrom:]):
                self.playNote(port, reversedNoteNumberSequence[revIndxToStartFrom + indx - 4], noteDuration)
                self.playNote(port, reversedNoteNumberSequence[revIndxToStartFrom + indx - 2], noteDuration)
                self.playNote(port, anote, noteDuration)

        # Close MIDI output
        port.close()

class Chorder():
    def __init__(self, chordSymbology):
        self.chordsymbology = chordSymbology
        if self.chordsymbology == ChordSymbol.RAW:
            self.rep = {'q':'q'}
        elif self.chordsymbology == ChordSymbol.COMMON:
            self.rep = {'sev':'<sup>7</sup>'}
        elif self.chordsymbology == ChordSymbol.JAZZ:
            self.rep = {'dim':'<sup>o</sup>',
                         'aug':'<sup>+</sup>',
                         'sev':'<sup>7</sup>',
                         'maj':'<span class="music-symbol" style="font-family: Arial Unicode MS, Lucida Sans Unicode;">Δ</span>',
                          'min':'-'}
        else:
            Exception("Chorder error due to chordsymbology unknow")


    def chordformater(self, raw):
        ''' reformats chord to a specific symbology'''
        rep = dict((re.escape(k), v) for k, v in self.rep.items())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], raw)
        return text

    def getChordNames(self, sindx, notes, sintervals, level=ChordLevel.OFF):
        '''
        this method takes a scale, the scale degree and the note at that scale degree and returns a string
        of chords at Note that fit in the scale.  This provides an aid in music composition as to what chords
        can be used within a particular scale.   There are multiple levels:
        Simple:min, maj, 7th, dim and aug
        all: min[6 7 M7], maj[6 7], 7th[b5], aug, dim, sus2 ...

        13th chords define the basic chord types.  If the 13th is missing, then the 9th, 7th, and triad are checked.
        All thes chords are named by the highest note. Ex Cmaj13, Cmaj9, Cmaj7, Cmaj, C13, C9, C7, Cmin13, Cmin9, Cmin

        maj13 =
        min13
        dom13 =


        '''

        basicChordTypes = {(4, 7, 10): {'7<sup>th</sup>': ['?']}, (4, 7): {'maj': ['?']}, (3, 7): {'min': ['?']},
                           (3, 6): {'dim': ['?']}}

        advChordTypes = {(4, 8): {'aug': ['?']}, (2, 7): {'sus2': ['?']}}  # C+(9), C6, C6/E

        allChordtypes = {(5, 7): {'sus4': ['?']}, (2, 5, 7): {'sus24': ['?']}}

        accidentals = {(2, 5, 9): {'13<sup>th</sup>': ['?']}, (2, 5): {'11<sup>th</sup>': ['?']},
                       (2): {'9<sup>th</sup>': ['?']}}

        nydanaIntervals = {(0, 4, 7): {'maj': ['maj']},
                           (0, 3, 7): {'min': ['min']},
                           (0, 4, 7, 10): {'7<sup>th</sup>': ['7th']},
                           (4, 8): {'aug': ['R-4, 7th']},
                           (0, 3, 6): {'dim': ['R, dim', 'R, dim-3', 'R_, dim+1'],
                                       'm(-5)': ['R, dim-3', 'R_, dim+1']},
                           (0, 2, 7, 10): {'7sus2': ['R, min+1'], '9(≠3)': ['R, min+1']},
                           (0, 3, 6, 9): {'dim7': ['R, dim-3, dim', 'R_, dim-2, (dim+1)', 'R_, dim-2, (dim-5)']},
                           (0, 2, 4, 8): {'(+5, 9)': ['R_, sev-4']},
                           (0, 4, 7, 9): {'6': ['R, min+3, (maj)'], '6/R+4': ['R+4, min-1, (maj-4)'],
                                          '6/R+7': ['R+7, min+2, (maj-1)'],
                                          '6/R+9': ['R+9, maj-3, (min)', 'R_+9, maj+1']},
                           (0, 1, 4, 7, 9): {'6(m9)': ['R, maj+3, (maj)']},
                           (0, 4, 6, 9): {'6(-5)': ['R_, dim-5, min-5']},
                           (0, 4, 7, 10): {'7': ['R, sev, (maj)', 'R, dim+1, (maj)'], '7/R+10': ['R+10, maj+2']},
                           (0, 1, 4, 7, 10): {'7(m9)': ['R, maj, dim-2', 'R, sev, dim-2'],
                                              '7(m9)/R+10': ['R+10, dim, maj+2']},
                           (0, 1, 7, 10): {'7(≠3, m9)': ['R, dim-2']},
                           (0, 3, 4, 7, 10): {'7(m10)': ['R, min, sev', 'R, min, dim+1', 'R, maj-3, sev'],
                                              '7(m10)/R+7': ['R+7, min-1, dim', 'R+7, min-1, sev-1']},
                           (0, 4, 9, 10): {'7(13)': ['R, sev, min+3']},
                           (0, 4, 6, 10): {'7(-5)': ['R, sev-6', 'R_, sev-2']},
                           (0, 3, 4, 6, 10): {'7(-5, m10)': ['R, dim-3, sev']},
                           (0, 4, 6, 8, 10): {'7(+5, +11)': ['R, sev-4, sev']},

                           (0, 1, 5, 7, 10): {'7sus4(m9)': ['R, min-2, dim-2'], '11(m9)': ['R, min-2, (dim-2)']},
                           (0, 2, 4, 7, 10): {'9': ['R, maj, min+1', 'R, sev, min+1', 'R, min+1, dim+1'],
                                              '9/R+2': ['R+2, maj-2, dim-1'], '9/R+7': ['R+7, min, sev-1']},
                           (0, 2, 4, 6, 10): {'9(-5)': ['R, sev, sev+2']},
                           (0, 2, 4, 8, 10): {'9(+5)': ['R, sev-2, sev', 'R_, sev-4, sev+2']},
                           (0, 2, 8, 10): {'9(≠3, +5)': ['R, sev-2']},
                           (0, 2, 5, 7, 10): {'9sus4': ['R, maj-2, min+1'], '11': ['R, maj-2, (min+1)']},
                           (0, 2, 5, 8, 10): {'11(+5)': ['R, maj-2, dim-1', 'R, maj-2, min-1']},
                           (0, 2, 6, 7, 10): {'11(+11)': ['R, min+1, sev+2']},
                           (0, 2, 4, 7, 9, 10): {'13': ['R, min+1, min+3'], '13/R+4': ['R+4, min-3, min-1']},
                           (0, 2, 4, 5, 9, 10): {'13': ['R, sev, min+2']},
                           (0, 4, 5, 9, 10): {'13': ['R, maj-1, sev']},
                           (0, 2, 5, 7, 9, 10): {'13(≠3)': ['R, maj-1, min+1', 'R, min+1, min+2']},
                           (0, 2, 5, 9, 10): {'13(≠3)': ['R, maj-1, maj-2']},
                           (0, 1, 4, 9, 10): {'13(m9)': ['R, sev, maj+3']},
                           (0, 2, 4, 6, 9, 10): {'13(+11)': ['R, sev, maj+2']},
                           (0, 2, 4, 6, 7, 9, 10): {'13(+11)': ['R, dim+1, maj+2']},
                           (0, 4, 6, 9, 10): {'13(+11)': ['R, sev, dim+3']},
                           (0, 4, 7, 11): {'maj7': ['R, min+4, (maj)', 'R_, min-4']},
                           (0, 4, 8, 11): {'maj7(+5)': ['R, maj+4']},
                           (0, 2, 4, 7, 11): {'maj9': ['R, maj, maj+1', 'R, maj+1, min+4'],
                                              'maj9/R+2': ['R+2, maj-1, maj-2']},
                           (0, 2, 7, 11): {'maj9(≠3)': ['R, maj+1']},
                           (0, 2, 4, 8, 11): {'maj9(+5)': ['R_, maj-4, sev-4', 'R_, sev-4, dim-3']},
                           (0, 2, 5, 11): {'maj11': ['R, dim+2']},
                           (0, 2, 5, 7, 11): {'maj11': ['R, maj+1, sev+1']},
                           (0, 2, 5, 8, 11): {
                               'maj11(+5)': ['R_, dim, (dim-3)', 'R, min-1, dim+2', 'R, dim-1, dim+2']},
                           (0, 2, 4, 7, 9, 11): {'maj13': ['R, maj+1, min+3']},
                           (0, 4, 7, 9, 11): {'maj13': ['R_, min-4, min-5']},
                           (0, 2, 5, 7, 9, 11): {'maj13(≠3)': ['R, maj-1, maj+1']},
                           (0, 2, 4, 6, 7, 9, 11): {'maj13(+11)': ['R, maj+2, min+4']},
                           (0, 2, 4, 6, 9, 11): {'maj13(+11)': ['R_, min-5, min-3']},
                           (0, 1, 3, 7): {'m(m9)': ['R, sev-3, (min)', 'R_, sev+1']},
                           (0, 3, 6, 8): {'m(-5, m6)': ['R_, maj, sev']},
                           (0, 2, 3, 6): {'m(-5, 9)': ['R, dim-3, sev+2']},
                           (0, 3, 8): {'m(+5)': ['R, maj-4', 'R_, maj']},
                           (0, 3, 7, 9): {'m6': ['R, dim, (min)'], 'm6/R+3': ['R_+3, dim-5, (min-5)'],
                                          'm6/R+7': ['R+7, dim-1, (min-1)'],
                                          'm6/R+9': ['R+9, min-3, (dim-3)', 'R_+9, min+1, (dim+1)']},
                           (0, 1, 3, 7, 9): {'m6(m9)': ['R, min, sev+3']},
                           (0, 3, 7, 10): {'m7': ['R, maj-3, (min)', 'R_, maj+1'],
                                           'm7/R+10': ['R+10, min+2, (maj-1)']},
                           (0, 1, 3, 7, 10): {'m7(m9)': ['R, maj-3, sev-3', 'R, sev-3, dim-2', 'R, maj-3, dim-2']},
                           (0, 3, 6, 10): {'m7(-5)': ['R, min-3', 'R_, min+1'], 'm7(-5)/R+3': ['R+3, min, dim'],
                                           'm7(-5)/R+6': ['R_+6, min-5, dim-5'],
                                           'm7(-5)/R+10': ['R+10, dim-1, (min-1)']},
                           (0, 3, 6, 8, 10): {'m7(-5, m6)': ['R_, maj, min+1']},
                           (0, 2, 3, 7, 10): {'m9': ['R, min, min+1', 'R, maj-3, min+1'],
                                              'm9/R+2': ['R+2, min-2, min-1', 'R+2, maj-5, min-2']},
                           (0, 2, 3, 5, 7, 10): {'m9/R+5': ['R+5, min+1, min+2'],
                                                 'm11': ['R, maj-2, min', 'R, maj-3, maj-2']},
                           (0, 2, 3, 6, 10): {'m9(-5)': ['R, min-3, sev+2']},
                           (0, 2, 3, 7, 9, 10): {'m13': ['R, min+1, dim']},
                           (0, 3, 7, 9, 10): {'m13': ['R, maj-3, dim', 'R_, maj+1, dim+4']},
                           (0, 2, 3, 6, 9, 10): {'m13(+11)': ['R, min-3, maj+2']},
                           (0, 3, 6, 9, 10): {'m13(+11)': ['R_, min+1, dim-2']},
                           (0, 2, 3, 5, 8, 10): {'m13(m13)': ['R, maj-4, maj-2']},
                           (0, 3, 6, 11): {'mMaj7(-5)': ['R_, maj-3, (dim+1)']},
                           (0, 3, 8, 11): {'mMaj7(+5)': ['R_, min, (maj)']},
                           (0, 2, 3, 7, 11): {'mMaj9': ['R, min, maj+1']},
                           (0, 2, 3, 8, 11): {'mMaj9(+5)': ['R_, dim-3, min']},
                           (0, 3, 5, 7, 11): {'mMaj11': ['R, min, sev+1']},
                           (0, 2, 3, 5, 7, 11): {'mMaj11': ['R, min, dim+2']},
                           (0, 2, 3, 6, 11): {'mMaj11(+11)': ['R_, maj-3, min-3', 'R_, maj-3, sev-6']},
                           (0, 3, 5, 7, 9, 11): {'mMaj13': ['R, dim, sev+1']},
                           (0, 2, 3, 7, 9, 11): {'mMaj13': ['R, maj+1, dim']},
                           (0, 2, 3, 5, 9, 11): {'mMaj13': ['R, dim, dim+2']},
                           (0, 3, 6, 9, 11): {
                               'mMaj13(+11)': ['R_, maj-3, sev-3', 'R_, maj-3, dim-5', 'R_, dim-5, sev-3']},
                           (0, 3, 5, 8, 11): {'mMaj13(m13)': ['R_, maj, dim', 'R_, min, dim', 'R, min-4, min-1']}}

        chordTypes = nydanaIntervals
        chordNames = []
        hovertext = []
        #print(notes)

        logger.debug(f'ChordLevel: {level}')

        if level == ChordLevel.BASIC_ACCORD:
            ctstop = 4
        elif level == ChordLevel.ADV_ACCORD:
            ctstop = 20
        elif level == ChordLevel.ALL:
            ctstop = len(chordTypes.keys())

        for scaleDeg in range(len(sindx) - 1):

            if level == ChordLevel.OFF:
                chordNames.append(f'<p>{notes[scaleDeg]} </p>')
                hovertext.append("Change displayed chords \nthru edit->preference")
            else:
                intervals = sintervals.copy()
                intervals.rotate(-scaleDeg)
                intervals = deque(list(intervals))

                semitones = Cumulative(list(intervals))
                semitones.insert(0, 0)
                logger.debug(f"{scaleDeg}, {semitones}")

                cName = ''
                htxt = ''
                for ctindx, achdtypints in enumerate(chordTypes):
                    if ctindx > ctstop:
                        if len(cName) != 0:
                            continue
                    if all(elem in semitones for elem in achdtypints):
                        for chdName in chordTypes[achdtypints]:
                            fullChdNam = self.chordformater(chdName)
                            hoverTxt = chordTypes[achdtypints][chdName][0]  # TODO:

                            break  # TODO:

                        if len(cName) == 0:
                            cName =  fullChdNam
                            htxt =  hoverTxt
                        else:
                            cName = cName + ', ' + fullChdNam
                            htxt = htxt + ', \n' + hoverTxt
                # print(self.notes)
                if len(cName) == 0:
                    cName = f'<p>{notes[scaleDeg]}: {semitones} </p>'
                else:
                    cName = f'<p>{notes[scaleDeg]}: ' + cName + '</p>'

                chordNames.append(cName)
                hovertext.append(htxt)
                #print(chordNames)
                #print(hovertext)

        return (chordNames, hovertext)

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scale Smithy")
        self.label = QLabel("Scale Smithy v0.1")
        self.button = QPushButton("Close")
        self. button.clicked.connect(self.accept)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

class DocsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("docs")

        self.layout = QVBoxLayout()
        self.backward_button = QPushButton("<")
        self.forward_button = QPushButton(">")

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.backward_button)
        hlayout.addWidget(self.forward_button)
        hlayout.addStretch()
        self.layout.addLayout(hlayout)

        self.label = QLabel("Table of contents")
        self.tb = QTextBrowser(minimumWidth=800, minimumHeight=600)
        self.tb.document().setDefaultStyleSheet(
            'body {color: #333; font-size: 14px;} '
            'h2 {background: #CCF; color: #443;} '
            'h1 {background: #001133; color: white;} '
        )

        # TextBrowser background is a widget style, not a document style
        self.tb.setStyleSheet('background-color: #EEF;')
        iurl = QUrl('help/index.html')
        self.tb.setSource(iurl)
        # with open('index.html', 'r') as fh:
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

class FaqDialog(QDialog):
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
        with open('faq.html', 'r') as fh:
            self.tb.insertHtml(fh.read())

        self.tb.setAcceptRichText(True)
        self.tb.setOpenExternalLinks(True)
        self.button = QPushButton("Close")
        self.button.clicked.connect(self.accept)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.tb)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

class ContactDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AContact")
        self.label = QLabel("keith@github.com")
        self.button = QPushButton("Close")
        self.button.clicked.connect(self.accept)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info('\nScale Smithy Started.  The configuration file being used is:')
        self.settings = QSettings("santabayanian", "ScaleSmithy")
        logger.info(self.settings.fileName())
        # fdb = QFontDatabase()
        # print(fdb.families())
        priScaleName, priScaleMode, priScaleKey, refScaleName, refScaleMode, refScaleKey = self.readSettings()
        self.setStyleSheet("QMainWindow { border: 1px solid black; }")
        # print(self.chordNameLevel)
        self.angOffset = float(self.rootPos.value)

        self.chorder = Chorder(self.chordSymbology)

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
        createPDF_action = QAction(QIcon("bug.png"), "Create &PDF", self)
        file_menu.addAction(createPDF_action)

        # Edit Menu
        edit_menu = menu.addMenu("&Edit")
        fscEdit = QAction("Find Scale", self)
        fscEdit.triggered.connect(self.findScale)
        edit_menu.addAction(fscEdit)
        scEdit = QAction("Scale editor", self)
        scEdit.triggered.connect(self.scaleEdit)
        edit_menu.addAction(scEdit)
        scDel = QAction("Delete scale", self)
        scDel.triggered.connect(self.scaleDelete)
        edit_menu.addAction(scDel)
        scRst = QAction("Restore Default Scales", self)
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

        # draw chromatic circle and stradella layout 
        self.drawChromCircle()
        self.draw_Stradella(0, 420)

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

        dlg = ScaleSelect(self, "Select which scales to save to file", self.scales)
        if dlg.exec():
            with open(fileName, "w") as fp:
                json.dump(dlg.getSelectedScales(), fp)

    def load(self):
        fileNameInfo = QFileDialog.getOpenFileName(self, "Load Scales", "", "JSON Files (*.json)")
        with open(fileNameInfo[0], "r") as fp:
            ldscales = json.load(fp)
        dlg = ScaleSelect(self, ("Select which scales to load from file.\n" +
                                 "Red indicates a conflict that will \n" +
                                 "overwrite an existing scale"),ldscales, self.scales)
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
        dlg = FindScale(self.scales)
        if dlg.exec():
            logger.debug("set to this scale")
            self.primaryScale.deleteGraphicItems()
            if dlg.found:
                scaleName = dlg.scalefamily
                self.primaryScale = Scale( dlg.scalefamily, self.scales[ dlg.scalefamily], self.scene)
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

        dlg = ScaleEditor(self.scaleEditMode, self)
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
        dlg = PrefEditor(self, self.chordNameLevel, self.chordSymbology, self.rootPos)
        if dlg.exec():
            print("Success!")
            self.chordNameLevel = dlg.chordLevel
            self.chordSymbology = dlg.chordSymbol
            self.chorder = Chorder(self.chordSymbology)
            self.rootPos = dlg.rootPos
            self.angOffset = float(self.rootPos.value)
            self.drawChromCircle()
            self.drawScale()

        else:
            print("Cancel!")

    def midiSettings(self):
        dlg = MidiSettings(self)
        if dlg.exec():
            print('success')

    def clearRef(self):
        if self.refScale:
            self.refScale.deleteGraphicItems()
            self.refScale = None

    def setRef(self):
        self.clearRef()
        refScaleName = copy.copy(self.primaryScale.name)
        refScaleMode = copy.copy(self.primaryScale.mode)
        refScaleKey = copy.copy(self.primaryScale.key)
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
        about_dialog = AboutDialog()
        about_dialog.exec()

    def documentation(self):
        docs_dialog = DocsDialog()
        docs_dialog.exec()

    def faq(self):
        faq_dialog = FaqDialog()
        faq_dialog.exec()

    def contact(self):
        cont_dialog = ContactDialog()
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
                                                      size=12, position=Pos.RADIAL_OUT, refPt=[cx,cy]))

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

    def draw_Stradella(self, x0, y0):
        # Draws the bass and couter-bass rows relative to each other
        buttonR = 23
        spacing = 2.25 * buttonR
        numOfRows = 14
        xOffset = (numOfRows * spacing) / 2
        rOffset = buttonR / 2
        yOffset = spacing / 2
        keyints = [['P4', 'R', 'P5', 'M2', 'M6', 'M3', 'M7', 'T', 'm2', 'm6', 'm3', 'm7', 'P4', 'R'],
                   ['m2', 'm6', 'm3', 'm7', 'P4', 'R', 'P5', 'M2', 'M6', 'M3', 'M7', 'T', 'm2', 'm6']]
        for xindx in range(numOfRows):
            for yindx in range(2):
                x = x0 + (xindx * spacing) - xOffset + (yindx * rOffset)
                y = y0 + (yindx * spacing) - yOffset
                drawCircle(self.scene, x, y, 2 * buttonR, self.pen.black)
                text = keyints[yindx][xindx]
                drawText(self.scene, [x, y], text, size=16)

    def drawScale(self):

        x0 = 0
        y0 = 0
        rmax = 300
        angOffset = self.angOffset
        pen = self.pen.black
        self.primaryScale.drawScale(x0, y0, rmax, angOffset, pen, self.chordNameLevel, self.chorder)

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
        chordLevel = ChordLevel.OFF
        self.refScale.drawScale(x0, y0, rmax, angOffset, pen, chordLevel, self.chorder, alignNote=self.primaryScale.key)

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
    def playSynth(self):
        '''
        Plays the scale on fluid synth
        :return:
        '''
        self.primaryScale.playScale(self.midiPortName, self.midiProgNum, self.midiTempo, self.midiNumOctaves, self.midiPattern)


if __name__ == '__main__':
    # You need one (and only one) QApplication instance per application.
    # Pass in sys.argv to allow command line arguments for your app.
    # If you know you won't use command line arguments QApplication([]) works too.
    app = QApplication([])

    # Create a Qt widget, which will be our window.
    window = MainWindow()
    window.show()  # IMPORTANT!!!!! Windows are hidden by default.

    # Start the event loop.
    app.exec()

    # Your application won't reach here until you exit and the event  # loop has stopped.
