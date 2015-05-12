import sys
from ROOT import TH1F, TRandom3, TF1, TCanvas, TMath, TGraph, TH2F, TLegend

def getNextTrig(triggers, trig_prev):
    trig_sel = None
    for trig in triggers:
        # skip the exising one
        if trig_prev == trig:
            continue
        # is there a prev trigger?
        if trig_prev!=None:                
            # yes, use this trig only if it came later
            if trig.time<trig_prev.time:
                continue
        # get the latest one
        # if there is none selected, use the current one
        if trig_sel==None:
            trig_sel = trig
        elif trig.time < trig_sel.time:
            trig_sel = trig
    
    return trig_sel

def getSorted(triggers):
    #print "getSorted"
    #print triggers.toString()
    triggers_sorted = []
    t_prev = None
    tnext = getNextTrig(triggers, t_prev)
    while tnext!= None:
        #print "got tnext ", tnext.toString()
        triggers_sorted.append(tnext)
        t_prev = tnext
        tnext = getNextTrig(triggers, t_prev)
    return triggers_sorted


def getGlobalTriggerTime(period, time, ave_per):
    return period*ave_per + time

def getGlobalTime(trigger, ave_per):
    return getGlobalTriggerTime(trigger.period, trigger.time, ave_per)


class Trigger():
    def __init__(self,period, timestamp):
        self.period = period
        self.time = timestamp
    def toString(self):
        return " Trigger: period " + str(self.period) + " time " + str(self.time)

class Triggers():
    def __init__(self):
        self.triggers = []
    def add(self,trig):
        self.triggers.append(trig)
    def getList(self):
        return self.triggers
    def sort(self):
        t_sort = getSorted(self.triggers)
        self.triggers = t_sort        
    def toString(self):
        str = ""
        for trig in self.triggers:
            str += trig.toString() + "\n"
        return str



def updatePipeline(globalTime, pipeline, ave_per, readoutTime):
    print "updatePipeline: called with globaltime ", globalTime, " and ", len(pipeline.triggers), " triggers in the pipeline"
    pops = []
    for trig in pipeline.triggers:
        tGlobal = getGlobalTime(trig, ave_per)
        dt = globalTime - tGlobal
        print "updatePipeline: testing trigger ", trig.toString(), " with global time ", tGlobal
        if dt > readoutTime:
            print "pop trigger with dt ", dt
            pops.append(trig)
    # actually pop them
    for trig in pops:
        pipeline.triggers.remove(trig)
    return pops


def getLastTrigger(pipeline, ave_per):
    lastTrig = None
    for trig in pipeline.triggers:            
        tGlobal = getGlobalTime(trig, ave_per)
        if lastTrig==None:
            lastTrig = trig
        else:            
            t = getGlobalTime(trig, ave_per)
            lastT = getGlobalTime(lastTrig, ave_per)
            if (t-lastT)>0:
                lastTrig = trig
    return lastTrig





