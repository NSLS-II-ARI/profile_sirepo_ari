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
    data, schema = connection.auth("srw", "00000003")
    classes, objects = create_classes(connection.data,
                                      connection=connection,
                                      extra_model_fields=['undulator', 'intensityReport'])
    globals().update(**objects)

    # Hinting
    undulator.verticalAmplitude.kind = "hinted"

else:
    warnings.warn("Not using Sirepo. Continuing without it...")
    single_electron_spectrum = None
    undulator = None
