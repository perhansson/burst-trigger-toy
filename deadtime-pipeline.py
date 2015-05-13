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


def getLastTrigger(pipeline, ave_per):
    lastTrig = None
    for trig in pipeline.triggers:            
        tGlobal = trig.getGlobalTime( ave_per)
        if lastTrig==None:
            lastTrig = trig
        else:            
            t = trig.getGlobalTime( ave_per)
            lastT = lastTrig.getGlobalTime(ave_per)
            if (t-lastT)>0:
                lastTrig = trig
    return lastTrig





def getLiveTime(N, aveRate, deadTime, pipelineDepth, readoutTime, tiRules=None, draw=False, save=False):

    print "go N ", N, ", aveRate ", aveRate, ", deadTime ", deadTime, ", readoutTime ", readoutTime

    ave_per = 1.0/aveRate*1e6 #average period between triggers in us

    tiStrTag = ""
    if tiRules!=None:
        tiStrTag = tiRules.getTiStrTag()

    hp = TH1F("hp","Triggers within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",10,0.,10)
    hr = TH1F("hr","Trigger time within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",10,0.,ave_per)
    hrs = TH1F("hrs","Selected; trigger time within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",10,0.,ave_per)
    hts = TH1F("hts","Trigger time b/w accepted triggers (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",50,0.,max(deadTime,ave_per)*4)
    hrsti = TH1F("hrsti","Selected TI trigger; trigger time within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",10,0.,ave_per)
    htsti = TH1F("htsti","TI Trigger time b/w accepted triggers (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",50,0.,max(deadTime,ave_per)*4)
    hpipelinestatus = TH1F("hpipelinestatus","Triggers in pipeline at each period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",7,0.,7)
    hpipelinestatusvstime = TGraph()#"hpipelinestatusvstime","Triggers in pipeline at each period vs global time (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",7,0.,7)
    hpipelinestatusvstime.SetTitle("Triggers in pipeline at each period vs global time (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+");Time;Triggers in pipeline")
    htitriggers = TH1F("htitriggers","TI triggers outstanding at each period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+")",7,0.,7)
    htitriggersvstime = TGraph()
    htitriggersvstime.SetTitle("TI triggers outstanding at each period vs global time (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+");Time;Outstanding triggers")
    htriggersvstime = TGraph()
    htriggersvstime.SetTitle("Triggers issues previous period vs global time (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus "+tiStrTag+");Time;Triggers")
    
    r = TRandom3()
    fp = TF1("fp","TMath::PoissonI(x,[0])",0.,10.)
    fp.SetParameter(0,1.)
    if draw:
        c1 = TCanvas("c1","c1",10,10,700,500)
        c1.cd()
        fp.Draw()

    
    pipeline = Pipeline(readoutTime)
    tiTriggers = Triggers()
    nTotTrig = 0
    nPipelineFull = 0
    nDeadtime = 0
    nTotTrigAcc = 0
    nTotTrigAccTi = 0
    nTiRule1 = 0
    nTiRule4 = 0
    npl = 0
    triggersInPeriod = Triggers()

    
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

        if tiRules!=None:
            print "tiTriggers status before update "
            print tiTriggers.toString()                
            tiTriggers_readout = updateTiTriggers(tGlobalStart, tiTriggers, ave_per, tiRules)
            print "popped ", len(tiTriggers_readout), " triggers from tiTriggers"
            print "tiTriggers status after update "
            print tiTriggers.toString()
            htitriggers.Fill(len(tiTriggers.triggers))
        
        hpipelinestatus.Fill(len(pipeline.triggers))

        # plot status of pipeline after update
        # plot nr trigger issues last period
        if npl < 50:
            htriggersvstime.SetPoint(npl,tGlobalStart,len(triggersInPeriod.triggers))
            hpipelinestatusvstime.SetPoint(npl,tGlobalStart,len(pipeline.triggers))
            if tiRules!=None:
                htitriggersvstime.SetPoint(npl,tGlobalStart,len(tiTriggers.triggers))
            npl+=1
        


        # run the trigger
        n = int(fp.GetRandom()) # rounds to lower
        nTotTrig += n
        hp.Fill(n)
        print n, " triggers in this period, ", nTotTrig, " total trigger sent"

        # clear the old one
        triggersInPeriod = Triggers()
        ts = []
        for j in range(n):
            t = r.Rndm()*ave_per
            hr.Fill(t)
            ts.append(t)
        # sort them in ascending order
        ts.sort()
        # create "triggers"
        for t in ts:
            triggersInPeriod.triggers.append(Trigger(i,t))
            

        #print triggers.toString()
        #print "sort"
        #triggers.sort()
        print triggersInPeriod.toString()



        
        for trig in triggersInPeriod.triggers:
            print "test ", trig.toString()
            print len(pipeline.triggers), " existing triggers "
            # update pipeline
            print "Pipeline status before update"
            print pipeline.toString()                
            # check if we are still dead from any of the previous triggers
            triggers_readout = updatePipeline(trig.getGlobalTime(ave_per), pipeline, ave_per, readoutTime)
            print "popped ", len(triggers_readout), " triggers from pipeline"
            print "Pipeline status after update "
            print pipeline.toString()                


            # check the TI trigger rules
            passTiRules = True
            if tiRules!=None:
                print "tiTriggers status before update "
                print tiTriggers.toString()                
                tiTriggers_readout = updateTiTriggers(trig.getGlobalTime( ave_per), tiTriggers, ave_per, tiRules)
                print "popped ", len(tiTriggers_readout), " triggers from tiTriggers"
                print "tiTriggers status after update "
                print tiTriggers.toString()
                # check if this trigger is accepted
                #lastTrig = getLastTrigger(tiTriggers,ave_per)
                lastTrig = None
                if len(tiTriggers.triggers) > 0:
                    lastTrig = tiTriggers.triggers[len(tiTriggers.triggers)-1]
                if lastTrig!=None:
                    print "Last tiTrigger found ", lastTrig.toString(), " (glTime = ", lastTrig.getGlobalTime(ave_per), " )"
                    deltaT = trig.getGlobalTime(ave_per)-lastTrig.getGlobalTime(ave_per)
                    if deltaT < tiRules.get(1):
                        passTiRules = False
                        print "failed tiRules 1 with deltaT ", deltaT
                        nTiRule1 += 1
                    else:
                        print "passed tiRules 1 with deltaT ", deltaT
                        if len(tiTriggers.triggers) > tiRules.longestHoldOffMult:
                            passTiRules = False
                            print "failed longestHoldOffMult(",tiRules.longestHoldOffMult,") ,", len(tiTriggers.triggers), " tiTriggers outstanding"
                            nTiRule4 += 1                            
                        else:
                            print "passed longestHoldOffMult(",tiRules.longestHoldOffMult,"),", len(tiTriggers.triggers), " tiTriggers outstanding"
                            hrsti.Fill(trig.time)
                            htsti.Fill(deltaT)


            ###
            # If the trigger passes the TI rules then check if the APV can accept it
            ###
            if passTiRules:
                nTotTrigAccTi += 1
                print "TI-ACCEPTED"
                if tiRules!=None:
                    tiTriggers.triggers.append(trig)

                # check if the APV accepts this trigger
                
                if len(pipeline.triggers)==0:
                    print "APV-ACCEPTED"                
                    hrs.Fill(trig.time)
                    hts.Fill(0.)
                    pipeline.add(trig,ave_per)
                    nTotTrigAcc += 1
                else:                
                    # check if this trigger is accepted
                    #lastTrig = getLastTrigger(pipeline,ave_per)
                    lastTrig = pipeline.triggers[len(pipeline.triggers)-1]

                    print "Last trigger found ", lastTrig.toString()
                    deltaT = trig.getGlobalTime(ave_per)-lastTrig.getGlobalTime(ave_per)

                    if( deltaT > deadTime):
                        print "APV-ACCEPTED for dead time"
                        # is there depth in the pipeline available
                        if len(pipeline.triggers) < pipelineDepth:
                            print "APV-ACCEPTED: space in pipeline exists"
                            nTotTrigAcc += 1
                            hrs.Fill(trig.time)
                            hts.Fill(deltaT)
                            pipeline.add(trig,ave_per)
                        else:
                            nPipelineFull += 1
                            print "APV-FAILED: pipeline full (",pipelineDepth,")"
                    else:
                        print "APV-FAILED: deadtime not expired"
                        nDeadtime += 1
            else:
                print "TI-REJECTED"


    
    if draw:
        c2 = TCanvas("c2","c2",10,10,700,500)
        c2.cd()
        hp.Draw()
        c3 = TCanvas("c3","c3",10,10,700,500)
        c3.cd()
        hr.Draw()
        hrs.SetLineColor(2)
        hrs.DrawNormalized("same",hr.Integral())
        c31 = TCanvas("c31","c31",10,10,700,500)
        c31.cd()
        hr.Draw()
        hrsti.SetLineColor(2)
        if tiRules!=None:
            hrsti.DrawNormalized("same",hr.Integral())
        c33 = TCanvas("c33","c33",10,10,700,500)
        c33.cd()
        hts.Draw()
        c331 = TCanvas("c331","c331",10,10,700,500)
        c331.cd()
        htsti.Draw()
        c333 = TCanvas("c333","c333",10,10,700,500)
        c333.cd()
        hpipelinestatus.Draw()
        c5 = TCanvas("c5","c5",10,10,700,500)
        c5.cd()
        hpipelinestatusvstime.SetMarkerStyle(20)
        hpipelinestatusvstime.Draw("AXLP")
        c55 = TCanvas("c55","c55",10,10,700,500)
        c55.cd()
        htriggersvstime.SetMarkerStyle(20)
        htriggersvstime.Draw("AXLP")
        if tiRules!=None:
            c4 = TCanvas("c4","c4",10,10,700,500)
            c4.cd()
            htitriggers.Draw()
            c44 = TCanvas("c44","c44",10,10,700,500)
            c44.cd()
            htitriggersvstime.SetMarkerStyle(20)
            htitriggersvstime.Draw("AXLP")
            c6 = TCanvas("c6","c6",10,10,700,500)
            c6.cd()
            hpipelinestatusvstime.SetMaximum(6.0)
            hpipelinestatusvstime.SetLineColor(2)
            hpipelinestatusvstime.SetMarkerColor(2)
            hpipelinestatusvstime.Draw("AXLP")
            htitriggersvstime.Draw("LP,same")
            htriggersvstime.SetLineColor(4)
            htriggersvstime.SetMarkerStyle(22)
            htriggersvstime.SetMarkerColor(4)
            htriggersvstime.Draw("LP,same")
            tleg = TLegend(0.6,0.92,0.95,0.67)
            tleg.AddEntry(hpipelinestatusvstime,"APV pipeline","LP")
            tleg.AddEntry(htitriggersvstime,"TI: outst. triggers","LP")
            tleg.AddEntry(htriggersvstime,"Issued triggers prev. period","LP")
            tleg.SetFillColor(0)
            tleg.Draw()
        ins = raw_input('press enter to end prog')

    if save:
        tag = "-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+"-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+tiStrTag.replace(" ","_").replace("=","_")
        c1.SaveAs("fp"+tag+".png")
        c2.SaveAs("hp"+tag+".png")
        c3.SaveAs("hr"+tag+".png")
        c31.SaveAs("hrti"+tag+".png")
        c33.SaveAs("hts"+tag+".png")
        c331.SaveAs("htsti"+tag+".png")
        c333.SaveAs("pipelinestatus"+tag+".png")
        c5.SaveAs("pipelinestatusvstime"+tag+".png")
        if tiRules!=None:
            c4.SaveAs("titriggers"+tag+".png")
            c44.SaveAs("titriggersvstime"+tag+".png")
            c6.SaveAs("buffervstime"+tag+".png")

    return [nTotTrig, nTotTrigAcc, nDeadtime, nPipelineFull, nTotTrigAccTi, nTiRule1, nTiRule4]


