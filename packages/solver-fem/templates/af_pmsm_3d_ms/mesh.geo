// Mo AF PMSM 3D — magnetostatic min stack (PM/coil + airgap + iron)
// equationMode=magnetostatic; pending_calibration; NOT heat-proxy
// Physical: vol 1=coil_pm, 2=airgap, 3=iron; surf 1=exterior
SetFactory("OpenCASCADE");
L = 0.04; W = 0.04;
h_pm = 0.008; g = 0.004; h_fe = 0.008;
Box(1) = {0, 0, 0, L, W, h_pm};
Box(2) = {0, 0, h_pm, L, W, g};
Box(3) = {0, 0, h_pm + g, L, W, h_fe};
BooleanFragments{ Volume{1, 2, 3}; Delete; }{}
Physical Volume("coil_pm", 1) = {1};
Physical Volume("airgap", 2) = {2};
Physical Volume("iron", 3) = {3};
Physical Surface("exterior", 1) = CombinedBoundary{ Volume{1, 2, 3}; };
Mesh.CharacteristicLengthMax = 0.01;
Mesh.CharacteristicLengthMin = 0.004;
