from psychrochart import PsychroChart

# Load default style:
chart_default = PsychroChart.create()
# customize anything
chart_default.limits.range_temp_c = (15.0, 35.0)
chart_default.limits.range_humidity_g_kg = (5, 25)
chart_default.config.saturation.linewidth = 1
chart_default.config.constant_wet_temp.color = "darkblue"
# plot
axes = chart_default.plot()
axes.get_figure()
# or store on disk
chart_default.save("my-custom-chart.svg")