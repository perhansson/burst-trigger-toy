#!/usr/bin/python


import os,sys,argparse,string
from numpy import random
from ROOT import TH1F,TCanvas,TLatex
import config
from Apv25 import Apv25
from Buffer import Buffer

def getParser():
    parser = argparse.ArgumentParser(description='Run rate prediction')
    parser.add_argument('-r','--rate',action='store',required=True,help='Average trigger rate')
    parser.add_argument('-l','--bufferdepth',action='store',required=False,default=5,help='Buffer depth')
    parser.add_argument('-t','--deadtime',action='store',required=False,default=25.0e-6,help='Readout time per trigger')
    parser.add_argument('-n','--trigperiods',action='store',default=10000,help='# of trigger periods to run')
    parser.add_argument('-d','--debug',action='store_true',default=False,help='Print debug output')

    return parser


def myText(x,y,text):
    l = TLatex();
    l.SetNDC()
    l.SetTextSize(0.05)
    l.SetTextColor(1)
    l.DrawLatex(x,y,text)


def usage():
    print 'Usage: ratepred [debug] ave_rate'
    print 'Parameters:'
    print 'ave_rate: average trigger rate in Hz'


def runRatePred(name,ave_rate,roTime,buffer_depth):

    NtrigsPerPeriod = 1
    ave_rate = ave_rate*NtrigsPerPeriod
    ave_time = 1/ave_rate

    N = int(config.Nperiods)
    title1 =  '<rate>=%.1fkHz buf depth=%d, roTime=%.3f#mus' % ((ave_rate*1.0e-3),buffer_depth,(roTime*1e6))
    hnumTrigs = TH1F("hnumTrigs%s"%name,"# triggers %s;# triggers per %.1f#mus"%(title1,(ave_time*1.0e6)),buffer_depth+3,0,buffer_depth+3)
    htTrigs = TH1F("htTrigs%s"%name,"Trigger time %s;Trigger time in %.1f#mus window"%(title1,(ave_time*1.0e6)),40,-ave_time/5,ave_time+ave_time/5)
    hnbufTrigs = TH1F("hnbufTrigs%s"%name,"# buffered triggers %s;# buffered triggers at each %.1f#mus window"% (title1,(ave_time*1.0e6)),buffer_depth+3,0,buffer_depth+3)
    htrigAcc = TH1F("htrigAcc%s"%name,"htrigAcc %s;# triggers accepted %.1f#mus window"% (title1,(ave_time*1.0e6)),2,0,2)
    hnTrigsReadout = TH1F("hnTrigsReadout%s"%name,"# triggers readout %s;# triggers readout at each %.1f#mus window"% (title1,(ave_time*1.0e6)),buffer_depth+3,0,buffer_depth+3)
    hdtTrigs = TH1F("hdtTrigs%s"%name,"Time between adjacent triggers %s;#Deltat (s) between triggers"% (title1),40,0,2*ave_time)
    hdeadTime = TH1F("hdeadTime%s"%name,"Dead time %s;Dead time (s)"% (title1),40,0,2*roTime)

    useConstantRate = False

    apv = Apv25(roTime,buffer_depth)    
    apv.clear_buffers()

    # Loop is over each period in time where we expect 1 trigger on average
    numTrigsReadout = 0
    numTrigsSent = 0
    t_prev = -1
    firstT = True
    for ievent in range(N):
        if not useConstantRate: numTrigs = random.poisson(NtrigsPerPeriod)
        else:  numTrigs=1

        hnumTrigs.Fill(numTrigs)

        trigtimes = []

        if useConstantRate:
            trigtimes.append(0.)
        else:
            #find the points during this time interval when the trigger(s) happened
            for itrig in range(numTrigs):
                t = random.uniform(0.,ave_time)
                htTrigs.Fill(t)
                trigtimes.append(t)
            trigtimes.sort()
            if config.debug:
                print 'period %d has %d triggers at t = %s ' % (ievent,numTrigs,trigtimes)
        
        if ievent==0:
            if config.debug:
                print 'First event buffer status:'
                apv.print_buffer_status()
        
        # count the nr of buffers readout in this time period

        nBuffersReadoutInPeriod = 0
        if t_prev>=0: t_prev = t_prev-ave_time
        for t in trigtimes:
            numTrigsSent = numTrigsSent + 1
            n = apv.update_buffers(t)
            nBuffersReadoutInPeriod = nBuffersReadoutInPeriod + n;
            trig_acc = apv.trigger(t)
            if config.debug:
                print 'trig_acc=%d for trigger at t=%f' % ( trig_acc, t)
            if trig_acc:
                htrigAcc.Fill(1.)
                if apv.buffer_is_full():
                    deadtime = apv.get_dead_time()
                    hdeadTime.Fill(deadtime)
            else:
                htrigAcc.Fill(0.)
            if not firstT:
                hdtTrigs.Fill(t-t_prev)
            else :
                firstT = False
            t_prev = t
        
        # Readout buffers at the end of this period
        n = apv.update_buffers(ave_time)
        nBuffersReadoutInPeriod = nBuffersReadoutInPeriod + n;
        apv.rollaroundbuffers(ave_time)
        hnbufTrigs.Fill(len(apv.buffers))
        hnTrigsReadout.Fill(nBuffersReadoutInPeriod)
        numTrigsReadout = numTrigsReadout + nBuffersReadoutInPeriod
    
    
    ave_output_rate = numTrigsReadout/(N*ave_time);
    ave_input_rate = numTrigsSent/(N*ave_time);
    frac_acc_triggers = htrigAcc.GetMean()
    poisson_integ = hnumTrigs.Integral(-1,100000)
    poisson_integ_overbuf = hnumTrigs.Integral(hnumTrigs.FindBin(buffer_depth)+1,100000)
    poisson_frac = poisson_integ_overbuf/poisson_integ

    cnumTrigs = TCanvas('cnumTrigs_%s'%name,'cnumTrigs_%s'%name,10,10,1300,800)
    cnumTrigs.Divide(2,3)
    cnumTrigs.cd(1)
    hnumTrigs.Draw()
    myText(0.5,0.65,'#int_{%d} P(%d) = %.4f%s' % (buffer_depth+1,NtrigsPerPeriod,poisson_frac,'%'))
    cnumTrigs.cd(2)
    hdeadTime.Draw()
    cnumTrigs.cd(4)
    hnbufTrigs.Draw()
    cnumTrigs.cd(3) 
    hnTrigsReadout.Draw()
    myText(0.5,0.65,'# triggers sent/accept=%d/%d' % (numTrigsSent,numTrigsReadout))
    myText(0.5,0.55,'# input/output rate %.4f/%.4f kHz' % (ave_input_rate*1e-3,ave_output_rate*1e-3))
    cnumTrigs.cd(5) 
    htrigAcc.Draw()
    myText(0.65,0.35,'%.2f%s accepted triggers' % (frac_acc_triggers*100,'%'))
    cnumTrigs.cd(6) 
    hdtTrigs.Draw()

    #ctTime = TCanvas('ctTime_%s'%name,'ctTime_%s'%name,20,20,710,510)
    #ctTime.cd()
    #htTrigs.Draw()
    
    print "%d/%d triggers sent/readout over %d periods --> Average output rate = %.2f kHz" % (numTrigsSent,numTrigsReadout,N,ave_output_rate)
    print "Number of triggers %.2f%s triggers accepted with %f s deadtime" % (frac_acc_triggers*100.0,'%',hdeadTime.GetMean())
    print "Number of triggers %.2f%s triggers accepted" % (frac_acc_triggers*100.0,'%')

    if not config.batch:
        ans = raw_input('Press anything to quit')

    cnumTrigs.SaveAs("ratepredsummary_%s.png"%name,'png')

    v = [frac_acc_triggers,ave_output_rate,hdeadTime.GetMean(),hdeadTime.GetMeanError()]
    return v
    

    
    

    

if __name__=='__main__':
    print 'Run rate estimation program'
    parser = getParser()
    args = parser.parse_args()
    config.debug = args.debug
    config.batch = False
    config.Nperiods = args.trigperiods

    ave_rate = float(args.rate)
    ave_time = float(1.0/ave_rate)
    roTime = float(args.deadtime)
    buffer_depth = int(args.bufferdepth)
    print "Average rate: %f kHz" % (ave_rate*1.0e-3)
    print "Average time between triggers: %f us" % (ave_time*1.0e6)
    print "Buffer depth: %d" % buffer_depth
    print "Readout time: %f us" % (roTime*1.0e6)

    name = '_averate%.2f_buf%d_rot%.2f' % ((ave_rate*1.0e-3),buffer_depth,(roTime*1.0e6))
    mean = runRatePred(name,ave_rate,roTime,buffer_depth)

