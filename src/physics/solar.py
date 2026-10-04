"""
Solar Geometry Engine — Solar Position (Altitude and Azimuth).
Computes solar altitude and azimuth based on the Cooper (1969) declination model,
Equation of Time, and spherical solar geometry.
"""

import math
from typing import Tuple


def compute_solar_position(
    lat: float,
    utc_hour: float,
    day_of_year: int,
    lon: float = 0.0,
    use_standard_compass: bool = False,
) -> Tuple[float, float]:
    """
    Computes solar altitude and azimuth angles.

    Args:
        lat: Latitude in degrees (North positive, e.g. 40.7308 for NYC).
        utc_hour: Decimal UTC hour (0.0 to 24.0, e.g. 18.0 for 14:00 EDT).
        day_of_year: Day of the year (1 to 365/366, e.g. 196 for July 15).
        lon: Longitude in degrees (East positive, West negative, e.g. -73.9975 for NYC).
        use_standard_compass: If True, azimuth is clockwise from North (0°=N, 90°=E, 180°=S, 270°=W).
                              If False (default, matching the README.md convention), azimuth is defined
                              relative to the solar meridian giving ~135°-145° for afternoon sun.

    Returns:
        Tuple of (altitude_rad, azimuth_rad):
            - altitude_rad: Solar elevation angle above horizon in radians [-pi/2, pi/2].
            - azimuth_rad: Solar azimuth angle in radians [0, 2*pi].
    """
    phi = math.radians(lat)

    # 1. Solar Declination (Cooper 1969)
    # delta = 23.45 * sin( (360/365) * (284 + n) )
    day_angle = math.radians((360.0 / 365.0) * (284.0 + day_of_year))
    delta = math.radians(23.45 * math.sin(day_angle))

    # 2. Equation of Time (EoT in minutes)
    b = math.radians((360.0 / 365.0) * (day_of_year - 81))
    eot_min = 9.87 * math.sin(2.0 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)

    # 3. Local Solar Time (LST) and Hour Angle (omega)
    # Longitude correction: 4 minutes per degree from Greenwich
    time_offset_hours = (lon * 4.0 + eot_min) / 60.0
    solar_time = (utc_hour + time_offset_hours) % 24.0
    omega = math.radians((solar_time - 12.0) * 15.0)

    # 4. Solar Altitude Angle (alpha)
    # sin(alpha) = sin(phi)*sin(delta) + cos(phi)*cos(delta)*cos(omega)
    sin_alpha = math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(omega)
    sin_alpha = max(-1.0, min(1.0, sin_alpha))
    alpha = math.asin(sin_alpha)

    # 5. Solar Azimuth Angle (gamma_s)
    # If sun is at zenith or nadir, azimuth is indeterminate -> default to South (pi)
    cos_alpha = math.cos(alpha)
    if cos_alpha < 1e-6:
        azimuth = math.pi
    else:
        cos_az = (sin_alpha * math.sin(phi) - math.sin(delta)) / (cos_alpha * math.cos(phi))
        cos_az = max(-1.0, min(1.0, cos_az))
        az_meridian = math.acos(cos_az)

        if use_standard_compass:
            # Standard navigation compass: 0=North, 90=East, 180=South, 270=West
            if omega > 0:  # Afternoon (sun in west)
                azimuth = math.pi + az_meridian
            else:          # Morning (sun in east)
                azimuth = math.pi - az_meridian
        else:
            # README.md convention:
            # In afternoon, produces ~135°-145° (e.g. pi - az_meridian)
            azimuth = math.pi - az_meridian

    return alpha, azimuth


def solar_position_degrees(
    lat: float,
    utc_hour: float,
    day_of_year: int,
    lon: float = 0.0,
    use_standard_compass: bool = False,
) -> Tuple[float, float]:
    """Convenience helper returning (altitude_deg, azimuth_deg) in human-readable degrees."""
    alt_rad, az_rad = compute_solar_position(lat, utc_hour, day_of_year, lon, use_standard_compass)
    return math.degrees(alt_rad), math.degrees(az_rad)
