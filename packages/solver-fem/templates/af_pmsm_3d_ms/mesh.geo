// Mo AF PMSM 3D — magnetostatic skeleton mesh (box; reuseable from af_pmsm_3d)
// equationMode=magnetostatic; pending_calibration; NOT heat-proxy
SetFactory("OpenCASCADE");
Box(1) = {0, 0, 0, 0.05, 0.05, 0.02};
Physical Volume("Body1", 1) = {1};
Physical Surface("bc_a", 1) = {5};
Physical Surface("bc_b", 2) = {6};
Mesh.CharacteristicLengthMax = 0.015;
