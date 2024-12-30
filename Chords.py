'''


'''
from logging import exception
import itertools

NydanaChords = ("dim",
                "dim7",
                "(+5, 9)",
                "6",
                "6/R+4",
                "6/R+7",
                "6/R+9",
                "6(m9)",
                "6(-5)",
                "7",
                "7/R+10",
                "7(m9)",
                "7(≠3, m9)",
                "7(m9)/R+10",
                "7(m10)",
                "7(m10)/R+7",
                "7(13)",
                "7(-5)",
                "7(-5, m10)",
                "7(+5, +11)",
                "7sus2",
                "7sus4(m9)",
                "9",
                "9(≠3)",
                "9/R+2",
                "9/R+7",
                "9(-5)",
                "9(+5)",
                "9(≠3, +5)",
                "9sus4",
                "11",
                "11(+5)",
                "11(m9)",
                "11(+11)",
                "13",
                "13(≠3)",
                "13/R+4",
                "13(m9)",
                "13(+11)",
                "maj7",
                "maj7(+5)",
                "maj9",
                "maj9(≠3)",
                "maj9/R+2",
                "maj9(+5)",
                "maj11",
                "maj11(+5)",
                "maj13",
                "maj13(≠3)",
                "maj13(+11)",
                "m(m9)",
                "m(-5)",
                "m(-5, m6)",
                "m(-5, 9)",
                "m(+5)",
                "m6",
                "m6/R+3",
                "m6/R+7",
                "m6/R+9",
                "m6(m9)",
                "m7",
                "m7/R+10",
                "m7(m9)",
                "m7(-5)",
                "m7(-5)/R+3",
                "m7(-5)/R+6",
                "m7(-5)/R+10",
                "m7(-5, m6)",
                "m9",
                "m9/R+2",
                "m9/R+5",
                "m9(-5)",
                "m11",
                "m13",
                "m13(+11)",
                "m13(m13)",
                "mMaj7(-5)",
                "mMaj7(+5)",
                "mMaj9",
                "mMaj9(+5)",
                "mMaj11",
                "mMaj11(+11)",
                "mMaj13",
                "mMaj13(+11)",
                "mMaj13(m13)")
# Stradella bass intervals
accordKeys = {"maj":(0, 4, 7), "min":(0, 3, 7), "sev":(0, 4, 10), "dim":(0, 3, 9)}
#C Major IONIAN scale semitones relative to root
#D=2, Eb=3, E=4, F=5, Gb=6, G=7, A=9, Bb=10, B=11

notes = ('C', "Db/C#", "D", "Eb/D#", "E", "F", "Gb/F#", "G", "Ab/G#", "A", "Bb/A#", "B")
intervals = ('R', 'm2/m9', 'M2/M9', 'm3/m10', 'M3/M10', 'P4/P11', 'b5/T', 'P5', '#5/m6/m13', 'M6/M13', 'm7', 'M7')
rootOffsets = {'R':0, 'R_':8}
R = 0
R_ = 8

