// ms_gap_force_3d — stack inside air box (open domain)
// vols: 1 iron_return, 2 pm, 3 airgap, 4 iron_target, 5 air_box(exterior)
SetFactory("OpenCASCADE");
L = 0.08; W = 0.08;
h_fe = 0.010; h_pm = 0.008; g = 0.001;
z1 = h_fe;
z2 = h_fe + h_pm;
z3 = h_fe + h_pm + g;
z4 = h_fe + h_pm + g + h_fe;
// air envelope (pad)
pad = 0.04;
Box(10) = {-pad, -pad, -pad, L+2*pad, W+2*pad, z4+2*pad};
Box(1) = {0, 0, 0, L, W, h_fe};
Box(2) = {0, 0, z1, L, W, h_pm};
Box(3) = {0, 0, z2, L, W, g};
Box(4) = {0, 0, z3, L, W, h_fe};
BooleanFragments{ Volume{10, 1, 2, 3, 4}; Delete; }{}

vols() = Volume{:};
iron_return = {};
pm = {};
airgap = {};
iron_target = {};
air = {};
For i In {0 : #vols()-1}
  v = vols(i);
  bb() = BoundingBox Volume{v};
  // size heuristic: large volume = air envelope remnant
  dx = bb(3)-bb(0); dy = bb(4)-bb(1); dz = bb(5)-bb(2);
  vol = dx*dy*dz;
  zc = 0.5*(bb(2)+bb(5));
  xc = 0.5*(bb(0)+bb(3));
  yc = 0.5*(bb(1)+bb(4));
  inStack = (xc > -1e-9 && xc < L+1e-9 && yc > -1e-9 && yc < W+1e-9);
  If (vol > 0.5*(L+2*pad)*(W+2*pad)*(z4+2*pad)*0.5)
    air += {v};
  ElseIf (inStack && zc < z1)
    iron_return += {v};
  ElseIf (inStack && zc < z2)
    pm += {v};
  ElseIf (inStack && zc < z3)
    airgap += {v};
  ElseIf (inStack && zc < z4 + 1e-9)
    iron_target += {v};
  Else
    air += {v};
  EndIf
EndFor

Physical Volume("iron_return", 1) = iron_return[];
Physical Volume("pm", 2) = pm[];
Physical Volume("airgap", 3) = airgap[];
Physical Volume("iron_target", 4) = iron_target[];
Physical Volume("air", 5) = air[];
Physical Surface("exterior", 1) = CombinedBoundary{ Volume{vols[]}; };
Mesh.CharacteristicLengthMax = 0.008;
Mesh.CharacteristicLengthMin = 0.0004;
