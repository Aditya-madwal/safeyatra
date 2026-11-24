# SafeYatra – app mockups (for future reference)

Made on 24 Nov 2026 with `scripts/make_mockups.py`. The maps use our real data
(`output/`): real Chamoli roads coloured by computed risk, real landslide points,
rivers and hospitals, and real routes found with A*. Re-run the script after the
data changes (e.g. when GSI data is added) to refresh the pictures.

| Image | Screen / feature | Phase |
|---|---|---|
| 01_home_risk_map.png | Home: risk map of all Chamoli roads + network stats | MVP |
| 02_route_search.png | Choosing start / destination with place suggestions | MVP |
| 03_route_comparison_safety_slider.png | Safety slider + safest vs shortest route (Karnaprayag → Gopeshwar) | MVP |
| 04_route_risk_breakdown.png | Route details: distance, time, risk profile, dangerous stretches (Gopeshwar → Joshimath) | MVP |
| 05_hazard_layers.png | Layer toggles: landslides (NASA / news), rivers, hospitals | MVP |
| 06_road_segment_details.png | Click a road: its risk score and the reasons behind it | MVP |
| 07_weather_alerts.png | Rain warning + GSI alert; risk map on an example monsoon day | Phase 2 |
| 08_nearest_help.png | Hospitals, clinics, police, fuel along the route | Phase 3 |
| 09_report_blockage.png | User reports a landslide / blocked road | Phase 2 |
| 10_admin_panel.png | Admin verifies reports and manages road closures | Phase 2 |
| 11_mobile_view.png | Phone layout with bottom sheet | Phase 3 |

Note: 07 uses made-up rain numbers to show what a monsoon day would look like.
Report and admin data in 09–10 are example entries.
