from Hpluscharm.workflows import workflows as hplusc_wf

cfg = {
    "dataset": {
        "jsons": [
            "src/Hpluscharm/input_json/UL16_preVFP.json",
            "src/Hpluscharm/input_json/signal_UL16pre_off.json",
        ],
        "campaign": "2016preVFP_UL",
        "year": "2016",
        # "filter": {
        #     "samples": [
        #         "HPlusCharm_4FS_MuRFScaleDynX0p50_HToWWTo2L2Nu_M125_TuneCP5_13TeV-amcatnloFXFX-pythia8"]}
    },
    # Input and output files
    "workflow": hplusc_wf["HWWtest"],
    "output": "MC_fixHLT_preVFP_UL16",
    "run_options": {
        "executor": "parsl/condor/naf_lite",
        # "executor":"futures",
        # "executor":"iterative",
        "workers": 2,
        "scaleout": 500,
        "walltime": "03:00:00",
        "mem_per_worker": 2,  # GB
        "chunk": 150000,
        "skipbadfiles": True,
        "retries": 40,
        "index": "10,0,11,1",
        "sample_size": 150,
        # "limit":1,
        # "max":1,
        # "index":"0,0",
        #     "voms": None,
        "splitjobs": False,
    },
    ## selections
    "categories": {"cats": [], "cats2": []},
    "preselections": {
        "mu1hlt": ["IsoMu27"],
        "mu2hlt": [
            "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8",
            "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8",
        ],
        "e1hlt": ["Ele35_WPTight_Gsf"],
        "e2hlt": ["Ele23_Ele12_CaloIdL_TrackIdL_IsoVL"],
        "emuhlt": [
            "Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL",
            "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL",
            "Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL",
            "Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ",
            "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
        ],
    },
    ## weights
    "weights": {
        "common": {
            "inclusive": {
                "lumiMask": "Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt",
                "PU": None,
                "roccor": None,
                "JME": "jec_compiled.pkl.gz",
                "BTV": {"deepJet": "shape"},
                "LSF": {
                    "ele_ID 2016preVFP": "wp90iso",
                    "ele_Reco 2016preVFP": "RecoAbove20",
                    "ele_Reco_low 2016preVFP": "RecoBelow20",
                    "mu_Reco 2016preVFP_UL": "NUM_TrackerMuons_DEN_genTracks",
                    "mu_ID 2016preVFP_UL": "NUM_TightID_DEN_TrackerMuons",
                    "mu_Iso 2016preVFP_UL": "NUM_TightRelIso_DEN_TightIDandIPCut",
                    "mu_ID_low NUM_TightID_DEN_TrackerMuons": "Efficiency_muon_trackerMuon_Run2016preVFP_UL_ID.histo.json",
                    "mu_Reco_low NUM_TrackerMuons_DEN_genTracks": "Efficiency_muon_generalTracks_Run2016preVFP_UL_trackerMuon.histo.json",
                },
            },
        },
    },
    "systematic": {
        "JERC": "split",
        "weights": True,
    },
    ## user specific
    "userconfig": {
        "export_array": False,
        "BDT": {
            "json": "src/Hpluscharm/MVA/xgb_output/None_binary_LM_nsv_UL17_nofocal.json",
            "binning": {
                "SR2_LM": [
                    0.0,
                    0.023,
                    0.045,
                    0.068,
                    0.09,
                    0.113,
                    0.135,
                    0.158,
                    0.18,
                    0.202,
                    0.225,
                    0.248,
                    0.27,
                    0.293,
                    0.315,
                    0.338,
                    0.36,
                    0.383,
                    0.405,
                    0.428,
                    0.45,
                    0.473,
                    0.495,
                    0.518,
                    0.54,
                    0.563,
                    0.585,
                    0.608,
                    0.63,
                    0.653,
                    0.675,
                    0.698,
                    0.72,
                    0.742,
                    0.765,
                    0.788,
                    0.81,
                    0.833,
                    0.855,
                    0.878,
                    0.9,
                    0.923,
                    0.945,
                    0.968,
                    0.99,
                    1.0,
                ],
                "SR_LM": [
                    0.0,
                    0.034,
                    0.068,
                    0.101,
                    0.135,
                    0.169,
                    0.203,
                    0.237,
                    0.27,
                    0.304,
                    0.338,
                    0.372,
                    0.406,
                    0.439,
                    0.473,
                    0.507,
                    0.541,
                    0.574,
                    0.608,
                    0.642,
                    0.676,
                    0.71,
                    0.743,
                    0.777,
                    0.811,
                    0.845,
                    0.879,
                    0.912,
                    0.946,
                    0.98,
                    1.0,
                ],
            },
        },
    },
}