NydanaCombos = (("R, dim-3", "R_, dim+1"),
                ("R, dim-3, dim", "R_, dim-2, (dim+1)", "R_, dim-2, (dim-5)"),
                ("R_, sev-4",),
                ("R, min+3, (maj)",),
                ("R+4, min-1, (maj-4)",),
                ("R+7, min+2, (maj-1)",),
                ("R+9, maj-3, (min)", "R_+9, maj+1"),
                ("R, maj+3, (maj)",),
                ("R_, dim-5, min-5",),
                ("R, sev, (maj)", "R, dim+1, (maj)"),
                ("R+10, maj+2",),
                ("R, maj, dim-2", "R, sev, dim-2"),
                ("R, dim-2",),
                ("R+10, dim, maj+2",),
                ("R, min, sev", "R, min, dim+1", "R, maj-3, sev"),
                ("R+7, min-1, dim", "R+7, min-1, sev-1"),
                ("R, sev, min+3",),
                ("R, sev-6", "R_, sev-2"),
                ("R, dim-3, sev",),
                ("R, sev-4, sev",),
                ("R, min+1",),
                ("R, min-2, dim-2",),
                ("R, maj, min+1", "R, sev, min+1", "R, min+1, dim+1"),
                ("R, min+1",),
                ("R+2, maj-2, dim-1",),
                ("R+7, min, sev-1",),
                ("R, sev, sev+2",),
                ("R, sev-2, sev", "R_, sev-4, sev+2"),
                ("R, sev-2",),
                ("R, maj-2, min+1",),
                ("R, maj-2, (min+1)",),
                ("R, maj-2, dim-1", "R, maj-2, min-1"),
                ("R, min-2, (dim-2)",),
                ("R, min+1, sev+2",),
                ("R, min+1, min+3", "R, sev, min+2", "R, maj-1, sev"),
                ("R, maj-1, min+1", "R, min+1, min+2", "R, maj-1, maj-2"),
                ("R+4, min-3, min-1",),
                ("R, sev, maj+3",),
                ("R, sev, maj+2", "R, dim+1, maj+2", "R, sev, dim+3"),
                ("R, min+4, (maj)", "R_, min-4"),
                ("R, maj+4",),
                ("R, maj, maj+1", "R, maj+1, min+4"),
                ("R, maj+1",),
                ("R+2, maj-1, maj-2",),
                ("R_, maj-4, sev-4", "R_, sev-4, dim-3"),
                ("R, dim+2", "R, maj+1, sev+1"),
                ("R_, dim, (dim-3)", "R, min-1, dim+2", "R, dim-1, dim+2"),
                ("R, maj+1, min+3", "R_, min-4, min-5"),
                ("R, maj-1, maj+1",),
                ("R, maj+2, min+4", "R_, min-5, min-3"),
                ("R, sev-3, (min)", "R_, sev+1"),
                ("R, dim-3", "R_, dim+1"),
                ("R_, maj, sev",),
                ("R, dim-3, sev+2",),
                ("R, maj-4", "R_, maj"),
                ("R, dim, (min)",),
                ("R_+3, dim-5, (min-5)",),
                ("R+7, dim-1, (min-1)",),
                ("R+9, min-3, (dim-3)", "R_+9, min+1, (dim+1)"),
                ("R, min, sev+3",),
                ("R, maj-3, (min)", "R_, maj+1"),
                ("R+10, min+2, (maj-1)",),
                ("R, maj-3, sev-3", "R, sev-3, dim-2", "R, maj-3, dim-2"),
                ("R, min-3", "R_, min+1"),
                ("R+3, min, dim",),
                ("R_+6, min-5, dim-5",),
                ("R+10, dim-1, (min-1)",),
                ("R_, maj, min+1",),
                ("R, min, min+1", "R, maj-3, min+1"),
                ("R+2, min-2, min-1", "R+2, maj-5, min-2"),
                ("R+5, min+1, min+2",),
                ("R, min-3, sev+2",),
                ("R, maj-2, min", "R, maj-3, maj-2"),
                ("R, min+1, dim", "R, maj-3, dim", "R_, maj+1, dim+4"),
                ("R, min-3, maj+2", "R_, min+1, dim-2"),
                ("R, maj-4, maj-2",),
                ("R_, maj-3, (dim+1)",),
                ("R_, min, (maj)",),
                ("R, min, maj+1",),
                ("R_, dim-3, min",),
                ("R, min, sev+1", "R, min, dim+2"),
                ("R_, maj-3, min-3", "R_, maj-3, sev-6"),
                ("R, dim, sev+1", "R, maj+1, dim", "R, dim, dim+2"),
                ("R_, maj-3, sev-3", "R_, maj-3, dim-5", "R_, dim-5, sev-3"),
                ("R_, maj, dim", "R_, min, dim", "R, min-4, min-1")
                )

