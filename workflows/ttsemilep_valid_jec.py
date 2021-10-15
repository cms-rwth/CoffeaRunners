import gzip
import pickle
import coffea
from coffea import hist, processor
import numpy as np
import awkward as ak
from coffea.analysis_tools import Weights
from coffea.lumi_tools import LumiMask
import cloudpickle
import gc

from utils.correction  import *
import inspect
from coffea.jetmet_tools import FactorizedJetCorrector, JetCorrectionUncertainty
from coffea.jetmet_tools import JECStack, CorrectedJetsFactory
from coffea.lookup_tools import extractor

ext = extractor()
ext.add_weight_sets([
    "* * data/Summer19UL17_V5_MC_L1FastJet_AK4PFchs.jec.txt",
    "* * data/Summer19UL17_V5_MC_L2Relative_AK4PFchs.jec.txt",
    "* * data/Summer19UL17_V5_MC_L3Absolute_AK4PFchs.jec.txt",
    "* * data/Summer19UL17_V5_MC_L2L3Residual_AK4PFchs.jec.txt",
#     "* * data/Summer19UL17_JRV2_MC_SF_AK4PFchs.jersf.txt",
#     "* * data/Summer19UL17_JRV2_MC_PtResolution_AK4PFchs.jr.txt",  
])
# ext.add_weight_sets([
#     "* * data/Fall17_17Nov2017_V32_MC_L1FastJet_AK4PFchs.jec.txt",
#     "* * data/Fall17_17Nov2017_V32_MC_L2Relative_AK4PFchs.jec.txt",
#     "* * data/Fall17_17Nov2017_V32_MC_L3Absolute_AK4PFchs.jec.txt",
#     "* * data/Fall17_17Nov2017_V32_MC_L2L3Residual_AK4PFchs.jec.txt",
#     # "* * data/Fall17_V3b_MC_PtResolution_AK4PFchs.jr.txt",
#     # "* * data/Fall17_V3b_MC_SF_AK4PFchs.jersf.txt",   
# ])
ext.finalize()
jec_stack_names = [
                    "Summer19UL17_V5_MC_L1FastJet_AK4PFchs",
                   "Summer19UL17_V5_MC_L2Relative_AK4PFchs",
                   "Summer19UL17_V5_MC_L3Absolute_AK4PFchs",
                   "Summer19UL17_V5_MC_L2L3Residual_AK4PFchs",
                   ]
evaluator = ext.make_evaluator()
jec_inputs = {name: evaluator[name] for name in jec_stack_names}
jec_stack = JECStack(jec_inputs)
ext_data = extractor()
ext_data.add_weight_sets([
    "* * data/Summer19UL17_RunD_V5_DATA_L1FastJet_AK4PFchs.jec.txt",
    "* * data/Summer19UL17_RunD_V5_DATA_L2Relative_AK4PFchs.jec.txt",
    "* * data/Summer19UL17_RunD_V5_DATA_L3Absolute_AK4PFchs.jec.txt",
    "* * data/Summer19UL17_RunD_V5_DATA_L2L3Residual_AK4PFchs.jec.txt"
    # "* * data/Summer19UL17_JRV2_DATA_PtResolution_AK4PFchs.jr.txt",
    # "* * data/Summer19UL17_JRV2_DATA_SF_AK4PFchs.jersf.txt"
    ])
# ext_data.add_weight_sets([
#     "* * data/Fall17_17Nov2017DE_V32_DATA_L1FastJet_AK4PFchs.jec.txt",
#     "* * data/Fall17_17Nov2017DE_V32_DATA_L2Relative_AK4PFchs.jec.txt",
#     "* * data/Fall17_17Nov2017DE_V32_DATA_L3Absolute_AK4PFchs.jec.txt",
#     "* * data/Fall17_17Nov2017DE_V32_DATA_L2L3Residual_AK4PFchs.jec.txt"
#     ])

ext_data.finalize()
jec_datastack_names = [
    "Summer19UL17_RunD_V5_DATA_L1FastJet_AK4PFchs",
    "Summer19UL17_RunD_V5_DATA_L2Relative_AK4PFchs",
    "Summer19UL17_RunD_V5_DATA_L3Absolute_AK4PFchs",
    "Summer19UL17_RunD_V5_DATA_L2L3Residual_AK4PFchs"
    ]
evaluator_data = ext_data.make_evaluator()
jec_inputs_data = {name: evaluator_data[name] for name in jec_datastack_names}
jec_stack_data = JECStack(jec_inputs_data)


