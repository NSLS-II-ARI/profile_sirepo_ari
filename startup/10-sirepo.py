from sirepo_bluesky.sirepo_bluesky import SirepoBluesky
from sirepo_bluesky.sirepo_ophyd import create_classes

# Assumption: there is a running local instance of Sirepo. Please follow the
# instructions at http://nsls-ii.github.io/sirepo-bluesky/installation.html to
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