def processChord(chordName):
    idx = NydanaChords.index(chordName)
    combos = NydanaCombos[idx]
    comboChordNotes = [chordName]
    #print("")
    #print(chordName)
    #print(combos)
    for cindx, combo in enumerate(combos):
        #print(f"via combination {combo}")
        parts = combo.split(',')
        rootOffset = eval(parts[0])
        bassNote = eval(parts[0].replace("_", ""))
        chrdNotes = []
        for aChrd in parts[1:]:
            #print(aChrd)
            procChrd = aChrd.strip()
            if procChrd[0] == '(':
                #print("optional chord is skipped")
                procChrd = procChrd.replace("(", "").replace(")", "")


            rowtoken = procChrd[3:]

            if len(rowtoken) > 0:
                if rowtoken[0] == '-':
                    row = 5 * int(rowtoken[1:])
                elif rowtoken[0] == '+':
                    row = 7 * int(rowtoken[1:])
                else:
                    exception('OOPS!')
            else:
                row = 0
            for aChrdnote in accordKeys[procChrd[:3]]:
                chrdNotes.append((rootOffset  + row + aChrdnote) % 12 )
            chrdNotes.append(bassNote % 12)
        chrdNotes = sorted(set(chrdNotes))
        #print(chrdNotes)
        if cindx == 0:
            #print("creating first")
            comboChordNotes.append([[chrdNotes, combo]])
        else:
            for sindx,aset in enumerate(comboChordNotes[1]):
                #print(f" is {chrdNotes} == {aset[0]}")
                if chrdNotes == aset[0]:
                    #print("adding to")
                    comboChordNotes[1][sindx].append( combo)
                    break
            else:
                #print("creating new")
                comboChordNotes[1].append([ chrdNotes, combo])

        chrdIntrvals = None
        for anItvl in chrdNotes:
            if not  chrdIntrvals:
                chrdIntrvals = intervals[anItvl]
            else:
                chrdIntrvals += ', ' + intervals[anItvl]


    return comboChordNotes



