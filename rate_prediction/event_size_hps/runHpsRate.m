
clear; close all; clc

% Run conditions
ndays = 30; %2*7; % 30; %
toBits=1e3*8;
kHz=1e3;
svt_event_size = [2.45*toBits 1.72*toBits 1.5*toBits];
trigger_rate_ecal = [17.6*kHz 15.8*kHz 12.6*kHz];
trigger_rate_muon = [0.0*kHz 0.0*kHz 0.0*kHz];
trigger_rate = trigger_rate_ecal + trigger_rate_muon;
run_cond = [1.1 trigger_rate(1,1) ndays svt_event_size(1,1); 2.2 trigger_rate(1,2) ndays svt_event_size(1,2); 6.6 trigger_rate(1,3) ndays svt_event_size(1,3);];

for run = 1:size(run_cond)(1)
  fprintf('E=%f trigrate=%f time=%fdays\n',run_cond(run,1),run_cond(run,2),run_cond(run,3));
  tot_rate = hpsRate(run_cond(run,1),run_cond(run,2),run_cond(run,3),run_cond(run,4));
endfor
