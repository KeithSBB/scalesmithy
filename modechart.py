'''
Created on Sep 27, 2020

@author: keith
'''
from tkinter import *
from tkinter import filedialog as fd 
from PIL import Image, ImageDraw, ImageFont
import math
from collections import deque
from fpdf import FPDF
import tempfile, copy
from functools import partial
#from django.conf.locale import pt



class ListBoxChoice(object):
    def __init__(self, master=None, title=None, message=None, list=[], curModeindx=0):
        self.master = master
        self.value = None
        self.index = curModeindx
        self.list = list[:]
        
        self.modalPane = Toplevel(self.master)

        self.modalPane.transient(self.master)
        self.modalPane.grab_set()

        self.modalPane.bind("<Return>", self._choose)
        self.modalPane.bind("<Escape>", self._cancel)

        if title:
            self.modalPane.title(title)

        if message:
            Label(self.modalPane, text=message).pack(padx=5, pady=5)

        listFrame = Frame(self.modalPane)
        listFrame.pack(side=TOP, padx=5, pady=5)
        
        scrollBar = Scrollbar(listFrame)
        scrollBar.pack(side=RIGHT, fill=Y)
        self.listBox = Listbox(listFrame, selectmode=SINGLE)
        self.listBox.pack(side=LEFT, fill=Y)
        scrollBar.config(command=self.listBox.yview)
        self.listBox.config(yscrollcommand=scrollBar.set)
        #self.list.sort()
        for item in self.list:
            self.listBox.insert(END, item)

        self.listBox.selection_set(curModeindx)
        buttonFrame = Frame(self.modalPane)
        buttonFrame.pack(side=BOTTOM)

        chooseButton = Button(buttonFrame, text="Choose", command=self._choose)
        chooseButton.pack()

        cancelButton = Button(buttonFrame, text="Cancel", command=self._cancel)
        cancelButton.pack(side=RIGHT)

    def _choose(self, event=None):
        try:
            self.index = self.listBox.curselection()[0]
            self.value = self.list[int(self.index)]

        except IndexError:
            self.value = None
        self.modalPane.destroy()

    def _cancel(self, event=None):
        self.modalPane.destroy()
        
    def returnValue(self):
        self.master.wait_window(self.modalPane)
        return (self.value, self.index)




