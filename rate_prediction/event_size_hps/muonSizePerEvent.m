function event_size = muonSizePerEvent(occupancy)
%% Assumes in total 232 channels -> 16chs per FADC -> 1 FADC boards
%% 20-slot VXS crates -> need single crate
debug = false;
muon_bank_header = 32;
n_vxs = 1;
nch_per_vxs = 232;
nfadc_per_vxs = 15;
fadc_header = 8*8;
hit_size = 4*8;
hits_size_vxs = hit_size*nch_per_vxs*occupancy;
header_size_vxs = fadc_header*nfadc_per_vxs;
size_vxs = header_size_vxs + hits_size_vxs;
event_size = muon_bank_header + size_vxs*n_vxs;

fprintf('Muon occupancy: %.2f%s\n',occupancy*100,'%'); 
if debug==true
fprintf('FADC/VXS: %d \n',nfadc_per_vxs);
fprintf('Muon hits size/vxs: %.2f bits (%.2f bytes) \n',hits_size_vxs,hits_size_vxs/8);
fprintf('Muon header size/vxs: %.2f bits (%.2f bytes) \n',header_size_vxs,header_size_vxs/8);
fprintf('Muon bank header: %d bits\n',muon_bank_header);
fprintf('Muon VXS size: %.2f bits (%.2f bytes) \n',size_vxs,size_vxs/8);
fprintf('--> Muon event size : %.2f bits (%.2f bytes) \n',event_size,event_size/8);

endif


