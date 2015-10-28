function datavol = dataTakingVolume(dataRate,ndays,dutyfactor)

datavol = dataRate*ndays*24*3600*dutyfactor;
