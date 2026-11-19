#!/bin/bash
# Rebuild the mesh and the 12 Nastran decks of report v3 (idealised hand-calc reference, 0-60 kPa).
# Verified 19 Nov 2026: the mesh and all 12 decks come out identical to the committed ones (comment lines aside).
# Usage (Git Bash or any bash, from anywhere):  bash scripts/make_decks_v3.sh [--mesh]
#   --mesh  also rebuild 02_Nastran_Model/mesh_M0.pkl from cad_build_code/ (otherwise the committed mesh is used)
set -e
cd "$(dirname "$0")"
M=../02_Nastran_Model
PY=${PY:-python}
if [ "$1" = "--mesh" ]; then
  $PY -P mesh_a07.py --level M0 --out $M --norender
fi
FIX="--rigid_leg --bond_skin --padE 9.65 --core 25 --slstab 1e-4 --cov_endiso 0.7 --floor_bond --tissue contracted --calib $M/calib_rigid.json --mesh $M/mesh_M0.pkl"
deck() {   # deck <run> <deck_a07 options...>
  n=$1; shift; mkdir -p $M/$n
  $PY -P deck_a07.py $FIX --out $M/$n/$n.nas --run $n "$@" > $M/$n/gen.log 2>&1
  $PY -P seal_check_a10.py $M/$n/$n.nas $M/$n/${n}_mesh.pkl > /dev/null 2>&1 || true   # writes <run>_seal_check.txt itself
  tail -1 $M/$n/gen.log
}
# fixed-angle cases: bend vented to the angle, then pressurise (CHK_FB = the 3 deg case; its deck still lists 80 / 100 kPa,
# which were never reached - the run stopped near 70 kPa, E-123 - and are not used)
deck CHK_FB   --seq MULTI --theta 3.0  --plist 20,40,60,80,100
for a in 7.3:7.28 8.6:8.63 9.8:9.78 13.0:13.0 16.0:16.0 19.0:19.0; do
  deck HC_A${a%%:*} --seq MULTI --theta ${a##*:} --plist 20,40,60
done
# gait cycles (Option-2 window 13-36 % stance)
deck HCC_P0   --seq CYCLE --cyc_p 0
deck HCC_P20  --seq CYCLE --cyc_p 20
deck HCC_PROJ --seq CYCLE --cyc_p PROJ --cyc_end 36
deck HCC_P40  --seq CYCLE --cyc_p 40 --cyc_end 36 --cyc_step 3
deck HCC_P60  --seq CYCLE --cyc_p 60 --cyc_end 36 --cyc_step 3
