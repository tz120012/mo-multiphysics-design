// Mo AF PMSM 3D — Q3 E2E mesh (heat-proxy box; magnetostatic TBD)
SetFactory("OpenCASCADE");
Box(1) = {0, 0, 0, 0.05, 0.05, 0.02};
Physical Volume("Body1", 1) = {1};
Physical Surface("cold", 1) = {5};
Physical Surface("hot", 2) = {6};
Mesh.CharacteristicLengthMax = 0.015;
