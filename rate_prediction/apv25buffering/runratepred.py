#!/usr/bin/python

import ratepred,argparse,config,sys
from ROOT import TGraph2D,TGraph,TGraphErrors,TCanvas,TH2F, TPaletteAxis, gPad

def getParser():
    parser = argparse.ArgumentParser(description='Run rate prediction')
    parser.add_argument('-d','--debug',action='store_true',default=False,help='Print debug output')
    parser.add_argument('-n','--trigperiods',action='store',default=10000,help='# of trigger periods to run')
    return parser


if __name__=='__main__':
    print 'Run rate estimation program'
    parser = getParser()
    args = parser.parse_args()
    config.debug = args.debug
    config.batch = True
    config.Nperiods = args.trigperiods
    sys.argv.append('-b-')
    roTime = 23.5e-6 #s
    ave_rate = 43.0e3 # nominal
    buffer_depth = 5
    #ave_rates = [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.,90.,100.]
    #ave_rates = [1.,5.,10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.,90.]
    ave_rates = [30.,35.,40.,45.,50.,60.,70.,100.]
    #ave_rates = [46.,48.]
    ave_rates = [ x*1e3 for x in ave_rates ]
    print 'Run for %d rates (kHz): %s ' % (len(ave_rates),ave_rates)
    print "Buffer depth: %d" % buffer_depth
    print "Readout time: %f us" % (roTime*1.0e6)
    roTimes = [22.,24.]
    #roTimes = [20.,21.,22.,23.,24.,25.,26.,27.]
    roTimes = [ x*1e-6 for x in roTimes]



    gr_trigAccVsRoTime = TGraph()
    gr_trigAccVsRoTime.SetTitle("Trigger Acceptance buffer_depth=%d, Average Trigger Rate %.2fkHz; Readout time (#mus);Trigger acceptance (%s)" % (buffer_depth,ave_rate,'%'))
    gr_deadTimeVsAveRate = TGraphErrors()
    gr_deadTimeVsAveRate.SetTitle("Dead time buffer_depth=%d, roTime=%.2fus; Average Trigger Rate (kHz);Mean dead time (#mus)"%(buffer_depth,(roTime*1.0e6)))
    gr_outputRateVsAveRate = TGraph()
    gr_outputRateVsAveRate.SetTitle("Output rate buffer_depth=%d, roTime=%.2fus; Average Trigger Rate (kHz);Output rate (kHz)"%(buffer_depth,(roTime*1.0e6)))
    gr_trigAccVsAveRate = TGraph()
    gr_trigAccVsAveRate.SetTitle("Triggers Accepted buffer_depth=%d, roTime=%.2fus; Average Trigger Rate (kHz);Triggers Accepted (%s)"%(buffer_depth,(roTime*1.0e6),'%'))
    gr_trigAccVsAveRateRoTime = TGraph2D()

    for r in range(len(ave_rates)):
        ave_time = 1.0/(ave_rates[r])
        print "Run average rate %.2fkHz (dt=%.2fus) " % (ave_rates[r]*1e-3,ave_time*1e6)
        name = '_averate%.2f_dt%.2f_buf%d_rot%.2f' % ((ave_rates[r]),ave_time,buffer_depth,(roTime*1.0e6))
        v = ratepred.runRatePred(name,ave_rates[r],roTime,buffer_depth)
        print "Average rate %.2fkHz (dt=%.2fus) ->  %.2f%s triggers accepted" % (ave_rates[r]*1e-3,ave_time*1e6,v[0]*100.0,'%')
        gr_trigAccVsAveRate.SetPoint(r,ave_rates[r]*1e-3,v[0]*100)
        gr_deadTimeVsAveRate.SetPoint(r,ave_rates[r]*1e-3,v[2]*1e6)
        gr_deadTimeVsAveRate.SetPointError(r,0.,v[3]*1e6)
        gr_outputRateVsAveRate.SetPoint(r,ave_rates[r]*1e-3,v[1]*1e-3)
        
        for t in range(len(roTimes)):
            print "Run average rate %.2fkHz (dt=%.2fus) and roTime=%.2fus " % (ave_rates[r]*1e-3,ave_time*1e6,roTimes[t]*1e6)
            name = '_averate%.2f_dt%.2f_buf%d_rot%.2f' % ((ave_rates[r]),ave_time,buffer_depth,(roTimes[t]*1.0e6))
            v = ratepred.runRatePred(name,ave_rates[r],roTimes[t],buffer_depth)
            print "Average rate %.2fkHz (dt=%.2fus) roTime=%.2fus ->  %.2f%s triggers accepted" % (ave_rates[r]*1e-3,ave_time*1e6,roTimes[t]*1e6,v[0]*100.0,'%')
            gr_trigAccVsAveRateRoTime.SetPoint(r+t*len(roTimes),ave_rates[r]*1e-3,roTimes[t]*1e6,v[0]*100);# = TGraph(len(acc_frac),ave_rates,acc_frac)    
    
    for t in range(len(roTimes)):
        print "Run roTime=%.2fus " % (roTimes[t]*1e6)
        name = '_rotimeaverate%.2f_dt%.2f_buf%d_rot%.2f' % (ave_rate,ave_time,buffer_depth,(roTimes[t]*1.0e6))
        v = ratepred.runRatePred(name,ave_rate,roTimes[t],buffer_depth)
        print "Average rate %.2fkHz (dt=%.2fus) roTime=%.2fus ->  %.2f%s triggers accepted" % (ave_rate*1e-3,ave_time*1e6,roTimes[t]*1e6,v[0]*100.0,'%')
        gr_trigAccVsRoTime.SetPoint(t,roTimes[t]*1e6,v[0]*100);# = TGraph(len(acc_frac),ave_rates,acc_frac)    
    

    cAcc = TCanvas("cAcc","cAcc",10,10,700,500)
    cAcc.Divide(2,2)
    cAcc.cd(1)
    gr_trigAccVsAveRate.Draw('ALP')
    cAcc.cd(2)
    gr_deadTimeVsAveRate.Draw('ALP')
    cAcc.cd(3)
    gr_outputRateVsAveRate.Draw('ALP')    
    gPad.SetGrid()
    cAcc.cd(4)
    gr_trigAccVsRoTime.Draw('ALP')
    
    ans = raw_input('press anything to exit')
    cAcc.SaveAs('runratepredsummary.png','png')
