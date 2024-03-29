print(f"{datetime.datetime.now().isoformat()} Loading {__file__}...")

import numpy as np
from ophyd import Component as Cpt
from ophyd import Device, Signal, SignalRO
from ophyd.sim import NullStatus
from scipy import interpolate
from sirepo_bluesky.sirepo_ophyd import SirepoSignal


def _get_cff(e_ph, grating, r2, r1, m, gratings):
    """
    Returns the fine focus constant given the energy, grating and output focal length.

    Based on the photon energy, grating, the output focal length and several other
    instantiation time parameters, seen as keywords, this function returns the fine
    focus constant using the relations:
    $$c_{ff} = \sqrt((B_{0}+B_{1})/B{2})\\
        \begin{align}
        \text{where: } B_{0} &= 2A_{1}+4(A_{1}/A_{0})^2+(4+2A_{1}-A_{0}^{2})
                              (\frac{r_{2}}{r_{1}})\\
                     B_{1} &= -4(A_{1}/A_{0})\sqrt((1+\frac{r_{2}}{r_{1}})^2+
                              2A_{1}(1+\frac{r_{2}}{r_{1}})-
                              A_{0}^{2}(\frac{r_{2}}{r_{1}})\\
                     B_{2} &= -4+A_{0}^{2}-4A_{2}+4(A_{2}/A_{0})^2\\
                     A_{0} &= m\lambda a_{0}\\
                     A_{1} &= -\frac{1}{2}m\lambda r_{2}a_{1}\\
                     \lambda &= (12398.4197/E_{ph})1e-7\\
        \end{align}
    $$

    Units for each parameter are: eV for energies, mm for lengths and mm^{-1}/
    mm^{-2}/ mm^{-3}/ mm^{-4} for the respective grating equation parameters.

    Parameters
    ----------
    e_ph : float
        The photon energy in eV.
    grating : string
        The grating name.
    r2 : float
        The output focal length for the PGM in mm
    r1 : float, optional
        The input focal length for the PGM in mm
    m : integer, optional
        The diffraction order.
    gratings : dict, optional
        A dictionary that matches grating names to a dictionary of grating parameters.

    Returns
    -------
    cff : float
        The fine focus constant.
    """

    lambda_ = (12398.4197 / e_ph) * 1e-7  # wavelength in mm from e_ph in eV
    A1 = -0.5 * m * lambda_ * r2 * gratings[grating]["a1"]
    A0 = m * lambda_ * gratings[grating]["a0"]
    B2 = -4 + A0**2 - 4 * A1 + 4 * (A1 / A0) ** 2
    B1 = (
        -4
        * (A1 / A0)
        * np.sqrt((1 + r2 / r1) ** 2 + 2 * A1 * (1 + r2 / r1) - A0**2 * (r2 / r1))
    )
    B0 = 2 * A1 + 4 * (A1 / A0) ** 2 + (4 + 2 * A1 - A0**2) * (r2 / r1)
    cff = np.sqrt((B0 + B1) / B2)

    return cff


