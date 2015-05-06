
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


def getGlobalTime(trigger, ave_per):
    return trigger.period*ave_per + trigger.time

class Trigger():
    def __init__(self,period, timestamp):
        self.period = period
        self.time = timestamp
    def toString(self):
        return " Trigger at " + str(self.period) + " time " + str(self.time)

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



def getLiveTime(N, aveRate, deadTime, draw=False, save=False):



    print "go ", N, ", ", aveRate, ", ", deadTime 

    ave_per = 1.0/aveRate*1e6 #average period between triggers in us

    hp = TH1F("hp","Triggers within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",10,0.,10)
    hr = TH1F("hr","Trigger time within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",10,0.,ave_per)
    hrs = TH1F("hrs","Selected; trigger time within period (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",10,0.,ave_per)
    hts = TH1F("hts","Trigger time b/w accepted triggers (per=" + str(ave_per) + "#mus" + " dt="+str(deadTime)+"#mus)",50,0.,max(deadTime,ave_per)*4)
    r = TRandom3()
    fp = TF1("fp","TMath::PoissonI(x,[0])",0.,10.)
    fp.SetParameter(0,1.)
    if draw:
        c1 = TCanvas("c1","c1",10,10,500,700)
        c1.cd()
        fp.Draw()

    
    trig_prev = None
    nTotTrig = 0
    nTotTrigAcc = 0
    for i in range(N):
        #print "--- Period ", i , " start ---"
        n = int(fp.GetRandom()) # rounds to lower
        nTotTrig += n
        hp.Fill(n)
        #print n, " triggers in this period, ", nTotTrig, " total trigger sent"
        triggers = Triggers()
        for j in range(n):
            t = r.Rndm()*ave_per
            hr.Fill(t)
            triggers.add(Trigger(i,t))
        #print triggers.toString()
        #print "sort"
        triggers.sort()
        #print triggers.toString()
        for trig in triggers.getList():
            #print "test ", trig.toString()
            if trig_prev==None:
                #print "ACCEPTED"                
                hrs.Fill(trig.time)
                trig_prev = trig
                nTotTrigAcc += 1
            else:
                #print "existing trigger: ", trig_prev.toString()
                # check if we are still dead
                deltaT = getGlobalTime(trig, ave_per)-getGlobalTime(trig_prev,ave_per)
                if( deltaT > deadTime):
                    #print "ACCEPTED"
                    nTotTrigAcc += 1
                    hrs.Fill(trig.time)
                    hts.Fill(deltaT)
                    # replace old trigger
                    trig_prev = trig
                    #print "REJECTED"
    
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
        ins = raw_input('press enter to end prog')

    if save:
        c1.SaveAs("fp-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+".png")
        c2.SaveAs("hp-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+".png")
        c3.SaveAs("hr-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+".png")
        c33.SaveAs("hts-rate-"+str(aveRate)+"-deadTime-"+str(deadTime)+".png")

    return [nTotTrig, nTotTrigAcc]

def main():
    N = 10000 #number of periods
    aveRate = 20.0e3 #average Poission trigger rate in Hz
    deadTime = 25.0 # min time required between triggers in us 
    
    res = getLiveTime(N, aveRate, deadTime, True, True)
    
    print "Total triggers: sent ", res[0], ", accepted ", res[1], ", livetime ", float(res[1])/float(res[0])

    ins = raw_input('press anything to continue')

    N = 1000
    gr_dt_lt = {}
    for dt in range(5,30,5):
        gr_lt = TGraph()
        n=0
        for irate in range(int(10e3),int(100e3),5000):
            res = getLiveTime(N,float(irate),float(dt),False,False)
            gr_lt.SetPoint(n,irate,float(res[1])/float(res[0])) 
            print irate, " ", dt, " ",  n, " ", res
            n = n+1
        gr_dt_lt[dt] = gr_lt
    
    c4 = TCanvas("c4","c4",10,10,500,700)
    c4.cd()
    lt_template = TH2F("lt_template","Live time;Average trigger rate (Hz);Live time fraction",10,0,100000,10,0.2,1.0)
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
    c4.SaveAs("livetime-vs-rate.png")
    ins = raw_input('press anything to continue')


if __name__ == "__main__":
    main()
    ins = raw_input('press enter to end prog')

