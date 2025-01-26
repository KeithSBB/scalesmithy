'''
The utils module contains utility functions
'''


import math
from collections import deque
from enum import Enum
from math import sqrt
import logging

from PyQt6 import sip
from PyQt6.QtCore import Qt, QPointF, QLineF, QRectF
from PyQt6.QtGui import QFont, QBrush, QPen, QPolygonF, QTransform
from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem, \
    QGraphicsItem, QDialog, QListWidget, QVBoxLayout
from poetry.console.commands import self

logger = logging.getLogger(__name__)

def distance_to_polygon(point, polygon):
    min_distance = float('inf')
    for i in range(len(polygon) - 1):
        p1 = polygon[i]
        p2 = polygon[i + 1]
        # Calculate the distance from the point to the line segment p1-p2
        distance = distance_to_segment(point, p1, p2)
        if distance < min_distance:
            min_distance = distance
    return min_distance

def distanceOfPtToLine(line, point):
   return  math.fabs((line.y2() - line.y1())*point.x() - (line.x2() - line.x1())*point.y() +
              line.x2() * line.y1() - line.x1() * line.y2())/line.length()


def closes_point_on_polygon(point, polygon):
    min_distance = float('inf')
    for i in range(len(polygon) - 1):
        p1 = polygon[i]
        p2 = polygon[i + 1]
        # Calculate the distance from the point to the line segment p1-p2
        segment = QLineF(p1, p2)
        polyPt = perpendicular_point_on_line(segment, point)
        perpendictLine = QLineF(point, polyPt)
        distance = perpendictLine.length()
        if distance < min_distance:
            min_distance = distance
            perpLine = perpendictLine

    return perpLine


def perpendicular_point_on_line(line: QLineF, point: QPointF) -> QPointF:
    # Extract coordinates
    x1, y1 = line.p1().x(), line.p1().y()
    x2, y2 = line.p2().x(), line.p2().y()
    px, py = point.x(), point.y()

    # Direction vector of the line
    dx, dy = x2 - x1, y2 - y1

    # Calculate the parameter `t` for the closest point on the line
    line_length_sq = dx ** 2 + dy ** 2
    if line_length_sq == 0:
        # The line is a single point
        return line.p1()

    t = ((px - x1) * dx + (py - y1) * dy) / line_length_sq
    if t < 0 or 1 < t:
        return None
    # Calculate the intersection point (projection)
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return QPointF(proj_x, proj_y)






def distance_to_segment(point, p1, p2):
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    if dx == 0 and dy == 0:
        return (point.x() - p1.x())**2 + (point.y() - p1.y())**2
    t = ((point.x() - p1.x()) * dx + (point.y() - p1.y()) * dy) / (dx**2 + dy**2)
    if t < 0:
        closest = p1
    elif t > 1:
        closest = p2
    else:
        closest = QPointF(p1.x() + t * dx, p1.y() + t * dy)
    return (point.x() - closest.x())**2 + (point.y() - closest.y())**2

def isInsidePolygon(point, polygon):
    x, y = point
    num_vertices = len(polygon)
    crossings = 0

    for i in range(num_vertices):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % num_vertices]

        if y1 <= y < y2 and (x - x1) * (y2 - y1) < (x2 - x1) * (y - y1):
            crossings += 1

    return crossings % 2 == 1

def Cumulative(lists):
    cu_list = []
    length = len(lists)
    cu_list = [sum(lists[0:x:1]) for x in range(0, length + 1)]
    return cu_list[1:]

def angleOfLine(line):
    dx = line.p2().x() - line.p1().x()
    dy = line.p2().y() - line.p1().y()
    return math.atan2(dy, dx)

def quadrantAngleOfLine(line):
    dx = line.p2().x() - line.p1().x()
    dy = line.p2().y() - line.p1().y()
    if dx == 0:
        rst = math.pi / 2
    else:
        rst = math.fabs(math.atan(dy/dx))
    return rst

class Pos(Enum):
    LEFT_CENTER = 1
    CENTER = 2
    RIGHT_CENTER = 3
    RADIAL_IN = 4
    RADIAL_OUT = 5