chordData = [['dim', [[[0, 3, 6], 'R, dim-3', 'R_, dim+1']]],
['dim7', [[[0, 3, 6, 9], 'R, dim-3, dim', 'R_, dim-2, (dim+1)', 'R_, dim-2, (dim-5)']]],
['(+5, 9)', [[[0, 2, 4, 8], 'R_, sev-4']]],
['6', [[[0, 4, 7, 9], 'R, min+3, (maj)']]],
['6/R+4', [[[0, 4, 7, 9], 'R+4, min-1, (maj-4)']]],
['6/R+7', [[[0, 4, 7, 9], 'R+7, min+2, (maj-1)']]],
['6/R+9', [[[0, 4, 7, 9], 'R+9, maj-3, (min)', 'R_+9, maj+1']]],
['6(m9)', [[[0, 1, 4, 7, 9], 'R, maj+3, (maj)']]],
['6(-5)', [[[0, 4, 6, 9], 'R_, dim-5, min-5']]],
['7', [[[0, 4, 7, 10], 'R, sev, (maj)', 'R, dim+1, (maj)']]],
['7/R+10', [[[0, 4, 7, 10], 'R+10, maj+2']]],
['7(m9)', [[[0, 1, 4, 7, 10], 'R, maj, dim-2', 'R, sev, dim-2']]],
['7(≠3, m9)', [[[0, 1, 7, 10], 'R, dim-2']]],
['7(m9)/R+10', [[[0, 1, 4, 7, 10], 'R+10, dim, maj+2']]],
['7(m10)', [[[0, 3, 4, 7, 10], 'R, min, sev', 'R, min, dim+1', 'R, maj-3, sev']]],
['7(m10)/R+7', [[[0, 3, 4, 7, 10], 'R+7, min-1, dim', 'R+7, min-1, sev-1']]],
['7(13)', [[[0, 4, 9, 10], 'R, sev, min+3']]],
['7(-5)', [[[0, 4, 6, 10], 'R, sev-6', 'R_, sev-2']]],
['7(-5, m10)', [[[0, 3, 4, 6, 10], 'R, dim-3, sev']]],
['7(+5, +11)', [[[0, 4, 6, 8, 10], 'R, sev-4, sev']]],
['7sus2', [[[0, 2, 7, 10], 'R, min+1']]],
['7sus4(m9)', [[[0, 1, 5, 7, 10], 'R, min-2, dim-2']]],
['9', [[[0, 2, 4, 7, 10], 'R, maj, min+1', 'R, sev, min+1', 'R, min+1, dim+1']]],
['9(≠3)', [[[0, 2, 7, 10], 'R, min+1']]],
['9/R+2', [[[0, 2, 4, 7, 10], 'R+2, maj-2, dim-1']]],
['9/R+7', [[[0, 2, 4, 7, 10], 'R+7, min, sev-1']]],
['9(-5)', [[[0, 2, 4, 6, 10], 'R, sev, sev+2']]],
['9(+5)', [[[0, 2, 4, 8, 10], 'R, sev-2, sev', 'R_, sev-4, sev+2']]],
['9(≠3, +5)', [[[0, 2, 8, 10], 'R, sev-2']]],
['9sus4', [[[0, 2, 5, 7, 10], 'R, maj-2, min+1']]],
['11', [[[0, 2, 5, 7, 10], 'R, maj-2, (min+1)']]],
['11(+5)', [[[0, 2, 5, 8, 10], 'R, maj-2, dim-1', 'R, maj-2, min-1']]],
['11(m9)', [[[0, 1, 5, 7, 10], 'R, min-2, (dim-2)']]],
['11(+11)', [[[0, 2, 6, 7, 10], 'R, min+1, sev+2']]],
['13', [[[0, 2, 4, 7, 9, 10], 'R, min+1, min+3'], [[0, 2, 4, 5, 9, 10], 'R, sev, min+2'], [[0, 4, 5, 9, 10], 'R, maj-1, sev']]],
['13(≠3)', [[[0, 2, 5, 7, 9, 10], 'R, maj-1, min+1', 'R, min+1, min+2'], [[0, 2, 5, 9, 10], 'R, maj-1, maj-2']]],
['13/R+4', [[[0, 2, 4, 7, 9, 10], 'R+4, min-3, min-1']]],
['13(m9)', [[[0, 1, 4, 9, 10], 'R, sev, maj+3']]],
['13(+11)', [[[0, 2, 4, 6, 9, 10], 'R, sev, maj+2'], [[0, 2, 4, 6, 7, 9, 10], 'R, dim+1, maj+2'], [[0, 4, 6, 9, 10], 'R, sev, dim+3']]],
['maj7', [[[0, 4, 7, 11], 'R, min+4, (maj)', 'R_, min-4']]],
['maj7(+5)', [[[0, 4, 8, 11], 'R, maj+4']]],
['maj9', [[[0, 2, 4, 7, 11], 'R, maj, maj+1', 'R, maj+1, min+4']]],
['maj9(≠3)', [[[0, 2, 7, 11], 'R, maj+1']]],
['maj9/R+2', [[[0, 2, 4, 7, 11], 'R+2, maj-1, maj-2']]],
['maj9(+5)', [[[0, 2, 4, 8, 11], 'R_, maj-4, sev-4', 'R_, sev-4, dim-3']]],
['maj11', [[[0, 2, 5, 11], 'R, dim+2'], [[0, 2, 5, 7, 11], 'R, maj+1, sev+1']]],
['maj11(+5)', [[[0, 2, 5, 8, 11], 'R_, dim, (dim-3)', 'R, min-1, dim+2', 'R, dim-1, dim+2']]],
['maj13', [[[0, 2, 4, 7, 9, 11], 'R, maj+1, min+3'], [[0, 4, 7, 9, 11], 'R_, min-4, min-5']]],
['maj13(≠3)', [[[0, 2, 5, 7, 9, 11], 'R, maj-1, maj+1']]],
['maj13(+11)', [[[0, 2, 4, 6, 7, 9, 11], 'R, maj+2, min+4'], [[0, 2, 4, 6, 9, 11], 'R_, min-5, min-3']]],
['m(m9)', [[[0, 1, 3, 7], 'R, sev-3, (min)', 'R_, sev+1']]],
['m(-5)', [[[0, 3, 6], 'R, dim-3', 'R_, dim+1']]],
['m(-5, m6)', [[[0, 3, 6, 8], 'R_, maj, sev']]],
['m(-5, 9)', [[[0, 2, 3, 6], 'R, dim-3, sev+2']]],
['m(+5)', [[[0, 3, 8], 'R, maj-4', 'R_, maj']]],
['m6', [[[0, 3, 7, 9], 'R, dim, (min)']]],
['m6/R+3', [[[0, 3, 7, 9], 'R_+3, dim-5, (min-5)']]],
['m6/R+7', [[[0, 3, 7, 9], 'R+7, dim-1, (min-1)']]],
['m6/R+9', [[[0, 3, 7, 9], 'R+9, min-3, (dim-3)', 'R_+9, min+1, (dim+1)']]],
['m6(m9)', [[[0, 1, 3, 7, 9], 'R, min, sev+3']]],
['m7', [[[0, 3, 7, 10], 'R, maj-3, (min)', 'R_, maj+1']]],
['m7/R+10', [[[0, 3, 7, 10], 'R+10, min+2, (maj-1)']]],
['m7(m9)', [[[0, 1, 3, 7, 10], 'R, maj-3, sev-3', 'R, sev-3, dim-2', 'R, maj-3, dim-2']]],
['m7(-5)', [[[0, 3, 6, 10], 'R, min-3', 'R_, min+1']]],
['m7(-5)/R+3', [[[0, 3, 6, 10], 'R+3, min, dim']]],
['m7(-5)/R+6', [[[0, 3, 6, 10], 'R_+6, min-5, dim-5']]],
['m7(-5)/R+10', [[[0, 3, 6, 10], 'R+10, dim-1, (min-1)']]],
['m7(-5, m6)', [[[0, 3, 6, 8, 10], 'R_, maj, min+1']]],
['m9', [[[0, 2, 3, 7, 10], 'R, min, min+1', 'R, maj-3, min+1']]],
['m9/R+2', [[[0, 2, 3, 7, 10], 'R+2, min-2, min-1', 'R+2, maj-5, min-2']]],
['m9/R+5', [[[0, 2, 3, 5, 7, 10], 'R+5, min+1, min+2']]],
['m9(-5)', [[[0, 2, 3, 6, 10], 'R, min-3, sev+2']]],
['m11', [[[0, 2, 3, 5, 7, 10], 'R, maj-2, min', 'R, maj-3, maj-2']]],
['m13', [[[0, 2, 3, 7, 9, 10], 'R, min+1, dim'], [[0, 3, 7, 9, 10], 'R, maj-3, dim', 'R_, maj+1, dim+4']]],
['m13(+11)', [[[0, 2, 3, 6, 9, 10], 'R, min-3, maj+2'], [[0, 3, 6, 9, 10], 'R_, min+1, dim-2']]],
['m13(m13)', [[[0, 2, 3, 5, 8, 10], 'R, maj-4, maj-2']]],
['mMaj7(-5)', [[[0, 3, 6, 11], 'R_, maj-3, (dim+1)']]],
['mMaj7(+5)', [[[0, 3, 8, 11], 'R_, min, (maj)']]],
['mMaj9', [[[0, 2, 3, 7, 11], 'R, min, maj+1']]],
['mMaj9(+5)', [[[0, 2, 3, 8, 11], 'R_, dim-3, min']]],
['mMaj11', [[[0, 3, 5, 7, 11], 'R, min, sev+1'], [[0, 2, 3, 5, 7, 11], 'R, min, dim+2']]],
['mMaj11(+11)', [[[0, 2, 3, 6, 11], 'R_, maj-3, min-3', 'R_, maj-3, sev-6']]],
['mMaj13', [[[0, 3, 5, 7, 9, 11], 'R, dim, sev+1'], [[0, 2, 3, 7, 9, 11], 'R, maj+1, dim'], [[0, 2, 3, 5, 9, 11], 'R, dim, dim+2']]],
['mMaj13(+11)', [[[0, 3, 6, 9, 11], 'R_, maj-3, sev-3', 'R_, maj-3, dim-5', 'R_, dim-5, sev-3']]],
['mMaj13(m13)', [[[0, 3, 5, 8, 11], 'R_, maj, dim', 'R_, min, dim', 'R, min-4, min-1']]]]





if __name__ == '__main__':
   # for aChrdname in NydanaChords:
   #      setsOfNotes = processChord(aChrdname)
   #      #setsOfNotes = processChord('mMaj13')
   #
   #      print(f"{setsOfNotes},")
    intervals2chord = {}
    for achrd in chordData:
        chordName = achrd[0]
        for intervalset in achrd[1]:
            dictKey = tuple(intervalset[0])
            try:
                existingentry = intervals2chord[dictKey]
                try:
                    existingchordcombos = existingentry[chordName]
                    intervals2chord[dictKey][chordName] = existingchordcombos + intervalset[1:]
                except:
                    intervals2chord[dictKey][chordName] =  intervalset[1:]

            except:
                print("Exception")
                entry = {chordName:intervalset[1:]}
                intervals2chord[dictKey] = entry

    for aninterval in intervals2chord:
        print(f"{aninterval}: {intervals2chord[aninterval]},")

