class ModeCircles(Frame):
    def __init__(self):
        # We need the master object to
        # initialize important stuff
        self.window = Tk() 
        # self.window.tk.call('tk', 'scaling', 0.5)
        self.window.title("test")
        self.window.geometry("800x1000")
        super().__init__(self.window) # Call tk.Frame.__init__(master)
        self.createCanvas(800, 1000)
        self.family = "Diatonic"
        self.scales = { "Diatonic":[0, 2, 2, 1, 2, 2, 2, 1],
                        "Ascending Melodic Minor":[0, 2, 1, 2, 2, 2, 2, 1],
                        "Harmonic Minor":[0, 2, 1, 2, 2, 1, 3, 1],
                        "Harmonic Major":[0, 2, 2, 1, 2, 1, 3, 1],
                        "Diminished":[0, 2, 1, 2, 1, 2, 1, 2, 1],
                        "Whole Tone":[0, 2, 2, 2, 2, 2, 2 ],
                        "Augmented":[0, 3, 1, 3, 1, 3, 1 ],
                        "Double Harmonic Major": [0, 1, 3, 1, 2, 1, 3, 1],
                        "Eight step scale": [0, 2, 3, 1, 1, 2, 1, 1, 1 ]}
        self.baseChrom = ["none", "C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B" ]
        self.notes = []
        self.mode = 'Ionian - Major'
        self.modeIndx = 0
        # New Reference feature
        self.refFamily = ""
        self.refMode = ""
        self.refModeIndx = 0
        self.refNotes = []
        
        self.listsOfModes = {"Diatonic":['Ionian - Major', 'Dorian', 'Phrygain', 'Lydian', 'Mixolydian', 'Aeolian - Natural Minor','Locrian'],
                             "Ascending Melodic Minor":[ 'Dorian #7', 'Phrygain #6', 'Lydian #5', 'Mixolydian #4', 'Aeolian #3','Locrian #2', 'Ionian #1 - The Altered Scale'],
                             "Harmonic Minor":['Aeolian #7','Locrian #6','Ionian #5', 'Dorian #4', 'Phrygain #3', 'Lydian #2', 'Mixolydian #1 - Super Locrian' ],
                             "Harmonic Major":['Ionian b6', 'Dorian b5', 'Phrygain b4', 'Lydian b3', 'Mixolydian b2', 'Aeolian b1','Locrian b7'],
                             "Diminished":['Diminished', 'Inverted Diminished'],
                             "Whole Tone":['Whole Tone'],
                             "Augmented":['Augmented', 'Inverted Augmented'],
                             "Double Harmonic Major":['Bizantine', 'Lydian #2 #6', 'Ultraphrygain', 'Hungarian Minor', 'Oriental', 'Ionian ♯2 ♯5','Locrian bb3 bb7'],
                             "Eight step scale":['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
                             }
  
        self.menubar = Menu(self.window)
        self.fmenu = Menu(self.menubar, tearoff=0)
        self.fmenu.add_command(label="save Image",command=self.saveImage)
        self.fmenu.add_command(label="Generate PDF",command=self.makePDF)
        self.menubar.add_cascade(label='File', menu=self.fmenu)
        self.smenu = Menu(self.menubar, tearoff=0)
        self.keymenu = Menu(self.menubar, tearoff=0)
        
        
        self.buildMenu(self.smenu, self.scales.keys(), self.Family)
        self.buildMenu(self.keymenu, self.baseChrom, self.SetNoteName)
        
        self.menubar.add_cascade(label='Scales', menu=self.smenu)
        
        self.menubar.add_command(label="Mode", command=self.selectMode)
        self.menubar.add_cascade(label='Key', menu=self.keymenu)
        self.menubar.add_command(label="Set Ref", command=lambda:self.Reference(True))
        self.menubar.add_command(label="Clear Ref", command=lambda:self.Reference(False))
       
        
        self.window.config(menu = self.menubar)
        self.draw()
        

    def createCanvas(self, canvas_width, canvas_height):
        # Create our canvas (blue background)
        self.canvas = Canvas(self.window, bg="blue", width=canvas_width, height=canvas_height)
        self.canvas.pack()
        self.canvas.configure(scrollregion=(-400, -400, 400, 400), background="white")
        
    def buildMenu(self, smenu, itemNames, cmd):
        for i,item in enumerate(itemNames):
            smenu.add_command(label=item, command= partial(cmd, item))
            
    def SetNoteName(self, rootNote):
        if rootNote == "none":
            self.notes = []
        else:
            offset = self.baseChrom[1:].index(rootNote)
            self.notes = [self.baseChrom[1:] [(i + offset) % len(self.baseChrom[1:] )]
                          for i, x in enumerate(self.baseChrom[1:])]
        self.draw()

    def Reference(self, setClear):
        if setClear:
            self.refFamily = copy.copy(self.family)
            self.refMode = copy.copy(self.mode)
            self.refModeIndx = copy.copy(self.modeIndx)
            self.refNotes = copy.copy(self.notes)
            self.draw()
        else:
            self.refFamily = ""
            self.refMode = ""
            self.refNotes = []
              
     

    def getChordName(self, scaleDeg, intervals, notes):
        intervals = deque(list(intervals)[1:])
        nsemitones = self.Cumulative(list(intervals))[:-1]
        nsemitones.insert(0, 0)
        #print(nsemitones)
        #print(intervals)
        intervals.rotate(-scaleDeg)
        #print(intervals)
        intervals.appendleft(0)
        #print(intervals)
        semitones = self.Cumulative(list(intervals))
        print(semitones[:-1])
        cNoteInts = semitones[:-1]
        cNoteInts = [ aNum for aNum in cNoteInts if aNum < 12]
        if len(notes) == 12:
            roman = [notes[index] for index in nsemitones]
        else:
            roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
        # cName = "unknown
        # if cNoteInts == [0, 3, 7, 10]:
        #     cName = f'{roman[scaleDeg]}min7'
        # elif cNoteInts == [0, 3, 7, 9]:
        #     cName = f'{roman[scaleDeg]}min6'
        # elif cNoteInts == [0, 3, 7, 11]:
        #     cName = f'{roman[scaleDeg]}minM7'
        # elif cNoteInts == [0, 4, 7, 11]:
        #     cName = f'{roman[scaleDeg]}maj7'
        # elif cNoteInts == [0, 4, 7, 9]:
        #     cName = f'{roman[scaleDeg]}maj6'
        # elif cNoteInts == [0, 4, 7, 10]:
        #     cName = f'{roman[scaleDeg]}7th'
        # elif cNoteInts == [0, 4, 6, 10]:
        #     cName = f'{roman[scaleDeg]}7th-b5'
        # elif cNoteInts == [0, 4, 8]:
        #     cName = f'{roman[scaleDeg]}aug'
        # elif cNoteInts == [0, 3, 6]:
        #     cName = f'{roman[scaleDeg]}dim'
        # elif cNoteInts == [0, 2, 7]:
        #     cName = f'{roman[scaleDeg]}sus2'
        # elif cNoteInts == [0, 2, 6]:
        #     cName = f'{roman[scaleDeg]}sus2-b5'
        # elif cNoteInts == [0, 5, 7]:
        #     cName = f'{roman[scaleDeg]}sus4'
        # else:
        #     cName = f'{roman[scaleDeg]} ???'
        #     print(cNoteInts)
         
        chordTypes = {'min':[0, 3, 7],
                      'min7':[0, 3, 7, 10],
                      'min6':[0, 3, 7, 9],
                      'minM7':[0, 3, 7, 11],
                      'maj':[0, 4, 7],
                      'maj7':[0, 4, 7, 11],
                      'maj6':[0, 4, 7, 9],
                      '7th':[0, 4, 7, 10],
                      '7th-b5':[0, 4, 6, 10],
                      'aug':[0, 4, 8],
                      'dim':[0, 3, 6],
                      'sus2':[0, 2, 7],
                      '7sus2':[0, 2, 7, 10],
                      'sus2-b5':[0, 2, 6],
                      'sus4':[0, 5, 7],
                      '9sus4':[0, 2, 5, 7],
                      '7sus4':[0, 5, 7, 10]} 
        cName = ''
        for achdtyp in chordTypes:
            if all(elem in cNoteInts for elem in chordTypes[achdtyp]):
                if len(cName) == 0:
                    cName = cName +achdtyp 
                else:
                    cName = cName +', '+achdtyp
        if len(cName) == 0:
            cName = f'{roman[scaleDeg]}: {cNoteInts}' 
        else:
            cName = f'{roman[scaleDeg]}: ' + cName
     
        return cName
        

    def saveImage(self):
        fn = fd.asksaveasfilename()
        self.createImage(fn)
    
    def createImage(self, fileName):
        
        img = self.draw(toPIL=True)
        size = 550, 550
        img.thumbnail(size, Image.LANCZOS)
        img.save(fileName + ".png", "png", quality=99)

    def makePDF(self):
        # This routine steps through all possible scales, generates temp png files and assemblies them into a PDF
        orgFamily = self.family
        orgMode = self.mode
        orgModeIndx = self.modeIndx
        pngFileList = []
        pdfFn = fd.asksaveasfilename()
        defult_tmp_dir = tempfile._get_default_tempdir()
        for family in self.scales.keys():
            self.family = family
            for modeIndx, mode in enumerate(self.listsOfModes[family]):
                self.mode = mode
                self.modeIndx = modeIndx
                pngFile = defult_tmp_dir + "/" + next(tempfile._get_candidate_names())
                self.createImage(pngFile)
                pngFileList.append(pngFile + ".png")
                
        # Now assemblt into PDF
        pdf = FPDF(orientation="P", unit="in", format="Letter")
        pdf.set_font('helvetica', 'B', 16)
        for pngFile in pngFileList:
            pdf.add_page()
            pdf.image(pngFile, w=7.5)
            
        pdf.output(pdfFn + ".pdf")
        self.family = orgFamily
        self.mode = orgMode
        self.modeIndx = orgModeIndx
        
    def KeyCenter(self, note):
        pass 
    
    def Family(self, fam):
        self.family = fam
        self.modeIndx = 0
        self.mode = self.listsOfModes[self.family][self.modeIndx]
        # print(fam)
        self.draw()
        

    def selectMode(self):
        # modeDlg = ListBoxChoice(self, self.listsOfModes[self.family], self.mode)
        mode, self.modeIndx = ListBoxChoice(self, "Mode", "Select Desired Mode", self.listsOfModes[self.family], self.modeIndx).returnValue()
        if mode:
            self.mode = mode
            self.draw()
#
# root = Tk()
# root.geometry() #"800x1000")
# myCanvas = Canvas(root, width=800, height=800)
# myCanvas.pack()
# myCanvas.

    def draw_circle(self, obj, x, y, r,  aFill=''): #center coordinates, radius
        x0 = x - r
        y0 = y - r
        x1 = x + r
        y1 = y + r

        if isinstance(obj, ImageDraw.ImageDraw):
            obj.ellipse([x0, y0, x1, y1], fill=aFill, width=1, outline=(0,0,0))
        else:
            obj.create_oval(x0, y0, x1, y1, fill=aFill)
    
    def draw_Line(self, obj, x0, y0, x1, y1, color="#000" ):
        if isinstance(obj, ImageDraw.ImageDraw):
            obj.line([x0, y0, x1, y1], fill=color )
        else:
            obj.create_line(x0, y0, x1, y1, fill=color )
     
    def draw_Text(self, obj, x, y, text, font, color="#000"):
        if isinstance(obj, ImageDraw.ImageDraw):
            w  = obj.textlength(text)
            h = font.size
            obj.text(((x-w/2),(y-h/2)), text, font=font, fill=color)
        else:
            obj.create_text(x, y, text=text, font=font, fill=color)
     
    def draw_Stradella(self, obj, x0, y0, font, fill):
        #Draws the bass and couter-bass rows relative to each other
        buttonR = 23
        spacing = 2.25 * buttonR
        numOfRows = 14
        xOffset = (numOfRows * spacing) / 2
        rOffset = buttonR / 2
        yOffset = spacing / 2
        keyints = [['P4', 'R', 'P5', 'M2', 'M6', 'M3', 'M7', 'T', 'm2', 'm6', 'm3', 'm7', 'P4', 'R'],
                   ['m2', 'm6', 'm3', 'm7','P4', 'R', 'P5', 'M2', 'M6', 'M3', 'M7', 'T', 'm2', 'm6']]
        for xindx in range(numOfRows):
            for yindx in range(2):
                x = x0 + (xindx * spacing) - xOffset + (yindx * rOffset)
                y = y0 + (yindx * spacing) - yOffset
                self.draw_circle( obj, x, y, buttonR,  aFill=fill)
                text = keyints[yindx][xindx]
                self.draw_Text(obj, x, y, text, font)
     
            
        
    def Cumulative(self, lists): 
        cu_list = [] 
        length = len(lists) 
        cu_list = [sum(lists[0:x:1]) for x in range(0, length+1)] 
        return cu_list[1:]

    def draw(self, toPIL=False):
        if toPIL:
            xOffset = 400
            yOffset = 400
            image1 = Image.new("RGB", (800, 1000), (255,255,255))
            font1 = ImageFont.truetype("/usr/share/fonts/google-roboto/RobotoCondensed-MediumItalic.ttf", 20)
            font2 = ImageFont.truetype("/usr/share/fonts/google-roboto/RobotoCondensed-MediumItalic.ttf", 15)
            obj = ImageDraw.Draw(image1)
            black = (0,0,0)
            red = (255, 0, 0)
            white = (255, 255, 255)
            print(obj)
        else:
            xOffset = 0
            yOffset = 0
            self.canvas.delete("all")
            font1 = "Times 20 italic bold"
            font2 = "Times 10 italic bold"
            obj = self.canvas
            black = "black"
            red = "red"
            white = ""
            print(obj)
            
        rmax = 300
        self.draw_circle(obj, 0 + xOffset, 0 + yOffset, rmax, aFill = white)
        self.draw_Stradella(obj, 0 + xOffset, 450 + yOffset, font1, white)
        
        scaleIntrvls = deque(self.scales[self.family][1:])
        scaleIntrvls.rotate(-self.modeIndx)
        scaleIntrvls.appendleft(0)
        #print(scaleIntrvls)
        s = self.Cumulative(list(scaleIntrvls))
        
        pts = []
        
        self.draw_Text(obj, -200+ xOffset, -380 + yOffset, text="Family "+self.family, font=font1)
        self.draw_Text(obj,200+ xOffset, -380 + yOffset, text="Mode: "+self.mode, font=font1)
        # self.canvas.create_text(-350, 0, text="Root-", font="Times 20 italic bold")
        
        intervals = ["Root", "min 2nd", "Maj 2nd", "min 3rd", "Maj 3rd", "Perfect 4th", "Tritone", "Perfect 5th", "Min 6th", "Maj 6th", "min 7th", "Maj 7th"]
        
        for i in range(12):
            a = math.radians(-180 + i*30)
            r = rmax
            x = r*math.cos(a)
            y = r*math.sin(a)
            
            rt = r * 1.12
            xt = rt*math.cos(a)
            yt = rt*math.sin(a)
           
            self.draw_Text(obj,xt + xOffset, yt + yOffset, text=intervals[i] , font=font2)
            try:
                #search for the item
                index = s.index(i)
                # print('The index of', i, 'in the list is:', index)
                chName = self.getChordName(index, deque(scaleIntrvls), self.notes)
                self.draw_Text(obj,0.75*xt + xOffset, 0.75*yt + yOffset, text=chName , font=font2)
                #print(chName)
                pts.append((x,y))
                self.draw_circle(obj, x + xOffset, y + yOffset, 10,  black)
            except ValueError:
                #print('item not present')
                self.draw_circle(obj, x + xOffset, y + yOffset, 10, white)
        
        firstTime = True
        for pt in pts:
            if firstTime:
                start = pts[-1]
                firstTime = False
            stop = pt
            self.draw_Line(obj, start[0] + xOffset, start[1] + yOffset, stop[0] + xOffset, stop[1] + yOffset)
            start = stop
            
        #Reference scale if defined
        if self.refFamily  and self.refMode and (len(self.refNotes) == 12) and (len(self.notes) == 12):
            scaleIntrvls = deque(self.scales[self.refFamily][1:])
            scaleIntrvls.rotate(-self.refModeIndx)
            scaleIntrvls.appendleft(0)
            #print(scaleIntrvls)
            s = self.Cumulative(list(scaleIntrvls))

            pts = []
            rmax = 200
            color = "#F00"            
            #relative key differences
            semitoneDelta = self.notes.index( self.refNotes[1])
            self.draw_Text(obj, xOffset,  yOffset - 25, text=self.refFamily, font=font1, color=color)
            self.draw_Text(obj, xOffset, yOffset + 25, text=self.refMode, font=font1, color=color)
            
            
            for i in range(12):
               
                a = math.radians(-180 + (i + semitoneDelta - 1)*30)
                r = rmax 

                x = r*math.cos(a)
                y = r*math.sin(a)
                
                rt = r * 1.12
                xt = rt*math.cos(a)
                yt = rt*math.sin(a)
               
                if i == 0:
                    self.draw_Text(obj,xt + xOffset, yt + yOffset, text=intervals[i] , font=font2, color=color)
                try:
                    #search for the item
                    index = s.index(i)
                    # print('The index of', i, 'in the list is:', index)
                    chName = self.getChordName(index, deque(scaleIntrvls), self.refNotes)
                    self.draw_Text(obj,0.75*xt + xOffset, 0.75*yt + yOffset, text=chName , font=font2, color=color)
                    #print(chName)
                    pts.append((x,y))
                    self.draw_circle(obj, x + xOffset, y + yOffset, 10,  red)
                except ValueError:
                    print('item not present')
                    #self.draw_circle(obj, x + xOffset, y + yOffset, 10, white)
            
            firstTime = True
            for pt in pts:
                if firstTime:
                    start = pts[-1]
                    firstTime = False
                stop = pt
                self.draw_Line(obj, start[0] + xOffset, start[1] + yOffset, stop[0] + xOffset, stop[1] + yOffset,  red)
                start = stop
            
        
        
        if  toPIL:
            return image1
        else:
            return self.canvas.update()

    



if __name__ == "__main__":
    # Create our master object to the Application
    print(TkVersion)
    # Create our application object
    app = ModeCircles()


    
    # Start the mainloop
    app.mainloop()
    
