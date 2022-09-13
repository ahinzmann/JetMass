#!/bin/env python
from __future__ import print_function
import sys,os
sys.path.append(os.getcwd()+'/rhalphalib/')
import rhalphalib as rl
import numpy as np
import ROOT
from ROOT import gROOT,gSystem
rl.util.install_roofit_helpers()


def scale_lumi(hist,lumiscale):
    if(lumiscale == 1.0):
        return hist
    hist_old = hist.Clone()
    hist.Reset()
    for i in range(1,hist.GetNbinsX()+1):
        hist.SetBinContent(i,hist_old.GetBinContent(i)*lumiscale)
        hist.SetBinError(i,hist_old.GetBinError(i)*np.sqrt(lumiscale))
    return hist


def build_pseudo(samples,hist_file,hist_dir,vary_pseudo_like,MINIMAL_MODEL=False,seed=123456, msd_bins = None):
    gSystem.ProcessEvents()
    lumiScale=1.0
    if(len(vary_pseudo_like)>0 and 'lumiScale' in vary_pseudo_like[0]):
        lumiScale = float(vary_pseudo_like[0].split(':')[-1])
    print('LumiScale:',lumiScale)
    if(len(vary_pseudo_like)>1):
        print('building pseudo data from ',samples,' (varied like',vary_pseudo_like,')')
        first_hist_dir = (hist_dir+'__%s')%(samples[0],vary_pseudo_like[1],vary_pseudo_like[2])
        print(first_hist_dir)
        print(hist_file)
        pseudo_data_hist = hist_file.Get(first_hist_dir)
        for sample in samples[1:]:
            this_hist_dir = (hist_dir+'__%s')%(sample,vary_pseudo_like[1],vary_pseudo_like[2])
            pseudo_data_hist.Add(hist_file.Get(this_hist_dir))
        pseudo_data_hist = scale_lumi(pseudo_data_hist,lumiScale)
        return pseudo_data_hist
    else:        
        print('building pseudo data from ',samples,' (unvaried)')
        toys=False
        if(len(vary_pseudo_like)>0 and 'toys' in vary_pseudo_like[0]):
            toys=True
        first_hist_dir = hist_dir%(samples[0],"")
        pseudo_data_hist = hist_file.Get(str(first_hist_dir))
        # print(pseudo_data_hist)
        for sample in samples[1:]:
            if ('qcd' not in sample.lower() or "WJetsMatched" not in sample.lower()) and MINIMAL_MODEL:
                continue
            this_hist_dir = hist_dir%(sample,"")
            print(this_hist_dir)
            pseudo_data_hist.Add(hist_file.Get(str(this_hist_dir)))

        pseudo_data_hist.GetXaxis().SetTitle('msd')
        pseudo_data_hist.SetName("msd")
        print(msd_bins)
        if(msd_bins is not None):
            pseudo_data_hist = pseudo_data_hist.Rebin(len(msd_bins)-1, 'msd', msd_bins)

        if(toys):
            N_entries_toys = pseudo_data_hist.Integral()*lumiScale
            toy_pseudo_data = pseudo_data_hist.Clone()
            toy_pseudo_data.Reset()
            n_toys=100
            for i in range(n_toys):
                ROOT.gRandom.SetSeed(seed+i)
                toy_pseudo_data.FillRandom(pseudo_data_hist,int(N_entries_toys/n_toys))
            toy_pseudo_data.Scale(N_entries_toys/toy_pseudo_data.Integral())
            return toy_pseudo_data
        else:
            pseudo_data_hist = scale_lumi(pseudo_data_hist,lumiScale) 
            return pseudo_data_hist
        
def build_mass_scale_variations(configs, args):
    grid_hist_file_name = configs['gridHistFileName']
    # print('reading grid for nuisance parameter:')
    grid_hist_file = ROOT.TFile(grid_hist_file_name,'READ')
    grid_hist = grid_hist_file.Get('grid')
    grid_axes = dict(item.strip().split("=") for item in grid_hist.GetTitle().split(","))
    x_bins=range(grid_hist.GetNbinsX())
    y_bins=range(grid_hist.GetNbinsY())

    categories_hist=grid_hist_file.Get('categories')
    particle_categories=[]
    for i in range(1,categories_hist.GetNbinsX()+1):
        particle_categories.append(categories_hist.GetXaxis().GetBinLabel(i))

    grid_hist_file.Close()

    # building dictionary to help setup the massScales in actual workspace creator. dict hold the massScale substrings containing pT-bin info
    # and application info sub-dict, which tells the code on which samples/regions the respective nuisance should act on.
    # and can also be separated into W/Z/top scales.
    #
    # for the simple cases of one scale per pT bin (or inclusive in pT) we want the scale(s) to act on either all or just the signal templates:
    base_application_info = {'regions':['pass','passW','fail'],'samples':'signal' if args.VaryOnlySignal else 'all'}
    if(args.pTdependetMassScale):
        mass_scale_setup_dict={("PT"+ch_name.split("Pt")[-1]):base_application_info for ch_name in configs['channels'].keys()}
    else:
        mass_scale_setup_dict={'inclusive':base_application_info}

    #get set of selections to decide which massScale names to return
    selections = set([configs['channels'][c]['selection'] for c in configs['channels'].keys()])
    
    if(args.separateMassScales):
        separate_mass_scale_setup_dict = {}
        for mass_scale_suffix in mass_scale_setup_dict.keys():
            separate_mass_scale_setup_dict.update({"W_"+mass_scale_suffix:{"regions":['pass','passW','fail'],'samples':["WJetsMatched","TTToSemiLeptonic_mergedW"]}})
            if any(s in selections for s in ['W','Zbb']):
                separate_mass_scale_setup_dict.update({"Z_"+mass_scale_suffix:{"regions":['pass','passW','fail'],'samples':["ZJetsMatched"]}})
            if 'top' in selections:
                separate_mass_scale_setup_dict.update({"top_"+mass_scale_suffix:{"regions":['pass','passW','fail'],'samples':["TTToSemiLeptonic_mergedTop"]}})
        mass_scale_setup_dict = separate_mass_scale_setup_dict

    #setting up nuisances correspondig to consituent-variation according to categories from grid
    grid_nuisances = []
    mass_scale_names = []
    
    for category in particle_categories:
        for x_bin in x_bins:
            for y_bin in y_bins:
                mass_scale_names = ['massScale_%s%i_%s%i_%s_%s'%(grid_axes['x'],x_bin,grid_axes['y'],y_bin,category,mass_scale_suffix) for mass_scale_suffix in mass_scale_setup_dict.keys()]
                grid_nuisances.append([{mass_scale_setup_dict.keys()[i]:{'application_info':list(mass_scale_setup_dict.values())[i],'nuisance':rl.NuisanceParameter(mass_scale_names[i],'shape',0,-0.5,0.5)} for i in range(len(mass_scale_names))},x_bin,y_bin,category])
    return grid_nuisances, mass_scale_names

