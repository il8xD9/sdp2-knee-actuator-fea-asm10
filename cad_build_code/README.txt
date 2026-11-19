CAD v8 (12 Nov 2026) - CAD\last v2\last v6. Copies of the last v5 parts; originals unchanged. Owner decisions C1-C6, Q1-Q3.
  geo8.py A150|A100   geometry -> geo_A150.json / geo_A100.json (thigh far strap +150 main / +100 comparison; calf -120;
                      pad -143/+173 or +123; M3 carriers; cover8(): 1 mm gap everywhere, end caps R11, M3 notch 42 x 4.5 R1)
  build8.ps1 -Opt A150|A100 [-Only part.ipt] [-Rebuild] [-CopySame]   build ONE part per run (low RAM); -CopySame copies unchanged parts
  mk_asm8.ps1 -Opt A150|A100   full asseymbly 07 / 08 (grounded), gaps, masses, materials
  chk8.ps1 -file <iam>   pairwise interference;  repoint_b.ps1   route (b) reference asm 06 -> its own folder
  axes8.ps1 -Dir -List -Ucs   anatomical axis names + UCS;  pics8.ps1 -Img <dir>   pictures;  rng.ps1   read-only range/mass
Traps: body tags get a _v8 suffix (names of suppressed source bodies cannot be reused); bands outside the cover range are
skipped in rin_steps; notch entry fillet selects short edges only (max_len); end views need the tangent camera (curved path).
