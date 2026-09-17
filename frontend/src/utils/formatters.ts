export function formatTemp(celsius: number | null | undefined): string {
  if (celsius === null || celsius === undefined || isNaN(celsius)) return '—';
  return `${celsius.toFixed(1)} °C`;
}

export function formatPercent(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `${val.toFixed(1)}%`;
}

export function formatDistance(meters: number | null | undefined): string {
  if (meters === null || meters === undefined || isNaN(meters)) return '—';
  return `${meters.toFixed(1)} m`;
}

export function formatTime(utcString: string | null | undefined): string {
  if (!utcString) return '—';
  const timePart = utcString.split('T')[1];
  if (!timePart) return utcString;
  const [hh, mm] = timePart.split(':');
  const utcHour = parseInt(hh, 10);
  // EDT is UTC - 4 hours
  let localHour = (utcHour - 4 + 24) % 24;
  return `${localHour.toString().padStart(2, '0')}:${mm} EDT`;
}

export function formatCompass(azDeg: number | null | undefined): string {
  if (azDeg === null || azDeg === undefined || isNaN(azDeg)) return '—';
  const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
  const idx = Math.round(((azDeg % 360) / 22.5)) % 16;
  return `${azDeg.toFixed(1)}° (${directions[idx]})`;
}
