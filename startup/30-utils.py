import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import peakutils


def find_peaks(df, harm_num=0, thres=0.01, ax=None):
    """Find peaks for the pandas dataframe."""

    energies  = np.array(list(df["single_electron_spectrum_photon_energy"]))
    intensities = np.array(list(df["single_electron_spectrum_image"]))
    mag_fields = np.array(list(df["undulator_verticalAmplitude"]))

    lookup = pd.DataFrame(columns=['mag_field', 'energy'])

    if ax is None:
        fig, ax = plt.subplots(nrows=1, ncols=1)

    ax.grid(visible=True)
    ax.set_xlabel("Vertical Magn. Field [T]")
    ax.set_ylabel("Energy [eV]")
    ax.set_title(f"Energy vs. Magn. Field")

    for i in range(len(df)):
        energy, intensity, mag_field = energies[i], intensities[i], mag_fields[i]

        idx = peakutils.indexes(intensity, thres=thres)

        print(f"{energy[idx][harm_num] = :8.3f} [eV]  "
              f"{intensity[idx][harm_num] = :3g} [arb.u.]  "
              f"{mag_field = :.3f} [T]")

        lookup.loc[len(lookup)] = mag_field, energy[idx][harm_num]

    ax.plot(lookup["mag_field"], lookup["energy"],
            label=f"Harmonic #{harm_num + 1}",
            marker="o", linestyle='dashed')

    ax.legend(prop={"size": 6})

    return lookup
