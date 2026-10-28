// ms_gap_force_3d — closed pot-core side-yoke return
// Physical: 1 iron_stator, 2 pm, 3 airgap, 4 iron_target, 5 air
SetFactory("OpenCASCADE");

L = 0.050;
W = 0.050;
cr = 0.00025;
t = 0.014;
h_bot = 0.014;
h_pm = 0.008;
g = 0.001;
h_lid = 0.025;

L_cav = L + 2*cr;
W_cav = W + 2*cr;
L_out = L_cav + 2*t;
W_out = W_cav + 2*t;
ox = t + cr;
oy = t + cr;
h_wall = h_pm + g + h_lid;
z_pm = h_bot;
z_gap = h_bot + h_pm;
z_lid = h_bot + h_pm + g;
z_top = h_bot + h_pm + g + h_lid;

Box(1) = {0, 0, 0, L_out, W_out, h_bot};
Box(20) = {0, 0, h_bot, L_out, W_out, h_wall};
Box(21) = {t, t, h_bot, L_cav, W_cav, h_wall};
BooleanDifference(2) = { Volume{20}; Delete; }{ Volume{21}; Delete; };
Box(3) = {ox, oy, z_pm, L, W, h_pm};
Box(4) = {ox, oy, z_gap, L, W, g};
Box(5) = {ox, oy, z_lid, L, W, h_lid};

pad = 0.02;
Box(10) = {-pad, -pad, -pad, L_out+2*pad, W_out+2*pad, z_top+2*pad};

BooleanFragments{ Volume{10, 1, 2, 3, 4, 5}; Delete; }{}

vols() = Volume{:};
iron_stator = {}; pm = {}; airgap = {}; iron_target = {}; air = {};

For i In {0 : #vols()-1}
  v = vols(i);
  bb() = BoundingBox Volume{v};
  dx = bb(3)-bb(0); dy = bb(4)-bb(1); dz = bb(5)-bb(2);
  vol = dx*dy*dz;
  zc = 0.5*(bb(2)+bb(5));
  xc = 0.5*(bb(0)+bb(3));
  yc = 0.5*(bb(1)+bb(4));
  If (vol > 0.35*(L_out+2*pad)*(W_out+2*pad)*(z_top+2*pad))
    air += {v};
  ElseIf (zc < h_bot - 1e-9)
    iron_stator += {v};
  ElseIf (dx > L_cav + t*0.5 && dy > W_cav + t*0.5 && zc >= h_bot-1e-9 && zc <= z_top+1e-9)
    iron_stator += {v};
  ElseIf (xc > ox-1e-7 && xc < ox+L+1e-7 && yc > oy-1e-7 && yc < oy+W+1e-7)
    If (zc < z_gap - 1e-9)
      pm += {v};
    ElseIf (zc < z_lid - 1e-9)
      airgap += {v};
    ElseIf (zc < z_top + 1e-9)
      iron_target += {v};
    Else
      air += {v};
    EndIf
  Else
    air += {v};
  EndIf
EndFor

Physical Volume("iron_stator", 1) = iron_stator[];
Physical Volume("pm", 2) = pm[];
Physical Volume("airgap", 3) = airgap[];
Physical Volume("iron_target", 4) = iron_target[];
Physical Volume("air", 5) = air[];
Physical Surface("exterior", 1) = CombinedBoundary{ Volume{vols[]}; };

Mesh.CharacteristicLengthMax = 0.011;
Mesh.CharacteristicLengthMin = 0.0004;
Field[1] = Box;
Field[1].VIn = 0.00085;
Field[1].VOut = 0.011;
Field[1].XMin = ox - 0.002; Field[1].XMax = ox + L + 0.002;
Field[1].YMin = oy - 0.002; Field[1].YMax = oy + W + 0.002;
Field[1].ZMin = z_gap - 0.002; Field[1].ZMax = z_lid + 0.003;
Background Field = 1;
