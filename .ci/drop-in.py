print(epu.energy.get())
epu.energy.set(250)

# HighR case:
pgm.grating_name.set("HighR")
RE(bp.scan([after_v_slit], pgm.energy, 240, 260, 21))

# HighE case:
pgm.grating_name.set("HighE")
epu.energy.set(800)
RE(bp.scan([after_v_slit], pgm.energy, 795, 805, 11))