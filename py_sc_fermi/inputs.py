import numpy as np
from .defect_species import DefectSpecies
from .defect_charge_state import DefectChargeState
from py_sc_fermi.dos import DOS
from pymatgen.core import Structure
from typing import Union


def read_unitcell_data(filename: str) -> float:
    """
    get volume in A^3 from `unitcell.dat` file used in SC-Fermi

    Args:
        filename (str): `unitcell.dat` file to parse
    Returns:
        volume (float): cell volume in A^3
    """
    with open(filename, "r") as f:
        readin = [l for l in f.readlines() if l[0] != "#"]
    factor = float(readin[0])
    lattvec = np.array([[float(s) for s in l.split()] for l in readin[1:4]], order="F")
    lattvec *= factor
    volume = np.linalg.det(lattvec)
    return volume


def read_input_data(
    filename: str, volume: float = None, frozen: bool = False
) -> dict[str, Union[list["py_sc_fermi.defect_species.DefectSpecies"], float, int]]:
    """
    return all information from a input file correctly formated to work
    for `SC-Fermi`.

    Args:
        filename (str): path to input file to parse
        volume (float): volume of structure in A^3
        frozen (bool): if the file to be read contains frozen defect concentrations
    Returns:
        input_data (dict): a dictionary of data required to initialise a defect system
    """

    with open(filename, "r") as f:
        readin = f.readlines()
        pure_readin = [line for line in readin if line[0] != "#"]
    nspinpol = int(pure_readin.pop(0))
    nelect = int(pure_readin.pop(0))
    egap = float(pure_readin.pop(0))
    temperature = float(pure_readin.pop(0))
    ndefects = int(pure_readin.pop(0))

    defect_species = read_defect_species(pure_readin, ndefects)
    if frozen == True:
        nfrozen_defects = int(pure_readin.pop(0))
        update_frozen_defect_species(
            pure_readin, defect_species, volume, nfrozen_defects
        )
        nfrozen_chgstates = int(pure_readin.pop(0))
        update_frozen_chgstates(pure_readin, defect_species, volume, nfrozen_chgstates)

    input_data = {
        "defect_species": defect_species,
        "egap": egap,
        "temperature": temperature,
        "nspinpol": nspinpol,
        "nelect": nelect,
    }

    return input_data


def read_dos_data(filename: str, egap: float, nelect: int) -> "py_sc_fermi.dos.DOS":
    """
    return dos information from a `totdos.dat` file.

    Args:
        filename (str): path to `totdos.dat` to parse
        egap (float): bandgap of host material
        nelect (int): number of the electrons in host material calculation
    Returns:
        dos (DOS): py_sc_fermi.DOS object
    """
    data = np.loadtxt(filename)
    edos = data[:, 0]
    dos = np.sum(data[:, 1:], axis=1)
    if np.any(data[:, 1:] < 0.0):
        print("WARNING: Found negative value(s) of DOS!")
        print("         Do you know what you are doing?")
        print("         These may cause serious problems...")
    dos = DOS(dos=dos, edos=edos, nelect=nelect, egap=egap)
    return dos


def inputs_from_files(
    unitcell_filename: str = 'unitcell.dat',
    totdos_filename: str = 'totdos.dat',
    input_fermi_filename: str = 'input-fermi.dat',
    frozen: bool = False,
) -> dict[str, Union[list["py_sc_fermi.defect_species.DefectSpecies"], float, int]]:
    """
    return a set of inputs descrbing a full defect system from py_sc_fermi input files

    Args:
        unitcell_filename (str): path to `unitcell.dat` to parse
        totdos_filename (str): path to `totdos.dat` to parse
        input_fermi_filename (str): path to `SC-Fermi` to parse
    Returns:
        inputs (dict): set of input data for py_sc_fermi.DefectSystem
    """
    inputs = {}
    inputs["volume"] = read_unitcell_data(unitcell_filename)
    inputs.update(
        read_input_data(input_fermi_filename, frozen=frozen, volume=inputs["volume"])
    )
    inputs["dos"] = read_dos_data(
        totdos_filename, egap=inputs["egap"], nelect=inputs["nelect"]
    )
    return inputs