def jet_mass_producer(args,configs):
    """
    configs: configuration dict including:
    ModelName,gridHistFileName,channels,histLocation
      -> channels: dict with dict for each channels:
        -> includes histDir,samples,NormUnc,signal,regions,QcdEstimation
    """
    rebin_msd = True
    binnings = {"W":np.linspace(50,300,26),"top":np.linspace(50,300,26)}
    binning_info = configs.get('binning',binnings["W"])
    min_msd, max_msd = (binning_info[0],binning_info[1])
    binwidth = binning_info[2]
    nbins = int(np.floor((max_msd-min_msd)/binwidth))
    msd_bins = np.linspace(min_msd, nbins*binwidth+min_msd, nbins+1)

    #channels for combined fit
    channels = configs['channels']
    qcd_estimation_channels = {k:v for k,v in channels.items() if "QcdEstimation" in v and v["QcdEstimation"]=="True"}
    
    if(args.verbose>0):
        print('channels:',channels.keys())
    
    #getting path of dir with root file from config
    if(args.verbose>0):
        print('histfilename',configs['histLocation'])
    hist_file = ROOT.TFile(configs['histLocation'])

    do_qcd_estimation =  len(qcd_estimation_channels)>0
    do_initial_qcd_fit = (configs.get("InitialQCDFit","False") == "True")
    qcd_fail_region_constant = (configs.get("QCDFailConstant","False") == "True")
    qcd_fail_sigma_scale = configs.get("QCDSigmaScale",1.0)
    TF_ranges = (-50,50)
    qcdparam_lo,qcdparam_hi = (-100,100)
    QCDFailUnbound = False

    lumi_scale = 1.
    if('Pseudo' in configs and len(configs['Pseudo'])>0 and  'lumiScale' in configs['Pseudo'][0]):
        lumi_scale = float(configs['Pseudo'][0].split(':')[-1])


    def get_hist(hist_dir):
        hist = hist_file.Get(str(hist_dir))
        hist.SetName('msd')
        hist.GetXaxis().SetTitle('msd')
        if(rebin_msd > 0):
            hist = hist.Rebin(len(msd_bins)-1, 'msd', msd_bins)
        if(lumi_scale != 1.0):
            hist = scale_lumi(hist,lumi_scale) 
        return hist

    model_name=  configs.get('ModelName','Jet_Mass_Model')  #get name from config, or fall back to default

    #specify if QCD estimation (using Bernstein-polynomial as TF) should be used
    ################
    #QCD Estimation#
    ################
    # derive pt bins from channel names for the pt,rho grid for the Bernstein-Polynomial

    def get_process_normalizations(process):
        norms = {'channels':[],'fail':[],'pass':[]} 
        for channel_name, config in qcd_estimation_channels.items():
            if(args.verbose>0):                
                print(config['selection']+'_%s__mjet_'%process+config['pt_bin']+ additional_bin+'_fail')
            fail_hist = get_hist(config['selection']+'_%s__mjet_'%process+config['pt_bin']+ additional_bin+'_fail')
            pass_hist = get_hist(config['selection']+'_%s__mjet_'%process+config['pt_bin']+ additional_bin+'_pass')
            # fail_hist = hist_file.Get('W_%s__mjet_'%process+config['pt_bin']+ additional_bin+'_fail')
            # pass_hist = hist_file.Get('W_%s__mjet_'%process+config['pt_bin']+ additional_bin+'_pass')
            # if(rebin_msd > 0):
            #     fail_hist = fail_hist.Rebin(len(msd_bins)-1, 'msd', msd_bins)
            #     pass_hist = pass_hist.Rebin(len(msd_bins)-1, 'msd', msd_bins)
            norms['channels'].append(channel_name)
            norms['fail'].append(fail_hist.Integral())
            norms['pass'].append(pass_hist.Integral())
        norms['fail'] = np.array(norms['fail'])
        norms['pass'] = np.array(norms['pass'])
        norms['eff'] = norms['pass']/norms['fail']
        norms['eff_arr'] = np.array([[norms['eff'][i]]*(len(msd_bins)-1) for i in range(len(norms['eff']))] )
        return norms
            
            
    if(do_qcd_estimation):
        if(args.verbose>0):
            print('Doing some preparations for data driven QCD Estimate (Bernstein TF)')
        bernstein_orders = tuple(configs.get('BernsteinOrders',[2,2]))
        qcd_model = rl.Model('qcdmodel')
        qcd_pass, qcd_fail = 0.,0.
        qcd_estimation_relevant_selection = 'W'
        for channel_name, config in qcd_estimation_channels.items():
            qcd_estimation_relevant_selection = config['selection']
            fail_ch = rl.Channel(str(channel_name + 'fail'))
            pass_ch = rl.Channel(str(channel_name + 'pass'))
            fail_ch._renderExtArgs = not args.skipExtArgRender 
            pass_ch._renderExtArgs = not args.skipExtArgRender
            qcd_model.addChannel(fail_ch)
            qcd_model.addChannel(pass_ch)
            additional_bin = config.get('additional_bin','')
            
            fail_hist = get_hist(qcd_estimation_relevant_selection+'_QCD__mjet_'+config['pt_bin']+ additional_bin+'_fail')
            pass_hist = get_hist(qcd_estimation_relevant_selection+'_QCD__mjet_'+config['pt_bin']+ additional_bin+'_pass')            

            empty_hist = fail_hist.Clone()
            empty_hist.Reset()
            signal_fail = rl.TemplateSample(channel_name + 'fail' + '_' + 'Signal', rl.Sample.SIGNAL, empty_hist)
            fail_ch.addSample(signal_fail)
            signal_pass = rl.TemplateSample(channel_name + 'pass' + '_' + 'Signal', rl.Sample.SIGNAL, empty_hist)
            pass_ch.addSample(signal_pass)

            fail_ch.setObservation(fail_hist)
            pass_ch.setObservation(pass_hist)
            qcd_fail += fail_ch.getObservation().sum()
            qcd_pass += pass_ch.getObservation().sum()
        qcd_eff = qcd_pass / qcd_fail
        qcd_norms = get_process_normalizations('QCD')
        data_norms = get_process_normalizations('Data')

        #get all lower edges from channel names
        # pt_edges = configs.get('pt_edges',[500,550,600,675,800,1200])
        pt_edges = configs.get('pt_edges',[500,650,800,1200])
        pt_bins = np.array(pt_edges)
        # pt_bins = np.array([500, 550, 600, 675, 800, 1200])
        n_pt = len(pt_bins) - 1
        msd = rl.Observable('msd',msd_bins)

        # here we derive these all at once with 2D array
        ptpts, msdpts = np.meshgrid(pt_bins[:-1] + 0.3 * np.diff(pt_bins), msd_bins[:-1] + 0.5 * np.diff(msd_bins), indexing='ij')
        rhopts = 2*np.log(msdpts/ptpts)
        ptscaled = (ptpts - 500.) / (1200. - 500.)
        rhoscaled = (rhopts - (-6)) / ((-2.1) - (-6))
        validbins = (rhoscaled >= 0) & (rhoscaled <= 1)
        rhoscaled[~validbins] = 1  # we will mask these out later

        TF_suffix = configs.get('TFSuffix',"")
        
        if(do_initial_qcd_fit):
            initial_qcd_fit_orders = tuple(configs.get('InitialQCDFitOrders',[2,2]))        
            if not os.path.exists(model_name):
                os.makedirs(model_name)
            if(args.verbose>0):
                print('QCD eff:',qcd_eff)
            # tf_MCtempl = rl.BernsteinPoly("tf_MCtempl", initial_qcd_fit_orders, ['pt', 'rho'], init_params = np.ones((initial_qcd_fit_orders[0]+1,initial_qcd_fit_orders[1]+1)), limits=(-1,10))
            # tf_MCtempl = rl.BernsteinPoly("tf_MCtempl_"+model_name+TF_suffix, initial_qcd_fit_orders, ['pt', 'rho'], init_params = np.ones((initial_qcd_fit_orders[0]+1,initial_qcd_fit_orders[1]+1)), limits=TF_ranges)
            tf_MCtempl = rl.BernsteinPoly("tf_MCtempl", initial_qcd_fit_orders, ['pt', 'rho'], init_params = np.ones((initial_qcd_fit_orders[0]+1,initial_qcd_fit_orders[1]+1)), limits=TF_ranges)
            tf_MCtempl_params = qcd_norms['eff_arr'] * tf_MCtempl(ptscaled, rhoscaled)
            for channel_name, config in qcd_estimation_channels.items():
                # ptbin = np.where(pt_bins==float(channel_name.split('Pt')[-1]))[0][0]
                ptbin = np.where(pt_bins==float(config['pt_bin'].split('to')[0]))[0][0]
                failCh = qcd_model[channel_name + 'fail']
                passCh = qcd_model[channel_name + 'pass']
                failObs = failCh.getObservation()
                if(qcd_fail_region_constant and args.verbose>0):
                    print("Setting QCD parameters in fail region constant")
                # qcdparams = np.array([rl.IndependentParameter('qcdparam_'+model_name+TF_suffix+'_ptbin%d_msdbin%d' % (ptbin, i), 0, constant=qcd_fail_region_constant) for i in range(msd.nbins)])
                # qcdparams = np.array([rl.IndependentParameter('qcdparam_'+model_name+TF_suffix+'_ptbin%d_msdbin%d' % (ptbin, i), 0) for i in range(msd.nbins)])
                qcdparams = np.array([rl.IndependentParameter('qcdparam_ptbin%d_msdbin%d' % (ptbin, i), 0, constant=qcd_fail_region_constant,lo=qcdparam_lo,hi=qcdparam_hi) for i in range(msd.nbins)])
                for param in qcdparams:
                    param.unbound = QCDFailUnbound

                # scaledparams = failObs * (1 + sigmascale/np.maximum(1., np.sqrt(failObs)))**qcdparams
                scaledparams = failObs * ( 1 + qcd_fail_sigma_scale / 100.)**qcdparams
                fail_qcd = rl.ParametericSample('%sfail_qcd' %channel_name, rl.Sample.BACKGROUND, msd, scaledparams)
                failCh.addSample(fail_qcd)
                pass_qcd = rl.TransferFactorSample('%spass_qcd' %channel_name, rl.Sample.BACKGROUND, tf_MCtempl_params[ptbin, :], fail_qcd)
                passCh.addSample(pass_qcd)
                
                failCh.mask = validbins[ptbin]
                passCh.mask = validbins[ptbin]

            qcd_model.renderCombine(model_name+"/qcdmodel")

            qcdfit_ws = ROOT.RooWorkspace('w')
            simpdf, obs = qcd_model.renderRoofit(qcdfit_ws)
            ROOT.Math.MinimizerOptions.SetDefaultPrecision(1e-18)
            # ROOT.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2")
            # ROOT.Math.MinimizerOptions.SetDefaultTolerance(0.0001)
            # ROOT.Math.MinimizerOptions.SetDefaultPrecision(-1.0)
            qcdfit = simpdf.fitTo(obs,
                                  ROOT.RooFit.Extended(True),
                                  ROOT.RooFit.SumW2Error(True),
                                  ROOT.RooFit.Strategy(1),
                                  ROOT.RooFit.Save(),
                                  ROOT.RooFit.Minimizer('Minuit2', 'migrad'),
                                  # ROOT.RooFit.PrintLevel(-1),                              
                                  ROOT.RooFit.PrintLevel(1),
                                  ROOT.RooFit.Minos(0)
            )

            qcdfit_ws.add(qcdfit)
            if "pytest" not in sys.modules:
                qcdfit_ws.writeToFile(model_name+ '/qcdfit_'+model_name+TF_suffix+'.root')
            if qcdfit.status() != 0:
                raise RuntimeError('Could not fit qcd')

            qcd_model.readRooFitResult(qcdfit)
            
            param_names = [p.name for p in tf_MCtempl.parameters.reshape(-1)]
            decoVector = rl.DecorrelatedNuisanceVector.fromRooFitResult(tf_MCtempl.name + '_deco', qcdfit, param_names)
            tf_MCtempl.parameters = decoVector.correlated_params.reshape(tf_MCtempl.parameters.shape)
            tf_MCtempl_params_final = tf_MCtempl(ptscaled, rhoscaled)
            # tf_dataResidual = rl.BernsteinPoly("tf_dataResidual_"+model_name+TF_suffix, bernstein_orders, ['pt', 'rho'], limits=TF_ranges)
            tf_dataResidual = rl.BernsteinPoly("tf_dataResidual", bernstein_orders, ['pt', 'rho'], limits=TF_ranges)
            # tf_dataResidual = rl.BernsteinPoly("tf_dataResidual", bernstein_orders, ['pt', 'rho'], limits=(0,10))
            tf_dataResidual_params = tf_dataResidual(ptscaled, rhoscaled)
            tf_params = data_norms['eff_arr']* tf_MCtempl_params_final * tf_dataResidual_params
        else:
            tf_params = None # define later
        

    #Reading categories of consituent-variations for nuisance paramters from gridHist    

    grid_nuisances, _ = build_mass_scale_variations(configs, args)
    
    #setting up rhalphalib roofit model
    model = rl.Model(model_name)

    if(args.unfolding):
        for channel_name, config in channels.items():
            #Signal sample division in genbins
            from copy import deepcopy
            signal_samples = deepcopy(config['signal'])
            unfolding_bins = configs['unfolding_bins']
            genbins = ['onegenbin'] if args.one_bin else ["ptgen%i_msdgen%i"%(iptgen,imsdgen) for iptgen in range(len(unfolding_bins['ptgen'])-1) for imsdgen in range(len(unfolding_bins['msdgen'])-1)]
            configs['genbins']=genbins
            for signal_sample in signal_samples:
                config['samples'].remove(signal_sample)
                config['signal'].remove(signal_sample)
                for genbin in genbins:
                    sample_genbin_name = "{SAMPLE}_{GENBIN}".format(SAMPLE=signal_sample,GENBIN=genbin)
                    config['samples'].append(sample_genbin_name)
                    config['signal'].append(sample_genbin_name)

    #setting up nuisances for systematic uncertainties
    if(args.verbose>0):
        print('CMS_lumi', 'lnN')
    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')
    lumi_effect = 1.027
    pt_bins_for_jmr_nuisances = list(configs['channels'].keys())
    pt_bins_for_jmr_nuisances.append("inclusive")
    
    jmr_nuisances = {parname:rl.NuisanceParameter(parname,'shape',0,-10,10) for parname in ['jmr_variation_PT'+ch_name.split("Pt")[-1] for ch_name in pt_bins_for_jmr_nuisances]}

    norm_nuisances = {}
    for channel_name in channels.keys():
        if( args.minimalModel ):
            break
        for i, sample in enumerate(channels[channel_name]['samples']):
            if 'NormUnc' not in channels[channel_name]:
                continue
            norm_uncertainties = channels[channel_name]['NormUnc']
            for name,norm_unc in norm_uncertainties.items():
                nuisance_par = [rl.NuisanceParameter(name+'_normUnc','lnN'),norm_unc]
                for k,v in norm_nuisances.items():
                    if name in v[0].name:
                        nuisance_par = v
                if norm_unc>0 and name in sample and  sample not in norm_nuisances:
                    print(sample)
                    norm_nuisances.update({sample:nuisance_par})
    print(norm_nuisances)

    # tagging eff sf for ttbar semileptonic samples
    
    
    # top_tag_eff = rl.IndependentParameter("top_tag_eff_sf",1.,-10,10)
    # W_tag_eff = rl.IndependentParameter("W_tag_eff_sf",1.,-10,10)
    for channel_name, config in channels.items():
        top_tag_eff = rl.IndependentParameter(channel_name+"top_tag_eff_sf",1.,-4,4)
        W_tag_eff = rl.IndependentParameter(channel_name+"W_tag_eff_sf",1.,-4,4)
        
        #using hists with /variable/ in their name (default: Mass, if defined get from config) 
        variable = 'mjet' if 'variable' not in config else config['variable']        
        #getting list of samples from config
        if args.minimalModel:
            config['samples'] = ['QCD','WJetsMatched'] 
        samples =  config['samples']
        #for WMass fit there are multiple regions per sample
        regions = [''] if 'regions' not in config else config['regions']
        if(args.verbose>0):
            print('setting up channel:',channel_name)
            print('getting template of variable:',variable)
            print('samples:',samples)
            print('regions:',regions)
        # #Signal sample division in genbins
        # if(args.unfolding):
        #     from copy import deepcopy
        #     signal_samples = deepcopy(config['signal'])
        #     for signal_sample in signal_samples:
        #         samples.remove(signal_sample)
        #         config['signal'].remove(signal_sample)                
        #         unfolding_bins = configs['unfolding_bins']
        #         genbins = ['onegenbin'] if args.one_bin else ["ptgen%i_msdgen%i"%(iptgen,imsdgen) for iptgen in range(len(unfolding_bins['ptgen'])-1) for imsdgen in range(len(unfolding_bins['msdgen'])-1)]
        #         configs['genbins']=genbins
        #         for genbin in genbins:
        #             sample_genbin_name = "{SAMPLE}_{GENBIN}".format(SAMPLE=signal_sample,GENBIN=genbin)
        #             samples.append(sample_genbin_name)
        #             config['signal'].append(sample_genbin_name)
        #             # samples.append()
            

        for region in regions:
            additional_bin = config.get('additional_bin','')
            region_suffix = '_'+region if len(region)>0 else ''            
            hist_dir = config['selection']+'_%s__'+variable+'_%s'+config['pt_bin'] + additional_bin + region_suffix
            #setting up channel for fit (name must be unique and can't include any '_')
            region_name = str(channel_name + region)
            ch = rl.Channel(region_name)
            ch._renderExtArgs = not args.skipExtArgRender 
            model.addChannel(ch)
            if(args.verbose>0):
                print('hist_dir:',hist_dir)
                print('rl.Channel:',ch)
            # if(not args.noNormUnc):
            #     ch.addParamGroup("NormUnc",set([norm_nuisances[sample_name][0] for sample_name in norm_nuisances.keys()]))

            for sample_name in samples:
                #do not include QCD template here, but rather use qcd estimation below
                if(('QcdEstimation' in config and config['QcdEstimation']=='True') and  'qcd' in sample_name.lower()):
                    continue

                #specify if sample is signal or background type
                sample_type = rl.Sample.SIGNAL if sample_name in config['signal'] else rl.Sample.BACKGROUND
                sample_hist = get_hist(hist_dir%(sample_name,""))

                #setup actual rhalphalib sample
                sample = rl.TemplateSample(ch.name + '_' + sample_name, sample_type, sample_hist)                
                
                #setting effects of constituent variation nuisances (up/down)
                for grid_nuisance_dict, x, y, category in grid_nuisances:
                    for grid_nuisance_name in grid_nuisance_dict.keys():

                        if(args.unfolding):
                            continue
                        
                        #this should strictly not be necessary
                        if(sample.sampletype != rl.Sample.SIGNAL and args.VaryOnlySignal):
                            continue

                        
                        # at this point this just decides to skip massScale based on pT bin since mass_scale_substring hold just info about pT bin
                        mass_scale_substring = "PT"+channel_name.split("Pt")[-1] if args.pTdependetMassScale else "inclusive"
                        if(mass_scale_substring not in grid_nuisance_name):
                            continue
                        
                        #getting rhalphalib paramter from setup_dict
                        grid_nuisance = grid_nuisance_dict[grid_nuisance_name]['nuisance']

                        #getting and "applying" info on which region and sample the respective massScale shoud act on
                        application_info = grid_nuisance_dict[grid_nuisance_name]['application_info']
                        if(sample_name not in application_info['samples'] and application_info['samples'] not in  ['all','signal']):
                            continue
                        if(region not in application_info['regions']):
                            continue

                        #getting hists with up/down varaition for Parameter Effect
                        hist_up = get_hist(hist_dir%(sample_name,str(x) + '_' + str(y) + '_' + category +'_')+ '__up')
                        hist_down = get_hist(hist_dir%(sample_name,str(x) + '_' + str(y) + '_' + category +'_')+ '__down')

                        #if we want to use massScales in fit, we add the actual ParamEffect to NuisanceParamters, this will get them rendered into the workspace.
                        if(not args.noMassScales and not args.noNuisances):
                            sample.setParamEffect(grid_nuisance, hist_up, hist_down,scale=configs.get("massScaleFactor",1.0))
                            
                if(not args.noNuisances):
                    #setting effects of JMR variation nuisance(s)
                    if( args.JMRparameter and sample.sampletype == rl.Sample.SIGNAL):
                        hist_jmr_up = get_hist(hist_dir%(sample_name,"")+"_jer_up")
                        hist_jmr_down = get_hist(hist_dir%(sample_name,"")+"_jer_down")
                        if(args.pTdependetJMRParameter):
                            sample.setParamEffect(jmr_nuisances.get("jmr_variation_PT"+channel_name.split("Pt")[-1]), hist_jmr_up, hist_jmr_down)
                        else:
                            sample.setParamEffect(jmr_nuisances.get("jmr_variation_PTinclusive"), hist_jmr_up, hist_jmr_down)
                    #other nuisances (lumi, norm unc)
                    sample.setParamEffect(lumi, lumi_effect)
                    if(not args.noNormUnc):
                        if sample_name in norm_nuisances.keys():
                            sample.setParamEffect(norm_nuisances[sample_name][0],norm_nuisances[sample_name][1])

                
                ch.addSample(sample)

            PseudoData = 'Pseudo' in configs and len(configs['Pseudo'])>0
            if PseudoData:
                # try:
                data_hist = build_pseudo(samples,hist_file,hist_dir,configs['Pseudo'],args.minimalModel,msd_bins=msd_bins)
                # except:
                # data_hist = build_pseudo_uproot(samples,hist_dir,msd_bins,configs) 
            else:
                if(args.verbose>0):
                    print('using data!!!!!')
                data_hist=get_hist(hist_dir%("Data",""))
                
            # if(rebin_msd > 0):
            #     data_hist = data_hist.Rebin(len(msd_bins)-1, 'msd', msd_bins)
            # data_hist.SetName('msd')
            ch.setObservation(data_hist,read_sumw2=PseudoData)
            if('QcdEstimation' in config and config['QcdEstimation']=='True'):
                mask = validbins[np.where(pt_bins==float(config['pt_bin'].split('to')[0]))[0][0]]
                # dropped_events = np.sum(ch.getObservation().astype(float)[~mask])
                # percentage = dropped_events/np.sum(ch.getObservation().astype(float))
                # print('dropping due to mask: %.2f events (out of %.2f -> %.2f%%)'%(dropped_events,np.sum(ch.getObservation().astype(float)),percentage*100))
                ch.mask = mask
                
        #setting effect for tagging eff scale factors
        #top tagging
        if(args.TTbarTaggingEff and config["selection"]=="top"):
            top_pass_sample = model[channel_name + 'pass']["TTToSemiLeptonic_mergedTop"]
            top_passW_sample = model[channel_name + 'passW']["TTToSemiLeptonic_mergedTop"]
            top_fail_sample = model[channel_name + 'fail']["TTToSemiLeptonic_mergedTop"]
            rpf_top_Wfail = top_pass_sample.getExpectation(nominal=True).sum()/(top_passW_sample.getExpectation(nominal=True).sum() + top_fail_sample.getExpectation(nominal=True).sum())
            top_pass_sample.setParamEffect(top_tag_eff,1.0*top_tag_eff)
            top_passW_sample.setParamEffect(top_tag_eff,(1-top_tag_eff)*rpf_top_Wfail + 1.0)
            top_fail_sample.setParamEffect(top_tag_eff,(1-top_tag_eff)*rpf_top_Wfail + 1.0)
            #W tagging
            W_pass_sample = model[channel_name + 'pass']["TTToSemiLeptonic_mergedW"]
            W_passW_sample = model[channel_name + 'passW']["TTToSemiLeptonic_mergedW"]
            W_fail_sample = model[channel_name + 'fail']["TTToSemiLeptonic_mergedW"]
            rpf_W_topfail = W_passW_sample.getExpectation(nominal=True).sum()/(W_pass_sample.getExpectation(nominal=True).sum() + W_fail_sample.getExpectation(nominal=True).sum())
            W_passW_sample.setParamEffect(W_tag_eff,1.0*W_tag_eff)
            W_pass_sample.setParamEffect(W_tag_eff,(1-W_tag_eff)*rpf_W_topfail + 1.0)
            W_fail_sample.setParamEffect(W_tag_eff,(1-W_tag_eff)*rpf_W_topfail + 1.0)
            
    if(do_qcd_estimation):
        #QCD TF
        if(not do_initial_qcd_fit):
            # tf_params = rl.BernsteinPoly('tf_params_'+model_name+TF_suffix, bernstein_orders, ['pt','rho'], limits = TF_ranges)
            tf_params = rl.BernsteinPoly('tf_params', bernstein_orders, ['pt','rho'], limits = TF_ranges)

            # for a in tf_params.parameters:
            #     for params in a:
            #         params.unbound = True 
            if(args.verbose>0):
                print('Using QCD efficiency (N2-ddt) of %.2f%% to scale initial QCD in pass region'%(qcd_eff*100))
            # tf_params = qcd_eff * tf_params(ptscaled,rhoscaled)
            tf_params = data_norms['eff_arr'] * tf_params(ptscaled,rhoscaled)
        
        for channel_name, config in channels.items():
            if('QcdEstimation' not in config or config['QcdEstimation']=="False"):
                continue
            fail_ch = model[channel_name + 'fail']
            pass_ch = model[channel_name + 'pass']
            ptbin = np.where(pt_bins==float(config['pt_bin'].split('to')[0]))[0][0]
            if(qcd_fail_region_constant and args.verbose>0):
                print("Setting QCD parameters in fail region constant")
            qcd_params = np.array( [rl.IndependentParameter('qcdparam_ptbin%i_msdbin%i'%(ptbin,i), 0 , constant=qcd_fail_region_constant,lo=qcdparam_lo,hi=qcdparam_hi) for i in range(msd.nbins)] )
            # qcd_params = np.array( [rl.IndependentParameter('qcdparam_'+model_name+TF_suffix+'_ptbin%i_msdbin%i'%(ptbin,i), 0 , constant=qcd_fail_region_constant,lo=qcdparam_lo,hi=qcdparam_hi) for i in range(msd.nbins)] )
            for param in qcd_params:
                param.unbound = QCDFailUnbound

            initial_qcd = fail_ch.getObservation()[0].astype(float) if isinstance(fail_ch.getObservation(), tuple) else fail_ch.getObservation().astype(float)
            for sample in fail_ch:
                initial_qcd -= sample.getExpectation(nominal=True)
            if np.any(initial_qcd<0.):
                initial_qcd  = np.where(initial_qcd<=0.,0,initial_qcd)
                if(args.verbose>0):
                    print('negative bins in initial_qcd in ',channel_name)
                # continue
                minimum = np.amin(initial_qcd)
                initial_qcd = np.where(initial_qcd == 0,minimum,initial_qcd)
                initial_qcd += abs(minimum)
                raise ValueError('inital qcd (fail qcd from data - mc) negative at least one bin')
            # scaledparams = initial_qcd * ( 1 + sigmascale / np.maximum(1., np.sqrt(initial_qcd)))**qcd_params
            # scaledparams = initial_qcd * ( 1 + qcd_fail_sigma_scale / np.maximum(1., np.sqrt(initial_qcd)))**qcd_params
            scaledparams = initial_qcd * ( 1 + qcd_fail_sigma_scale / 100.)**qcd_params
            fail_qcd = rl.ParametericSample('%sfail_qcd' %channel_name, rl.Sample.BACKGROUND, msd, scaledparams)
            fail_ch.addSample(fail_qcd)
            # fail_ch.addParamGroup("QCDFail",fail_qcd.parameters)
            pass_qcd = rl.TransferFactorSample('%spass_qcd'% channel_name, rl.Sample.BACKGROUND, tf_params[ptbin,:], fail_qcd)            
            pass_ch.addSample(pass_qcd)
            raw_tf_params = []
            for param in pass_qcd.parameters:
                if("tf" in param.name):
                    raw_tf_params.append(param)
            # pass_ch.addParamGroup("QCDPass",raw_tf_params)
            
    model.renderCombine(model_name)


