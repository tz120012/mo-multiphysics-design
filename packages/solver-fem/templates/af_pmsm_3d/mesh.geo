// Mo AF PMSM 3D Gmsh stub — container only
SetFactory("OpenCASCADE");
Cylinder(1) = {0, 0, 0, 0, 0, 0.02, 0.05, 2*Pi};
Mesh.CharacteristicLengthMax = 0.01;
