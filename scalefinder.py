'''
Created on Jul 26, 2022

@author: keith
'''


class Chord:
    _notes = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A3/Bb", "B"]
    def __init__(self, cName):
        self.root = cName[0]
        if "maj" in cName:
            self.st = [0, 4, 7]
        elif "min" in cname:
            self.st = [0, 3, 7]
        elif "7" in cName:
            self.st = [0, 4, 7, 10]
        elif "dim" in cName:
            self.st = [0, 3, 6]
        else:
            Exception("bad chord name")
    def notes(self):
        i = Chord._notes.index(self.root)
        nlist = ""
        for st in self.st:
            nlist = nlist + " " + Chord._notes[i + st % 12]
        return nlist

if __name__ == '__main__':
    c = Chord("Emaj")
    print(c.notes())