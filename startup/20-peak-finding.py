import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import peakutils
import scipy.signal


DATA_DIR = "data"
HARMONICS_JSON = os.path.join(DATA_DIR, "harmonics.json")


def find_peaks(df, harm_num=0, thres=0.10, filter_thres=0.2, ax=None):
    """Find peaks for the pandas dataframe."""

    energies = np.array(list(df["single_electron_spectrum_photon_energy"]))
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

        filtered_peaks_idx = [idx[0]]

        for idx in idx[1:]:
            print(f"{intensity[idx] = :2g}  {intensity[idx-1] =:2e}  {intensity[idx-1] / intensity[idx] = }")
            if intensity[idx-1] / intensity[idx] >= filter_thres:
                filtered_peaks_idx.append(idx)

        print(f"{energy[filtered_peaks_idx][harm_num] = :8.3f} [eV]  "
              f"{intensity[filtered_peaks_idx][harm_num] = :3g} [arb.u.]  "
              f"{mag_field = :.3f} [T]")

        lookup.loc[len(lookup)] = mag_field, energy[filtered_peaks_idx][harm_num]

    ax.plot(lookup["mag_field"], lookup["energy"],
            label=f"Harmonic #{harm_num + 1}",
            marker="o", linestyle='dashed')

    ax.legend(prop={"size": 6})

    return lookup


def plot_all_peaks(df, method="scipy", thres=0.10, filter_thres=0.2,
                   num_plots=21, ncols=7, nrows=3):
    """
    Usage
    -----

        df = pd.read_json("data/scan-spectra-vs-und-magn-field.json")
        all_energies = plot_all_peaks(df, method="peakutils", thres=0.05, filter_thres=0.20)

    """

    allowed_methods = ["scipy", "peakutils"]
    if method not in allowed_methods:
        raise ValueError("Unknown method: {method}. Allowed methods: {allowed_methods}")

    energies = np.array(list(df["single_electron_spectrum_photon_energy"]))
    intensities = np.array(list(df["single_electron_spectrum_image"]))
    mag_fields = np.array(list(df["undulator_verticalAmplitude"]))

    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=(ncols * 4, nrows * 3))
    fig.suptitle(f"{method} / threshold={thres * 100:.0f}% / filter threshold={filter_thres * 100:.0f}%")

    all_energies = {}

    for i in range(num_plots):
        ax = axes.ravel()[i]
        ax.grid()
        energy, intensity, mag_field = energies[i], intensities[i], mag_fields[i]

        # TODO: implement it via the `find_peaks()` function.
        if method == "scipy":
            peaks_idx = scipy.signal.find_peaks(intensity, height=intensity.max() * thres)[0]
        elif method == "peakutils":
            peaks_idx = peakutils.indexes(intensity, thres=thres)

        print(f"{i = }")

        diff_ratios = np.exp(np.diff(np.log(intensity[peaks_idx])))
        filtered_peaks_idx = peaks_idx[np.r_[True, diff_ratios > filter_thres]]

        # filtered_peaks_idx = [peaks_idx[0]]
        # for idx in peaks_idx[1:]:
        #     print(f"{intensity[idx] = :2g}  {intensity[idx-1] = :2g}  {intensity[idx-1] / intensity[idx] = :0.3f}")
        #     if intensity[idx] / intensity[filtered_peaks_idx[-1]] > filter_thres:
        #         filtered_peaks_idx.append(idx)
        #     else:
        #         print(f"  Removing peak idx {idx}")

        print(f"{len(peaks_idx) = } -> {len(filtered_peaks_idx) = }\n")

        ax.plot(energy, intensity, label=f"{i:3d}: {mag_field:.2f}T full")
        ax.plot(energy[filtered_peaks_idx], intensity[filtered_peaks_idx], marker="x", label=f"{i:3d}: {mag_field:.2f}T peaks")
        ax.legend(prop={"size": 6})
        plt.tight_layout()
        plt.savefig(f"{method}-{thres:.2f}.png")

        all_energies[mag_fields[i]] = energy[filtered_peaks_idx]

    return all_energies


def create_harmonics_dataframe(all_energies, harmonic_list=[1, 3, 5]):
    """
    Usage
    -----

        df_harm = create_harmonics_dataframe(all_energies)

    """
    magn_field = np.array(list(all_energies.keys()))[::-1]
    harmonics = {}
    for harm_num in harmonic_list:
        harmonics[harm_num] = []
        for en_list in all_energies.values():
            internal_idx = int((harm_num + 1) / 2 - 1)
            if len(en_list) > internal_idx:
                harmonics[harm_num].append(en_list[internal_idx])
            else:
                harmonics[harm_num].append(np.nan)
        harmonics[harm_num] = np.array(harmonics[harm_num])[::-1]

    data = np.array([magn_field, *[x for x in harmonics.values()]]).T
    df = pd.DataFrame(data, columns=["magn_field", *[f"harmonic{h}" for h in harmonics.keys()]])

    return df


def create_harmonics_json(df, path=HARMONICS_JSON):
    """
    Usage
    -----

        create_harmonics_json(df_harm, path="data/harmonics.json")

    """
    json_str = df.to_json(indent=2)
    with open(path, "w") as f:
        f.write(json_str)


def load_harmonics_json(path=HARMONICS_JSON):
    """
    Usage
    -----

        df_harm = load_harmonics_json(path="data/harmonics.json")

    """
    return pd.read_json(path)
