Hand-calc-matching reference (rigid leg halves on the knee axis, bladder bonded) - saved 16 Nov 2026 ~04:00
Model: core model (decisions D-A10-CORE / FILL13 / SKIP): two rigid halves hinged on the knee axis (X 4.0573, Y 0), bladder floor and
cover flange bonded for |y| >= 25 mm, fold band |y| < 25 mm (bladder wall 1 % axial E, flange cut), rigid support under the floor.
Moment = knee moment about the knee centre from the shank-half reactions; device moment = run - vented (0 kPa) at the same angle.
Hand calc: M = p k, k = 206 990 mm3 (M1-M7 v12 E.3) = 0.20699 N m per kPa.

handcalc_reference_points.csv / Images\v3_B0\handcalc_reference_points.png = every converged pressurised point (24):
  cycles (fill from heel strike) B0C_PROJ to 14 % stance, B0C_P20 (first attempt) to 9 %; fixed angle CHK_CORE 5.78 deg / 20 kPa.
  FEA / hand calc = 0.6-0.8 in hyperextension (-1.9..0 deg), 0.9-1.05 at 0.2-2.6 deg, 1.11-1.18 at 3.3-3.9 deg, 1.25 at 5.78 deg.
  Above hand calc at larger angles: the FEA bladder is a mid-surface shell inflated to the cover (larger section than the inner
  cavity of the hand calc, about +7..+16 % in k) and the fold band bulges.
Not converged (error log E-64..E-71): every attempt above ~13-15 kPa at 3-4.5 deg and above 20 kPa (fold band balloons along the
leg - a tension-only wall is not available on shells in this solver); P40 failed at the first fill step; P60/P80/P100 cycles
skipped; angle cases 3 and 7.28 deg failed at 20 kPa; 8.63-19 deg not run (queue stopped); rigid-sleeve variant stiffer, failed.
cycle_moment.csv / cycle_summary.csv / margin_moment.csv = collector output (cycle_a10.py --tag v3_B0) incl. the not-converged rows.
