'''
The utils module contains utility functions
'''


import math
from enum import Enum
from math import sqrt
import logging
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QFont, QBrush, QPen
from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem

logger = logging.getLogger(__name__)




def Cumulative(lists):
    cu_list = []
    length = len(lists)
    cu_list = [sum(lists[0:x:1]) for x in range(0, length + 1)]
    return cu_list[1:]


class Pos(Enum):
    LEFT_CENTER = 1
    CENTER = 2
    RIGHT_CENTER = 3
    RADIAL_IN = 4
    RADIAL_OUT = 5


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