# print(dir(evaluator))
name_map = jec_stack.blank_name_map
name_map['JetPt'] = 'pt'
name_map['JetMass'] = 'mass'
name_map['JetEta'] = 'eta'
name_map['JetA'] = 'area'
name_mapd = jec_stack_data.blank_name_map
name_mapd['JetPt'] = 'pt'
name_mapd['JetMass'] = 'mass'
name_mapd['JetEta'] = 'eta'
name_mapd['JetA'] = 'area'

def update(events, collections):
    """Return a shallow copy of events array with some collections swapped out"""
    out = events
    for name, value in collections.items():
        out = ak.with_field(out, value, name)
    return out

class NanoProcessor(processor.ProcessorABC):
    # Define histograms
    def __init__(self):        
        # Define axes
        # Should read axes from NanoAOD config
        dataset_axis = hist.Cat("dataset", "Primary dataset")
        flav_axis = hist.Bin("flav", r"Genflavour",[0,1,4,5,6])
        cutflow_axis   = hist.Cat("cut",   "Cut")

        # Events
        nmu_axis   = hist.Bin("nmu",   r"N muons",     [0,1,2,3,4,5,6,7,8,9,10])
        njet_axis  = hist.Bin("njet",  r"N jets",      [0,1,2,3,4,5,6,7,8,9,10])
        nbjet_axis = hist.Bin("nbjet", r"N b-jets",    [0,1,2,3,4,5,6,7,8,9,10])       
        lmupt_axis   = hist.Bin("lmupt",   r"Muon pt", 45, 20, 200)
        met_axis = hist.Bin("met",   r"Missing ET", 50, 0, 500)


        # Jet
        jet_pt_axis   = hist.Bin("pt",   r"Jet $p_{T}$ [GeV]", 100, 20, 400)
        jet_rawpt_axis   = hist.Bin("rawpt",   r"Jet $p_{T}$ [GeV]", 100, 20, 400)
        jet_rawfactor_axis = hist.Bin("rawfactor", r"raw factor", 50,0,10)

        jet_eta_axis  = hist.Bin("eta",  r"Jet $\eta$", 60, -3, 3)
        jet_phi_axis  = hist.Bin("phi",  r"Jet $\phi$", 60, -3, 3)
        jet_mass_axis = hist.Bin("mass", r"Jet $m$ [GeV]", 100, 0, 50)
        jet_dr_axis = hist.Bin("dr", r"Jet $\Delta$R(l,j)", 50, 0, 5)
        ljpt_axis     = hist.Bin("ljpt", r"Leading jet $p_{T}$ [GeV]", 100, 20, 400)
        sljpt_axis     = hist.Bin("sljpt", r"Subleading jet $p_{T}$ [GeV]", 100, 20, 400)        
        ssljpt_axis     = hist.Bin("ssljpt", r"3rd jet $p_{T}$ [GeV]", 100, 20, 400)
        sssljpt_axis     = hist.Bin("sssljpt", r"4th jet $p_{T}$ [GeV]", 100, 20, 400) 
        ljrawpt_axis     = hist.Bin("ljrawpt", r"Leading jet $p_{T}$ [GeV]", 100, 20, 400)
        sljrawpt_axis     = hist.Bin("sljrawpt", r"Subleading jet $p_{T}$ [GeV]", 100, 20, 400)        
        ssljrawpt_axis     = hist.Bin("ssljrawpt", r"3rd jet $p_{T}$ [GeV]", 100, 20, 400)
        sssljrawpt_axis     = hist.Bin("sssljrawpt", r"4th jet $p_{T}$ [GeV]", 100, 20, 400) 
        ljdr_axis = hist.Bin("ljdr", "Leading jet $\Delta$R(l,j)", 50,0,5)
        sljdr_axis = hist.Bin("sljdr", "Subleading jet $\Delta$R(l,j)", 50,0,5)
        ssljdr_axis = hist.Bin("ssljdr", "3rd jet $\Delta$R(l,j)", 50,0,5)
        sssljdr_axis = hist.Bin("sssljdr", "4th jet $\Delta$R(l,j)", 50,0,5)

        # Define similar axes dynamically
        disc_list = ["btagCMVA", "btagCSVV2", 'btagDeepB', 'btagDeepC', 'btagDeepFlavB', 'btagDeepFlavC', 'deepcsv_CvB', 'deepcsv_CvL','deepflav_CvB','deepflav_CvL']
        ddx_list = ["btagDDBvLV2","btagDDCvBV2","btagDDCvLV2"]
        btag_axes = []
        for d in disc_list:
            btag_axes.append(hist.Bin(d, d, 50, 0, 1))     
           
        deepddx_list = ["DDX_jetNTracks","DDX_jetNSecondaryVertices","DDX_tau1_trackEtaRel_0","DDX_tau1_trackEtaRel_1","DDX_tau1_trackEtaRel_2","DDX_tau2_trackEtaRel_0","DDX_tau2_trackEtaRel_1","DDX_tau2_trackEtaRel_3","DDX_tau1_flightDistance2dSig","DDX_tau2_flightDistance2dSig","DDX_tau1_vertexDeltaR","DDX_tau1_vertexEnergyRatio","DDX_tau2_vertexEnergyRatio","DDX_tau1_vertexMass","DDX_tau2_vertexMass","DDX_trackSip2dSigAboveBottom_0","DDX_trackSip2dSigAboveBottom_1","DDX_trackSip2dSigAboveCharm","DDX_trackSip3dSig_0","DDX_tau1_trackSip3dSig_0","DDX_tau1_trackSip3dSig_1","DDX_trackSip3dSig_1","DDX_tau2_trackSip3dSig_0","DDX_tau2_trackSip3dSig_1"]
        deepcsv_list = [
        "DeepCSV_trackDecayLenVal_0", "DeepCSV_trackDecayLenVal_1", "DeepCSV_trackDecayLenVal_2", "DeepCSV_trackDecayLenVal_3", "DeepCSV_trackDecayLenVal_4", "DeepCSV_trackDecayLenVal_5", 
        "DeepCSV_trackDeltaR_0", "DeepCSV_trackDeltaR_1", "DeepCSV_trackDeltaR_2", "DeepCSV_trackDeltaR_3", "DeepCSV_trackDeltaR_4", "DeepCSV_trackDeltaR_5",
        "DeepCSV_trackEtaRel_0","DeepCSV_trackEtaRel_1","DeepCSV_trackEtaRel_2","DeepCSV_trackEtaRel_3", 	
        "DeepCSV_trackJetDistVal_0","DeepCSV_trackJetDistVal_1","DeepCSV_trackJetDistVal_2","DeepCSV_trackJetDistVal_3","DeepCSV_trackJetDistVal_4","DeepCSV_trackJetDistVal_5", 
        "DeepCSV_trackPtRatio_0","DeepCSV_trackPtRatio_1","DeepCSV_trackPtRatio_2","DeepCSV_trackPtRatio_3","DeepCSV_trackPtRatio_4","DeepCSV_trackPtRatio_5", 
        "DeepCSV_trackPtRel_0", "DeepCSV_trackPtRel_1","DeepCSV_trackPtRel_2","DeepCSV_trackPtRel_3","DeepCSV_trackPtRel_4","DeepCSV_trackPtRel_5",
        "DeepCSV_trackSip3dSig_0","DeepCSV_trackSip3dSig_1","DeepCSV_trackSip3dSig_2","DeepCSV_trackSip3dSig_3","DeepCSV_trackSip3dSig_4","DeepCSV_trackSip3dSig_5",
        "DeepCSV_trackSip2dSig_0","DeepCSV_trackSip2dSig_1","DeepCSV_trackSip2dSig_2","DeepCSV_trackSip2dSig_3","DeepCSV_trackSip2dSig_4","DeepCSV_trackSip2dSig_5",
        "DeepCSV_trackSip2dValAboveCharm","DeepCSV_trackSip2dSigAboveCharm","DeepCSV_trackSip3dValAboveCharm","DeepCSV_trackSip3dSigAboveCharm",
        "DeepCSV_vertexCategory","DeepCSV_vertexEnergyRatio", "DeepCSV_vertexJetDeltaR","DeepCSV_vertexMass", 
        "DeepCSV_flightDistance2dVal","DeepCSV_flightDistance2dSig","DeepCSV_flightDistance3dVal","DeepCSV_flightDistance3dSig","DeepCSV_trackJetPt", 
        "DeepCSV_jetNSecondaryVertices","DeepCSV_jetNSelectedTracks","DeepCSV_jetNTracksEtaRel","DeepCSV_trackSumJetEtRatio","DeepCSV_trackSumJetDeltaR","DeepCSV_vertexNTracks"]
    
        deepcsv_axes = []
        for d in deepcsv_list:
            if "flightDistance2dSig" in d or "flightDistance3dSig" in d :
                deepcsv_axes.append(hist.Bin(d, d, 101, -0.1, 100))
            elif "flightDistance2dVal" in d :
                deepcsv_axes.append(hist.Bin(d, d, 27, -0.1, 2.6))
            elif "flightDistance3dVal" in d :
                deepcsv_axes.append(hist.Bin(d, d, 51, -0.1, 5.))
            elif "trackDecayLenVal" in d :
                deepcsv_axes.append(hist.Bin(d, d, 22, -0.1, 1.))
            elif "trackPtRatio" in d or "DeltaR" in d:
                deepcsv_axes.append(hist.Bin(d, d, 30, -0.001, 0.301))
            elif "trackEtaRel" in d:
                deepcsv_axes.append(hist.Bin(d, d, 30, 0, 9))
            elif "trackJetDistVal" in d :
                deepcsv_axes.append(hist.Bin(d, d, 35, -0.08,0.0025))
            elif "trackJetPt" in d : 
                deepcsv_axes.append(hist.Bin(d, d, 50, 0.,250.))
            elif "trackPtRel" in d:
                deepcsv_axes.append(hist.Bin(d, d, 32, -0.1, 3.1))
            elif "trackSip2dSigAboveCharm" in d:
                deepcsv_axes.append(hist.Bin(d, d, 22, -5.5, 5.5))
            elif "trackSip2dSig_0" in d:
                deepcsv_axes.append(hist.Bin(d, d, 21, -5, 16))
            elif "trackSip2dSig_1" in d:
                deepcsv_axes.append(hist.Bin(d, d, 18, -5, 13))
            elif "trackSip2dSig_2" in d:
                deepcsv_axes.append(hist.Bin(d, d, 16, -6, 10))
            elif "trackSip2dSig_3" in d:
                deepcsv_axes.append(hist.Bin(d, d, 26, -6, 7))
            elif "trackSip2dSig_4" in d:
                deepcsv_axes.append(hist.Bin(d, d, 22, -6.5, 4.5))
            elif "trackSip2dSig_5" in d:
                deepcsv_axes.append(hist.Bin(d, d, 18, -7, 2))
            elif "trackSip2dValAboveCharm" in d or "trackSip3dValAboveCharm " in d:
                deepcsv_axes.append(hist.Bin(d, d, 24, -0.06, 0.06))
            elif "trackSip3dSigAboveCharm" in d :
                deepcsv_axes.append(hist.Bin(d, d, 26, -6.5, 6.5)) 
            elif "trackSip3dSig" in d : 
                deepcsv_axes.append(hist.Bin(d, d, 25, -25, 50)) 
            elif "trackSumJetEtRatio" in d:
                deepcsv_axes.append(hist.Bin(d, d, 25, 0., 1.4)) 
            elif "vertexCategory" in d:
                deepcsv_axes.append(hist.Bin(d, d, 32, -0.6,2.6)) 
            elif "vertexEnergyRatio" in d:
                deepcsv_axes.append(hist.Bin(d, d, 25, 0,2.5)) 
            elif "vertexMass" in d:
                deepcsv_axes.append(hist.Bin(d, d, 20, 0,20))
            else:
                deepcsv_axes.append(hist.Bin(d, d, 25, -0.5,0.))
        
        
        # Define histograms from axes
        _hist_jet_dict = {
                'pt'  : hist.Hist("Counts", dataset_axis, flav_axis,jet_pt_axis),
                'rawpt'  : hist.Hist("Counts", dataset_axis, flav_axis,jet_rawpt_axis),
                'eta' : hist.Hist("Counts", dataset_axis, flav_axis,jet_eta_axis),
                'phi' : hist.Hist("Counts", dataset_axis, flav_axis,jet_phi_axis),
                'mass': hist.Hist("Counts", dataset_axis, flav_axis,jet_mass_axis),
                # 'dr': hist.Hist("Counts", dataset_axis, flav_axis,jet_dr_axis)
            }
        _hist_deepcsv_dict = {
                'pt'  : hist.Hist("Counts", dataset_axis, flav_axis,jet_pt_axis),
                'eta' : hist.Hist("Counts", dataset_axis, flav_axis,jet_eta_axis),
                'phi' : hist.Hist("Counts", dataset_axis, flav_axis,jet_phi_axis),
                'mass': hist.Hist("Counts", dataset_axis, flav_axis,jet_mass_axis),
                'rawpt'  : hist.Hist("Counts", dataset_axis, flav_axis, jet_rawpt_axis),
                # 'rawfactor': hist.Hist("Counts",dataset_axis, flav_axis, jet_rawfactor_axis)
            }
        
       
        # Generate some histograms dynamically
        for disc, axis in zip(disc_list, btag_axes):
            _hist_deepcsv_dict[disc] = hist.Hist("Counts", dataset_axis, flav_axis, axis)
        for deepcsv, axises in zip(deepcsv_list, deepcsv_axes):
             _hist_deepcsv_dict[deepcsv] = hist.Hist("Counts", dataset_axis,flav_axis,  axises)
        _hist_event_dict = {
                'njet'  : hist.Hist("Counts", dataset_axis,  njet_axis),
                'nbjet' : hist.Hist("Counts", dataset_axis,  nbjet_axis),
                'nmu'   : hist.Hist("Counts", dataset_axis,  nmu_axis),
                'lmupt' : hist.Hist("Counts", dataset_axis,  lmupt_axis),
                'ljpt'  : hist.Hist("Counts", dataset_axis, flav_axis, ljpt_axis),
                'sljpt'  : hist.Hist("Counts", dataset_axis, flav_axis, sljpt_axis),
                'ssljpt'  : hist.Hist("Counts", dataset_axis, flav_axis, ssljpt_axis),
                'sssljpt'  : hist.Hist("Counts", dataset_axis, flav_axis, sssljpt_axis),
                'ljrawpt'  : hist.Hist("Counts", dataset_axis, flav_axis, ljrawpt_axis),
                'sljrawpt'  : hist.Hist("Counts", dataset_axis, flav_axis, sljrawpt_axis),
                'ssljrawpt'  : hist.Hist("Counts", dataset_axis, flav_axis, ssljrawpt_axis),
                'sssljrawpt'  : hist.Hist("Counts", dataset_axis, flav_axis, sssljrawpt_axis),
                'ljdr'  : hist.Hist("Counts", dataset_axis, flav_axis, ljdr_axis),
                'sljdr'  : hist.Hist("Counts", dataset_axis, flav_axis, sljdr_axis),
                'ssljdr'  : hist.Hist("Counts", dataset_axis, flav_axis, ssljdr_axis),
                'sssljdr'  : hist.Hist("Counts", dataset_axis, flav_axis, sssljdr_axis),
                'met' : hist.Hist("Counts", dataset_axis, met_axis)
            }
        self.jet_hists = list(_hist_jet_dict.keys())
        self.deepcsv_hists = list(_hist_deepcsv_dict.keys())
        self.event_hists = list(_hist_event_dict.keys())
        _hist_dict = {**_hist_deepcsv_dict,**_hist_event_dict}
        self._accumulator = processor.dict_accumulator(_hist_dict)
        self._accumulator['sumw'] = processor.defaultdict_accumulator(float)
        print("----------pre--------")
        


    @property
    
    def accumulator(self):
        # objgraph.show_growth()
        print("----------accumulator--------")
        return self._accumulator
    
    def process(self, events):

        print("======>process_shift<======")
        objgraph.show_growth()
        output = self.accumulator.identity()
        # print(output.items())
        dataset = events.metadata['dataset']
        isRealData = not hasattr(events, "genWeight")
        
        if(isRealData):output['sumw'][dataset] += 1.
        else:output['sumw'][dataset] += ak.sum(events.genWeight)
        req_lumi=np.ones(len(events), dtype='bool')
        if(isRealData): req_lumi=lumiMasks['2017'](events.run, events.luminosityBlock)
        weights = Weights(len(events), storeIndividual=True)
        if not isRealData:
            weights.add('genweight',events.genWeight)
            weights.add('puweight', compiled['2017_pileupweight'](events.Pileup.nPU))
        ##############
        # Trigger level
        triggers = [
        "HLT_IsoMu24",
        ]
        
        trig_arrs = [events.HLT[_trig.strip("HLT_")] for _trig in triggers]
        req_trig = np.zeros(len(events), dtype='bool')
        for t in trig_arrs:
            req_trig = req_trig | t
        
        ############
        # Event level
        
        ## Muon cuts
        # muon twiki: https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideMuonIdRun2
        events.Muon = events.Muon[(events.Muon.pt > 30) & (abs(events.Muon.eta) < 2.4) & (events.Muon.tightId > .5)&(events.Muon.pfRelIso04_all<0.12)] #
        
        # print(ak.all(events.Jet.metric_table(events.Muon) > 0.4, axis=2))
        event_muon = ak.pad_none(events.Muon, 1, axis=1) 
        
        req_muon =(ak.count(event_muon.pt, axis=1) == 1)
        ## Jet cuts 

        jets = events.Jet
        
        jets['pt_raw'] = (1 - jets['rawFactor']) * jets['pt']
        jets['mass_raw'] = (1 - jets['rawFactor']) * jets['mass']
        if not isRealData:jets['pt_gen'] = ak.values_astype(ak.fill_none(jets.matched_gen.pt, 0), np.float32)
        jets['rho'] = ak.broadcast_arrays(events.fixedGridRhoFastjetAll, jets.pt)[0]
        if not isRealData:
            name_map['ptGenJet'] = 'pt_gen'
            name_map['ptRaw'] = 'pt_raw'
            name_map['massRaw'] = 'mass_raw'
            name_map['Rho'] = 'rho'
            events_cache = events.caches[0]
            jet_factory = CorrectedJetsFactory(name_map, jec_stack)
            corrected_jets = jet_factory.build(jets, lazy_cache=events_cache)
        else :
            # name_mapd['ptGenJet'] = 'pt_gen'
            name_mapd['ptRaw'] = 'pt_raw'
            name_mapd['massRaw'] = 'mass_raw'
            name_mapd['Rho'] = 'rho'
            events_cache = events.caches[0]
            jet_factory_data = CorrectedJetsFactory(name_mapd, jec_stack_data)
            corrected_jets = jet_factory_data.build(jets, lazy_cache=events_cache)
        event_jet = corrected_jets[(corrected_jets.pt> 25) & (abs(corrected_jets.eta) <= 2.4)&(corrected_jets.puId > 0)&(corrected_jets.jetId > 0)&(ak.all(corrected_jets.metric_table(events.Muon) > 0.4, axis=2))]
        # event_jet = events.Jet[(events.Jet.pt> 25) & (abs(events.Jet.eta) <= 2.4)&(events.Jet.puId > 0)&(events.Jet.jetId > 0)&(ak.all(events.Jet.metric_table(events.Muon) > 0.4, axis=2))]
        req_jets = (ak.num(event_jet)>=4)
        req_MET = events.METFixEE2017.pt>50
        
        event_level = req_trig  & req_jets & req_muon&req_MET &req_lumi
        #event_level = req_trig  & req_jets & req_muon&req_MET
        # Selected
        selev = events[event_level]    
   
        #########
 
        # Per muon
        mu_eta   = (abs(selev.Muon.eta) < 2.4)
        mu_pt    = selev.Muon.pt > 30
        mu_idiso = (selev.Muon.tightId > .5)&(selev.Muon.pfRelIso04_all<0.12)
        mu_level = mu_eta & mu_pt & mu_idiso
        
        smu=selev.Muon[mu_level]
        # Per jet : https://twiki.cern.ch/twiki/bin/viewauth/CMS/PileupJetID
        
        jet_eta    = (abs(corrected_jets[event_level].eta) <= 2.4)
        jet_pt =    corrected_jets[event_level].pt>25
        jet_pu     = (corrected_jets[event_level].puId > 0) &(corrected_jets[event_level].jetId>0)
        jet_dr     = (ak.all(corrected_jets[event_level].metric_table(smu) > 0.4, axis=2))
        # jet_eta    = (abs(selev.Jet.eta) <= 2.4)
        # jet_pt =    selev.Jet.pt>25
        # jet_pu     = (selev.Jet.puId > 0) &(selev.Jet.jetId>0)
        # jet_dr     = (ak.all(selev.Jet.metric_table(smu) > 0.4, axis=2))

        
        jet_level  = jet_pu & jet_eta & jet_pt & jet_dr
        
        # b-tag twiki : https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X
        # bjet_disc  =corrected_jets[event_level].btagDeepB > 0.7264 # L=0.0494, M=0.2770, T=0.7264
        # bjet_level = jet_level & bjet_disc
        
        
        # sjets  = corrected_jets[event_level]
        sjets = events.Jet[event_level]
        # sjets = selev.correct_jets[jet_level]
        # sbjets = corrected_jets[event_level&corrected_jets[event_level].btagDeepB > 0.7264]
        
        if isRealData :
            genflavor = ak.zeros_like(sjets.pt)
        else:
            par_flav = (sjets.partonFlavour == 0 ) & (sjets.hadronFlavour==0)
            genflavor = sjets.hadronFlavour + 1*par_flav 
            
                
        gc.collect()
        print("======>return output<======")
        
        del jets
        del event_jet    
        # del corrected_jets
        del events_cache
        # Fill histograms dynamically  
        for histname, h in output.items():
            if histname in self.deepcsv_hists:
                if(isRealData):
                    if histname == 'rawpt':
                        h.fill(dataset=dataset,flav=5, rawpt =ak.flatten(events.Jet[event_level].pt))
                    elif 'btagDeep' in histname or 'CvL' in histname or 'CvB' in histname:
                         output['btagDeepFlavB'].fill(dataset=dataset,flav=5,  btagDeepFlavB=ak.flatten(sjets.btagDeepFlavB))
                         output['btagDeepFlavC'].fill(dataset=dataset,flav=5,  btagDeepFlavC=ak.flatten(sjets.btagDeepFlavC)) 
                         output['btagDeepB'].fill(dataset=dataset,flav=5,  btagDeepB=ak.flatten(sjets.btagDeepB))
                         output['btagDeepC'].fill(dataset=dataset,flav=5,  btagDeepC=ak.flatten(sjets.btagDeepC))
                         output['deepcsv_CvB'].fill(dataset=dataset,flav=5,  deepcsv_CvB=ak.flatten(sjets.btagDeepC/(1.-sjets.btagDeepB)))
                         output['deepcsv_CvL'].fill(dataset=dataset,flav=5,  deepcsv_CvL=ak.flatten(sjets.btagDeepC/(sjets.btagDeepC+sjets.btagDeepB)))
                         output['deepflav_CvB'].fill(dataset=dataset,flav=5,  deepflav_CvB=ak.flatten(sjets.btagDeepFlavC/(1.-sjets.btagDeepFlavB)))
                         output['deepflav_CvL'].fill(dataset=dataset,flav=5,  deepflav_CvL=ak.flatten(sjets.btagDeepFlavC/(sjets.btagDeepFlavC+sjets.btagDeepFlavB)))

                    else:
                        fields = {l: ak.flatten(sjets[l.replace('jet_','')], axis=None) for l in h.fields if l.replace('jet_','') in dir(corrected_jets[event_level])}
                        h.fill(dataset=dataset,flav=5, **fields)
                else:
                    genweiev=ak.flatten(ak.broadcast_arrays(weights.weight()[event_level],sjets['pt'])[0])
                    if histname == 'rawpt' :
                        
                        h.fill(dataset=dataset,flav=ak.flatten(genflavor), rawpt =ak.flatten(sjets.pt*(1-sjets.rawFactor)) ,weight=genweiev)
                    elif 'btagDeep' in histname or 'CvL' in histname or 'CvB' in histname:
                         output['btagDeepFlavB'].fill(dataset=dataset,flav=ak.flatten(genflavor),  btagDeepFlavB=ak.flatten(sjets.btagDeepFlavB),weight=genweiev)
                         output['btagDeepFlavC'].fill(dataset=dataset,flav=ak.flatten(genflavor),  btagDeepFlavC=ak.flatten(sjets.btagDeepFlavC),weight=genweiev) 
                         output['btagDeepB'].fill(dataset=dataset,flav=ak.flatten(genflavor),  btagDeepB=ak.flatten(sjets.btagDeepB),weight=genweiev)
                         output['btagDeepC'].fill(dataset=dataset,flav=ak.flatten(genflavor),  btagDeepC=ak.flatten(sjets.btagDeepC),weight=genweiev)
                         output['deepcsv_CvB'].fill(dataset=dataset,flav=ak.flatten(genflavor),  deepcsv_CvB=ak.flatten(sjets.btagDeepC/(1.-sjets.btagDeepB)),weight=genweiev)
                         output['deepcsv_CvL'].fill(dataset=dataset,flav=ak.flatten(genflavor),  deepcsv_CvL=ak.flatten(sjets.btagDeepC/(sjets.btagDeepC+sjets.btagDeepB)),weight=genweiev)
                         output['deepflav_CvB'].fill(dataset=dataset,flav=ak.flatten(genflavor),  deepflav_CvB=ak.flatten(sjets.btagDeepFlavC/(1.-sjets.btagDeepFlavB)),weight=genweiev)
                         output['deepflav_CvL'].fill(dataset=dataset,flav=ak.flatten(genflavor),  deepflav_CvL=ak.flatten(sjets.btagDeepFlavC/(sjets.btagDeepFlavC+sjets.btagDeepFlavB)),weight=genweiev)
                    else:
                        fields = {l: ak.flatten(sjets[histname]) for l in h.fields if l in dir(sjets)}
                        genweiev=ak.flatten(ak.broadcast_arrays(weights.weight()[event_level],sjets['pt'])[0])
                        h.fill(dataset=dataset,flav=ak.flatten(genflavor), **fields,weight=genweiev)
            


        def flatten(ar): # flatten awkward into a 1d array to hist
            return ak.flatten(ar, axis=None)

        def num(ar):
            return ak.num(ak.fill_none(ar[~ak.is_none(ar)], 0), axis=0)
        if(isRealData):
            output['njet'].fill(dataset=dataset,  njet=flatten(ak.num(corrected_jets[event_level])))
            output['nmu'].fill(dataset=dataset,   nmu=flatten(ak.num(smu)))
            output['lmupt'].fill(dataset=dataset, lmupt=flatten((smu.pt)))
            output['ljpt'].fill(dataset=dataset, flav=0, ljpt=flatten(sjets[:,0].pt))
            output['sljpt'].fill(dataset=dataset, flav=0, sljpt=flatten(sjets[:,1].pt))
            output['ssljpt'].fill(dataset=dataset, flav=0, ssljpt=flatten(sjets[:,2].pt))
            output['sssljpt'].fill(dataset=dataset, flav=0, sssljpt=flatten(sjets[:,3].pt))
            output['ljrawpt'].fill(dataset=dataset, flav=0, ljrawpt=flatten(sjets[:,0].pt*(1-sjets[:,0].rawFactor)))
            output['sljrawpt'].fill(dataset=dataset, flav=0, sljrawpt=flatten(sjets[:,1].pt*(1-sjets[:,0].rawFactor)))
            output['ssljrawpt'].fill(dataset=dataset, flav=0, ssljrawpt=flatten(sjets[:,2].pt*(1-sjets[:,0].rawFactor)))
            output['sssljrawpt'].fill(dataset=dataset, flav=0, sssljrawpt=flatten(sjets[:,3].pt*(1-sjets[:,0].rawFactor)))
            output['ljdr'].fill(dataset=dataset, flav=0, ljdr=flatten(sjets[:,0].delta_r(smu)))
            output['sljdr'].fill(dataset=dataset, flav=0, sljdr=flatten(sjets[:,1].delta_r(smu)))
            output['ssljdr'].fill(dataset=dataset, flav=0, ssljdr=flatten(sjets[:,2].delta_r(smu)))
            output['sssljdr'].fill(dataset=dataset, flav=0, sssljdr=flatten(sjets[:,3].delta_r(smu)))
            output['met'].fill(dataset=dataset, met=flatten((selev.METFixEE2017.pt)))
        else:
            
                output['njet'].fill(dataset=dataset,  njet=flatten(ak.num(sjets)),weight=weights.weight()[event_level])
                output['nmu'].fill(dataset=dataset,   nmu=flatten(ak.num(smu)),weight=weights.weight()[event_level])
                output['lmupt'].fill(dataset=dataset, lmupt=flatten((smu.pt)),weight=weights.weight()[event_level])
                output['ljpt'].fill(dataset=dataset, flav=flatten(sjets[:,0].hadronFlavour), ljpt=flatten(sjets[:,0].pt),weight=weights.weight()[event_level])
                output['sljpt'].fill(dataset=dataset, flav=flatten(sjets[:,1].hadronFlavour), sljpt=flatten(sjets[:,1].pt),weight=weights.weight()[event_level])
                output['ssljpt'].fill(dataset=dataset, flav=flatten(sjets[:,2].hadronFlavour), ssljpt=flatten(sjets[:,2].pt),weight=weights.weight()[event_level])
                output['sssljpt'].fill(dataset=dataset, flav=flatten(sjets[:,3].hadronFlavour), sssljpt=flatten(sjets[:,3].pt),weight=weights.weight()[event_level])
                output['ljrawpt'].fill(dataset=dataset, flav=flatten(sjets[:,0].hadronFlavour), ljrawpt=flatten(sjets[:,0].pt*(1-sjets[:,0].rawFactor)),weight=weights.weight()[event_level])
                output['sljrawpt'].fill(dataset=dataset, flav=flatten(sjets[:,1].hadronFlavour), sljrawpt=flatten(sjets[:,1].pt*(1-sjets[:,1].rawFactor)),weight=weights.weight()[event_level])
                output['ssljrawpt'].fill(dataset=dataset, flav=flatten(sjets[:,2].hadronFlavour), ssljrawpt=flatten(sjets[:,2].pt*(1-sjets[:,2].rawFactor)),weight=weights.weight()[event_level])
                output['sssljrawpt'].fill(dataset=dataset, flav=flatten(sjets[:,3].hadronFlavour), sssljrawpt=flatten(sjets[:,3].pt*(1-sjets[:,3].rawFactor)),weight=weights.weight()[event_level])
                output['ljdr'].fill(dataset=dataset, flav=flatten(sjets[:,0].hadronFlavour), ljdr=flatten(sjets[:,0].delta_r(smu)),weight=weights.weight()[event_level])
                output['sljdr'].fill(dataset=dataset, flav=flatten(sjets[:,1].hadronFlavour), sljdr=flatten(sjets[:,1].delta_r(smu)),weight=weights.weight()[event_level])
                output['ssljdr'].fill(dataset=dataset, flav=flatten(sjets[:,2].hadronFlavour), ssljdr=flatten(sjets[:,2].delta_r(smu)),weight=weights.weight()[event_level])
                output['sssljdr'].fill(dataset=dataset, flav=flatten(sjets[:,3].hadronFlavour), sssljdr=flatten(sjets[:,3].delta_r(smu)),weight=weights.weight()[event_level])
                output['met'].fill(dataset=dataset, met=flatten((selev.METFixEE2017.pt)),weight=weights.weight()[event_level])
        
        # del events_cache
        # schedule.every(20).minutes.do(dosomething)
        return output
    

    def postprocess(self, accumulator):
        print("----------post--------")
        return accumulator