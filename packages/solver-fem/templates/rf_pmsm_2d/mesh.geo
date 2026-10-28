// Mo RF PMSM 2D — Q3 E2E mesh (heat-proxy rectangle; magnetostatic TBD)
// Run only inside FEM container / worker-fem with gmsh.
SetFactory("OpenCASCADE");
Rectangle(1) = {0, 0, 0, 0.1, 0.1, 0};
Physical Surface("Body1", 1) = {1};
Physical Curve("cold", 1) = {1};
Physical Curve("hot", 2) = {3};
Mesh.CharacteristicLengthMax = 0.02;
