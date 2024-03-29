print(epu.energy.get())
epu.energy.set(250)

# HighR case:
pgm.grating_name.set("HighR")
RE(bp.scan([after_v_slit], pgm.energy, 240, 260, 21))

# HighE case:
pgm.grating_name.set("HighE")
epu.energy.set(800)
RE(bp.scan([after_v_slit], pgm.energy, 795, 805, 11))

# Simulation similar to '00000004':
pgm.grating_name.set("HighR")
epu.energy.set(400)
RE(bp.scan([after_v_slit], pgm.energy, 390, 410, 11))

# Simulation '00000004':
RE(bp.scan([after_v_slit], pgm.energy, 790, 810, epu.energy, 790 - 6, 810 - 6, num=11))
