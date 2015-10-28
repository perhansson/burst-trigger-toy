function event_size = ecalSizePerEvent(hits_per_event)

%% Assume that on average 1/2 of the hits are on top and bottom resp.
%% Assumes that every FADC board report a header for every event!?
%% 442 channels -> 16-chs/FADC -> 14 FADC boards per VXS crate
debug = false;
ecal_bank_header = 32;
n_vxs = 2;
nfadc_per_vxs = 14;
fadc_header = 8*8;
hit_size = 4*8;
occupancy = hits_per_event/442;
hits_size_vxs = hit_size*hits_per_event/2; #1/2 hits on top and bot resp.
header_size_vxs = fadc_header*nfadc_per_vxs; 
size_vxs = header_size_vxs + hits_size_vxs;
event_size = ecal_bank_header + size_vxs*n_vxs;

  fprintf('ECal hits per event: %.2f -> occupancy %.2f%s\n',hits_per_event,occupancy*100,'%');
if debug==true 
  fprintf('nFADC/VXS: %d \n',nfadc_per_vxs);
fprintf('Hits size/vxs: %.2f bits (%.2f bytes) \n',hits_size_vxs,hits_size_vxs/8);
fprintf('Header size/vxs: %.2f bits (%.2f bytes) \n',header_size_vxs,header_size_vxs/8);
fprintf('ECal bank header: %d bits\n',ecal_bank_header);
fprintf('VXS size: %.2f bits (%.2f bytes) \n',size_vxs,size_vxs/8);
fprintf('--> Ecal event size : %.2f bits (%.2f bytes) \n',event_size,event_size/8);
endif