if(__name__ == "__main__"):
    import json,argparse
    import fitplotter
    from CombineWorkflows import CombineWorkflows

    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str, help="path to json with config")
    parser.add_argument('--justplots',action='store_true', help='just make plots.')
    parser.add_argument('--build', action='store_true', help='just build workspace for combine')
    parser.add_argument('--job_index', default="", type=str)
    parser.add_argument('--minimalModel',action='store_true')
    parser.add_argument('--noMassScales',action='store_true')
    parser.add_argument('--defaultPOI',action='store_true')
    parser.add_argument('--skipTemplatePlots',action='store_true')
    parser.add_argument('--customCombineWrapper',action='store_true')
    parser.add_argument('--noNuisances',action='store_true')
    parser.add_argument('--JMRparameter',action='store_true')
    parser.add_argument('--pTdependetJMRParameter', action='store_true')
    parser.add_argument('--noNormUnc',action='store_true')
    parser.add_argument('--skipExtArgRender',action='store_true')
    parser.add_argument('--seed',type=str,default='42')
    parser.add_argument('--method',type=str,default='diagnostics')
    parser.add_argument('--combineOptions',type=str,help="string with additional cli-options passed to combine",default="")
    parser.add_argument('--verbose',type=int,default=-1)
    parser.add_argument('--unfolding',action='store_true')
    parser.add_argument('--one-bin',action='store_true')
    
    
    args = parser.parse_args()
    
    try:
        if args.config.endswith(".json"):
            configs = json.load(open(args.config))
        else:
            execfile(args.config)
        existing_config = configs['ModelName']+'/config.json'
        if(os.path.isfile(existing_config)):
            use_existing_config = (raw_input("There already is a directory corresponding to this config. Do you want to load the existing config? [Y/N]").lower() == "y")
            if(use_existing_config):
                configs = json.load(open(existing_config))
        
    except IndexError:
        print("You must specify a configuration JSON!")
        sys.exit(0)

    configs['ModelName'] = configs['ModelName']+str(args.job_index)

    args.TTbarTaggingEff = configs.get("TTbarTaggingEff","True") == "True"
    args.pTdependetMassScale = configs.get("pTdependentMassScale","True") == "True"
    args.separateMassScales = configs.get("separateMassScales","False") == "True"
    args.VaryOnlySignal = configs.get("VaryOnlySignal","False") == "True"
    
    if(not args.justplots):
        jet_mass_producer(args,configs)
        open(configs['ModelName']+'/config.json','w').write(json.dumps(configs,sort_keys=False,indent=2))
        use_r_poi = (args.defaultPOI or args.noMassScales) and (not args.unfolding)
        if not args.customCombineWrapper:
            if(args.unfolding):
                cw = CombineWorkflows()
                cw.workspace = configs['ModelName']+'/model_combined.root'
                cw.method = 'unfolding'
                cw.write_wrapper()
            else:
                _,mass_scale_names = build_mass_scale_variations(configs,args)
                cw = CombineWorkflows()
                # cw.workspace = configs['ModelName']+'/'+configs['ModelName']+'_combined.root'
                cw.workspace = configs['ModelName']+'/model_combined.root'
                cw.extraOptions = "--freezeParameters r --preFitValue 0 " + args.combineOptions
                cw.POIRange = (-100,100)
                cw.POI = "r" if use_r_poi else mass_scale_names
                cw.method = args.method
                cw.write_wrapper()
                cw.method = 'FastScanMassScales'
                cw.write_wrapper(append=True)
        else:
            if(not os.path.isfile(configs['ModelName']+'/wrapper.sh')):
                import warnings
                warnings.warn("\033[93mYou used the option --CustomCombineWrapper, but no wrapper can be found in the modeldir!\033[0m",RuntimeWarning)
            #write_wrapper([configs['ModelName']],"r" if use_r_poi else mass_scale_names,additional_options=args.combineOptions,combineWorkflow=args.combineWorkflow)
        if(args.build):
            exit(0)     
        # from runFit import runFits        
        # runFits([configs['ModelName']])
        # exedir = os.getcwd()
        os.system("bash "+configs['ModelName']+"/wrapper.sh")
        # os.system("cd "+exedir)

    if(args.customCombineWrapper):
        exit(0)
        
    do_postfit = True
    try:
        fit_diagnostics = ROOT.TFile(configs['ModelName']+'/fitDiagnostics.root',"READ")
        fit_result = fit_diagnostics.Get("fit_s")

        fit_result_parameters = {}
        for p in fit_result.floatParsFinal():
            fit_result_parameters[p.GetName()]=[p.getVal(),p.getErrorHi(),p.getErrorLo()]
        open(configs['ModelName']+"/"+configs['ModelName']+'fitResult.json','w').write(json.dumps(fit_result_parameters,sort_keys=True,indent=2))
        
        if(not args.unfolding):
            massScales = []
            fitargs = fit_diagnostics.Get("fit_s").floatParsFinal()
            for name in build_mass_scale_variations(configs, args)[1]:
                param = fitargs.find(name)
                center = param.getValV()
                error_up = abs(param.getErrorHi())
                error_down = abs(param.getErrorLo())
            
                massScales.append([center,error_up,-error_down])
            np.save(configs['ModelName']+"/"+configs['ModelName']+'MassScales.npy',np.array(massScales,dtype=float))
        
        do_postfit = fit_result.status() <= 3
    except:
        print("fit failed. only plotting prefit distributions from fitDiangnostics (beware weird shape uncertainties)")
        
        do_postfit = False
    if(not args.skipTemplatePlots):
        fitplotter.plot_fit_result(configs,plot_total_sig_bkg = False,do_postfit=do_postfit, use_config_samples=args.unfolding)
        fitplotter.plot_fit_result(configs,logY=True,plot_total_sig_bkg = False,do_postfit=do_postfit, use_config_samples=args.unfolding)
    if(do_postfit and not args.noMassScales and not args.unfolding):
        fitplotter.plot_mass_scale_nuisances(configs)
    
    qcd_estimation_channels = {k:v for k,v in configs['channels'].items() if "QcdEstimation" in v and v["QcdEstimation"]=="True"}
    if(len(qcd_estimation_channels)>0 and do_postfit):
        fitplotter.plot_qcd_bernstein(configs,do_3d_plot = False)
        if(configs.get('QCDFailConstant','False') == 'False'):
            fitplotter.plot_qcd_fail_parameters(configs)