def getLiveTime(N, aveRate, deadTime, pipelineDepth, readoutTime, draw=False, save=False):

    print "go N ", N, ", aveRate ", aveRate, ", deadTime ", deadTime, ", readoutTime ", readoutTime

    ave_per = 1.0/aveRate*1e6 #average period between triggers in us

    hp = TH1F("hp","Triggers within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",10,0.,10)
    hr = TH1F("hr","Trigger time within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",10,0.,ave_per)
    hrs = TH1F("hrs","Selected; trigger time within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",10,0.,ave_per)
    hts = TH1F("hts","Trigger time b/w accepted triggers (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",50,0.,max(deadTime,ave_per)*4)
    hpipelinestatus = TH1F("hpipelinestatus","Triggers in pipeline at each period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",7,0.,7)
    r = TRandom3()
    fp = TF1("fp","TMath::PoissonI(x,[0])",0.,10.)
    fp.SetParameter(0,1.)
    if draw:
        c1 = TCanvas("c1","c1",10,10,500,700)
        c1.cd()
        fp.Draw()

    
    pipeline = Triggers()
    nTotTrig = 0
    nPipelineFull = 0
    nDeadtime = 0
    nTotTrigAcc = 0
    for i in range(N):
        print "--- Period ", i , " start ---"
        # update pipeline status at start of this period to make it simpler to understand
        tGlobalStart = getGlobalTriggerTime(i, 0.0, ave_per)
        print tGlobalStart, " at start of period"
        print "Update pipeline status for global time ", tGlobalStart
        print len(pipeline.triggers), " triggers in pipeline before update"
        print "Pipeline status:"
        print pipeline.toString()
        triggers_readout = updatePipeline(tGlobalStart, pipeline, ave_per, readoutTime)
        print "after update of pipeline"
        print len(triggers_readout), " triggers popped"
        print len(pipeline.triggers), " triggers in pipeline "
        print "Pipeline status:"
        print pipeline.toString()

        hpipelinestatus.Fill(len(pipeline.triggers))

        # run the trigger
        n = int(fp.GetRandom()) # rounds to lower
        nTotTrig += n
        hp.Fill(n)
        print n, " triggers in this period, ", nTotTrig, " total trigger sent"
        triggers = Triggers()
        for j in range(n):
            t = r.Rndm()*ave_per
            hr.Fill(t)
            triggers.add(Trigger(i,t))
        #print triggers.toString()
        #print "sort"
        triggers.sort()
        print triggers.toString()
        
        for trig in triggers.getList():
            print "test ", trig.toString()
            print len(pipeline.triggers), " existing triggers "
            # update pipeline
            print "Pipeline status before update"
            print pipeline.toString()                
            # check if we are still dead from any of the previous triggers
            triggers_readout = updatePipeline(getGlobalTime(trig, ave_per), pipeline, ave_per, readoutTime)
            print "popped ", len(triggers_readout), " triggers from pipeline"
            print "Pipeline status after update "
            print pipeline.toString()                

            if len(pipeline.triggers)==0:
                print "ACCEPTED"                
                hrs.Fill(trig.time)
                hts.Fill(0.)
                pipeline.add(trig)
                nTotTrigAcc += 1
            else:                
                # check if this trigger is accepted
                lastTrig = getLastTrigger(pipeline,ave_per)
                
                print "Last trigger found ", lastTrig.toString()
                deltaT = getGlobalTime(trig, ave_per)-getGlobalTime(lastTrig,ave_per)

                if( deltaT > deadTime):
                    print "ACCEPTED for dead time"
                    # is there depth in the pipeline available
                    if len(pipeline.triggers) < pipelineDepth:
                        print "ACCEPTED: space in pipeline exists"
                        nTotTrigAcc += 1
                        hrs.Fill(trig.time)
                        hts.Fill(deltaT)
                        pipeline.add(trig)
                    else:
                        nPipelineFull += 1
                        print "FAILED: pipeline full (",pipelineDepth,")"
                else:
                    print "FAILED: deadtime not expired"
                    nDeadtime += 1
    
    if draw:
        c2 = TCanvas("c2","c2",10,10,500,700)
        c2.cd()
        hp.Draw()
        c3 = TCanvas("c3","c3",10,10,500,700)
        c3.cd()
        hr.Draw()
        hrs.SetLineColor(2)
        hrs.DrawNormalized("same",hr.Integral())
        c33 = TCanvas("c33","c33",10,10,500,700)
        c33.cd()
        hts.Draw()
        c333 = TCanvas("c333","c333",10,10,500,700)
        c333.cd()
        hpipelinestatus.Draw()
        ins = raw_input('press enter to end prog')

    if save:
        c1.SaveAs("fp-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+"-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+".png")
        c2.SaveAs("hp-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+"-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+".png")
        c3.SaveAs("hr-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+"-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+".png")
        c33.SaveAs("hts-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+"-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+".png")
        c333.SaveAs("pipelinestatus-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+"-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+".png")

    return [nTotTrig, nTotTrigAcc, nDeadtime, nPipelineFull]


def usage():
    print "Usage: Nperiods aveRate deadTime readoutTime pipelinedepth"

def main():
    if len(sys.argv) < 6:
        usage()
        return
    N = int(sys.argv[1]) #1000 #number of periods
    aveRate = float(sys.argv[2]) #50.0e3 #average Poission trigger rate in Hz
    deadTime = float(sys.argv[3]) #0.001 # min time required between triggers in us
    readoutTime = float(sys.argv[4]) #21.0
    pipelineDepth = int(sys.argv[5]) #2
    
    res = getLiveTime(N, aveRate, deadTime, pipelineDepth, readoutTime, True, True)
    
    print "Total triggers: sent ", res[0], ", accepted ", res[1], " nDeadtime cut ", res[2], " nPipelineFull ", res[3], ", livetime ", float(res[1])/float(res[0])

    ins = raw_input('press anything to continue')

    N = 500
    gr_dt_lt = {}
    dtRange = [0.001, 1.0, 5.0, 10.0, 20.0, 25.0]
    #for dt in range(5,30,5):
    for dt in dtRange:
        gr_lt = TGraph()
        n=0
        for irate in range(int(10e3),int(100e3),5000):
            res = getLiveTime(N,float(irate),float(dt),pipelineDepth,readoutTime,False,False)
            gr_lt.SetPoint(n,irate,float(res[1])/float(res[0])) 
            print irate, " ", dt, " ",  n, " ", res
            n = n+1
        gr_dt_lt[dt] = gr_lt
    
    c4 = TCanvas("c4","c4",10,10,500,700)
    c4.cd()
    lt_template = TH2F("lt_template","Live time;Average trigger rate (Hz);Live time fraction",10,0,100000,10,0.2,1.1)
    lt_template.SetStats(False)
    lt_template.Draw()
    n=0
    leg = TLegend(0.15,0.15,0.35,0.35)
    for dt in gr_dt_lt:
        gr_lt = gr_dt_lt[dt]
        gr_lt.SetMarkerSize(1.0)
        gr_lt.SetMarkerStyle(20)
        gr_lt.SetMarkerColor(1+n)
        gr_lt.SetLineColor(1+n)
        gr_lt.Draw("LP,same")
        leg.AddEntry(gr_lt,"DT="+str(dt)+"#mus","LP")
        n = n+1
    leg.SetFillColor(0)
    leg.SetBorderSize(0)
    leg.Draw()
    c4.SaveAs("livetime-vs-rate" + "-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+".png")

    ins = raw_input('press anything to continue')


if __name__ == "__main__":
    main()

