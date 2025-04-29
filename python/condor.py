for variation in ["prefiring", "jec_AbsoluteStat_up", "jec_AbsoluteScale_up", "jec_AbsoluteMPFBias_up", "jec_Fragmentation_up", "jec_SinglePionECAL_up", "jec_SinglePionHCAL_up", "jec_FlavorQCD_up", "jec_TimePtEta_up", "jec_RelativePtBB_up", "jec_RelativePtEC1_up", "jec_RelativePtEC2_up", "jec_RelativePtHF_up", "jec_RelativeBal_up", "jec_RelativeFSR_up", "jec_RelativeSample_up", "jec_RelativeStatFSR_up", "jec_RelativeStatEC_up", "jec_RelativeStatHF_up", "jec_RelativeJEREC1_up", "jec_RelativeJEREC2_up", "jec_RelativeJERHF_up", "jec_PileUpDataMC_up", "jec_PileUpPtRef_up", "jec_PileUpPtBB_up", "jec_PileUpPtEC1_up", "jec_PileUpPtEC2_up", "jec_PileUpPtHF_up", "jec_AbsoluteStat_down", "jec_AbsoluteScale_down", "jec_AbsoluteMPFBias_down", "jec_Fragmentation_down", "jec_SinglePionECAL_down", "jec_SinglePionHCAL_down", "jec_FlavorQCD_down", "jec_TimePtEta_down", "jec_RelativePtBB_down", "jec_RelativePtEC1_down", "jec_RelativePtEC2_down", "jec_RelativePtHF_down", "jec_RelativeBal_down", "jec_RelativeFSR_down", "jec_RelativeSample_down", "jec_RelativeStatFSR_down", "jec_RelativeStatEC_down", "jec_RelativeStatHF_down", "jec_RelativeJEREC1_down", "jec_RelativeJEREC2_down", "jec_RelativeJERHF_down", "jec_PileUpDataMC_down", "jec_PileUpPtRef_down", "jec_PileUpPtBB_down", "jec_PileUpPtEC1_down", "jec_PileUpPtEC2_down", "jec_PileUpPtHF_down"]:
#for variation in ["nominal"]:
  f = open(variation+"-condor.submit", "w")
  f.write("""
#HTC Submission File for GEN sample production
#requirements      =  OpSysAndVer == "EL9"
universe          = vanilla
notification      = Error
notify_user       = andreas.hinzmann@desy.de
initialdir        = /data/dust/user/hinzmann/jetmass/JetMass/python
#output            = gen$(JobId).o
#error             = gen$(JobId).e
#log               = gen$(JobId).log
#Requesting CPU and DISK Memory - default +RequestRuntime of 3h stays unaltered
+RequestRuntime   = 100000
RequestMemory     = 10G
JobBatchName      = submit_jms_templates
#RequestDisk       = 10G
getenv            = True
executable        = /usr/bin/sh
arguments         = " condor.sh """+variation+'"'+"""
queue 1
""")
  f.close()
  print("condor_submit "+variation+"-condor.submit")
