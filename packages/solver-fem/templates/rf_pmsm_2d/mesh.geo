// Mo RF PMSM 2D Gmsh stub — run only inside FEM container
SetFactory("OpenCASCADE");
Rectangle(1) = {0, 0, 0, 0.1, 0.1, 0};
Mesh.CharacteristicLengthMax = 0.01;
