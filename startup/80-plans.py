print(f"{datetime.datetime.now().isoformat()} Loading {__file__}...")

import bluesky.plan_stubs as bps
import bluesky.plans as bp


def scan_spectra_vs_mag_field(
    dets=[single_electron_spectrum],
    parameter=undulator.verticalAmplitude if undulator is not None else None,
    start=0.075,
    stop=1.5,
    num_spectra=21,
    initial_energy=0.1,
    final_energy=1100.0,
    num_points_per_spectrum=2000,
):
    # Prepare initial conditions:
    yield from bps.mv(
        single_electron_spectrum.initialEnergy,
        initial_energy,
        single_electron_spectrum.finalEnergy,
        final_energy,
        single_electron_spectrum.photonEnergyPointCount,
        num_points_per_spectrum,
    )

    uid = yield from bp.scan(dets, parameter, start, stop, num_spectra)
    return uid


# RE(bp.scan([sample], epu.energy, 100, 800, 8))
