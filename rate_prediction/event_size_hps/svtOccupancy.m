function n = svtOccupancy(nhitsperevent,nhybrids)

debug = false;
norm_3sigma_quantile = 0.9973;
fpga_rejection = 1.0;
n_SVT_channels = nhybrids*5*128;

f_occ = (1-norm_3sigma_quantile)/2.0;
nch = nhybrids*128.*5.;
n_noise_hits = nch*f_occ;
%if debug==true 
  fprintf('SVT Occupancy from noise: %.3f%s\n',f_occ*100.0,'%');
fprintf('SVT Noisy chs above threhold: %.3f\n',n_noise_hits);
fprintf('SVT FPGA rejection of noise channels: %.3f\n',fpga_rejection);
%endif

n_track_hits = nhitsperevent;

%if debug==true 
fprintf('# SVT chs/event from real hits: %.3f\n',n_track_hits);
fprintf('# SVT chs/event from noise hits: %.3f\n',n_noise_hits);
%endif
n_hits_total = n_track_hits + n_noise_hits;

total_occupancy = n_hits_total/n_SVT_channels/1.0;

fprintf('Total SVT occupancy: %.3f%s (%d SVT channels)\n',total_occupancy*100.0,'%',n_SVT_channels);

if debug==true 
  fprintf('# channels/event from all hits: %.3f\n',n_hits_total);
endif

n_samples_total = n_hits_total*6.0;

if debug==true 
  fprintf('# samples/event from all hits: %.3f\n',n_samples_total);
endif

n_samples_total = n_samples_total - n_noise_hits*6.0*(1.0-1.0/fpga_rejection);


if debug==true 
  fprintf('# samples/event with fpga rejection %.1f: %.3f\n',fpga_rejection,n_samples_total);
endif
n = n_samples_total;
