"""
Astronomical Sun Model for SOLARAEUS.

Provides high-precision astronomical solar positioning and continuous solar path generation
for Bengaluru (12.9749° N, 77.6054° E, UTC+05:30).
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import trimesh

from urban_comfort.solar.solar_position import calculate_solar_position, SolarPosition


IST = timezone(timedelta(hours=5, minutes=30))


@dataclass
class DailySolarProfile:
    date_str: str
    latitude_deg: float
    longitude_deg: float
    sunrise_time_str: str
    solar_noon_time_str: str
    sunset_time_str: str
    day_length_hours: float
    max_altitude_deg: float
    solar_noon_azimuth_deg: float
    passes_north_of_zenith: bool


class SunModel:
    """Astronomical solar positioning engine."""

    def __init__(
        self,
        latitude_deg: float = 12.9749,
        longitude_deg: float = 77.6054,
    ):
        self.latitude = latitude_deg
        self.longitude = longitude_deg

    def compute_position(
        self,
        target_date: date,
        hour_decimal: float,
    ) -> SolarPosition:
        """
        Compute solar position for a local clock time (IST, decimal hours e.g. 14.5 for 14:30).
        """
        hours = int(hour_decimal)
        rem = (hour_decimal - hours) * 60.0
        minutes = int(rem)
        seconds = int((rem - minutes) * 60.0)

        dt_local = datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            hours,
            minutes,
            seconds,
            tzinfo=IST,
        )
        dt_utc = dt_local.astimezone(timezone.utc)
        return calculate_solar_position(self.latitude, self.longitude, dt_utc)

    def compute_daily_profile(self, target_date: date) -> DailySolarProfile:
        """Computes sunrise, solar noon, sunset, and zenith passage."""
        # Step through day at 1-minute intervals to find events
        times = np.linspace(5.0, 19.5, 871)
        altitudes = []
        azimuths = []

        for h in times:
            pos = self.compute_position(target_date, h)
            altitudes.append(pos.altitude_deg)
            azimuths.append(pos.azimuth_deg)

        altitudes = np.array(altitudes)
        azimuths = np.array(azimuths)

        # Sunrise: altitude crosses 0 upward
        daylight_mask = altitudes > 0.0
        if np.any(daylight_mask):
            idx_rise = np.where(daylight_mask)[0][0]
            idx_set = np.where(daylight_mask)[0][-1]
            idx_noon = np.argmax(altitudes)

            t_rise = times[idx_rise]
            t_set = times[idx_set]
            t_noon = times[idx_noon]
            max_alt = altitudes[idx_noon]
            noon_az = azimuths[idx_noon]

            def fmt_h(th):
                hh = int(th)
                mm = int((th - hh) * 60)
                return f"{hh:02d}:{mm:02d}"

            # Check if sun passes north of zenith (noon azimuth close to 0°/360°)
            passes_north = (noon_az < 45.0) or (noon_az > 315.0)

            return DailySolarProfile(
                date_str=target_date.isoformat(),
                latitude_deg=self.latitude,
                longitude_deg=self.longitude,
                sunrise_time_str=fmt_h(t_rise),
                solar_noon_time_str=fmt_h(t_noon),
                sunset_time_str=fmt_h(t_set),
                day_length_hours=float(t_set - t_rise),
                max_altitude_deg=float(max_alt),
                solar_noon_azimuth_deg=float(noon_az),
                passes_north_of_zenith=bool(passes_north),
            )
        else:
            return DailySolarProfile(
                date_str=target_date.isoformat(),
                latitude_deg=self.latitude,
                longitude_deg=self.longitude,
                sunrise_time_str="None",
                solar_noon_time_str="None",
                sunset_time_str="None",
                day_length_hours=0.0,
                max_altitude_deg=0.0,
                solar_noon_azimuth_deg=180.0,
                passes_north_of_zenith=False,
            )

    def generate_sun_path_csv(
        self, target_date: date, output_path: Path, step_hours: float = 0.25
    ) -> List[Dict[str, Any]]:
        """Generates continuous timeseries table of solar positions."""
        records = []
        hours = np.arange(5.5, 19.0 + step_hours / 2.0, step_hours)
        for h in hours:
            pos = self.compute_position(target_date, h)
            hh = int(h)
            mm = int((h - hh) * 60)
            time_str = f"{hh:02d}:{mm:02d}:00"
            rec = {
                "date": target_date.isoformat(),
                "time_ist": time_str,
                "hour_decimal": round(float(h), 3),
                "altitude_deg": round(pos.altitude_deg, 3),
                "azimuth_deg": round(pos.azimuth_deg, 3),
                "zenith_deg": round(pos.zenith_deg, 3),
                "is_daylight": pos.is_daylight,
                "sun_vec_east": round(pos.sun_vector[0], 5),
                "sun_vec_north": round(pos.sun_vector[1], 5),
                "sun_vec_up": round(pos.sun_vector[2], 5),
            }
            records.append(rec)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

        return records

    def generate_sun_path_glb(
        self,
        target_date: date,
        output_path: Path,
        centroid: Tuple[float, float, float] = (105.0, 70.0, 0.0),
        dome_radius: float = 180.0,
    ) -> trimesh.Scene:
        """Construct 3D visual solar arc curve and hourly markers as GLB."""
        scene = trimesh.Scene()
        hours = np.linspace(6.0, 18.5, 100)
        curve_pts = []

        for h in hours:
            pos = self.compute_position(target_date, h)
            if pos.altitude_deg > 0:
                # Local coords: X East, Y North, Z Up
                px = centroid[0] + dome_radius * pos.sun_vector[0]
                py = centroid[1] + dome_radius * pos.sun_vector[1]
                pz = centroid[2] + dome_radius * pos.sun_vector[2]
                curve_pts.append([px, py, pz])

        if len(curve_pts) > 1:
            # Create a path
            path = trimesh.load_path(np.array(curve_pts))
            scene.add_geometry(path, node_name="solar_arc")

        # Add hourly spheres along the path
        for h in [6.0, 9.0, 12.0, 14.5, 17.0, 18.0]:
            pos = self.compute_position(target_date, h)
            if pos.altitude_deg > 0:
                px = centroid[0] + dome_radius * pos.sun_vector[0]
                py = centroid[1] + dome_radius * pos.sun_vector[1]
                pz = centroid[2] + dome_radius * pos.sun_vector[2]
                sphere = trimesh.creation.icosphere(radius=3.5)
                sphere.apply_translation([px, py, pz])
                scene.add_geometry(sphere, node_name=f"sun_marker_{int(h*10)}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        glb_data = scene.export(file_type="glb")
        with open(output_path, "wb") as f:
            f.write(glb_data)

        return scene


# Global default sun model
sun_model = SunModel()