def read_defect_species(
    pure_readin: str, ndefects: int
) -> list["py_sc_fermi.defect_species.DefectSpecies"]:
    """
    read defect data from SC-Fermi input file and return a list of DefectSpecies.
    Typically will only be called by `read_input_data()`

    Args:
        pure_readin (string): SC_Fermi input "free" defect data
        ndefects (int): number of defect species in the input file
    Returns:
        defect_species (list): list of `py_sc_fermi.DefectSpecies` objects
    """
    defect_species = []
    for i in range(ndefects):
        l = pure_readin.pop(0).split()
        name = l[0]
        ncharge = int(l[1])
        nsites = int(l[2])
        charges = []
        energies = []
        degs = []
        for j in range(ncharge):
            l = pure_readin.pop(0).split()
            charges.append(float(l[0]))
            energies.append(float(l[1]))
            degs.append(int(l[2]))
        charge_states = [
            DefectChargeState(charge=c, energy=e, degeneracy=d)
            for c, e, d in zip(charges, energies, degs)
        ]
        defect_species.append(DefectSpecies(name, nsites, charge_states))

    return defect_species


def update_frozen_defect_species(
    pure_readin: str, defect_species: list, volume: float, nfrozen_defects: int
) -> None:
    """
    read frozen DefectSpecies data from SC-Fermi input file and update a list of "free" DefectSpecies
    objects. Typically will only be called by `read_input_data()`.

    Args:
        pure_readin (string): SC_Fermi input frozen defect data
        defect_species (list): list of defect_species to update
        volume (float): volume of unit cell for coverting between concentration units
        nfrozen_defects (int): number of frozen concentration DefectSpecies
    """

    if nfrozen_defects > 0:
        frozen_defects = {}
        for i in range(nfrozen_defects):
            l = pure_readin.pop(0).split()
            frozen_defects.update({l[0]: l[1]})
        for k, v in frozen_defects.items():
            for defect in defect_species:
                if defect.name == k:
                    defect.fix_concentration(float(v) / 1e24 * volume)


def update_frozen_chgstates(
    pure_readin: str, defect_species: list, volume: float, nfrozen_chgstates: int
) -> None:
    """
    read frozen DefectChgStates data from SC-Fermi input file and update a list of "free" DefectSpecies
    objects. Typically will only be called by `read_input_data()`.

    Args:
        pure_readin (string): SC_Fermi input frozen defect data
        defect_species (list): list of defect_species to update
        volume (float): volume of unit cell for coverting between concentration units
        nfrozen_defects (int): number of frozen concentration DefectChgStates
    """
    if nfrozen_chgstates > 0:
        frozen_chgstates = []
        for i in range(nfrozen_chgstates):
            l = pure_readin.pop(0).split()
            frozen_chgstates.append(
                {"Name": l[0], "Chg_state": l[1], "Con": l[2].split()[0]}
            )
        defect_labels = [i.name for i in defect_species]
        for defect in frozen_chgstates:
            if defect["Name"] in defect_labels:
                defect_to_freeze = [
                    i for i in defect_species if defect["Name"] == i.name
                ][0]
                defect_to_freeze.charge_states[defect["Chg_state"]] = DefectChargeState(
                    charge=int(defect["Chg_state"]),
                    fixed_concentration=float(defect["Con"]) / 1e24 * volume,
                )
            else:
                defect_species.append(
                    DefectSpecies(
                        defect["Name"],
                        1,
                        [
                            DefectChargeState(
                                charge=int(defect["Chg_state"]),
                                fixed_concentration=float(defect["Con"])
                                / 1e24
                                * volume,
                            )
                        ],
                    )
                )


def volume_from_structure(structure_file: str) -> float:
    """
    return volume in A^3 for a given structure file. Relies on pymatgen structure parser
    so accepts a wide range of formats inc. POSCAR, .cif, vasp output files (OUTCAR, vasprun.xml) etc.

    Args:
        structure_file (str): path to structure file to parse

    Returns:
        volume (float): volume of structure in A^3
    """
    structure = Structure.from_file(structure_file)
    volume = structure.volume
    return float(volume)