class TextPentagonContainer(QPolygonF):
    '''
    The text pentagon is a five sided polygon that all the
    GraphicsTextItems for a scale degree must liw within.  It
    has specialized methods to test for GraphicsTextItem placement
    compliance and return info to aid in readjusting the position.
    The pentagon has named sides relative to the scale vertex position
    and increasing clockwise: LeftExpanding, LeftRadial, Inner, RightRadial, RightExpanding
    '''
    def __init__(self, relchordtonepos, rt, vtxPt, centerPt, chordTextDepthFactor ):
        '''
        Constructor for the TextPentagonContainer class.
        :param relchordtonepos: list of ints
        :param rt: float - distance from centerPt to initial position of first text item (note or scale degree)
        :param vtxPt: QPointF - scale vertex point and initial pentagon point
        :param centerPt: QPointF - center of the scale from which all angles and distances are referenced
        :param chordTextDepthFactor: float - a fraction less than 1 which controls how far towards centerPt
                                                the inner pentagon points are placed.
        '''
        logger.debug("NEW PENTAGON CONTAINER")
        logger.debug(f"centerPt = {centerPt.x(), centerPt.y()}")
        self._gTxtItems = None
        self.centerRadial = QLineF(centerPt, vtxPt)
        self.rs = self.centerRadial.length()
        self.a = angleOfLine(self.centerRadial)

        logger.debug(f"a = {math.degrees(self.a)}")
        self.vtxPt = vtxPt
        logger.debug(f"vtxPt = {vtxPt}")
        self.centerPt = centerPt
        self.keyPt = QPointF(centerPt.x() + rt * math.cos(self.a), centerPt.y() + rt * math.sin(self.a))
        self.chordTextDepthFactor = chordTextDepthFactor

        #relAngCCW = math.radians((180 - relchordtonepos[1] * 30) / 2)

        angCW = math.radians(relchordtonepos[1] * 30.0)
        logger.debug(f"angCW = {math.degrees(angCW)}")
        ptCW = QPointF(self.rs * math.cos(self.a - angCW) + centerPt.x(),
                        self.rs * math.sin(self.a - angCW) + centerPt.y())
        lineToPtCW = QLineF(vtxPt, ptCW )
        halfLengthToCW = 0.5 * lineToPtCW.length() - 3
        relAngToPtCW = angleOfLine(lineToPtCW)
        logger.debug(f"halfLengthToCCW = {halfLengthToCW}")
        ptHlCW = QPointF(vtxPt.x() + halfLengthToCW * math.cos(relAngToPtCW),
                        vtxPt.y() + halfLengthToCW * math.sin(relAngToPtCW))
        ptinCW = QPointF(chordTextDepthFactor * ptHlCW.x() + centerPt.x() ,
                          chordTextDepthFactor * ptHlCW.y() + centerPt.y())

        #relAngCW = math.radians(-(180 - (12 - relchordtonepos[-2]) * 30) / 2)
        angCCW = math.radians((12 - relchordtonepos[-2]) * 30.0)
        logger.debug(f"angCCW = {math.degrees(angCCW)}")
        ptCCW = QPointF(self.rs * math.cos(self.a + angCCW) + centerPt.x(),
                        self.rs * math.sin(self.a + angCCW) + centerPt.y())
        lineToPtCCW = QLineF(vtxPt, ptCCW)
        halfLengthToCCW = 0.5 * lineToPtCCW.length() - 3
        relAngToPtCCW = angleOfLine(lineToPtCCW)
        logger.debug(f"halfLengthToCW = {halfLengthToCCW}")
        ptHlCCW = QPointF(vtxPt.x() + halfLengthToCCW * math.cos(relAngToPtCCW),
                       vtxPt.y() + halfLengthToCCW * math.sin(relAngToPtCCW))
        ptinCCW = QPointF(chordTextDepthFactor * ptHlCCW.x() + centerPt.x(),
                         chordTextDepthFactor * ptHlCCW.y() + centerPt.y())



        # Calculate the alignment point for initial positioning of first col = 0
        self.leftSideAlignmentPt = QPointF( (self.keyPt.x() + halfLengthToCW * math.cos(relAngToPtCW)),
                                            (self.keyPt.y() + halfLengthToCW * math.sin(relAngToPtCW)))

        self.leftSideAlignmentAngle = angleOfLine(QLineF(self.keyPt, self.leftSideAlignmentPt))
        self.fromPoints([vtxPt, ptHlCW, ptinCW, ptinCCW, ptHlCCW, vtxPt])

    def fromPoints(self, points):
        if len(points) != 6:
            raise Exception("TextPentagonContainer must have 6 points listed clockwise starting at the scale vertex.  ")

        super().__init__(points)
        self.sides = {"LeftExpanding":QLineF(self.value(0), self.value(1)),
                        "LeftRadial":QLineF(self.value(1), self.value(2)),
                        "Inner":QLineF(self.value(2), self.value(3)),
                        "RightRadial":QLineF(self.value(3), self.value(4)),
                        "RightExpanding":QLineF(self.value(4), self.value(5))}

    def closestPointOnPolygon(self, abadPt):
        min_distance = float('inf')
        perpLine = None
        polyside = None
        for aSide in self.sides:
            segment = self.sides[aSide]
            polyPt = perpendicular_point_on_line(segment, abadPt)
            if polyPt is None:
                continue
            perpendictLine = QLineF(abadPt, polyPt)
            distance = perpendictLine.length()
            if distance < min_distance:
                min_distance = distance
                perpLine = perpendictLine
                polyside = aSide

        return perpLine, polyside

    def graphicTxtItemCompliance(self, gti):
        badPts = []
        perpLine = None
        polyside = None
        for apt in gti.getPoints():
            if not self.containsPoint(apt, Qt.FillRule.OddEvenFill):
                #logger.debug(f"bad point {apt} for {gti.toPlainText()}")
                badPts.append(apt)
            else:
                pass
                #logger.debug(f"Good point {apt} for {gti.toPlainText()}")
        if len(badPts) > 0:
            worsedist = 0
            for abadPt in badPts:
                # Need to find which side of te polygon
                # this point is outside
                aLine, polyside = self.closestPointOnPolygon(abadPt)
                if aLine is None:
                    continue

                if aLine.length() > worsedist:
                    worsedist = aLine.length()
                    perpLine = aLine
        if perpLine is None:
            contained = True
        else:
            contained = False
        return contained, polyside, perpLine

    @property
    def gTxtItems(self):
        return self._gTxtItems

    @gTxtItems.setter
    def gTxtItems(self, q):
        self._gTxtItems = q


    def getGTxtItems(self, ring, col):
        rst = []
        for gti in self.gTxtItems:
            if gti.ring == ring:
                if col is not None:
                    if gti.col == col:
                        rst.append(gti)
                else:
                    rst.append(gti)
        if len(rst) == 0:
            rst = [None]
        return rst

    def layoutGrphTxtItems(self):
        '''
        This method lays out the graphic text items.
        It uses an iterative method after initial positioning
        '''
        
        # The first agi is the scale degree note or roman numeral
        innerAgi = self._gTxtItems[0]
        innerAgi.ring = 0
        innerAgi.col = 0
        logger.debug(f"======= {innerAgi.toPlainText()} initial position set to {innerAgi.centerPos()}=======")
        
        # Layout controls
        newring = True
        agi = None
        indx = 1
        while indx < len(self._gTxtItems):
            # Either re-layout last agi (usually at higher ring)
            # or pop the next agi
            if agi is None:
                # Get the next agi to layout
                agi = self._gTxtItems[indx]
                agi.polycont = self
            
            # set the proper ring and col    
            if newring:
                if agi.col == 0:
                    agi.ring = agi.ring + 1
                else:
                    agi.ring = self._gTxtItems[indx-1].ring + 1
                agi.col = 0
                newring = False
                if agi.ring > 5:
                    logger.debug(f"******* Too many rings for {agi.toPlainText()}, breaking out")
                    break
            else:
                agi.ring = self._gTxtItems[indx-1].ring
                agi.col = self._gTxtItems[indx-1].col + 1
          
            # Calculate the initial position of the next text item
            # If agi.col == 0 then the innerAgi and the pentagon are the references
            # otherwise its the lastAgi and the closest inner ring GI
            if agi.col == 0:
                innerAgi = self.getGTxtItems(agi.ring - 1, col=0)[0]
                if innerAgi is None:
                    logger.debug(f"No innerAgi found for {agi.toPlainText()} ring {agi.ring} col {agi.col}")
                    break
                logger.debug(f"innerAgi {innerAgi.toPlainText()} ring {innerAgi.ring} col {innerAgi.col}")
                agi.setCenterPos(innerAgi.centerPos())
                logger.debug(f"{agi.toPlainText()} initial position set to {agi.centerPos()} = {innerAgi.centerPos()}")
                refdist = innerAgi.centerToEdgeTowardsRefPt(self.leftSideAlignmentPt)
                agiDist = agi.centerToEdgeTowardsRefPt(self.leftSideAlignmentPt)
                deltaDist = agiDist + refdist
                dx = deltaDist * math.cos(self.leftSideAlignmentAngle)
                dy = deltaDist * math.sin(self.leftSideAlignmentAngle)
                agi.moveBy(dx, dy)
                logger.debug(f"move by {dx} {dy} for {agi.toPlainText()} in ring {agi.ring} col {agi.col}")
                col = 1
            elif agi.col > 0:
                candidates = self.getGTxtItems(agi.ring - 1, None)
                for acan in candidates:
                    logger.debug(f"candidate {acan.toPlainText()} ring {acan.ring} col {acan.col}")

                #Need to first move agi to perpendicular from lastapi
                lastAgi = self._gTxtItems[indx - 1]
                lastRadial = QLineF(self._gTxtItems[0].centerPos(), lastAgi.centerPos())
                angOfPerpLine = angleOfLine(lastRadial) - math.pi / 2
                distguess = lastAgi.width + agi.width
                newPos = QPointF(distguess * math.cos(angOfPerpLine)+lastAgi.centerPos().x(),
                                 distguess * math.sin(angOfPerpLine)+lastAgi.centerPos().y())
                agi.setCenterPos(newPos)

                #find closest GItem in inner ring
                innerAgi = min(candidates, key=lambda x: x.centerToEdgeTowardsRefPt(agi.centerPos()))
                logger.debug(f"innerAgi {innerAgi.toPlainText()} ring {innerAgi.ring} col {innerAgi.col}")

            logger.debug(f"======= {agi.toPlainText()} initial position set to {agi.centerPos()}=======")
            
            # == the iterative fitting takes place here in this while loop ==
            trys = 0
            fit = False
            while not fit:
                if trys > 10:
                    logger.debug(f"******* Too many tries for {agi.toPlainText()}, breaking out")
                    break
                ideal1 = (agi.centerToEdgeTowardsRefPt( innerAgi.centerPos()) +
                          innerAgi.centerToEdgeTowardsRefPt(agi.centerPos()))
                actual1 = QLineF(agi.centerPos(), innerAgi.centerPos())
                dpt1 = (actual1.length() - ideal1)
                logger.debug(f"ideal1 {ideal1} actual1 {actual1.length()} dpt1 {dpt1}")
                if math.fabs(dpt1) > 1: #fuzzy compare, if less than one do nothing
                    a1 = angleOfLine(actual1)
                    # print(f"refgi1: angle {a1} and move by {dpt1}")
                    agi.moveBy(dpt1 * math.cos(a1), dpt1 * math.sin(a1))
                    logger.debug(f"move by {dpt1} for {agi.toPlainText()} in ring {agi.ring} col {agi.col}")

                if agi.col == 0:
                    contained, polyside, actual2 = self.graphicTxtItemCompliance(agi)
                    if contained:
                        dpt2 = 0
                    else:
                        dpt2 = actual2.length()
                        logger.debug(f"Iterative loop: graphical text item {agi.toPlainText()} out on {polyside}")

                else:
                    ideal2 = (agi.centerToEdgeTowardsRefPt(
                            lastAgi.centerPos()) + lastAgi.centerToEdgeTowardsRefPt(agi.centerPos()))
                    actual2 = QLineF(agi.centerPos(), lastAgi.centerPos())
                    dpt2 = (actual2.length() - ideal2)

                if math.fabs(dpt2) > 1:
                    a2 = angleOfLine(actual2)
                    agi.moveBy(dpt2 * math.cos(a2), dpt2 * math.sin(a2))
                    logger.debug(f"move by {dpt2} for {agi.toPlainText()} in ring {agi.ring} col {agi.col}")

                if math.fabs(dpt1) < 1 and math.fabs(dpt2) < 1:
                    fit = True
                trys += 1

            # check if inside pentagon container, if not start over with newring = True
            contained, polyside, actual2 = self.graphicTxtItemCompliance(agi)
            if not contained:
                if polyside is not None:
                    if polyside == "RightExpanding" or polyside == "RightRadial":
                        if agi.col == 0:
                            logger.debug(f">>>>>Item {agi.toPlainText()} will not fit on {polyside} side, already col = 0, give up")
                            break
                        else:
                            newring = True
                            logger.debug(f">>>>> Item {agi.toPlainText()}will not fit on {polyside} side, going to ring {agi.ring + 1} and try again")
                    else:
                        logger.debug(f">>>>>WARNING: Item {agi.toPlainText()} will not fit on {polyside} side")
                        break
                else:
                    logger.debug(f">>>>>ERROR: polyside for item {agi.toPlainText()} could not be determined.")
                    break
            else:
                logger.debug(f"{agi.toPlainText()} was successfully placed inside pentagon")
                indx += 1
                agi = None

