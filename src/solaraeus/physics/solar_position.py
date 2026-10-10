"""
Deterministic solar position calculation using NOAA astronomical formulas.
Calculates solar altitude, azimuth, and local Cartesian sun vectors.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Tuple
import numpy as np


@dataclass(frozen=True)
class SolarPosition:
    """Exact solar angles and directional unit vectors."""
    altitude_deg: float          # Solar elevation angle above horizon in degrees [-90, +90]
    azimuth_deg: float           # Solar azimuth in degrees [0, 360) clockwise from True North
    zenith_deg: float            # Solar zenith angle in degrees [0, 180]
    sun_vector: Tuple[float, float, float]  # Unit vector pointing TOWARDS sun (East, North, Up)
    is_daylight: bool            # True if altitude > 0.0

    @property
    def altitude_rad(self) -> float:
        return math.radians(self.altitude_deg)

    @property
    def azimuth_rad(self) -> float:
        return math.radians(self.azimuth_deg)


def calculate_julian_day(dt_utc: datetime) -> float:
    """Computes Julian Day from UTC datetime."""
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day + (dt_utc.hour + (dt_utc.minute + dt_utc.second / 60.0) / 60.0) / 24.0

    if month <= 2:
        year -= 1
        month += 12

    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5
    return jd


def calculate_solar_position(latitude_deg: float, longitude_deg: float,
                             dt_utc: datetime) -> SolarPosition:
    """
    Computes solar position for given geographical coordinates and UTC datetime
    using the NOAA solar position algorithm.
    """
    jd = calculate_julian_day(dt_utc)
    t = (jd - 2451545.0) / 36525.0  # Julian Century

    # Geometric Mean Longitude of the Sun (deg)
    l0 = (280.46646 + t * (36000.76983 + 0.0003032 * t)) % 360.0

    # Geometric Mean Anomaly of the Sun (deg)
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    m_rad = math.radians(m)

    # Eccentricity of Earth's orbit
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    # Sun Equation of the Center (deg)
    c = (math.sin(m_rad) * (1.914602 - t * (0.004817 + 0.000014 * t)) +
         math.sin(2.0 * m_rad) * (0.019993 - 0.000101 * t) +
         math.sin(3.0 * m_rad) * 0.000289)

    # Sun True Longitude and Anomaly (deg)
    sun_true_lon = l0 + c

    # Sun Apparent Longitude (deg)
    omega = 125.04 - 1934.136 * t
    lambda_deg = sun_true_lon - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    lambda_rad = math.radians(lambda_deg)

    # Mean Obliquity of the Ecliptic (deg)
    eps0 = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0
    eps = eps0 + 0.00256 * math.cos(math.radians(omega))
    eps_rad = math.radians(eps)

    # Solar Declination (deg)
    sin_delta = math.sin(eps_rad) * math.sin(lambda_rad)
    delta_rad = math.asin(sin_delta)

    # Equation of Time (minutes)
    y = math.tan(eps_rad / 2.0) ** 2
    l0_rad = math.radians(l0)
    eq_time = 4.0 * math.degrees(
        y * math.sin(2.0 * l0_rad) -
        2.0 * e * math.sin(m_rad) +
        4.0 * e * y * math.sin(m_rad) * math.cos(2.0 * l0_rad) -
        0.5 * (y ** 2) * math.sin(4.0 * l0_rad) -
        1.25 * (e ** 2) * math.sin(2.0 * m_rad)
    )

    # True Solar Time (minutes)
    time_offset = eq_time + 4.0 * longitude_deg
    utc_minutes = dt_utc.hour * 60.0 + dt_utc.minute + dt_utc.second / 60.0
    true_solar_time = (utc_minutes + time_offset) % 1440.0

    # Solar Hour Angle (deg)
    hour_angle_deg = (true_solar_time / 4.0) - 180.0
    if hour_angle_deg < -180.0:
        hour_angle_deg += 360.0
    hour_angle_rad = math.radians(hour_angle_deg)

    # Solar Zenith and Altitude (deg)
    lat_rad = math.radians(latitude_deg)
    cos_zenith = (math.sin(lat_rad) * math.sin(delta_rad) +
                  math.cos(lat_rad) * math.cos(delta_rad) * math.cos(hour_angle_rad))
    cos_zenith = max(-1.0, min(1.0, cos_zenith))
    zenith_rad = math.acos(cos_zenith)
    altitude_deg = 90.0 - math.degrees(zenith_rad)

    # Solar Azimuth Angle (clockwise from North, 0 to 360 deg)
    sin_zenith = math.sin(zenith_rad)
    if sin_zenith > 1e-6:
        cos_azimuth = ((math.sin(delta_rad) - math.sin(lat_rad) * math.cos(zenith_rad)) /
                       (math.cos(lat_rad) * sin_zenith))
        cos_azimuth = max(-1.0, min(1.0, cos_azimuth))
        azimuth_deg = math.degrees(math.acos(cos_azimuth))
        if hour_angle_deg > 0:
            azimuth_deg = (360.0 - azimuth_deg) % 360.0
    else:
        azimuth_deg = 180.0 if latitude_deg > 0 else 0.0

    # Unit vector pointing towards the sun: (East = +X, North = +Y, Up = +Z)
    alt_rad = math.radians(altitude_deg)
    az_rad = math.radians(azimuth_deg)

    cos_alt = math.cos(alt_rad)
    s_x = cos_alt * math.sin(az_rad)  # East component
    s_y = cos_alt * math.cos(az_rad)  # North component
    s_z = math.sin(alt_rad)          # Up component

    norm = math.hypot(s_x, s_y, s_z)
    sun_vec = (s_x / norm, s_y / norm, s_z / norm)

    return SolarPosition(
        altitude_deg=altitude_deg,
        azimuth_deg=azimuth_deg,
        zenith_deg=math.degrees(zenith_rad),
        sun_vector=sun_vec,
        is_daylight=(altitude_deg > 0.0)
    )
