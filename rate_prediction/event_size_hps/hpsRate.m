function total_event_rate = hpsRate(beam_energy,trigger_rate, ndays, svtEventSizeExt)
debug=false;
% Run conditions
fprintf('--Run Conditions--\n');
duty_factor = 1;
fprintf('Beam energy: %.2f GeV\nTrigger rate: %.2f Hz\nExt. SVT event size: %.0f Bits\nDays of running: %d\nDuty factor: %.2f\n',beam_energy,trigger_rate,svtEventSizeExt,ndays,duty_factor);

if (beam_energy!=1.1 && beam_energy!=2.2 && beam_energy!=6.6)
  error('Ill-defined energy: %f GeV\n',beam_energy);
endif



%% SVT
svt_event_size=999999999.9;
if (svtEventSizeExt<0) 
  nHybrids = 36;
  nFpgas = 12;
  nTrackPerEvent = 10;
  if (beam_energy==1.1)
    nTrackPerEvent = 10;
  elseif  (beam_energy==2.2)
    nTrackPerEvent = 10;
  elseif  (beam_energy==6.6)
    nTrackPerEvent = 10;
  endif
  nLayersHitPerTrack = 10; % i.e. # sensors hit on average for each track
  clusterSize = 2;
  nSvtHitsPerEvent = svtHitsPerEvent(clusterSize,nTrackPerEvent,nLayersHitPerTrack)
  if (debug==true)
    fprintf('--SVT--\nnHybrids: %d nFPGA: %d\nAve. # tracks/event: %.2f\nAve. # sensors hit: %.2f\nAve. cluster size: %.2f\n',nHybrids,nFpgas,nTrackPerEvent,nLayersHitPerTrack,clusterSize);
    fprintf('=># SVT channels/event from tracks: %.2f\n',nSvtHitsPerEvent);
  endif
  svt_event_size = svtSizePerEvent(nSvtHitsPerEvent,nHybrids,nFpgas);
else 
  svt_event_size = svtEventSizeExt;
endif
fprintf('SVT event size:  %.2f kBits (%.2f kBytes)\n',svt_event_size*1e-3,svt_event_size*1e-3/8.);
svt_rate = svt_event_size*trigger_rate;
fprintf('SVT Rate:  %.2f Mbits/s (%.2f Mbytes/s)\n',svt_rate*1e-6,svt_rate*1e-6/8.);


%% ECAL
nEcalCrystalHitsPerEvent = 13.16;
%From Sho Dec. 15 2012
%18.53 hits/event for 2.2 GeV beam+tridents
%20.86 for 6.6
%13.16 for 1.1
if (beam_energy==1.1)
  nEcalCrystalHitsPerEvent = 13.16;
elseif  (beam_energy==2.2)
  nEcalCrystalHitsPerEvent = 18.53;
elseif  (beam_energy==6.6)
  nEcalCrystalHitsPerEvent = 20.86;
endif
ecal_event_size = ecalSizePerEvent(nEcalCrystalHitsPerEvent);
ecal_rate = ecal_event_size*trigger_rate;
if(debug==true)
  fprintf('\n--ECal--\nCrystal hits/event: %.2f\n',nEcalCrystalHitsPerEvent);
endif
fprintf('Ecal event size: %.2f kBits (%.2f kBytes)\n',ecal_event_size*1e-3,ecal_event_size*1e-3/8.);
fprintf('ECal Rate: %.2f Mbits/s (%.2f Mbytes/s)\n',ecal_rate*1e-6,ecal_rate*1e-6/8.);

%% MUON
muon_occ = 0.1;
if (beam_energy==1.1)
  muon_occ = 0.1;
elseif  (beam_energy==2.2)
  muon_occ = 0.1;
elseif  (beam_energy==6.6)
  muon_occ = 0.1;
endif
muon_event_size = muonSizePerEvent(muon_occ);
muon_rate = muon_event_size*trigger_rate;
if(debug==true)
  fprintf('\n--Muon--\nOccupancy: %.2f%s\n',muon_occ*100,'%');
endif
fprintf('Muon event size: %.2f kBits (%.2f kBytes)\n',muon_event_size*1e-3,muon_event_size*1e-3/8.);
fprintf('Muon Rate: %.2f Mbits/s (%.2f Mbytes/s)\n',muon_rate*1e-6,muon_rate*1e-6/8.);



total_event_size = svt_event_size + ecal_event_size + muon_event_size;
fprintf('----\nHPS Total\nHPS event size: %.2f kBits (%.2f kBytes)\n',total_event_size*1e-3,total_event_size*1e-3/8);

total_event_rate = svt_rate + ecal_rate + muon_rate;
fprintf('HPS event rate: %.2f Mbits/s (%.2f Mbytes/s)\n',total_event_rate*1e-6,total_event_rate*1e-6/8);
data_volume = dataTakingVolume(total_event_rate,ndays,duty_factor);

fprintf('\n----\n Data taking over %d days with a duty factor of %.2f\n',ndays,duty_factor);
fprintf('Total amount of data collected: %.2f Tbits (%.2fTbytes)\n',data_volume*1e-12,data_volume*1e-12/8);