class GraphicsTextItem(QGraphicsTextItem):
    def __init__(self, scene,  text, font, tcolor, parent=None):
        super().__init__( parent)
        self.scene = scene
        self.xfm = QTransform()
        self.xfm.scale(1, -1)
        self.setTransform(self.xfm )
        self.setFont(font)
        self.setDefaultTextColor(tcolor)
        if text[0] == '<':
            self.setHtml(text)
        else:
            self.setPlainText(text)
        self._polycont = None
        self.width = self.document().idealWidth()
        self.height = self.document().size().height()
        self.rect = super().boundingRect()
        self.rect.setHeight(self.rect.height() - 7)
        self.rect.setY(7.5)
        self.rectItem = None
        self._ring = None
        self._col = None
        self.debugBoundingRect()

    def boundingRect(self):
        return self.rect

    @property
    def polycont(self):
        return self._polycont

    @polycont.setter
    def polycont(self, val):
        self._polycont = val

    @property
    def ring(self):
        return self._ring
    @ring.setter
    def ring(self, val):
        self._ring = val
    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, val):
        self._col = val

    def xboundingRect(self):
        return self.xfm.mapRect(self.boundingRect())

    def debugBoundingRect(self):
        if logger.getEffectiveLevel() == logging.DEBUG:
            if self.rectItem is None:
                self.rectItem = QGraphicsRectItem(self.xboundingRect())
                self.rectItem.setParentItem(self.parentItem())
                self.rectItem.setPen(QPen(Qt.GlobalColor.darkCyan))
                self.rectItem.setPos(self.pos())
                self.scene.addItem(self.rectItem)
            else:
                self.rectItem.setPos(self.pos())

    def __del__(self):
        if logger.getEffectiveLevel() == logging.DEBUG:
            if self.rectItem is not None:
                self.scene.removeItem(self.rectItem )
                logger.debug(f"Removed rectItem for {self.toPlainText()}")
                sip.delete( self.rectItem)
                self.scene.update()

    def getPoints(self ):
        return [self.pos() + self.xfm.map(self.boundingRect().bottomLeft()),
                self.pos() + self.xfm.map(self.boundingRect().bottomRight()),
                self.pos() + self.xfm.map(self.boundingRect().topRight()),
                self.pos() + self.xfm.map(self.boundingRect().topLeft())]

    def centerPos(self):
        return self.pos() + self.xfm.map(self.boundingRect().center())

    def setCenterPos(self, pos):
        self.setPos(pos - self.xfm.map(self.boundingRect().center()))
        self.debugBoundingRect()

    # def pos(self):
    #     return self.xfm.map(super().pos() ) - self.boundingRect().bottomLeft()


    def centerToEdgeTowardsRefPt(self, refPt):
        '''
        This method calculates the length from the center to the boundingrect edge
        along the line from the center to refPt
        :param refPt: QPointF
        :return: float
        method used:  the bounding Rect center Pt, width and height are known.
        the rect is always aligned with the x and y axis.  The line from centerPt
        to refPt forms a right triangle with centerPt (A), perpendicular to the horizontal or vertical edge(B)
        and the intersection of the line with an edge (C). Knowns:
        angle (a) B-A-C from line direction
        side A-B
        A-B =R*sin(90 - a), or R = (A-B) / sin(90 - a) = (A-B) / cos(a)
        '''

        if self == refPt:
            raise Exception("Same Point, cannot calculate distance to self")
        # Calculate angle of line from center to refPt
        line = QLineF(self.centerPos(), refPt)
        if line.length() == 0:
            logger.debug(f"{self.toPlainText()} has the same position as refPt")
            raise Exception("Same location, refPt must be different than self.centerPos()")
        ang = quadrantAngleOfLine(line)
        rect = self.xboundingRect()
        angToRectCorner = math.fabs(math.atan(rect.height() / rect.width()))

        if  ang > angToRectCorner:
            rst = (rect.height() / 2) / math.sin(ang)
        else:
            rst = (rect.width() / 2) / math.cos(ang)

        return math.fabs(rst)

    def getMaxMinDistances(self,  refPt):
        x1 = self.pos().x()
        y1 = self.pos().y()
        x2 = x1 + self.width
        y2 = y1 - self.height
        rectVerts = [QPointF(x1, y1)]
        rectVerts.append(QPointF(x1, y2))
        rectVerts.append(QPointF(x2, y1))
        rectVerts.append(QPointF(x2, y2))
        dists = []
        for apt in rectVerts:
            dists.append(QLineF(apt, refPt).length())
        dists.append(QLineF(refPt, self.centerPos()).length() - self.centerToEdgeTowardsRefPt(refPt))
        return (max(dists), min(dists))

    def moveBy(self, dx, dy):
        super().moveBy(dx, dy)
        self.debugBoundingRect()


