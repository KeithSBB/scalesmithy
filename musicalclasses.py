'''
musicalclasses contains classes for musical objects such as Scales, chord creation
etc.  They also handle creation and deletion of PyQt graphical items
'''
import logging
import re
import time
from collections import deque
from enum import property, Enum, Flag, auto
from math import cos, radians, sin

import mido
from PyQt6.QtCore import QPointF

from PyQt6.QtWidgets import  QMessageBox, QGraphicsPolygonItem

from utils import Cumulative, drawText, Pos, drawCircle, drawLine, Pens, TextPentagonContainer

logger = logging.getLogger(__name__)

sharp = '<sup>#</sup>'
flat = '<sup>♭</sup>'


class ChordLevel(Enum):
    OFF = 0
    BASIC_ACCORD = 1
    ADV_ACCORD = 2
    ALL = 3


class ChordSymbol(Enum):
    RAW = 0
    JAZZ = 1
    COMMON = 2


class Scale:
    '''
    The scale class encapsulates all data and methods for a particular scale family with
    variable mode and key signature.
    param name:  The name of the scale family
    param scaleDef: A two element list containing:
                                firstModeIntervals in scaledef[0]
                                list of mode names in scaleDef[1]
    param scene:  The pyQt6 scene

    Note: firstModeIntervals are the intervals for the first (0 index) mode in semitones between the
          root tone - > 2nd scale degree,   2nd scale degree -> 3rd,
          3rd -> 4th, .... last scale degree -> root.  If there are 7 notes in a
          scale then there will be 7 intervals.  For octave scales the sum of the intervals = 12
          EX: Diatonic: Ionion mode (Maj): [2, 2, 1, 2, 2, 2, 1]
    '''
    allKeys = ["None", "C", "C" + sharp + '/D' + flat, "D", "D" + sharp + "/E" + flat, "E", "F",
               "F" + sharp + "/G" + flat, "G", "G" + sharp + "/A" + flat, "A", "A" + sharp + "/B" + flat, "B"]

    def __init__(self, name, scaleDef, scene):
        self.name = name
        logger.info(f"Scale created: {name}")
        logger.debug(scaleDef)
        self.modes = scaleDef[1]
        self.firstModeIntervals = deque(scaleDef[0])
        self.modeIndx = 0
        self.scene = scene
        self._key = None
        self._noteSemitonePositions = []
        self._notes = []
        self.CalculateModeNotePositions()
        self.CalculateNoteNames()
        self.graphicItems = []
        self.noteMidiNum = dict(zip(Scale.allKeys, [0, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71]))

    @property
    def numOfNotes(self):
        return len(self.firstModeIntervals)

    @property
    def mode(self):
        return self.modes[self.modeIndx]

    @mode.setter
    def mode(self, amode):
        try:
            self.modeIndx = self.modes.index(amode)
        except:
            logger.warning('Bad mode recalled')
        self.CalculateModeNotePositions()
        self.CalculateNoteNames()
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
        self.CalculateNoteNames()
        self.deleteGraphicItems()

    @property
    def notes(self):
        return self._notes

    @property
    def noteSemitonePositions(self):
        return self._noteSemitonePositions

    def CalculateModeNotePositions(self):
        self._noteSemitonePositions = self.getModeDegRelPositions(self.modeIndx)
        logger.debug(f" scale index = {self._noteSemitonePositions}")

    def getModeDegRelPositions(self, modeIndx, scaledeg=1):
        rotIntvls = self.firstModeIntervals.copy()
        rotIntvls.rotate(-(self.modeIndx + scaledeg - 1))
        rotIntvls.appendleft(0)
        return Cumulative(list(rotIntvls))

    def CalculateNoteNames(self):
        """Given the root note the 12 notes are reordered starting with the root note.
        Note that the first item in Scale.keys is 'none' that is why Scale.keys[1:] is
        used below as it starts with 'C'  """
        if self._key == "none" or not self._key:
            # no note was selected for the root, relative scale members will be shown with roman numerals
            self._notes = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'][:self.numOfNotes]
        else:
            # construct a chromatic list of 12 notes starting with the root
            offset = Scale.allKeys[1:].index(self._key)
            self._notes = [Scale.allKeys[1:][(i + offset) % len(Scale.allKeys[1:])] for i, x in
                           enumerate(Scale.allKeys[1:])]
            self._notes = [self.notes[i] for i in self._noteSemitonePositions[:-1]]

    def drawScale(self, centerPt, rs, angOffset, pen, chordLevel, chorder, alignNote=None, chordTextDepthFactor=0.75):
        '''
        This method draws the scale centered at x0, y0 with a radius of rs,
        an angular offset (root position), QPen to use (color, etc), chordlevel to display (simple, all, etc.),
        and if the scale should be realigned to some other root position reference note. (None for primary,
        primary root note for reference scale)
        '''
        # delete current scale graphics
        self.deleteGraphicItems()

        # If this is a reference scale (alignNote) then draw the scale family and mode in the center
        #  and calculate the semitone delate required to align notes between the primary and reference.
        if alignNote:
            self.graphicItems.append(
                    drawText(self.scene, centerPt - QPointF(0, 10), self.name, 14, position=Pos.CENTER, pen=pen))
            self.graphicItems.append(
                    drawText(self.scene, centerPt + QPointF(0, 10), self.mode, 14, position=Pos.CENTER, pen=pen))
            semitoneDelta = Scale.allKeys.index(self._key) - Scale.allKeys.index(alignNote)
        else:
            semitoneDelta = 0

        rt = 0.97 * rs
        if logger.getEffectiveLevel() == logging.DEBUG:
            refPtItem = drawCircle(self.scene, centerPt, 2 * rt, Pens().blue)
            self.graphicItems.append(refPtItem)

        # # statrPt is used to draw the side of the scale polygon.
        # startPt = QPointF(rs * cos(radians(angOffset + (semitoneDelta * 30))) + x0,
        #            rs * sin(radians(angOffset + (semitoneDelta * 30))) + y0)

        # scaleDeg starts with 0, not 1
        # note: increease in scale degree is CW while angle is CCW
        for scaleDeg, semitoneIndx in enumerate(self._noteSemitonePositions):
            a = radians(angOffset - (semitoneIndx + semitoneDelta) * 30)

            # coordinates of scale vertex at semitone position
            x = rs * cos(a) + centerPt.x()
            y = rs * sin(a) + centerPt.y()
            vtxPt = QPointF(x, y)

            # xt and yt are the text reference point that all text is to lie within radial to x0, y0
            xt = rt * cos(a) + centerPt.x()
            yt = rt * sin(a) + centerPt.y()

            refPt = QPointF(xt, yt)

            # This section calculates the chords for the current scaledeg and draws them
            if semitoneIndx < 12:
                noteName = self.notes[scaleDeg]
                logger.debug(f"========== {noteName} ==========")
                relchordtonepos = self.getModeDegRelPositions(self.modeIndx, scaleDeg + 1)

                logger.debug(f"INPUT TO CHORDER:  has {relchordtonepos}")
                chNames, hoverTexts = chorder.getChordNames(noteName, relchordtonepos)

                tmpgitems = []
                popuplist = []
                for cindx, chName in enumerate(chNames):
                    # This is where the graphical text items are created, all at the same point
                    if cindx == 0:
                        gitem = drawText(self.scene, QPointF(xt, yt),
                                         chName, size=14, position=Pos.RADIAL_IN, pen=pen)
                        self.graphicItems.append(gitem)
                        tmpgitems.append(gitem)

                    # if len(hoverTexts[cindx]) > 0:
                    #     gitem.setToolTip(hoverTexts[cindx])

                    if cindx > 0:
                        if chorder.chordLevel == ChordLevel.ALL:
                            popuplist.append([chName, hoverTexts[cindx]])
                        else:
                            gitem = drawText(self.scene, QPointF(xt, yt), chName, size=14, pen=pen)
                            self.graphicItems.append(gitem)
                            tmpgitems.append(gitem)
                            gitem.setToolTip(hoverTexts[cindx])

                if chorder.chordLevel == ChordLevel.ALL:
                    gitem = drawText(self.scene, QPointF(xt, yt), popuplist, size=14, pen=pen)
                    self.graphicItems.append(gitem)
                    tmpgitems.append(gitem)

                '''Approach
                change tmpgitems into a queue where items and be read and popped off it
                While tmpgitems is not empty:
                1. start with the first graphicaltextitem in the queue which is the note or scaledeg
                    by placing it in the vertex position
                2. Read the next item in tmptems
                3. Position item in the next otter ring referenced to the
                    previous item in the queue and the txtpolygonitem edges or other items 
                4. check that the item point are not outside the txtpoly boundary. If they are then
                   reposition the item to yet another outter ring and go back to step 3.  If the entire item is outside the
                   txtpoly then stop.  Otherwise,
                5. pop the item off tmpgitems. 
                6. repeat while..
                '''
                # tmpgitem contains all the text graphic items and their bounding rectangles
                # these will be used to adjust their postions for good layout



                # txtPoly defines a pentagon boundery that reqires text to stay within it
                txtPoly = TextPentagonContainer( relchordtonepos, rt, vtxPt, centerPt, chordTextDepthFactor )
                txtPoly.gTxtItems = tmpgitems
                txtPoly.layoutGrphTxtItems()

                if logger.getEffectiveLevel() == logging.DEBUG:
                    polyItem = QGraphicsPolygonItem(txtPoly)
                    self.scene.addItem(polyItem)
                    self.graphicItems.append(polyItem)


            scpt = QPointF(x, y)
            # Draw a small circle at the scaledeg  vertex
            self.graphicItems.append(drawCircle(self.scene, scpt, 10, pen))

            # if ref scale (alignNote) draw an additional circle to identify the root
            if scaleDeg == 0 and alignNote:
                self.graphicItems.append(drawCircle(self.scene, scpt, 16, pen))

            # draw a side of the scale polygon
            if scaleDeg > 0:
                self.graphicItems.append(drawLine(self.scene, startPt, scpt, pen=pen))
            startPt = QPointF(x, y)

    def deleteGraphicItems(self):
        logger.debug(f'deleting scale {len(self.graphicItems)} items')
        for anItem in self.graphicItems:
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
            msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)

            result = msgBox.exec()
            return

        if not self._key:
            msgBox = QMessageBox()
            msgBox.setText("You must select a key note for the scale root first")
            msgBox.setWindowTitle("MIDI Play ERROR")
            msgBox.setIcon(QMessageBox.Icon.Critical)
            msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)

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
        noteNumberSequence = [keyNum + st + octOff for octOff in octaveOffsets for st in
                              self.noteSemitonePositions[:-1]]
        noteNumberSequence.append(keyNum + 12 + octaveOffsets[-1])

        numOfNotesToPlay = ((len(self.noteSemitonePositions) - 1) * octaves) + 1

        reversedNoteNumberSequence = list(reversed(noteNumberSequence))
        logger.debug(reversedNoteNumberSequence)
        revIndxToStartFrom = len(reversedNoteNumberSequence) - numOfNotesToPlay

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
                    self.playNote(port, noteNumberSequence[indx + 2], noteDuration)
                    #self.playNote(port, noteNumberSequence[indx + 2], noteDuration)

        if MidiPattern.PATTERN_DOWN in scalePatterns:
            for indx, anote in enumerate(reversedNoteNumberSequence[revIndxToStartFrom:]):
                self.playNote(port, reversedNoteNumberSequence[revIndxToStartFrom + indx - 2], noteDuration)
               # self.playNote(port, reversedNoteNumberSequence[revIndxToStartFrom + indx - 1], noteDuration)
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
    def __init__(self, scene, chordSymbology, level=ChordLevel.OFF):
        self.scene = scene
        self.symbology = chordSymbology
        self.chordLevel = level
        self.graphicItems = []

    @property
    def chordLevel(self):
        return self.level

    @chordLevel.setter
    def chordLevel(self, newLevel):
        self.level = newLevel

    @property
    def symbology(self):
        return self.chordsymbology

    @symbology.setter
    def symbology(self, newSym):
        self.chordsymbology = newSym

        if self.chordsymbology == ChordSymbol.RAW:
            self.rep = {'q': 'q'}
        elif self.chordsymbology == ChordSymbol.COMMON:
            self.rep = {'sev': '<sup>7</sup>'}
        elif self.chordsymbology == ChordSymbol.JAZZ:
            self.rep = {'dim': '<sup>o</sup>', 'aug': '<sup>+</sup>', 'sev': '<sup>7</sup>',
                        'maj': '<span class="music-symbol" style="font-family: Arial Unicode MS, Lucida Sans Unicode;">Δ</span>',
                        'min': '-'}
        else:
            Exception("Chorder error due to chordsymbology unknow")

    def chordformater(self, raw):
        ''' reformats chord to a specific symbology'''
        rep = dict((re.escape(k), v) for k, v in self.rep.items())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], raw)
        return text

    def getChordNames(self, noteName, relchordTonePos):
        '''
        This method takes a scale, the scale degree and the note at that scale degree and returns a string
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

        basicChordTypes = {(4, 7, 10): {'7': ['R, sev']},
                           (4, 7): {'maj': ['R, maj']},
                           (3, 7): {'min': ['R, min']},
                           (3, 6): {'dim': ['R, dim']}}

        advChordTypes  = {(4, 8): {'aug': ['R-4, sev']}, (2, 7): {'7sus2': ['R, min+1']}}

        nydanaIntervals = {(0, 4, 7): {'maj': ['R, maj']},
                           (0, 3, 7): {'min': ['R, min']},
                           (0, 4, 7, 10): {'7': ['R, sev']},
                           (4, 8): {'aug': ['R-4, sev']},
                           (0, 3, 6): {'dim': ['R, dim', 'R, dim-3', 'R_, dim+1'], 'm(-5)': ['R, dim-3', 'R_, dim+1']},
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
                           (0, 2, 4, 5, 9, 10): {'13': ['R, sev, min+2']}, (0, 4, 5, 9, 10): {'13': ['R, maj-1, sev']},
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
                           (0, 2, 5, 11): {'maj11': ['R, dim+2']}, (0, 2, 5, 7, 11): {'maj11': ['R, maj+1, sev+1']},
                           (0, 2, 5, 8, 11): {'maj11(+5)': ['R_, dim, (dim-3)', 'R, min-1, dim+2', 'R, dim-1, dim+2']},
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
                           (0, 3, 7, 10): {'m7': ['R, maj-3, (min)', 'R_, maj+1'], 'm7/R+10': ['R+10, min+2, (maj-1)']},
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
                           (0, 3, 6, 9, 11): {'mMaj13(+11)': ['R_, maj-3, sev-3', 'R_, maj-3, dim-5', 'R_, dim-5, sev-3']},
                           (0, 3, 5, 8, 11): {'mMaj13(m13)': ['R_, maj, dim', 'R_, min, dim', 'R, min-4, min-1']}}

        chordNames = [f'<p>{noteName} </p>']
        hoverText = ['']

        logger.debug(f'ChordLevel: {self.level}')

        if self.level == ChordLevel.BASIC_ACCORD:
            chordTypes = basicChordTypes
        elif self.level == ChordLevel.ADV_ACCORD:
            chordTypes = {**basicChordTypes, **advChordTypes }
        elif self.level == ChordLevel.ALL:
            chordTypes = nydanaIntervals

        if self.level != ChordLevel.OFF:
            # cName = ''
            # htxt = ''
            for ctindx, achdtypints in enumerate(chordTypes):
                if all(elem in relchordTonePos for elem in achdtypints):
                    for chdName in chordTypes[achdtypints]:
                        fullChdNam = self.chordformater(chdName)
                        htxt = chordTypes[achdtypints][chdName]
                        chordNames.append(fullChdNam)
                        hoverText.append('\n'.join(htxt))
                    #
                    # if len(cName) == 0:
                    #     chordNames.append(fullChdNam)
                    # else:
                    #     chordNames.append(', ' + fullChdNam)

            #
            # if len(cName) == 0:
            #     cName = f'<p>{noteName}: {relchordTonePos} </p>'
            # else:
            #     cName = f'<p>{noteName}: ' + cName + '</p>'

        return (chordNames, hoverText)

    def drawChordKey(self, x, y):
        self.deleteGraphicItems()
        if self.symbology == ChordSymbol.RAW:
            pass
        elif self.symbology == ChordSymbol.COMMON:
            txtgi = drawText(self.scene, QPointF(x, y), "7 = dom 7th chord", 12, Pos.RIGHT_CENTER)
        elif self.symbology == ChordSymbol.JAZZ:
            txtgi = drawText(self.scene, QPointF(x, y), "Δ = maj\n- = min\n+ = aug\n7 = dom 7th ", 12, Pos.RIGHT_CENTER)
        self.graphicItems.append(txtgi)

    def deleteGraphicItems(self):
        for anItem in self.graphicItems:
            self.scene.removeItem(anItem)
            del anItem
        self.graphicItems = []


class StradellaBass():
    def __init__(self, scene, x0, y0, pen):
        self.scene = scene
        self.x0 = x0
        self.y0 = y0
        self.pen = pen
        self.graphicItems = []

    def draw_Stradella(self, notePositions, showStradella):
        self.deleteGraphicItems()

        if showStradella:
            # Draws the bass and couter-bass rows relative to each other
            buttonR = 23
            spacing = 2.25 * buttonR
            numOfRows = 14
            xOffset = (numOfRows * spacing) / 2
            rOffset = buttonR / 2
            yOffset = spacing / 2
            intervlIndcies = ['R', 'm2', 'M2', 'm3', 'M3', 'P4', 'T', 'P5', 'm6', 'M6', 'm7', 'M7']
            keyints = [['P4', 'R', 'P5', 'M2', 'M6', 'M3', 'M7', 'T', 'm2', 'm6', 'm3', 'm7', 'P4', 'R'],
                       ['m2', 'm6', 'm3', 'm7', 'P4', 'R', 'P5', 'M2', 'M6', 'M3', 'M7', 'T', 'm2', 'm6']]
            for xindx in range(numOfRows):
                for yindx in range(2):
                    sx = self.x0 + (xindx * spacing) - xOffset + (yindx * rOffset)
                    sy = self.y0 - (yindx * spacing) + yOffset
                    text = keyints[yindx][xindx]
                    if intervlIndcies.index(text) in notePositions:
                        pen = self.pen.black
                    else:
                        pen = self.pen.lightGray
                    spt = QPointF(sx, sy)
                    self.graphicItems.append(drawCircle(self.scene, spt, 2 * buttonR, pen))

                    self.graphicItems.append(drawText(self.scene, spt, text, size=16, pen=pen))

    def deleteGraphicItems(self):
        logger.debug(f'deleting scale {len(self.graphicItems)} items')
        for anItem in self.graphicItems:
            self.scene.removeItem(anItem)
            del anItem
        self.graphicItems = []


class MidiPattern(Flag):
    # supports: opts = MidiPattern.LINEAR_UP | MidiPattern.LINEAR_DOWN; MidiPattern.PATTERN_UP in opts
    NONE = auto()
    LINEAR_UP = auto()
    LINEAR_DOWN = auto()
    PATTERN_UP = auto()
    PATTERN_DOWN = auto()
    ARPEGGIO_UP = auto()
    ARPEGGIO_DOWN = auto()
