function event_size = svtSizePerEvent(ntracksperevent,nhybrids,nfpga)
debug = false;
if debug==true 
  fprintf('Number of FPGAs: %d\n',nfpga);
fprintf('Number of hybrids: %d\n',nhybrids);
endif

svt_bank_header = 32;
fpga_id = 32;
fpga_for_event_id = 32;
tail = 32;
hybrid_temp = 32*6; %Why?
% Comment from Omar: 
% The following is the header format that was used for the test run
% Header = 8 x 32-bits
%       Header[0] = BankHeader[31:0] ==> 32 bits
%       Header[1] = FpgaAddress[31:0] ==> 32 bits
%       Header[2] = TempB[15:0], TempA[15:0] ==> 32 bits x 6
%       Header[3] = TempD[15:0], TempC[15:0]
%       Header[4] = TempF[15:0], TempE[15:0]
%       Header[5] = TempH[15:0], TempG[15:0]
%       Header[6] = TempJ[15:0], TempI[15:0]
%       Header[7] = TempL[15:0], TempK[15:0]
%
% This is what I obtain from my notes.  I should update the confluence page
% at some point with the new format of the header.
%
% After the header then you have a single 32 bit event number used for syncing 
% which is then followed by the samples.
fpga_overhead = 80; %Why?
% Comment from Omar: 
% This is something that Ryan should clear up.  I suspect that this may be due
% to some frame gap but I'm just guessing.

min_size = svt_bank_header + nfpga*fpga_id + nfpga*fpga_for_event_id + nfpga*tail + nfpga*hybrid_temp + nfpga*fpga_overhead;

if debug==true 
fprintf('Minimum SVT event size: %d bits (%.1f bytes)\n',min_size,min_size/8.0);
endif

nsamples_event = svtOccupancy(ntracksperevent,nhybrids)

if debug==true 
fprintf('# samples per event: %.1f bytes\n',nsamples_event);
endif

nhits_event = nsamples_event/6;

if debug==true 
fprintf('# hits per event: %.1f\n',nhits_event);
endif

% 4 32-bit integers per hit
% Omar: break it down for me here to get to 4x32/hit
hit_size = 4*32;
% Comment from Omar: 
% Sample Data consists of the following: Z[xx:xx] = Zeros, O[xx:xx] = Ones
% Information required to identify where a hit emerges from
%    Sample[0] = O[0], Z[0], Hybrid[1:0], Z[0], ApvChip[2:0], Z[0], Channel[6:0], FpgaAddress[15:0] 
% Two samples are stored within every 32 bit int.  Each sample is 15 bits long
%    Sample[1] = Z[1:0], Sample1[13:0]], Z[1:0], Sample0[13:0]  ==> Sample 1 & 2
%    Sample[2] = Z[1:0], Sample3[13:0]], Z[1:0], Sample2[13:0]  ==> Sample 3 & 4
%    Sample[3] = Z[1:0], Sample5[13:0]], Z[1:0], Sample4[13:0]  ==> Sample 5 & 6

if debug==true 
fprintf('size/hit: %d bits (%.1f bytes)\n',hit_size,hit_size/8.);
endif

hits_size = nhits_event*hit_size;

if debug==true 
fprintf('hits size/event: %d bits (%.1f bytes)\n',hits_size,hits_size/8.);
endif

event_size = hits_size + min_size;

if debug==true 
fprintf('--> Event size: %d bits (%.1f bytes)\n',event_size,event_size/8.);
endif