class ChordDig(QDialog):
    def __init__(self, list):
        super().__init__()
        self.index = 0
        self.setWindowTitle("Documentation")
        self.listWidget = QListWidget(self)
        self.listWidget.addItems(list)
        self.listWidget.itemClicked.connect(self.accept)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.listWidget)


    def accept(self, item):
        self.index = self.listWidget.row(item)
        self.done(1)


class GraphicsTextItemDropDown(GraphicsTextItem):
    def __init__(self, scene,  textlist, font, tcolor,  parent=None):
        '''
        
        :param scene: 
        :param textlist: A list of 2-element lists where [0] is graphic text list and [1] is hover text list
        :param font: 
        :param tcolor: 
        :param parent: 
        '''

        self.textlist = textlist
        text = self.textlist[0][0]
        logger.debug(f"textlist is {textlist}")
        super().__init__( scene,  text, font, tcolor, parent=None)
        self.setToolTip(self.textlist[0][1])

        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable )
        self.chrddlg = ChordDig([i[0] for i in self.textlist])
        logger.debug(f"chords are {[i[0] for i in self.textlist]}")


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print("Left mouse button clicked on text item")
            self.chrddlg.exec()
            logger.debug(f"chord index is {self.chrddlg.index}")
            text = self.textlist[self.chrddlg.index][0]
            if text[0] == '<':
                self.setHtml(text)
            else:
                self.setPlainText(text)
            self.__del__()
            self.rectItem = None

            self.adjustSize()
            self.width = self.document().idealWidth()
            self.height = self.document().size().height()
            super().boundingRect().setWidth(self.width)
            self.rect = super().boundingRect()
            self.debugBoundingRect()
            self.setToolTip(self.textlist[self.chrddlg.index][1])
            self.polycont.layoutGrphTxtItems()

        elif event.button() == Qt.MouseButton.RightButton:
            print("Right mouse button clicked on text item")
        super().mousePressEvent(event)




