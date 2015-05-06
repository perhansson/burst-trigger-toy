

void run() {
  
  TF1 * f = new TF1("f","TMath::PoissonI(x,[0])", 0.,10.0);
  f->SetParameter(0,1);
  TH1F * hdead = new TH1F("hdead","hdead",2,0.,2.);
  TRandom3 r;
  
  f->Draw("XL");
  
  int dead;
  double v,ntrig;
  for(int i=0;i<1000;++i) {       
    dead = 0;
    ntrig = f->GetRandom();
    cout << " ntrig " << ntrig << endl;
    if(p>=1) {
      v = r.Rndm();  
      cout << " v " << v << endl;
      if(v<0.5) 
	dead = 1;
      else
	dead = 0;      
    }    
    
    hdead->Fill(dead);
    
  }
  
  hdead->Draw();
  
  
}
