import sys


def getGlobalTriggerTime(period, time, ave_per):
    return period*ave_per + time


def updatePipeline(globalTime, pipeline, ave_per, readoutTime):
    print "updatePipeline: called with globaltime ", globalTime, " and ", len(pipeline.triggers), " triggers in the pipeline"
    pops = []
    for trig in pipeline.triggers:
        dt = globalTime - trig.rotime
        print "updatePipeline: testing trigger ", trig.toString()
        if dt > readoutTime:
            print "updatePipeline: pop trigger with dt ", dt 
            pops.append(trig)
    # actually pop them
    for trig in pops:
        pipeline.remove(trig)
    return pops

def updateTiTriggers(globalTime, pipeline, ave_per, tiRules):
    print "updateTiTriggers: called with globaltime ", globalTime, " and ", len(pipeline.triggers), " triggers outstanding"
    pops = []
    # calculate start of sliding window from this particular global time
    tStartGlobal = globalTime - tiRules.longestHoldOff
    print "updateTiTriggers: tStartGlobal ", tStartGlobal
    # loop over triggers and pop the ones that expired
    for trig in pipeline.triggers:
        tGlobal = trig.getGlobalTime(ave_per)
        dt = tGlobal - tStartGlobal
        print "updateTiTriggers: testing trigger ", trig.toString(), " with global time ", tGlobal, " (dt=",dt,")"
        if dt < 0:
            print "updateTiTriggers: pop trigger with dt ", dt
            pops.append(trig)
    # actually pop them
    for trig in pops:
        pipeline.triggers.remove(trig)
    return pops





class Trigger():
    def __init__(self,period, timestamp):
        self.period = period
        self.time = timestamp
    def getGlobalTime(self, ave_per):
        return getGlobalTriggerTime(self.period, self.time, ave_per)
    def toString(self):
        return " Trigger: period " + str(self.period) + " time " + str(self.time)


class Triggers():
    def __init__(self):
        self.triggers = []
    def toString(self):
        str = ""
        for  t in self.triggers:
            str += t.toString() + "\n"
        return str

class PipelineEntry():
    def __init__(self,trig,rotime):
        self.trig = trig
        self.rotime = rotime
    def getGlobalTime(self, ave_per):
        return self.trig.getGlobalTime(ave_per)
    def toString(self):
        return self.trig.toString() + " rotimestart " + str(self.rotime)

class Pipeline():
    def __init__(self, readoutTime):
        self.triggers = []
        self.readoutTime = readoutTime
    def add(self,trig,ave_per):
        rotime = self.getRoTimeStart(trig,ave_per)
        self.triggers.append(PipelineEntry(trig,rotime))
    def remove(self,trig):
        self.triggers.remove(trig)
    def getRoTimeStart(self,trig,ave_per):
        tStart = -1.
        if len(self.triggers) > 0:
            # start when the last one is read out
            tStart = self.triggers[len(self.triggers)-1].rotime + self.readoutTime
        else:
            # start immediately
            tStart = trig.getGlobalTime(ave_per)        
        return tStart
    def toString(self):
        s = ""
        for entry in self.triggers:
            s += entry.toString() + "\n"
        return s


class TiRules():
    def __init__(self):
        self.rules = {}
        self.longestHoldOff = 0.
        self.longestHoldOffMult = 0.
    def add(self,n,t):
        self.rules[n] = t
    def get(self,n):
        return self.rules[n]
    def init(self):
        self.longestHoldOff = self.getLongestHoldOff()
        self.longestHoldOffMult = self.getLongestHoldOffMult()
    def getLongestHoldOff(self):
        vmax = -1
        for k,v in self.rules.iteritems():
            if v > vmax:
                vmax = v
        if vmax<0:
            print "ERROR on TiRules vmax=",vmax
            sys.exit(1)
        return vmax
    def getLongestHoldOffMult(self):
        kmax = -1
        for k,v in self.rules.iteritems():
            if self.longestHoldOff == v:
                kmax = k
        if kmax<0:
            print "ERROR on TiRules kmax=",kmax
            sys.exit(1)
        return kmax
    def getTiStrTag(self):
        s = ""
        for k,v in self.rules.iteritems():
            s += " TI-"+str(k)+"="+str(v)
        return s