def drawText(scene, pt, text, size=10, position=Pos.CENTER, refPt=QPointF(0,0), pen=QPen(Qt.GlobalColor.black), txtWidth=None):
    ''' drawText draws text relative to the position of the bounding box.  x, y define where that
    boundary box position will be located.
    '''
    font = QFont('[bold]')
    tcolor = pen.color()
    # print(QFontInfo(font).family())
    font.setPointSize(size)
    if isinstance(text, list):
        strItem = GraphicsTextItemDropDown(scene, text, font, tcolor)
    else:
        strItem = GraphicsTextItem(scene, text, font, tcolor)
    #strItem.setToolTip("This is the hover text")

    #DEBUG
    # pen = QPen(Qt.GlobalColor.red)
    # drawCircle(scene, pt, 5, pen)
    #strItem.setDefaultTextColor(tcolor)
    #strItem.setFont(font)

    # if text[:3] == '<p>':
    #     strItem.setHtml(text)
    # else:
    #     strItem.setPlainText(text)

    fm = strItem.font()

    if txtWidth is not None:
        if txtWidth > 0:
            strItem.setTextWidth(txtWidth)


    xoffset = 0
    yoffset = 0

    if position == Pos.CENTER:
        pass
        # xoffset = strItem.boundingRect().center().x()
        # yoffset = strItem.boundingRect().center().y()
    elif position == Pos.LEFT_CENTER:
        xoffset = strItem.boundingRect().center().x()
        yoffset = 0
    elif position == Pos.RIGHT_CENTER:
        xoffset = - strItem.boundingRect().center().x()
        yoffset = 0
    elif position == Pos.RADIAL_IN:
        # For radial in the bounding Rect is used to position the text so that the
        # rect fits within the centered at refPt circle at point pt on the circle
        strItem.setCenterPos(pt)
        maxDist, minDist = strItem.getMaxMinDistances(refPt)
        refLine = QLineF(refPt, pt)
        refDist = refLine.length()
        logger.debug(f"refLine length is {refDist}, maxDist is {maxDist}, minDist is {minDist}")
        delta = refDist - maxDist
        ang = math.atan2(pt.y()-refPt.y(), pt.x()-refPt.x())
        xoffset = delta * math.cos(ang)
        yoffset = delta * math.sin(ang)

    elif position == Pos.RADIAL_OUT:
        # For radial out the bounding Rect is used to position the text so that the
        # rect fits outside the centered at refPt circle at point pt on the circle
        # ==================

        strItem.setCenterPos(pt)
        maxDist, minDist = strItem.getMaxMinDistances(refPt)
        refLine = QLineF(refPt, pt)
        refDist = refLine.length()
        logger.debug(f"refLine length is {refDist}, maxDist is {maxDist}, minDist is {minDist}")
        delta = refDist - minDist
        ang = angleOfLine(refLine)
        xoffset = delta * math.cos(ang)
        yoffset = delta * math.sin(ang)
        logger.debug(f"QLineF center to refpt angle is {math.degrees(ang)}")
        logger.debug(f"x: {xoffset} is applied to {pt.x()}")
        logger.debug(f"y: {yoffset} is applied to {pt.y()}")


    newPt = QPointF(pt.x() + xoffset, pt.y() + yoffset)

    strItem.setCenterPos(newPt)

    scene.addItem(strItem)





    return strItem


def drawCircle(scene, cpt, d, pen, brush=None, noteId=None, acceptMousebuttons=False):
    x = cpt.x() - d / 2
    y = cpt.y() - d / 2
    # x, y w h  (x,y are the lower left corner)
    ellipse = CircleGraphicsItem(x, y, d, noteId=noteId, acceptMousebuttons=acceptMousebuttons)
    ellipse.setPen(pen)
    if brush:
        ellipse.setBrush(brush)
    scene.addItem(ellipse)
    return ellipse


def drawLine(scene, pt1, pt2, pen=None):
    if not pen:
        pen = Pens.black

    aline = QLineF(pt1, pt2)

    # Draw the line
    alineItem = QGraphicsLineItem(aline)
    alineItem.setPen(pen)
    scene.addItem(alineItem)
    return alineItem


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
        self.lightGray = QPen(Qt.GlobalColor.lightGray)
        self.lightGray.setWidth(3)
        self.red = QPen(Qt.GlobalColor.red)
        self.red.setWidth(3)
        self.blue = QPen(Qt.GlobalColor.blue)
        self.blue.setWidth(3)
        self.green = QPen(Qt.GlobalColor.green)
        self.green.setWidth(3)


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



