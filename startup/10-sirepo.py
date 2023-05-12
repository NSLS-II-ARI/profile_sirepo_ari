import os
import warnings

from sirepo_bluesky.sirepo_bluesky import SirepoBluesky
from sirepo_bluesky.sirepo_ophyd import create_classes

if os.getenv("USE_SIREPO", "no").lower() in ["y", "yes", "1", "true"]:
    USE_SIREPO = True
else:
    USE_SIREPO = False

if USE_SIREPO:

    # Assumption: there is a running local instance of Sirepo. Please follow the
    # instructions at https://nsls-ii.github.io/sirepo-bluesky/installation.html to
    # install/configure Sirepo and Sirepo-Bluesky.
    connection = SirepoBluesky("http://localhost:8000")

    # See https://nsls-ii.github.io/sirepo-bluesky/simulations.html for the list of
    # simulations.
    data, schema = connection.auth("srw", "00000004")
    classes, objects = create_classes(connection.data,
                                      connection=connection,
                                      extra_model_fields=['undulator', 'intensityReport'])
    globals().update(**objects)

    # In [234]: classes
    # Out[234]:
    # {'fixed_mask': sirepo_bluesky.sirepo_ophyd.FixedMask,
    #  'at_m1': sirepo_bluesky.sirepo_ophyd.AtM1,
    #  'ap_m1': sirepo_bluesky.sirepo_ophyd.ApM1,
    #  'm1': sirepo_bluesky.sirepo_ophyd.M1,
    #  'm1_lens': sirepo_bluesky.sirepo_ophyd.M1Lens,
    #  'm2': sirepo_bluesky.sirepo_ophyd.M2,
    #  'before_grating': sirepo_bluesky.sirepo_ophyd.BeforeGrating,
    #  'grating': sirepo_bluesky.sirepo_ophyd.Grating,
    #  'after_grating': sirepo_bluesky.sirepo_ophyd.AfterGrating,
    #  'before_h_slit': sirepo_bluesky.sirepo_ophyd.BeforeHSlit,
    #  'h_slit': sirepo_bluesky.sirepo_ophyd.HSlit,
    #  'after_h_slit': sirepo_bluesky.sirepo_ophyd.AfterHSlit,
    #  'before_v_slit': sirepo_bluesky.sirepo_ophyd.BeforeVSlit,
    #  'v_slit': sirepo_bluesky.sirepo_ophyd.VSlit,
    #  'after_v_slit': sirepo_bluesky.sirepo_ophyd.AfterVSlit,
    #  'before_m4': sirepo_bluesky.sirepo_ophyd.BeforeM4,
    #  'm4': sirepo_bluesky.sirepo_ophyd.M4,
    #  'after_m4': sirepo_bluesky.sirepo_ophyd.AfterM4,
    #  'before_kbv': sirepo_bluesky.sirepo_ophyd.BeforeKBV,
    #  'ap_kbv': sirepo_bluesky.sirepo_ophyd.ApKBV,
    #  'kbv_lens': sirepo_bluesky.sirepo_ophyd.KBVLens,
    #  'kbv': sirepo_bluesky.sirepo_ophyd.KBV,
    #  'after_kbv': sirepo_bluesky.sirepo_ophyd.AfterKBV,
    #  'before_ap_kbh': sirepo_bluesky.sirepo_ophyd.BeforeApKBH,
    #  'ap_kbh': sirepo_bluesky.sirepo_ophyd.ApKBH,
    #  'after_ap_kbh': sirepo_bluesky.sirepo_ophyd.AfterApKBH,
    #  'kbh_lens': sirepo_bluesky.sirepo_ophyd.KBHLens,
    #  'kbh': sirepo_bluesky.sirepo_ophyd.KBH,
    #  'after_kbh': sirepo_bluesky.sirepo_ophyd.AfterKBH,
    #  'sample': sirepo_bluesky.sirepo_ophyd.Sample,
    #  'undulator': sirepo_bluesky.sirepo_ophyd.Undulator,
    #  'single_electron_spectrum': sirepo_bluesky.sirepo_ophyd.SingleElectronSpectrum}

    # Hinting
    undulator.verticalAmplitude.kind = "hinted"  # vertical magnetic field component
    single_electron_spectrum.kind = "hinted"  # spectrum report
    sample.kind = "hinted"  # watchpoint at the sample position

else:
    warnings.warn("Not using Sirepo. Continuing without it...")
    single_electron_spectrum = None
    undulator = None
