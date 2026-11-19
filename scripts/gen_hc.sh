#!/bin/bash
# HC = fixed hand-calc-matching idealised reference (16 Nov 2026, D-A10-FIX / STAB / BLEND / ENDISO; error log E-108, E-109, E-112, E-120).
# Same model as the B0 / B0C core decks (rigid halves, bladder + cover, fold band 25 mm) plus:
#   --slstab 1e-4 (slide-line contact stabilisation), --cov_endiso 0.7, --floor_bond (band floor bonded to the smoothly bent leg surface; replaces --sup_blend / --floor_bed).
# Angle cases HC_A<a> (vented flexion, then 20..100 kPa); cycles HCC_P<p> (stance 1-50 %, fill at 13 %).
# Owner 16 Nov 14:30: cycles not yet run (PROJ, 40, 60, 80, 100) rebuilt with --cyc_end 36 (stance 1-36 %); P0 / P20 had already run to 50 %.
# Owner 16 Nov 17:40: stance stride 3 % (--cyc_step 3: frames 3,6,9,12,13,15,18,21,24,27,30,33,36) for P40/60/80/100; HCC_PROJ ran with stride 1 to 36 %.
cd "$(dirname "$0")"
M=../02_Nastran_Model
FIX="--rigid_leg --bond_skin --padE 9.65 --core 25 --slstab 1e-4 --cov_endiso 0.7 --floor_bond --tissue contracted --calib $M/calib_rigid.json --mesh $M/mesh_M0.pkl"
for a in 3.0:3.0 7.3:7.28 8.6:8.63 9.8:9.78 13.0:13.0 16.0:16.0 19.0:19.0; do
  n=HC_A${a%%:*}; th=${a##*:}; mkdir -p $M/$n
  python -P deck_a07.py $FIX --out $M/$n/$n.nas --run $n --seq MULTI --theta $th --plist 20,40,60,80,100 > $M/$n/gen.log 2>&1
  python -P seal_check_a10.py $M/$n/$n.nas $M/$n/${n}_mesh.pkl > /dev/null 2>&1; tail -1 $M/$n/gen.log
done
for p in 0 20 PROJ 40 60 80 100; do
  n=HCC_P$p; [ $p = PROJ ] && n=HCC_PROJ; mkdir -p $M/$n
  E=""; case $p in 0|20) ;; PROJ) E="--cyc_end 36";; *) E="--cyc_end 36 --cyc_step 3";; esac
  python -P deck_a07.py $FIX --out $M/$n/$n.nas --run $n --seq CYCLE --cyc_p $p $E > $M/$n/gen.log 2>&1
  python -P seal_check_a10.py $M/$n/$n.nas $M/$n/${n}_mesh.pkl > /dev/null 2>&1; tail -1 $M/$n/gen.log
done
