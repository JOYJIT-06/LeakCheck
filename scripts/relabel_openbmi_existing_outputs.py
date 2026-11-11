"""Relabel historical OpenBMI TS-LR global reference rows and regenerate derived outputs.

No EEG decoding is rerun. The script changes only the design label for the
68 TS-LR fold rows and 34 TS-LR participant rows, recomputes contrasts,
refreshes manifest hashes, and regenerates publication figures.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import pandas as pd
from scripts.run_openbmi_benchmark import compute_design_contrasts

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir",type=Path,default=Path("benchmark_results/openbmi_v2"))
    ap.add_argument("--figures-dir",type=Path,default=Path("figures/openbmi_v2"))
    ap.add_argument("--seed",type=int,default=0)
    a=ap.parse_args()
    foldp=a.results_dir/"fold_metrics.csv"
    partp=a.results_dir/"participant_metrics.csv"
    comp=a.results_dir/"design_comparisons.csv"
    man=a.results_dir/"benchmark_manifest.json"
    for x in (foldp,partp,man):
        if not x.is_file(): raise FileNotFoundError(x)
    fold=pd.read_csv(foldp); part=pd.read_csv(partp)
    fm=(fold.decoder=="ts_lr")&(fold.design=="P1_csp_on_all")
    pm=(part.decoder=="ts_lr")&(part.design=="P1_csp_on_all")
    if int(fm.sum())!=68 or int(pm.sum())!=34:
        raise ValueError(f"Unexpected TS-LR row counts: fold={int(fm.sum())}, participant={int(pm.sum())}; no changes made")
    fold.loc[fm,"design"]="T1_ts_reference_on_all"
    part.loc[pm,"design"]="T1_ts_reference_on_all"
    fold.to_csv(foldp,index=False); part.to_csv(partp,index=False)
    contrasts=compute_design_contrasts(part,seed=a.seed)
    if "T1_ts_reference_vs_D3" not in set(contrasts.contrast):
        raise RuntimeError("T1 contrast missing after relabel")
    contrasts.to_csv(comp,index=False)
    manifest=json.loads(man.read_text(encoding="utf-8"))
    for name,path in (("fold_metrics.csv",foldp),("participant_metrics.csv",partp),("design_comparisons.csv",comp)):
        manifest["output_files"][name]["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        manifest["output_files"][name]["rows"]=len(pd.read_csv(path))
    manifest["postprocessing"]={"operation":"relabel_ts_lr_global_reference_control","script":"scripts/relabel_openbmi_existing_outputs.py","decoding_rerun":False}
    man.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    subprocess.run([sys.executable,"scripts/plot_openbmi_figures.py","--results-dir",str(a.results_dir),"--output-dir",str(a.figures_dir)],check=True)
    print("Relabelled TS-LR as T1; refreshed contrasts, manifest hashes and figures.")
if __name__=="__main__": main()
