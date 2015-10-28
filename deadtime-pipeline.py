#!/usr/bin/python
import sys
import argparse
from ROOT import TH1F, TRandom3, TF1, TCanvas, TMath, TGraph, TH2F, TLegend
from utils import Trigger, Triggers, Pipeline, PipelineEntry, TiRules, getGlobalTriggerTime, updatePipeline, updateTiTriggers






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
                        if len(tiTriggers.triggers) >= tiRules.longestHoldOffMult:
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

            ans = raw_input("hit anything to continue")


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





def main(args):

    N = args.N
    aveRate = args.A
    deadTime = args.D
    readoutTime = args.R
    pipelineDepth = args.P
    tiRulesDefault = None

    if args.H!=None and len(args.H)>0:
        if(len(args.H)!=3):
            print "Wrong input: trigger rules must be three"
            sys.exit(1)
        tiRulesDefault = TiRules()
        tiRulesDefault.add(1, float(args.H[0]))
        if float(args.H[1]) < 0.0 and  float(args.H[2])<0:
            print "Wrong input: need to supply a 4 or 5 trigger holdoff rule, set one to negative"
            sys.exit(1)
        if float(args.H[1]) > 0.0 and  float(args.H[2])>0:
            print "Wrong input: only one rule out of 4 or 5 can be applied, set the other to negative"
            sys.exit(1)
        if float(args.H[1]) > 0.0:            
            tiRulesDefault.add(4, float(args.H[1]))
        else:
            tiRulesDefault.add(5, float(args.H[2]))
        tiRulesDefault.init()



    # Do it once with plots
    res = getLiveTime(N, aveRate, deadTime, pipelineDepth, readoutTime, tiRulesDefault, True, True)
    
    print "Total triggers: sent ", res[0], ", accepted ", res[1], " nDeadtime cut ", res[2], " nPipelineFull ", res[3], ", livetime ", float(res[1])/float(res[0]) , " nTotTrigAccTi ", res[4], " nTiRule1 ", res[5], " nTiRule2 ", res[6]



    ins = raw_input('press anything to scan over TI RULES')



    N = 500
    gr_tirules_lt = []
    gr_tirules_lt_titles = []
    dt = 0.1
    for i in range(5):
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
        elif i==4:
            tiRules.add(4,30.8)
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
    c4.SaveAs("livetime-vs-rate-for-TIRules"+tag+".root")





    ins = raw_input('press anything to scan over dead time')




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

    parser = argparse.ArgumentParser(description='Do toy simulation of APV25 rate capability')
    parser.add_argument('-N', type=int, default=1000, help='number of trigger periods to simulate')
    parser.add_argument('-A', type=float, default=50000.0, help='Average trigger rate in Hz')
    parser.add_argument('-D', type=float, default=0.1, help='Minimum time holdoff between triggers in us')
    parser.add_argument('-R', type=float, default=20.6, help='Readout time in us')
    parser.add_argument('-P', type=int, default=5, help='Pipeline depth')
    parser.add_argument('-H', nargs="*", help='Apply TI HOLDOFF rules 1, 4 and 5 in order')
    args = parser.parse_args()
    print args

    ans = raw_input("go")

    main(args)