def _get_pgm_angles(e_ph, grating, r2, r1, m, gratings, x_inc, x_diff, b, cff=None):
    """
    Returns the M2/Grating angles given the photon energy, grating and output focal
    length.

    Based on the photon energy, grating, the output focal length and several other
    instantiation time parameters, seen as keywords, this function returns the
    required angles for the M2 mirror and the grating using the _cff function and
    the relations:
    $$
        \Theta_{M2} = \frac{1}{2}(X_{diff}+X_{inc}+b(180-\alpha+\beta))\\
        \Theta_{GR} = b(90+\beta)+X_{diff}
        \begin{align}
        \text{where: }  \alpha &=sin^{-1}(-ma_{0}\lambda /(c_{eff}^{2}-1)+
                        \sqrt(1+(c_{ff}ma_{0}\lambda /(c_{eff}^{2}-1))^2))\\
                        \beta &= sin^{-1}(ma_{0}\lambda-sin(\alpha))\\
                        \lambda &= (12398.4197/E_{ph})1e-7\\
        \end{align}
    $$

    Units for each parameter are: eV for energies, mm for lengths, degrees for angles
    and mm^{-1}/ mm^{-2}/ mm^{-3}/ mm^{-4} for the respective grating equation
    parameters.

    Parameters
    ----------
    E_ph : float
        The photon energy in eV.
    grating : string
        The grating name.
    r2 : float
        The output focal length for the PGM in mm
    r1 : float, optional
        The input focal length for the PGM in mm
    m : integer, optional
        The diffraction order.
    gratings : dict, optional
        A dictionary that matches grating names to a dictionary of grating parameters.
    x_inc : float, optional
        The incident X-ray angle
    x_diff : float, optional
        The outgoing X-ray angle
    b : int, optional
        integer indicating the bounce direction: +1 (for upward bounce) or -1
        (for downward bounce)

    Returns
    -------
    (theta_m2, theta_gr) : (float, float)
        The required angles for M2 and the grating in degrees.
    """
    ##NOTE if I choose to read in cff from a read-only ophyd signal then I no longer
    ## need r2 and r1 as args/kwargs (but I will need cff as an arg)
    lambda_ = (12398.4197 / e_ph) * 1e-7  # wavelength in mm from e_ph in eV
    # NOTE the next line may be better read from the read-only axis instead of calculating

    if cff is None:
        cff = _get_cff(e_ph, grating, r2, r1=r1, m=m, gratings=gratings)

    alpha = np.degrees(
        np.arcsin(
            -m * gratings[grating]["a0"] * lambda_ / (cff**2 - 1)
            + np.sqrt(
                1 + (cff * m * gratings[grating]["a0"] * lambda_ / (cff**2 - 1)) ** 2
            )
        )
    )
    beta = np.degrees(
        np.arcsin(m * gratings[grating]["a0"] * lambda_ - np.sin(np.radians(alpha)))
    )
    theta_m2 = abs(0.5 * (x_diff + x_inc + b * (180 - alpha + beta)))
    theta_gr = b * (90 + beta) + x_diff

    return (theta_m2, theta_gr)


def _get_pgm_energy(theta_m2, theta_gr, grating, m, gratings, x_inc, x_diff, b):
    """
    Returns the energy given the M2/grating angles, grating and output focal
    length.

    Based on the M2/grating angles, grating, the output focal length and several other
    instantiation time parameters, seen as keywords, this function returns the
    photon energy using the _cff function and the relations:

        E_{ph}=(12398.4197/\lambda)1e-7\\
        \begin{align}
        \text{where: } \lambda &= (sin(\alpha)+sin(\beta))/(ma_{0})\\
                       \beta &= - 90 +b(\Theta_{Gr} - X_{diff})\\
                       \alpha &= 180 + \beta + b(X_{diff} + X_{inc} - 2\Theta_{M2})
        \end{align}

    Parameters
    ----------
    theta_m2 : float
        The angle of the M2 mirror
    theta_gr : float
        The angle of the Grating
    grating : string
        The grating name.
    m : integer, optional
        The diffraction order.
    gratings : dict, optional
        A dictionary that matches grating names to a dictionary of grating parameters.
    x_inc : float, optional
        The incident X-ray angle
    x_diff : float, optional
        The outgoing X-ray angle
    b : int, optional
        integer indicating the bounce direction: +1 (for upward bounce) or -1
        (for downward bounce)

    Returns
    -------
    e_ph : float
        The photon energy of the PGM in eV.
    """

    beta = -90 + b * (theta_gr - x_diff)
    alpha = 180 + beta + b * (x_diff + x_inc - 2 * theta_m2)
    lambda_ = (np.sin(np.radians(alpha)) + np.sin(np.radians(beta))) / (
        m * gratings[grating]["a0"]
    )
    e_ph = (12398.4197 / lambda_) * 1e-7  # energy in eV

    return e_ph


