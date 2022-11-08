import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import peakutils
import scipy.signal


def find_peaks(df, harm_num=0, thres=0.10, ax=None):
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
        # idx = scipy.signal.find_peaks(intensity, height=intensity.max() * thres)[0]

        print(f"{energy[idx][harm_num] = :8.3f} [eV]  "
              f"{intensity[idx][harm_num] = :3g} [arb.u.]  "
              f"{mag_field = :.3f} [T]")

        lookup.loc[len(lookup)] = mag_field, energy[idx][harm_num]

    ax.plot(lookup["mag_field"], lookup["energy"],
            label=f"Harmonic #{harm_num + 1}",
            marker="o", linestyle='dashed')

    ax.legend(prop={"size": 6})

    return lookup


def plot_all_peaks(df, method="scipy", thres=0.10,
                   num_plots=21, ncols=7, nrows=3):

    allowed_methods = ["scipy", "peakutils"]
    if method not in allowed_methods:
        raise ValueError("Unknown method: {method}. Allowed methods: {allowed_methods}")

    energies  = np.array(list(df["single_electron_spectrum_photon_energy"]))
    intensities = np.array(list(df["single_electron_spectrum_image"]))
    mag_fields = np.array(list(df["undulator_verticalAmplitude"]))

    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=(ncols * 4, nrows * 3))
    fig.suptitle(f"{method} / threshold={thres * 100:.0f}%")

    for i in range(num_plots):
        ax = axes.ravel()[i]
        ax.grid()
        energy, intensity, mag_field = energies[i], intensities[i], mag_fields[i]

        if method == "scipy":
            peaks = scipy.signal.find_peaks(intensity, height=intensity.max() * thres)[0]
        elif method == "peakutils":
            peaks = peakutils.indexes(intensity, thres=thres)

        ax.plot(energy[peaks], intensity[peaks], marker="x", label=f"{i:3d}: {mag_field:.2f}T peaks")
        ax.plot(energy, intensity, label=f"{i:3d}: {mag_field:.2f}T full")
        ax.legend(prop={"size": 6})
        plt.tight_layout()
        plt.savefig(f"{method}-{thres:.2f}.png")
