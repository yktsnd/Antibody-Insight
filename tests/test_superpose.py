import numpy as np
import pytest

from antibody_insight.structures import superpose
from antibody_insight import imports, project, structures
from antibody_insight.desktop import Desktop


def coordinates(points,zero=None):
    residues=[[10,""],[10,"A"],[12,""],[13,""]]
    lines=[]
    for index, ((number,insertion),(x,y,z)) in enumerate(zip(residues,points),1):
        occupancy=0 if index==zero else 1
        lines.append(f"ATOM  {index:5}  CA  ALA A{number:4}{insertion or ' '}   {x:8.3f}{y:8.3f}{z:8.3f}{occupancy:6.2f}  0.00           C")
    return dict(chain="A",mapping=residues,display_pdb="\n".join(lines)+"\nEND   \n")


def test_known_rotation_keeps_insertion_and_skips_zero_occupancy():
    fixed=np.array([[0,0,0],[2,0,0],[0,3,0],[0,0,4]])
    moving=np.array([[-y+2,x+3,z-5] for x,y,z in fixed])
    result=superpose(coordinates(fixed),coordinates(moving,zero=4),[[i,i] for i in range(1,5)])
    assert result["pairs"]==[[1,1],[2,2],[3,3]]
    assert result["rmsd"]<1e-6
    assert np.linalg.det(result["rotation"])==pytest.approx(1,abs=1e-6)
    assert moving@result["rotation"]+result["translation"]==pytest.approx(fixed,abs=1e-6)


def test_collinear_fit_is_undefined():
    line=coordinates([[0,0,0],[1,0,0],[2,0,0],[3,0,0]])
    with pytest.raises(ValueError,match="lie on a line"):
        superpose(line,line,[[i,i] for i in range(1,5)])


def test_fit_uses_aligned_positions_across_components(tmp_path):
    db=tmp_path/"Aligned structures.ais"
    project.create_project(db)
    records=tmp_path/"Chains.csv"
    records.write_text("candidate,component,kind,sequence\nFirst,Fixed,AA,MGSK\nSecond,Moving,AA,MAGTK\n")
    project.commit(db,imports.parse_file(records))
    points=[(0,0,0),(2,0,0),(0,3,0),(0,0,4)]
    shifted=[(-y+2,x+3,z-5) for x,y,z in points]
    def put(part,letters,positions):
        coords="\n".join(f"ATOM  {i:5}  CA  {aa} A{i+30:4}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C"
                         for i,(aa,(x,y,z)) in enumerate(zip(letters,positions),1))+"\nEND   \n"
        packet=structures.parse_coordinates(coords.encode(),part["label"]+".pdb",part)
        structures.save(db,packet,"A","Unknown")
        return project.component_detail(db,part["id"])["structures"][0]["id"]
    fixed,moving=[project.component_detail(db,c["id"]) for c in project.summary(db)["components"]]
    key1=put(fixed,["MET","GLY","SER","LYS"],points)
    key2=put(moving,["MET","ALA","GLY","THR","LYS"],[shifted[0],(7,8,9),*shifted[1:]])
    desktop=Desktop(db)
    session=desktop.current()["session"]
    args=(session,fixed["id"],key1,moving["id"],key2)
    result=desktop.overlay(*args,[2,4])
    assert result["pairs"]==[[2,3],[3,4],[4,5]]
    assert result["correspondence"]==[[1,1],[2,3],[3,4],[4,5]]
    assert result["rmsd"]<1e-6
    with pytest.raises(ValueError,match="valid positions"):
        desktop.overlay(*args,[2,5])
