from ophyd import Signal, Component as Cpt
from ophyd.sim import NullStatus
from scipy import interpolate
from sirepo_bluesky.sirepo_ophyd import SirepoSignal


class SignalWithParent(Signal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.parent is None:
            raise RuntimeError("This class should be used as a component in the EPU class")


class SirepoSignalWithParent(SirepoSignal):
    def __init__(self, sirepo_dict, sirepo_param, *args, **kwargs):
        super().__init__(sirepo_dict, sirepo_param, *args, **kwargs)
        if self.parent is None:
            raise RuntimeError("This class should be used as a component in the EPU class")


class EnergySignal(SignalWithParent):
    def set(self, value):
        magn_field = self.parent._get_magn_field(value)
        self.parent.magn_field_ver.put(magn_field)
        self._readback = float(value)
        return NullStatus()


class MagnFieldSignal(SirepoSignalWithParent):
    def set(self, value):
        super().set(value)
        energy = self.parent._get_energy()
        self.parent.energy._readback = energy
        return NullStatus()


class EPU(classes["undulator"]):
    """
    Note: `classes["undulator"]` and `undulator.verticalAmplitude` come from `10-sirepo.py`.
    """
    energy = Cpt(EnergySignal)
    harm_num = Cpt(Signal, value=1)
    polarization = Cpt(Signal, value="")
    magn_field_ver = Cpt(MagnFieldSignal,
                         value=undulator.verticalAmplitude.get(),
                         sirepo_dict=undulator.verticalAmplitude._sirepo_dict,
                         sirepo_param="verticalAmplitude")
    magn_field_hor = Cpt(Signal,  # TODO: update the base class when we deal with the hor. comp.
                         value=undulator.horizontalAmplitude.get(),
                         sirepo_dict=undulator.horizontalAmplitude._sirepo_dict,
                         sirepo_param="horizontalAmplitude")
    # We explicitly remove these components from the Sirepo class to avoid
    # accidental change of them to avoid conflicts.
    verticalAmplitude = None
    horizontalAmplitude = None
    def __init__(self, *args, harmonics_df=None, **kwargs):
        super().__init__(*args, **kwargs)
        if harmonics_df is None:
            raise ValueError(f"The 'harmonics' kwarg should be a pandas dataframe")
        self._harmonics_df = harmonics_df
        self._interp_kwargs = {"kind": "quadratic", "bounds_error": False, "fill_value": "extrapolate"}
        self.energy.put(self._get_energy())

    def _get_energy(self):
        magn_field = self.magn_field_ver.get()
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp1d.html
        interp_func = interpolate.interp1d(self._harmonics_df["magn_field"],
                                           self._harmonics_df[f"harmonic{self.harm_num.get()}"],
                                           **self._interp_kwargs)
        return float(interp_func(magn_field))

    def _get_magn_field(self, energy):
        interp_func = interpolate.interp1d(self._harmonics_df[f"harmonic{self.harm_num.get()}"],
                                           self._harmonics_df["magn_field"],
                                           **self._interp_kwargs)
        return float(interp_func(energy))


df_harm = load_harmonics_json(path=HARMONICS_JSON)

# Use interpolation interactively:
# f = interpolate.interp1d(df_harm["magn_field"], df_harm["harmonic1"],
#                          kind="quadratic", bounds_error=False, fill_value="extrapolate")
# plt.plot(df_harm["magn_field"], df_harm["harmonic1"])
# plt.scatter(df_harm["magn_field"]-0.05, f(df_harm["magn_field"]-0.05))

epu = EPU(name="epu", harmonics_df=df_harm)
epu.kind = 'hinted'
epu.energy.kind = 'hinted'