class CFFSignalRO(SirepoSignalWithParent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self):
        energy = self.parent.energy.get()
        grating = self.parent.grating_name.get()
        _r2 = self.parent._r2.get()
        _r1 = self.parent._r1.get()
        _m = self.parent._m.get()
        _gratings = self.parent._gratings.get()

        _cff = _get_cff(energy, grating, r2=_r2, r1=_r1, m=_m, gratings=_gratings)

        self._sirepo_dict["cff"] = _cff

        self._readback = _cff
        # self._value = _cff

        return _cff


class PreMirrorAngleSignal(SirepoSignalWithParent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = (
            np.degrees(self._readback * 1.0e-3) + 90.0
        )  # _readback is in mrad, converting _value to deg.
        self._readback = self._value  # needs to be in deg too.

    def set(self, value):
        super().set(
            np.radians(value - 90.0) * 1e3
        )  # updates Sirepo model, needs to be in mrad
        self._readback = float(value)  # in degrees.
        self._value = float(value)
        return NullStatus()


class GratingAngleSignal(SirepoSignalWithParent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = (
            np.degrees(self._readback * 1.0e-3) + 90.0
        )  # _readback is in mrad, converting _value to deg.
        self._readback = self._value  # needs to be in deg too.

    def set(self, value):
        super().set(
            np.radians(value - 90.0) * 1e3
        )  # updates Sirepo model, needs to be in mrad.
        self.parent.grating_angle._readback = float(value)  # in degrees.
        self._value = float(value)
        return NullStatus()


class GratingNameSignal(Signal):
    # TODO: update the parent class SignalWithParent to rely on `self.put()`.
    def put(self, value):
        super().put(value)

        _m = self.parent._m.get()
        _b = self.parent._b.get()
        _x_inc = self.parent._x_inc.get()
        _x_diff = self.parent._x_diff.get()
        _gratings = self.parent._gratings.get()

        energy = _get_pgm_energy(
            self.parent.pre_mirror_angle.get(),
            self.parent.grating_angle.get(),
            m=_m,
            grating=value,
            gratings=_gratings,
            x_inc=_x_inc,
            x_diff=_x_diff,
            b=_b,
        )

        for k, v in _gratings[value].items():
            getattr(self.parent, f"_{k}").put(v)

        self.parent.energy._readback = energy
        self.parent.energy._value = energy
        self.parent.cff.get()

    def set(self, *args, **kwargs):
        self.put(*args, **kwargs)
        return NullStatus()


class PGMEnergySignal(SignalWithParent):
    def set(self, value):  # value is in eV.
        self._readback = float(value)

        connection.data["models"]["simulation"]["photonEnergy"] = float(value)

        _gratings = self.parent._gratings.get()
        grating = self.parent.grating_name.get()

        _r2 = self.parent._r2.get()
        _r1 = self.parent._r1.get()
        _m = self.parent._m.get()
        _b = self.parent._b.get()
        _x_inc = self.parent._x_inc.get()
        _x_diff = self.parent._x_diff.get()
        _cff = self.parent.cff.get()

        theta_pm, theta_gr = _get_pgm_angles(
            e_ph=value,
            grating=grating,
            r2=_r2,
            r1=_r1,
            m=_m,
            gratings=_gratings,
            x_inc=_x_inc,
            x_diff=_x_diff,
            b=_b,
            cff=_cff,
        )

        self.parent.pre_mirror_angle.set(theta_pm)
        self.parent.grating_angle.set(theta_gr)

        return NullStatus()


_ari_gratings = {
    "LowE": {"a0": 50, "a1": 0.01868, "a2": 1.95e-06, "a3": 4e-9},
    "HighE": {"a0": 50, "a1": 0.02986, "a2": 2.87e-06, "a3": 8e-9},
    "HighR": {"a0": 200, "a1": 0.05743, "a2": 6.38e-06, "a3": 1.5e-8},
}

_sxn_gratings = {
    "LowE": {"a0": 150, "a1": 0.04341, "a2": 2.6e-06, "a3": 1.5e-8},
    "MedE": {"a0": 350, "a1": 0.0755, "a2": 4.95e-06, "a3": 2.5e-8},
    "HighE": {"a0": 350, "a1": 0.05739, "a2": 4.18e-06, "a3": 1.2e-8},
}


class PGM(Device):
    """
    Plane-grating Monochromator
    """

    _gratings = Cpt(Signal, value=_ari_gratings)

    energy = Cpt(
        PGMEnergySignal,
        value=connection.data["models"]["simulation"]["photonEnergy"],
        kind="hinted",
    )
    grating_name = Cpt(GratingNameSignal, value="HighR")
    grated_harm_num = Cpt(Signal, value=1)

    grating_dict = {
        "LowE": {"a0": 50, "a1": 0.01868, "a2": 1.95e-06, "a3": 4e-9},
        "HighE": {"a0": 50, "a1": 0.02986, "a2": 2.87e-06, "a3": 8e-9},
        "HighR": {"a0": 200, "a1": 0.05743, "a2": 6.38e-06, "a3": 1.5e-8},
    }

    pre_mirror_angle = Cpt(
        PreMirrorAngleSignal,
        value=objects["m2"].grazingAngle.get(),
        sirepo_dict=objects["m2"].grazingAngle._sirepo_dict,
        sirepo_param="grazingAngle",
    )

    grating_angle = Cpt(
        GratingAngleSignal,  # TODO: update the base class when we deal with the hor. comp.
        value=objects["grating"].grazingAngle.get(),
        sirepo_dict=objects["grating"].grazingAngle._sirepo_dict,
        sirepo_param="grazingAngle",
    )

    grating_output_focal_len = (
        objects["v_slit"].element_position.get()
        - objects["grating"].element_position.get()
    )  # in [m]
    _r2 = Cpt(
        Signal, value=grating_output_focal_len * 1e3
    )  # input in [mm]; 43.6 m (vertical slit) - 32.1 m

    grating_input_focal_len = objects["grating"].element_position.get()  # in [m]
    _r1 = Cpt(
        Signal, value=grating_input_focal_len * 1e3
    )  # input in [mm]; 32.1 m position for grating from Sirepo

    _m = Cpt(Signal, value=1)  #  Diffraction Order in Sirepo

    _x_inc = Cpt(Signal, value=90)  # in degrees
    _x_diff = Cpt(Signal, value=90)  # in degrees
    _b = Cpt(Signal, value=1)  # bounce direction, 1 is up -1 is down

    cff = Cpt(
        CFFSignalRO,
        value=objects["grating"].cff.get(),
        sirepo_dict=objects["grating"].cff._sirepo_dict,
        sirepo_param="cff",
    )

    _a0 = Cpt(
        SirepoSignalWithParent,
        value=objects["grating"].grooveDensity0.get(),
        sirepo_dict=objects["grating"].grooveDensity0._sirepo_dict,
        sirepo_param="grooveDensity0",
    )
    _a1 = Cpt(
        SirepoSignalWithParent,
        value=objects["grating"].grooveDensity1.get(),
        sirepo_dict=objects["grating"].grooveDensity1._sirepo_dict,
        sirepo_param="grooveDensity1",
    )
    _a2 = Cpt(
        SirepoSignalWithParent,
        value=objects["grating"].grooveDensity2.get(),
        sirepo_dict=objects["grating"].grooveDensity2._sirepo_dict,
        sirepo_param="grooveDensity2",
    )
    _a3 = Cpt(
        SirepoSignalWithParent,
        value=objects["grating"].grooveDensity3.get(),
        sirepo_dict=objects["grating"].grooveDensity3._sirepo_dict,
        sirepo_param="grooveDensity3",
    )


pgm = PGM(name="pgm")
pgm.grating_name.set("HighR")

pgm.energy.set(connection.data["models"]["simulation"]["photonEnergy"])
pgm.kind = "hinted"

after_v_slit.kind = "hinted"
after_v_slit.mean.kind = "hinted"
