fitValues=[]
fitValuesComes=999
impactValues=[]
name=None
previousName=None
previousImpactValues=[]

for json in ['UnfoldingParticleNet_N2Cut_18-09-24/FullRunII/impacts.json']:
  with open(json) as f:
    lines=f.readlines()
    for l in lines:
      if fitValuesComes<3:
        fitValues+=[float(l.strip(" ,\n"))*0.3]
        fitValuesComes+=1
      if '"fit"' in l:
        fitValuesComes=0
        fitValues=[]
      if 'impact_' in l:
        impactValues+=[float(l.split(':')[1].strip(" ,\n"))]
      if "name" in l:
         name=l.split('"')[3]
         if "wjets_W_tag_eff_sf" in l:
           print(name,fitValues[1]+1.0,"+",fitValues[2]-fitValues[1],"-",fitValues[1]-fitValues[0])
         if len(impactValues)>0:
           name=name.split("_UL")[0]
           if name==previousName:
             impactValues[0]=min(impactValues[0:4]+previousImpactValues[0:4])
             impactValues[4]=min(impactValues[4:8]+previousImpactValues[4:8])
             impactValues[8]=min(impactValues[8:12]+previousImpactValues[8:12])
             impactValues[12]=min(impactValues[12:16]+previousImpactValues[12:16])
             impactValues[0+1]=max(impactValues[0:4]+previousImpactValues[0:4])
             impactValues[4+1]=max(impactValues[4:8]+previousImpactValues[4:8])
             impactValues[8+1]=max(impactValues[8:12]+previousImpactValues[8:12])
             impactValues[12+1]=max(impactValues[12:16]+previousImpactValues[12:16])
           print(name,str(int(min(impactValues[0:4])*1000)/10).replace("0.0","$<$0.1")+" -- "+str(int(max(impactValues[0:4])*1000)/10) +" \% & "+ str(int(min(impactValues[4:8])*1000)/10).replace("0.0","$<$0.1")+" -- "+str(int(max(impactValues[4:8])*1000)/10) +" \% & "+ str(int(min(impactValues[8:12])*1000)/10).replace("0.0","$<$0.1")+" -- "+str(int(max(impactValues[8:12])*1000)/10) +" \% & "+ str(int(min(impactValues[12:16])*1000)/10).replace("0.0","$<$0.1")+" -- "+str(int(max(impactValues[12:16])*1000)/10)+" \%")
           previousName=name
           previousImpactValues=impactValues
           impactValues=[]
