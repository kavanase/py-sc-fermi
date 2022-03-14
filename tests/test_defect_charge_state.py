import unittest

from py_sc_fermi.defect_charge_state import DefectChargeState


class TestDefectChargeStateInit(unittest.TestCase):
    def test_defect_charge_state_is_initialised(self):
        charge = 1.0
        energy = 123.4
        degeneracy = 2
        defect_charge_state = DefectChargeState(
            charge=charge, energy=energy, degeneracy=degeneracy
        )
        self.assertEqual(defect_charge_state._charge, charge)
        self.assertEqual(defect_charge_state._energy, energy)
        self.assertEqual(defect_charge_state._degeneracy, degeneracy)
        self.assertEqual(defect_charge_state.fixed_concentration, None)


class TestDefectChargeState(unittest.TestCase):
    def setUp(self):
        charge = 1.0
        energy = 0.1234
        degeneracy = 2
        self.defect_charge_state = DefectChargeState(
            charge=charge, energy=energy, degeneracy=degeneracy
        )

    def test_charge_property(self):
        self.assertEqual(
            self.defect_charge_state.charge, self.defect_charge_state._charge
        )

    def test_energy_property(self):
        self.assertEqual(
            self.defect_charge_state.energy, self.defect_charge_state._energy
        )

    def test_degeneracy_property(self):
        self.assertEqual(
            self.defect_charge_state.degeneracy, self.defect_charge_state._degeneracy
        )

    def test_fix_concentration(self):
        self.assertEqual(self.defect_charge_state.fixed_concentration, None)
        self.defect_charge_state.fix_concentration(1)
        self.assertEqual(self.defect_charge_state.fixed_concentration, 1)

    def test_get_formation_energy(self):
        e_fermi = 1.2
        formation_energy = self.defect_charge_state.get_formation_energy(e_fermi)
        self.assertEqual(formation_energy, 0.1234 + (1.0 * 1.2))

    def test_get_concentration(self):
        e_fermi = 1.2
        temperature = 298.0
        conc = self.defect_charge_state.get_concentration(
            e_fermi=e_fermi, temperature=temperature
        )
        self.assertEqual(conc, 8.311501552630706e-23)


if __name__ == "__main__":
    unittest.main()