def usage():
    print "Usage: Nperiods aveRate deadTime readoutTime pipelinedepth [applyTiRules=1|0]"

def main():
    if len(sys.argv) < 6:
        usage()
        return
    N = int(sys.argv[1]) #1000 #number of periods
    aveRate = float(sys.argv[2]) #50.0e3 #average Poission trigger rate in Hz
    deadTime = float(sys.argv[3]) #0.001 # min time required between triggers in us
    readoutTime = float(sys.argv[4]) #21.0
    pipelineDepth = int(sys.argv[5]) #2

    tiRulesDefault = None
    if len(sys.argv) > 6:
        if int(sys.argv[6])==1:
            tiRulesDefault = TiRules()
            #tiRulesDefault.add(1,0.1)
            tiRulesDefault.add(1,1.4)
            #tiRulesDefault.add(5,110.0)
            tiRulesDefault.add(4,88.4)
            tiRulesDefault.init()

    # Do it once with plots
    res = getLiveTime(N, aveRate, deadTime, pipelineDepth, readoutTime, tiRulesDefault, True, True)
    
    print "Total triggers: sent ", res[0], ", accepted ", res[1], " nDeadtime cut ", res[2], " nPipelineFull ", res[3], ", livetime ", float(res[1])/float(res[0]) , " nTotTrigAccTi ", res[4], " nTiRule1 ", res[5], " nTiRule2 ", res[6]

    ins = raw_input('press anything to continue')


    # do it for a range

    N = 500
    gr_tirules_lt = []
    gr_tirules_lt_titles = []
    dt = 0.1
    for i in range(4):
        gr_lt = TGraph()
        n=0
        tiRules = TiRules()
        tiRules.add(1,1.4)
        if i==0:
            tiRules = None
        elif i==1:
            tiRules.add(4,83.0)
        elif i==2:
            tiRules.add(4,88.4)
        elif i==3:
            tiRules.add(5,110.0)
        else:
            print "error ", i
            sys.exit()
        tiStrTag = "none"
        if tiRules!=None:
            tiRules.init()
            tiStrTag = tiRules.getTiStrTag()
        
        for irate in range(int(10e3),int(100e3),5000):
            res = getLiveTime(N,float(irate),dt,pipelineDepth,readoutTime,tiRules, False,False)
            gr_lt.SetPoint(n,irate,float(res[1])/float(res[0])) 
            print irate, " ", dt, " ",  n, " ", res
            n = n+1
        gr_tirules_lt.append(gr_lt)
        gr_tirules_lt_titles.append(tiStrTag)
    
    c4 = TCanvas("c4","c4",10,10,700,500)
    c4.cd()
    lt_template = TH2F("lt_template","Data taking efficiency;Average trigger rate (Hz);Live time fraction",10,0,100000,10,0.2,1.1)
    lt_template.SetStats(False)
    lt_template.Draw()
    n=0
    leg = TLegend(0.15,0.15,0.55,0.35)
    for i in range(len(gr_tirules_lt)):
        gr_ti = gr_tirules_lt[i]
        gr_ti.SetMarkerSize(1.0)
        gr_ti.SetMarkerStyle(20)
        gr_ti.SetMarkerColor(1+n)
        gr_ti.SetLineColor(1+n)
        gr_ti.Draw("LP,same")
        leg.AddEntry(gr_ti,"TI rule="+gr_tirules_lt_titles[i],"LP")
        n = n+1
    leg.SetFillColor(0)
    leg.SetBorderSize(0)
    leg.Draw()
    tiStrTag = ""
    tag =  "-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+tiStrTag.replace(" ","_").replace("=","_")
    c4.SaveAs("livetime-vs-rate-for-TIRules"+tag+".png")

    ins = raw_input('press anything to continue')




    N = 500
    gr_dt_lt = {}
    dtRange = [0.1, 10.0, 20.0, 25.0]
    #for dt in range(5,30,5):
    for dt in dtRange:
        gr_lt = TGraph()
        n=0
        for irate in range(int(10e3),int(100e3),5000):
            res = getLiveTime(N,float(irate),float(dt),pipelineDepth,readoutTime,tiRulesDefault, False,False)
            gr_lt.SetPoint(n,irate,float(res[1])/float(res[0])) 
            print irate, " ", dt, " ",  n, " ", res
            n = n+1
        gr_dt_lt[dt] = gr_lt
    
    c4444 = TCanvas("c4444","c4444",10,10,700,500)
    c4444.cd()
    tiStrTag = ""
    if tiRulesDefault!=None:
        tiStrTag = tiRulesDefault.getTiStrTag()
    lt_template2 = TH2F("lt_template2","Data taking efficiency "+tiStrTag+";Average trigger rate (Hz);Live time fraction",10,0,100000,10,0.2,1.1)
    lt_template2.SetStats(False)
    lt_template2.Draw()
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
    tag =  "-depth-"+str(pipelineDepth)+"-readoutTime-"+str(readoutTime)+tiStrTag.replace(" ","_").replace("=","_")
    c4444.SaveAs("livetime-vs-rate-forDeadTime"+tag+".png")

    ins = raw_input('press anything to continue')



if __name__ == "__main__":
    main()

