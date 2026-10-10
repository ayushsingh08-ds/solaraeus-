"""Revise an existing data package. No simulation, external edits, or new measurements."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv, gzip, hashlib, json, math, os, shutil, zipfile
import numpy as np
import pyarrow.parquet as pq
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer, Geod, CRS

P = Path(os.environ['STRAWBERRY']) / 'default/projects/bengaluru-microclimate-pilot'
H = P / 'handoff_v2'
SESSION = Path(os.environ['STRAWBERRY']) / 'default/sessions/329d34f1-717f-440d-a0b1-49d789a694a1'
UTC = datetime.now(timezone.utc)
IST = UTC.astimezone(timezone(timedelta(hours=5, minutes=30)))
NOW = UTC.isoformat()
if H.exists():
    raise RuntimeError('Version directory already exists; preserve it and inspect before changing it.')
H.mkdir()
shutil.copytree(P/'data', H/'data')
shutil.copytree(P/'sources', H/'sources')
shutil.copy2(P/'site_inspection_map.png', H/'site_inspection_map.png')
shutil.copy2(P/'site_boundary.geojson', H/'site_boundary.geojson')
(H/'preparation').mkdir()
shutil.copy2(Path(__file__), H/'preparation'/Path(__file__).name)

operations = {}

def load(rel, root=H):
    return json.loads((root/rel).read_text(encoding='utf-8-sig'))

def dump(rel, obj, inputs=None, operation='Documented metadata or assumption revision'):
    f = H/rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    operations[rel] = {'operation':operation, 'inputs':inputs or [], 'processed_at_utc':NOW}

def read_csv(rel, root=H):
    with (root/rel).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write_csv(rel, rows, fields=None, inputs=None, operation='Static source extraction or documented derived table'):
    f = H/rel
    f.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0])
    with f.open('w', encoding='utf-8', newline='') as out:
        w = csv.DictWriter(out, fieldnames=fields, extrasaction='raise')
        w.writeheader()
        w.writerows(rows)
    operations[rel] = {'operation':operation, 'inputs':inputs or [], 'processed_at_utc':NOW}

def alias(old, new):
    shutil.copy2(H/old, H/new)
    operations[new] = {'operation':'Byte-identical handoff filename alias; no new download or content change', 'inputs':[old], 'processed_at_utc':NOW}

def text(rel, body):
    (H/rel).write_text(body, encoding='utf-8')
    operations[rel] = {'operation':'Human-readable handoff documentation assembled from preserved sources and explicit assumptions', 'inputs':[], 'processed_at_utc':NOW}

def sha(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()

def number(s):
    return None if s is None or s == '' else float(s)

# 1. The main reporting domain never changes. Context is a metric outward edge buffer.
TO_METRIC = Transformer.from_crs(4326, 32643, always_xy=True)
TO_WGS = Transformer.from_crs(32643, 4326, always_xy=True)
main_fc = load('site_boundary.geojson')
main = shape(main_fc['features'][0]['geometry'])
main_m = transform(TO_METRIC.transform, main)
context_fc = load('data/processed/shadow_context_boundary.geojson')
context = shape(context_fc['features'][0]['geometry'])
context_m = transform(TO_METRIC.transform, context)
expected = main_m.buffer(75.0, join_style=2)
assert expected.hausdorff_distance(context_m) < 0.001
core = load('data/processed/buildings_site.geojson')['features']
ctx = load('data/processed/buildings_shadow_context.geojson')['features']
assert len(core)==37 and len(ctx)==123
main_fc['features'][0]['properties'].update({
    'domain_role':'reported_pedestrian_results_boundary',
    'reported_results_must_be_inside_this_boundary':True,
    'shadow_context_file':'shadow_context_boundary.geojson'
})
dump('data/processed/site_boundary.geojson', main_fc, ['site_boundary.geojson'], 'Retain identical main polygon; add explicit reporting-domain metadata')
context_fc['features'][0]['properties'].update({
    'domain_role':'shadow_casting_geometry_selection_extent_only',
    'construction':'Transform main polygon to EPSG:32643; outward buffer 75.0 m with mitred/squared corners; transform back to EPSG:4326',
    'buffer_distance_measured_from':'Each main polygon edge, not the centre and not a 75 m radius',
    'corner_rule':'Squared/miter corners; diagonal corner reach may exceed 75 m',
    'buffer_reference_crs':'EPSG:32643',
    'main_boundary_file':'site_boundary.geojson',
    'results_reporting_boundary_expanded':False,
    'building_count_including_main':123,
    'geometry_rule':'Keep complete footprints intersecting this context; do not clip their roofs or walls'
})
dump('data/processed/shadow_context_boundary.geojson', context_fc, ['data/processed/site_boundary.geojson'], 'Verify existing geometry equals 75 m squared-corner UTM buffer; clarify its role')
domains = {
    'main_analysis_boundary':{'bbox_west_south_east_north':list(main.bounds),'file':'data/processed/site_boundary.geojson','role':'pedestrian reporting domain'},
    'shadow_context_boundary':{'bbox_west_south_east_north':list(context.bounds),'file':'data/processed/shadow_context_boundary.geojson','buffer_m':75.0,'metric_crs':'EPSG:32643','construction':'main polygon outward edge buffer, squared/miter corners','area_m2':context_m.area,'building_count_including_core':123,'context_only_building_count':86},
    'casting_geometry_rule':'Use all complete buildings intersecting the expanded context for shadow casting, after heights are reviewed. Do not clip geometry at either domain edge.',
    'pedestrian_reporting_mask':'Intersection of main analysis polygon and the proposed pedestrian-analysis area; report no outside receptors or context-only pedestrian statistics.',
    'height_policy':'All model heights remain null until researcher-approved. Unknown context heights must not be silently omitted or assigned defaults.',
    'adequacy':'75 m is a proposed acquisition buffer, not a proven shadow cutoff; perform shadow-reach and buffer-convergence checks after heights and solar geometry are available.',
    'coordinate_order':'GeoJSON longitude,latitude; metric geometry UTM easting,northing; always_xy=True',
    'simulation_engine_status':'No engine was inspected or run. These are handoff requirements, not claims that an existing engine implements them.'
}
dump('data/processed/analysis_domains.json', domains)
site = load('data/processed/site_selection.json')
site['study_boundary_file']='data/processed/site_boundary.geojson'
site['shadow_context'].update({'boundary_file':'data/processed/shadow_context_boundary.geojson','construction':domains['shadow_context_boundary']['construction'],'bbox_west_south_east_north':list(context.bounds),'results_reporting_expanded':False})
site['handoff_version']='2.0'
site['handoff_prepared_at_utc']=NOW
site['handoff_prepared_at_ist']=IST.isoformat()
dump('data/processed/site_selection.json', site)

# 2. Preserve parallel evidence streams, and never promote candidates to model heights.
old_review={r['building_id']:r for r in read_csv('data/processed/building_height_review.csv')}
old_context={r['building_id']:r for r in read_csv('data/processed/context_height_review.csv')}
ml={r['building_id']:r for r in read_csv('data/processed/estimated_building_heights.csv')}
review_fields=['map_label','building_id','name','longitude','latitude','footprint_area_m2','source_height_m','source_height_available_or_missing','source_height_classification','source_height_source','observed_height_m','observed_height_status','source_num_floors','floor_count_source','floor_count_review_status','proposed_height_from_floors_m','floor_height_classification','floor_height_inference_rule','google_2023_estimated_height_m','google_height_classification','google_height_source','google_ml_estimate_used_for_review','google_ml_estimate_used_in_model','google_height_valid_pixel_fraction','google_height_review_priority','height_available_or_missing','height_source_categories_available','confidence_or_review_status','quantitative_confidence','manual_estimate_height_m','verified_height_m','model_height_m','approved_height_classification','height_evidence_url_or_photo','manual_review_complete','reviewer','reviewed_at','source_datasets','source_record_ids']
review=[]
for f in core:
    bid=f.get('id') or f['properties']['id']
    old=old_review[bid]
    m=ml[bid]
    h=number(old.get('source_height_m'))
    floors=number(old.get('source_num_floors'))
    gh=number(m.get('estimated_height_m_median'))
    cats=[]
    if h is not None: cats.append('Overture-provided')
    if floors is not None: cats.append('floor-count-derived')
    if gh is not None: cats.append('Google/ML-estimated')
    review.append({
        'map_label':old['map_label'],'building_id':bid,'name':old['name'],'longitude':old['longitude'],'latitude':old['latitude'],'footprint_area_m2':old['footprint_area_m2'],
        'source_height_m':h,'source_height_available_or_missing':'available' if h is not None else 'missing','source_height_classification':'Overture-provided' if h is not None else 'unknown','source_height_source':'Overture 2026-09-23.1 source height field; source method not verified',
        'observed_height_m':None,'observed_height_status':'missing_not_measured_at_site','source_num_floors':int(floors) if floors is not None else None,
        'floor_count_source':('Overture 2026-09-23.1; '+old['source_datasets']+'; '+old['source_record_ids']) if floors is not None else 'unknown',
        'floor_count_review_status':'source_attribute_unverified' if floors is not None else 'missing',
        'proposed_height_from_floors_m':round(floors*3.2,3) if floors is not None else None,'floor_height_classification':'floor-count-derived' if floors is not None else 'unknown','floor_height_inference_rule':'source floors x ASSUMED 3.2 m floor-to-floor; unapproved' if floors is not None else '',
        'google_2023_estimated_height_m':gh,'google_height_classification':'Google/ML-estimated' if gh is not None else 'unknown','google_height_source':'Google Open Buildings 2.5D Temporal v1; 2023; footprint median; estimated_heights_metadata.json',
        'google_ml_estimate_used_for_review':gh is not None,'google_ml_estimate_used_in_model':False,'google_height_valid_pixel_fraction':m['valid_pixel_fraction'],'google_height_review_priority':m['review_priority'],
        'height_available_or_missing':'unapproved_candidates_only' if cats else 'missing','height_source_categories_available':'|'.join(cats) if cats else 'unknown',
        'confidence_or_review_status':'pending_manual_review_high_priority' if m['review_priority']=='high' else 'pending_manual_review_not_site_calibrated','quantitative_confidence':None,
        'manual_estimate_height_m':None,'verified_height_m':None,'model_height_m':None,'approved_height_classification':'unknown','height_evidence_url_or_photo':None,'manual_review_complete':False,'reviewer':None,'reviewed_at':None,
        'source_datasets':old['source_datasets'],'source_record_ids':old['source_record_ids']
    })
write_csv('data/processed/building_height_review.csv',review,review_fields,['data/processed/buildings_site.geojson','data/processed/estimated_building_heights.csv'],'Join all 37 existing records to separate source, inferred, ML and approval fields; no promotion or missing-height filling')
ctx_review=[]
for f in ctx:
    bid=f.get('id') or f['properties']['id']
    a=old_context[bid]
    m=ml[bid]
    floors=number(a.get('source_num_floors'))
    ctx_review.append({**a,'proposed_height_from_floors_m':round(floors*3.2,3) if floors is not None else None,'floor_height_classification':'floor-count-derived' if floors is not None else 'unknown','google_height_classification':'Google/ML-estimated' if number(m.get('estimated_height_m_median')) is not None else 'unknown','model_height_m':None,'google_ml_estimate_used_in_model':False,'manual_review_complete':False,'confidence_or_review_status':'pending_manual_review_not_site_calibrated'})
write_csv('data/processed/context_height_review.csv',ctx_review,inputs=['data/processed/buildings_shadow_context.geojson','data/processed/estimated_building_heights.csv'])
height_schema={
    'categories':['observed','Overture-provided','floor-count-derived','Google/ML-estimated','manual estimate','unknown'],
    'categories_are_separate_evidence_types_not_a_quality_ranking':True,
    'source_vs_measurement':'Overture-provided identifies provenance; it does not imply surveyed measurement. Floor counts are source tags, not verified metre heights.',
    'google_use_fields':'used_for_review means a separate ML candidate is included; used_in_model is false for every building.',
    'null_contract':'Blank CSV numeric/evidence fields mean missing, not zero. JSON uses null.',
    'confidence':'No site-calibrated statistical confidence is available. Presence-mask coverage is not probability/confidence; P10/P90 are spatial prediction summaries, not uncertainty bounds.',
    'approval_fields':'Researcher must record accepted height, source category, evidence, reviewer and review date before model_height_m becomes non-null.',
    'core_counts':{'buildings':37,'source_metre_heights':sum(r['source_height_m'] is not None for r in review),'floor_counts':sum(r['source_num_floors'] is not None for r in review),'ml_candidates':sum(r['google_2023_estimated_height_m'] is not None for r in review),'observed_heights':0,'approved_model_heights':0},
    'no_ml_estimate_labels':[r['map_label'] for r in review if r['google_2023_estimated_height_m'] is None],
    'high_priority_ml_review_labels':[r['map_label'] for r in review if r['google_height_review_priority']=='high']
}
dump('data/processed/building_height_review_schema.json',height_schema)

# Canonical requested names, with native originals preserved.
raw_parquet='data/raw/buildings/overture_building_context_original.parquet'
table=pq.read_table(H/raw_parquet)
geo_metadata=(table.schema.metadata or {}).get(b'geo')
canonical='data/raw/buildings/overture_buildings_2026-09-23.1.geoparquet'
if geo_metadata:
    json.loads(geo_metadata)
    alias(raw_parquet,canonical)
    geoparquet_note='Existing GeoParquet metadata preserved; canonical filename is a byte-identical alias.'
else:
    meta=dict(table.schema.metadata or {})
    meta[b'geo']=json.dumps({'version':'1.1.0','primary_column':'geometry','columns':{'geometry':{'encoding':'WKB','geometry_types':['Polygon','MultiPolygon'],'crs':CRS.from_epsg(4326).to_json_dict(),'edges':'planar'}}}).encode()
    pq.write_table(table.replace_schema_metadata(meta),H/canonical,compression='zstd')
    operations[canonical]={'operation':'Add explicit GeoParquet WKB/CRS metadata; retain every source row and value; preserve original acquisition Parquet separately','inputs':[raw_parquet],'processed_at_utc':NOW}
    geoparquet_note='Canonical GeoParquet adds CRS/WKB metadata; original acquisition Parquet is separately preserved.'
alias('data/raw/buildings/overture_building_context_original.geojson','data/raw/buildings/overture_buildings_raw.geojson')
raw_features=load('data/raw/buildings/overture_building_context_original.geojson')['features']
floor_rows=[]
for f in raw_features:
    props=f['properties']
    bid=f.get('id') or props['id']
    sources=props.get('sources') or []
    n=props.get('num_floors')
    floor_rows.append({'building_id':bid,'source_num_floors':n,'classification':'Overture-provided_source_attribute_not_manually_verified' if n is not None else 'unknown','overture_release':'2026-09-23.1','source_datasets':'|'.join(s.get('dataset','') for s in sources),'source_record_ids':'|'.join(s.get('record_id') or '' for s in sources),'in_main_analysis':bid in old_review})
write_csv('data/raw/buildings/floor_counts.csv',floor_rows,inputs=['data/raw/buildings/overture_building_context_original.geojson'],operation='Extract floor-count attributes for all 227 acquired footprint records; generated table, not a vendor-original CSV')
alias('data/processed/estimated_building_heights.csv','data/raw/buildings/google_ml_height_estimates.csv')
operations['data/raw/buildings/google_ml_height_estimates.csv']['operation']='Byte-identical copy of locally generated 123-footprint raster-summary CSV; not a vendor-original CSV; raster original window is separately preserved'

# 3. Lossless native point-grid format conversion, not a newly downloaded TIFF.
terrain=load('data/processed/terrain_metadata.json')
original_hgt='data/raw/terrain/N12E077.hgt.gz'
with gzip.open(H/original_hgt,'rb') as f:
    arr=np.frombuffer(f.read(),dtype='>i2').reshape(3601,3601).astype(np.int16)
step=1.0/3600.0
native_transform=from_origin(77-step/2,13+step/2,step,step)
tif='data/raw/terrain/elevation_original.tif'
with rasterio.open(H/tif,'w',driver='GTiff',height=3601,width=3601,count=1,dtype='int16',crs='EPSG:4326',transform=native_transform,nodata=-32768,compress='deflate',predictor=2,tiled=True) as ds:
    ds.write(arr,1)
    ds.update_tags(AREA_OR_POINT='Point',VERTICAL_DATUM='EGM96 orthometric',ELEVATION_UNITS='metres',SOURCE_ORIGINAL='N12E077.hgt.gz',PROCESSING='Lossless format conversion only; no resampling or vertical transformation')
operations[tif]={'operation':'Decompress original HGT; lossless signed-int16 GeoTIFF format conversion with point-grid georeferencing; no resampling, interpolation, clipping or vertical datum transformation','inputs':[original_hgt],'processed_at_utc':NOW}
terrain.update({
    'dataset_name':terrain['dataset'],'units':'metres','vertical_datum':'EGM96 orthometric','pixel_resolution':{'angular_degrees':step,'arcseconds':1.0,'approximate_metres_at_site':terrain['resolution_m_at_site']},'nodata_value':-32768,
    'elevation_product_classification':'composite_elevation_DEM_not_certified_bare_earth',
    'represents':'Composite Skadi elevation product. SRTM/radar-derived elevations are expected here but contributing images are not independently traced. Building/vegetation signals and merging artifacts may be present; do not label as surveyed bare-earth DTM or building roof heights.',
    'original_provider_format':'gzip-compressed SRTM-style HGT signed int16 big-endian point grid',
    'original_download_filename':'N12E077.hgt.gz','original_download_file':original_hgt,'original_download_sha256':sha(H/original_hgt),
    'requested_tiff_filename':tif,'requested_tiff_sha256':sha(H/tif),
    'requested_filename_warning':'elevation_original.tif is a lossless conversion of the preserved native HGT, not an original provider-delivered TIFF.',
    'native_sample_grid':'Point samples: first centre (77 E,13 N), last centre (78 E,12 N), 3601 x 3601 including shared tile edges. GeoTIFF pixel-corner transform is half a sample outside centres.',
    'initial_engine_use':'Metadata, extent and coarse elevation validation only. Do not modify a flat-ground mesh or use DEM-minus-roof building heights.',
    'flat_ground_model':{'enabled_as_proposal':True,'ground_z_m':0.0,'reference':'model-relative, not an absolute orthometric altitude','researcher_acceptance':None},
    'source_morphology_or_slope_verified':False,'no_horizontal_resampling':True,'no_vertical_transformation':True
})
dump('data/raw/terrain/elevation_metadata.json',terrain,[original_hgt,tif])
dump('data/processed/terrain_metadata.json',terrain,[original_hgt,tif])

# 4. Off-site station observations plus derived RH, separate from regional solar.
forcing_description='Bengaluru City station observations applied as spatially uniform forcing at the Church Street site.'
weather=load('data/processed/weather_forcing_metadata.json')
selected=load('data/processed/weather_selected_observation.json')
weather.update({
    'forcing_description':forcing_description,'spatial_application':'spatially_uniform_external_forcing_not_site_microclimate_measurement',
    'station_timestamp_original':selected['DATE'],'station_timestamp_time_standard':'UTC; the original DATE field has no timezone suffix, but ISD observation timestamps use UTC',
    'station_timestamp_not_local_time':True,
    'time_conversion':{'source_utc':'2024-04-15T09:00:00Z','offset_hours':5.5,'local_ist':'2024-04-15T14:30:00+05:30','timezone':'Asia/Kolkata','daylight_saving_applied':False},
    'variable_classification':[
        {'variable':'air_temperature','value':35.0,'units':'degC','classification':'Observed off-site'},
        {'variable':'dew_point','value':8.5,'units':'degC','classification':'Observed off-site'},
        {'variable':'relative_humidity','value':19.729121965807092,'units':'percent','classification':'Derived from observations'},
        {'variable':'wind_speed','value':1.5,'units':'m/s','classification':'Observed off-site'},
        {'variable':'wind_direction','value':90.0,'units':'degrees clockwise from true north, direction from','classification':'Observed off-site','interpretation':'from east'},
        {'variable':'solar_radiation','value':None,'classification':'Regional satellite/model estimate','values_file':'data/raw/weather/solar_estimates.csv','not_an_on_site_observation':True}
    ],
    'timestep_contract':'One station-observation instant, not a continuous hourly transient forcing series; original station reports on this day are three-hourly.'
})
weather['license']={
    'NOAA':{'license':'No separate record-specific SPDX license identified for the externally contributed international station observations','policy_url':'https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf','policy_scope':'NOAA/Federal-produced data are public-domain; externally contributed records are not automatically proven CC0 by this policy','attribution':'NOAA/NCEI Integrated Surface Database and originating station/provider; do not imply NOAA endorsement','redistribution_terms_status':'Record-specific license clarification remains open before public redistribution'},
    'NASA_POWER':{'license':'CC-BY-4.0 as listed for NASA POWER by the NASA-managed AWS Open Data Registry; original point API response contains no separate SPDX label','license_evidence_url':'https://registry.opendata.aws/nasa-power/','attribution_guide_url':'https://power.larc.nasa.gov/docs/referencing/','attribution':'The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center\'s Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division. POWER Hourly API v2.10.2, accessed 2026-10-06 UTC / 2026-10-07 IST; source CERES SYN1deg.','scope_note':'Registry license listing retained as evidence; do not claim the original API embeds license metadata.'}
}
dump('data/processed/weather_forcing_metadata.json',weather)
forcing=read_csv('data/processed/weather_forcing.csv')
assert len(forcing)==1
forcing[0].update({'forcing_description':forcing_description,'station_latitude':weather['station']['latitude'],'station_longitude':weather['station']['longitude'],'station_distance_km_geodesic':weather['station']['site_center_distance_km_geodesic'],'station_timestamp_time_standard':'UTC','local_timezone':'Asia/Kolkata','utc_offset_hours':5.5,'air_temperature_classification':'Observed off-site','dew_point_classification':'Observed off-site','relative_humidity_classification':'Derived from observations','wind_speed_classification':'Observed off-site','wind_direction_classification':'Observed off-site','solar_radiation_classification':'Regional satellite/model estimate','forcing_review_status':'pending_solar_interval_alignment_and_researcher_acceptance'})
write_csv('data/processed/weather_forcing.csv',forcing,inputs=['data/raw/weather/noaa_43295099999_2024_original.csv','data/raw/weather/nasa_power_solar_20240415_original.json'],operation='Retain one-row forcing values; add explicit observation/derived/estimate, station and timezone classification fields')
alias('data/raw/weather/noaa_43295099999_2024_original.csv','data/raw/weather/bengaluru_station_observations.csv')
solar=load('data/raw/weather/nasa_power_solar_20240415_original.json')
parameters=solar['properties']['parameter']
solar_rows=[]
for label in sorted(parameters['ALLSKY_SFC_SW_DWN']):
    vals=[parameters[k].get(label) for k in ['ALLSKY_SFC_SW_DWN','ALLSKY_SFC_SW_DNI','ALLSKY_SFC_SW_DIFF']]
    vals=[None if v==-999 else v for v in vals]
    solar_rows.append({'provider_hour_label_utc':label,'time_standard':'UTC','energy_period_hours':1.0,'global_horizontal_energy_Wh_m2':vals[0],'direct_normal_energy_Wh_m2':vals[1],'diffuse_horizontal_energy_Wh_m2':vals[2],'global_horizontal_mean_W_m2':vals[0],'direct_normal_mean_W_m2':vals[1],'diffuse_horizontal_mean_W_m2':vals[2],'classification':'Regional satellite/model estimate','source':'NASA POWER / CERES SYN1deg','api_version':'v2.10.2','interval_start_utc':None,'interval_end_utc':None,'interval_status':'provider_hour_label_preserved_start_end_convention_unverified','not_instantaneous_irradiance':True})
write_csv('data/raw/weather/solar_estimates.csv',solar_rows,inputs=['data/raw/weather/nasa_power_solar_20240415_original.json'],operation='Extract all 24 provider hourly labels and GHI/DNI/DHI energies; mean W/m2 equals Wh/m2 divided by 1 hour; no interval endpoints guessed; generated table, not vendor-original CSV')

# 5. Exact proposed panel; no posts, measured-material claim, or physical authorization.
panel=load('data/processed/intervention_definition.json')
ll=panel['modified_geometry']['geometry']['coordinates'][0]
xy=panel['modified_geometry_local']['geometry']['coordinates'][0]
dx=xy[0][0]-xy[1][0]
dy=xy[0][1]-xy[1][1]
grid=(math.degrees(math.atan2(dx,dy))+360)%360
azimuth,_,_=Geod(ellps='WGS84').inv(*ll[1],*ll[0])
true=(azimuth+360)%360
panel.update({
    'schema_version':'2.0','type':'overhead_shade_panel','length_m':6.0,'width_m':3.0,'underside_height_m':3.5,'thickness_m':0.1,'top_height_m':3.6,
    'orientation_deg':true,'orientation_reference':'clockwise from true north, bearing of long axis; reciprocal bearing defines the same rectangle',
    'orientation_grid_north_deg':grid,'orientation_grid_reference':'clockwise from EPSG:32643 UTM grid north',
    'location':{'crs':'EPSG:4326','coordinate_order':'longitude,latitude','center':panel['candidate_center'],'corners':ll[:-1],'complete_polygon':panel['modified_geometry']['geometry'],'metric_geometry':panel['modified_geometry_local'],'ground_reference':'assumed flat model-relative z=0'},
    'material':{'id':'SHADE_PANEL_ASSUMED_001','description':'Generic opaque solid rectangular panel; no specific construction material or structural design inferred','albedo':0.6,'emissivity':0.9,'surface_temperature_assumption_c':35.0,'value_status':'assumed_not_measured','surface_temperature_status':'initial_condition_only_not_observed_or_equilibrated'},
    'opaque_or_transmissive':'opaque','opacity':1.0,'shortwave_transmissivity':0.0,'supporting_posts_included':False,'supporting_posts_reason':'Omitted from the first geometric comparison; not a claim that a physical panel can stand without supports.',
    'intervention_status':'proposed','researcher_approval':None,'physical_installation_authorized':False,
    'geometry_dimension_reference':'6 x 3 m dimensions are defined in UTM metre coordinates. The corresponding WGS84 geodesic edge lengths differ slightly by projection scale.',
    'orientation_note':'Coordinates are authoritative; distinguish true-north azimuth from UTM-grid rotation in any later mesh engine.'
})
dump('data/processed/intervention_definition.json',panel,inputs=['data/processed/intervention_geometry.geojson'],operation='Retain candidate polygon; compute numeric true/grid bearings; expose exact proposed dimensions, opacity, materials and omitted-post policy')

# 6. Dataset-level licenses plus explicit per-file provenance and immutable original hashes.
acq_b=load('sources/overture_building_acquisition.json')
acq_r=load('sources/overture_segment_acquisition.json')
acq_t=load('sources/terrain_download.json')
acq_n=load('sources/noaa_city_2024_download.json')
acq_s=load('sources/nasa_power_solar_download.json')
acq_hist=load('sources/isd_stations_download.json')
height_meta=load('data/processed/estimated_heights_metadata.json')
policy_review={
    'checked_at_utc':NOW,'checked_at_ist':IST.isoformat(),
    'method':'Three policy pages reached via source extraction; summaries below are review notes, not provider-original downloads.',
    'policies':[
        {'url':weather['license']['NOAA']['policy_url'],'finding':'NOAA/Federal-produced data are open/public-domain; the policy encourages CC0 for external records but does not automatically prove every international station record is CC0.'},
        {'url':'https://power.larc.nasa.gov/docs/referencing/','finding':'Retain the POWER reference statement, service/version and access date. Publication/redistribution notifications are requested; none were sent.'},
        {'url':'https://registry.opendata.aws/nasa-power/','finding':'NASA-managed registry lists CC-BY-4.0 and requests NASA POWER citation. Preserve this scope and do not invent an in-file SPDX label.'}
    ]
}
dump('sources/licensing_review_v2.json',policy_review)


def dataset(key,name,url,download,version,license_,attribution,originals,processing,extra=None):
    date=datetime.fromisoformat(download.replace('Z','+00:00')) if download else None
    d={'dataset_id':key,'dataset_name':name,'source_url':url,'downloaded_at_utc':download,'download_date_utc':date.date().isoformat() if date else None,'download_date_ist':date.astimezone(timezone(timedelta(hours=5,minutes=30))).date().isoformat() if date else None,'dataset_version':version,'license':license_,'attribution_requirement':attribution,'original_files':[{'path':rel,'original_filename':Path(rel).name,'sha256':sha(H/rel),'bytes':(H/rel).stat().st_size} for rel in originals],'processing_operation':processing}
    if extra:d.update(extra)
    return d

DATASETS=[
 dataset('overture_buildings','Overture Maps buildings bounded acquisition','https://stac.overturemaps.org/2026-09-23.1/catalog.json',acq_b['retrieved_at_utc'],'2026-09-23.1','ODbL-1.0','Overture Maps Foundation plus underlying OpenStreetMap, Google Open Buildings and Microsoft ML Buildings; retain source-record license and attribution fields',[raw_parquet,'data/raw/buildings/overture_building_context_original.geojson'],'Original acquisition: HTTPS Parquet ranges plus bbox row selection yielding 227 whole geometries; core/context selected by intersection, not clipping. Canonical aliases, source-floor extraction and separate ML joins in v2.',{'provider_original_assets':[{'source_url':r['url'],'provider_original_filename':r['url'].split('/')[-1],'etag':r['etag'],'last_modified':r['source_last_modified']} for r in acq_b['files']],'bounded_acquisition_not_complete_provider_shard':True,'horizontal_crs':'EPSG:4326'}),
 dataset('overture_roads','Overture Maps transportation bounded acquisition','https://stac.overturemaps.org/2026-09-23.1/catalog.json',acq_r['retrieved_at_utc'],'2026-09-23.1','ODbL-1.0','Overture Maps Foundation and underlying OpenStreetMap attribution',['data/raw/buildings/overture_segment_context_original.parquet','data/raw/buildings/overture_segment_context_original.geojson'],'159 bounded road records retained; Church Street centreline extracted; proposed receptor envelope and panel placement are geometry-derived assumptions.',{'provider_original_assets':[{'source_url':r['url'],'provider_original_filename':r['url'].split('/')[-1],'etag':r['etag']} for r in acq_r['files']],'horizontal_crs':'EPSG:4326'}),
 dataset('google_ml_heights',height_meta['dataset'],height_meta['source_url'],height_meta['downloaded_at_utc'],'v1, imagery/year 2023','Dual CC-BY-4.0 / ODbL-1.0 per Google dataset documentation','Google Research / Google Open Buildings 2.5D Temporal Dataset; retain compatible original-source notices',['data/raw/buildings/google_open_buildings_temporal_2023_context_window.tif'],'Native 3-band window export; footprint median using presence >=0.5 and height 0–100 m; no resampling; P10/P90 are spatial summaries, not confidence bounds. No model-height promotion.',{'source_documentation':height_meta['source_documentation'],'provider_original_filename':height_meta['source_url'].split('/')[-1],'source_year':2023,'horizontal_crs':'EPSG:32643','vertical_quantity':'ML-estimated building height above ground in metres','native_window_not_complete_provider_tile':True,'stored_resolution_m':0.5,'effective_resolution_m_approx':4}),
 dataset('skadi_elevation',terrain['dataset'],acq_t['url'],acq_t['retrieved_at_utc'],terrain['dataset_version'],terrain['license'],terrain['attribution'],[original_hgt],'Preserve original HGT; lossless GeoTIFF conversion only; native coarse point samples; metadata/validation use only, flat simulation ground remains proposed.',{'etag':acq_t['etag'],'source_last_modified':acq_t['last_modified'],'horizontal_crs':'EPSG:4326','vertical_datum':'EGM96 orthometric','license_source_file':'sources/terrain_attribution.md','underlying_source_trace_status':'Exact contributing images not independently traced'}),
 dataset('noaa_station_observations','NOAA/NCEI Integrated Surface Database Bengaluru City station',acq_n['url'],acq_n['retrieved_at_utc'],'2024 annual file; snapshot ETag '+acq_n.get('etag','unknown'),weather['license']['NOAA']['license'],weather['license']['NOAA']['attribution'],['data/raw/weather/noaa_43295099999_2024_original.csv'],'Byte-identical canonical alias; select 2024-04-15 09 UTC record, decode documented temperature/dewpoint/wind scales and QC; derive RH with Magnus equation.',{'station_id':'43295099999','license_policy':weather['license']['NOAA'],'source_last_modified':acq_n.get('last_modified')}),
 dataset('noaa_station_catalogue','NOAA ISD station catalogue',acq_hist.get('url','https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv'),acq_hist.get('retrieved_at_utc'),'Unversioned live catalogue snapshot pinned by file hash','Public NOAA/NCEI metadata; source file contains no separate SPDX label','NOAA/NCEI Integrated Surface Database station history',['data/raw/weather/isd-history.csv'],'Locate station identifiers; selected station coordinates verified against the observation record; WGS84 geodesic station-to-site distance.'),
 dataset('nasa_power_solar','NASA POWER / CERES SYN1deg regional solar estimates',acq_s['url'],acq_s['retrieved_at_utc'],'POWER Hourly API v2.10.2; requested 2024-04-15',weather['license']['NASA_POWER']['license'],weather['license']['NASA_POWER']['attribution'],['data/raw/weather/nasa_power_solar_20240415_original.json'],'Extract all 24 UTC-labelled GHI/DNI/DHI hourly energies and one candidate forcing label; mean W/m2 = Wh/m2 / 1 h; preserve unresolved interval endpoints.',{'license_evidence_url':'https://registry.opendata.aws/nasa-power/','citation_guide_url':'https://power.larc.nasa.gov/docs/referencing/','time_standard':'UTC','interval_alignment_verified':False})
]

counts=height_schema['core_counts']
blockers=[
 'Researcher review/acceptance of source floors and separate ML or replacement heights for all relevant core/context casters; all approved model heights remain null.',
 'Independent footprint registration, geometry completeness, outlier and edge-crossing checks.',
 'Field/imagery confirmation of the proposed panel location, walkway, existing trees/awnings/canopies and clearances.',
 'NASA POWER hourly interval convention and temporal averaging alignment before solar use.',
 'Researcher acceptance or replacement of assumed materials, initial temperatures, flat ground and simplified unmapped-vegetation baseline.',
 'Shadow-reach and context-boundary convergence check after heights and solar geometry are known.',
 'Record researcher sign-off before simulator coding.'
]
dump('data/processed/package_status.json',{'schema_version':'2.0','handoff_version':'2.0','prepared_at_utc':NOW,'prepared_at_ist':IST.isoformat(),'status':'REVIEW_DRAFT_NOT_READY_FOR_SIMULATION_CODING','all_requested_handoff_fields_populated_or_explicitly_missing':True,'simulation_coding_started':False,'simulation_engine_inspected':False,'researcher_manual_signoff':None,'building_height_counts':counts,'blocking_items':blockers,'public_redistribution_note':'NOAA international-station record-specific license clarification remains open; no public publishing or sending was performed.'})

CHECKLIST=f'''# Manual review checklist — Bengaluru Church Street handoff v2\n\nPrepared {IST.isoformat()}. Data preparation is not manual sign-off.\n\n- [ ] Confirm the unchanged main reporting boundary and 75 m squared-corner UTM shadow-context boundary. Keep all reported pedestrian receptors inside the main boundary.\n- [ ] Review all 37 rows in `processed/building_height_review.csv`; keep observed, source-provided, floor-derived, ML and manual-estimate evidence separate. Record accepted height, source category, evidence, reviewer and date.\n- [ ] Resolve absent ML estimates for B19, B23, B32 and B36; B19/B36 have unverified two-floor tags, B23/B32 have no floor count. No default height is assigned.\n- [ ] Prioritise B02, B03, B17, B19, B23, B31, B32, B36 and B37; review tall Barton Centre B10 and small-footprint B27 as well. Automated priority is not calibrated confidence.\n- [ ] Review all 123 context-caster records, including 86 outside the main selection. Unknown context heights may affect main-boundary shadows.\n- [ ] Check footprint alignment/completeness against independent imagery or field evidence. Inspect edge-crossing geometry, trees, awnings and existing canopy shadows.\n- [ ] Accept elevation only as coarse DEM metadata/validation; it is not certified bare earth, roof data or local surveyed terrain. Flat model-relative z=0 remains an assumption.\n- [ ] Confirm off-site station forcing, 09:00 UTC = 14:30 IST, derived RH and unknown wind-instrument height. Do not call it on-site weather.\n- [ ] Resolve the solar provider hourly start/end convention and averaging before aligning solar fluxes to the station instant.\n- [ ] Accept/correct the exact panel coordinates, true/grid orientation, 0.10 m thickness, opaque material, assumed albedo/emissivity/initial temperature and omitted posts.\n- [ ] Check actual walkway and clearances. This panel is a hypothetical simulation object, not an approved physical installation.\n- [ ] Accept or replace each material and initial-temperature assumption; determine a defensible baseline vegetation policy.\n- [ ] Verify 75 m shadow-context adequacy using shadow reach and expanded-buffer sensitivity after heights are known.\n- [ ] Confirm record-specific NOAA station redistribution terms before public redistribution; retain all dataset attributions.\n- [ ] Sign below only when the manual package is genuinely accepted.\n\nResearcher: __________________\nReviewed date/time and timezone: __________________\nEvidence/changes: __________________\nReady for simulation coding: YES / NO (currently NO)\n'''
text('data/manual_checklist.md',CHECKLIST)
text('manual_completion_checklist.md',CHECKLIST)
quality=(P/'data/data_quality_report.md').read_text(encoding='utf-8')
quality += '''\n\n## Handoff v2 clarification and approval status\n\n- Main boundary geometry unchanged; the 75 m context is the outward UTM edge buffer with squared/miter corners, not a 75 m radius. Only main-boundary pedestrian receptors contribute reported results.\n- 37 complete height-review rows keep source, floor-derived, Google/ML and observed evidence separate. All 37 source metre heights are missing; 17 floor counts and 33 ML candidates exist, with zero measured or approved model heights. Four absent ML candidates do not necessarily mean four totally evidence-free buildings: B19/B36 have floor tags.\n- A generated Google ML CSV or floor-count CSV under `raw/` is a handoff table, not a vendor-original download. Original GeoParquet/GeoJSON, raster window and acquisition records are retained.\n- The requested terrain TIFF is a lossless conversion of preserved native HGT, not an original provider TIFF. Point-sample centres, pixel transform, EGM96 datum, metres, NoData and composite-DEM status are explicit. Use it for validation/metadata only.\n- Weather is Bengaluru City station observations applied as spatially uniform forcing, with derived RH and separate regional solar estimates. UTC source timestamps and IST conversion are explicit; solar interval alignment remains open.\n- The panel is precisely specified but proposed, opaque and without posts; coordinates and true/grid bearings are distinct. Location, permissions and measured material properties are not established.\n- Automated checks and this file do not constitute field inspection, researcher acceptance, local thermal validation or a simulator result. All approval gates remain open.\n'''
text('data/data_quality_report.md',quality)

README=f'''# Bengaluru Church Street — revised manual data handoff v2\n\nStatus: **REVIEW DRAFT — NOT READY FOR SIMULATION CODING**. Prepared {IST.isoformat()} (IST). The original v1 package is preserved; this folder is a separate revision. No simulator was coded, inspected or run, and no physical intervention or external write occurred.\n\n## 1. Main boundary versus shadow context\n\nMain analysis boundary: **77.6044–77.6064 E, 12.9743–12.9755 N** (approximately 217 × 133 m; 37 intersecting whole footprints).\n\nShadow context: transform that polygon to **EPSG:32643 UTM 43N**, expand every edge outward by **75.0 m**, with squared/miter corners, then return it to longitude/latitude. This is not a circle or a 75 m radius from the centre. Diagonal squared corners can be more than 75 m from an original corner.\n\nThe existing context geometry matches this construction to less than 1 mm. Its approximate bounding box is **{context.bounds[0]:.9f}–{context.bounds[2]:.9f} E, {context.bounds[1]:.9f}–{context.bounds[3]:.9f} N**, approximately 367 × 283 m (10.38 ha). It contains 123 intersecting whole footprints including the 37 main footprints; 86 are context-only. The GeoJSON polygon, not rounded bounding-box text, is authoritative.\n\nUse expanded-context buildings for shadow casting; **reported pedestrian results remain inside the unchanged main boundary**, intersected with the proposed pedestrian-analysis envelope. Preserve complete caster polygons; do not clip roofs/walls to either boundary. Buffer sufficiency is not yet proven. See `data/processed/analysis_domains.json`.\n\n## 2. Height review — 37 complete records, no fabricated approvals\n\n`data/processed/building_height_review.csv` has one row per B01–B37 and separate fields for source metre height, floor count, floor-derived proposal, Google/ML estimate, observed/manual/verified/model height, source labels, Google use, priority and reviewer evidence.\n\n| Evidence | Available | Classification/status |\n|---|---:|---|\n| Overture source metre height | 0/37 | missing; source provenance is not proof of measurement |\n| Source floor count | 17/37 | sourced tags, unverified |\n| Floor-count-derived proposal | 17/37 | floors × assumed 3.2 m; inferred, unapproved |\n| Google 2023 ML candidate | 33/37 | estimated, not measured, unapproved |\n| On-site observed / approved model height | 0/37 | missing; model heights stay null |\n\nGoogle estimates are used **for review only**, never as an approved model height. No ML candidate: **B19, B23, B32, B36**. B19/B36 have two-floor tags; B23/B32 have no floor tags. Nine automatic priority flags: **B02, B03, B17, B19, B23, B31, B32, B36, B37**. Also inspect tall B10 and small B27. Source-presence coverage is not calibrated confidence; P10/P90 are not confidence intervals. `context_height_review.csv` covers all 123 casters. Blank CSV values mean missing, not zero.\n\n## 3. Terrain metadata and use\n\nDataset: Mapzen/Tilezen Skadi tile N12E077. Horizontal CRS **EPSG:4326**; vertical datum **EGM96 orthometric**; units **metres**; NoData **−32768**; native sampling **1 arcsecond**, roughly 30 m. Composite elevation DEM, **not certified bare-earth DTM**, surveyed roof elevations or building heights. Exact contributing source images have not been independently traced.\n\nThe actual original download is `N12E077.hgt.gz` and is preserved. `elevation_original.tif` is explicitly a **lossless format conversion**, not a provider-original TIFF. All 3601 × 3601 samples and native point centres are preserved, with no resampling or vertical transformation. See `data/raw/terrain/elevation_metadata.json`.\n\nInitial engine requirement: use the DEM for extent/elevation validation and metadata only. Do not modify a flat mesh. Proposed ground remains **model-relative z=0**, subject to researcher acceptance. No existing engine was inspected.\n\n## 4. Weather status and timestamps\n\n“**{forcing_description}**”\n\n| Variable | Value | Classification |\n|---|---:|---|\n| Air temperature | 35.0°C | Observed off-site |\n| Dew point | 8.5°C | Observed off-site |\n| Relative humidity | 19.73% | Derived from observations (Magnus equation) |\n| Wind speed | 1.5 m/s | Observed off-site |\n| Wind direction | 90°, from east | Observed off-site; direction from true north |\n| Solar radiation | See separately preserved GHI/DNI/DHI estimates | Regional satellite/model estimate |\n\nStation **43295099999 / WMO 43295**, Bengaluru City (not HAL Airport), at **12.9666666 N, 77.5833333 E**. Geodesic station-to-centre distance **2.561595 km**. The original timestamp `2024-04-15T09:00:00` is **UTC**, not IST; local time is **2024-04-15 14:30:00 IST**, UTC+05:30 with no daylight saving. Selected temperature/dewpoint/wind fields have QC code 1. Wind measurement height is unknown.\n\nThis is a one-instant forcing row, not an hourly transient series. Station reports on this date are three-hourly. Solar source label **2024041509 UTC** contains GHI **755.97**, DNI **728.31**, DHI **172.18 Wh/m²** over one hour; dividing by one hour gives the same numeric hourly-mean W/m² values. These are not instantaneous or site-measured radiation. Provider hourly start/end alignment remains unverified and both endpoints remain null. DNI is direct normal, not horizontal.\n\n## 5. Precisely defined proposed shade panel\n\n- Object CANOPY_001 / intervention BLR_SHADE_001; one `overhead_shade_panel`.\n- UTM-defined length **6.0 m**, width **3.0 m**, area **18 m²**, underside **3.5 m**, thickness **0.10 m**, top **3.6 m** above proposed flat ground.\n- Centre **77.60561994802289 E, 12.974866036977149 N**; all four exact corners and local-metre coordinates are in `intervention_definition.json`.\n- Long-axis bearing **{true:.9f}° clockwise from true north**, corresponding to **{grid:.9f}° clockwise from UTM grid north**. Do not confuse these references.\n- **Opaque**, shortwave transmissivity 0; **no supporting posts** in this geometric pilot. This is not structural advice or a claim a real unsupported panel can stand.\n- Generic panel material: assumed **albedo 0.60**, **emissivity 0.90**, initial surface temperature **35°C**. Not measured or equilibrated.\n- Status **proposed**, researcher approval null. Source-footprint clearance approximately 1.751 m; no mapped-footprint collision, but actual sidewalk, trees/awnings, existing shade, traffic clearance and permissions remain unverified.\n\nThe intervention JSON exposes the requested top-level fields without placeholder values. The baseline has no proposed new panel; `original_geometry:null` is not evidence that no real canopy exists.\n\n## 6. Provenance, licensing and honest raw-file roles\n\n`data/processed/provenance.json` records every dataset's source URL, original download timestamps (UTC and IST), version/snapshot, license evidence, attribution, original filenames and hashes, plus per-file processing lineage. File inventory excludes the manifest itself to avoid a self-hash cycle; `SHA256SUMS.txt` also hashes the manifest.\n\nOverture release **2026-09-23.1** is historical relative to this handoff's actual date **7 October 2026 IST**. The original downloads occurred **6 October UTC / 7 October IST**. Download dates are not observation, imagery, release or terrain-acquisition dates. Geometry 2026, height imagery 2023, forcing 2024 and older terrain are non-contemporaneous controlled-scenario inputs, not a verified historical reconstruction.\n\n- Overture: **ODbL-1.0**, with underlying source attribution retained.\n- Google temporal heights: **CC-BY-4.0 / ODbL-1.0** dual terms; Google Research attribution.\n- Terrain: provider/source attribution and SRTM/GMTED public-domain source terms; exact source mix not independently traced. Do not assign a new blanket license.\n- NASA POWER: **CC-BY-4.0 per the NASA-managed AWS registry listing**, with POWER service/version/access-date and CERES attribution. The original API file itself contains no SPDX label.\n- NOAA international station records: publicly accessible archive; **no record-specific SPDX license identified**. NOAA's policy distinguishes Federal-produced from externally contributed data, so universal CC0 is not invented. Clarify station-specific terms before public redistribution.\n\nRaw originals are preserved separately from requested aliases/exports. {geoparquet_note} `floor_counts.csv`, `google_ml_height_estimates.csv` and `solar_estimates.csv` are documented generated handoff tables, **not vendor-original CSV downloads**. The terrain TIFF is a format conversion.\n\n## Folder to hand off\n\n```text\ndata/\n  raw/\n    buildings/\n      overture_buildings_2026-09-23.1.geoparquet\n      overture_buildings_raw.geojson\n      floor_counts.csv\n      google_ml_height_estimates.csv\n      [preserved original acquisition exports and native ML window]\n    terrain/\n      elevation_original.tif\n      elevation_metadata.json\n      N12E077.hgt.gz\n    weather/\n      bengaluru_station_observations.csv\n      solar_estimates.csv\n      [original station/solar/catalogue files]\n  processed/\n    site_selection.json\n    site_boundary.geojson\n    shadow_context_boundary.geojson\n    analysis_domains.json\n    building_height_review.csv\n    building_height_review_schema.json\n    context_height_review.csv\n    weather_forcing.csv\n    weather_forcing_metadata.json\n    material_assumptions.json\n    intervention_definition.json\n    provenance.json\n    package_status.json\n    validation_report.json\n    [preserved geometry and supporting data]\n  data_quality_report.md\n  manual_checklist.md\n```\n\n## Acceptance before coding\n\nThe records and formats are populated; **manual height verification is not complete**. Follow `data/manual_checklist.md`. Researcher must validate geometry/heights and panel placement, settle solar intervals, accept assumptions, check buffer adequacy and sign off. All CSVs are **static data outputs**, with raw sources and methods preserved. Automated checks are not human approval.\n\n### Source references\n\n- https://stac.overturemaps.org/2026-09-23.1/catalog.json\n- https://sites.research.google/gr/open-buildings/temporal\n- https://github.com/tilezen/joerd/blob/master/docs/formats.md\n- https://github.com/tilezen/joerd/blob/master/docs/attribution.md\n- https://www.ncei.noaa.gov/data/global-hourly/access/2024/43295099999.csv\n- https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf\n- https://power.larc.nasa.gov/docs/referencing/\n- https://registry.opendata.aws/nasa-power/\n- https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf\n'''
text('README.md',README)

# Validate all consequential numerical and structural contracts before packaging.
checks=[]
def check(name,ok,details=None):
    if not ok:raise AssertionError(name)
    checks.append({'check':name,'passed':True,'details':details})

required=[
 'data/raw/buildings/overture_buildings_2026-09-23.1.geoparquet','data/raw/buildings/overture_buildings_raw.geojson','data/raw/buildings/floor_counts.csv','data/raw/buildings/google_ml_height_estimates.csv',
 'data/raw/terrain/elevation_original.tif','data/raw/terrain/elevation_metadata.json','data/raw/weather/bengaluru_station_observations.csv','data/raw/weather/solar_estimates.csv',
 'data/processed/site_selection.json','data/processed/site_boundary.geojson','data/processed/shadow_context_boundary.geojson','data/processed/building_height_review.csv','data/processed/weather_forcing.csv','data/processed/material_assumptions.json','data/processed/intervention_definition.json','data/data_quality_report.md','data/manual_checklist.md'
]
check('All 17 requested data files besides the separately generated provenance manifest exist',all((H/f).is_file() for f in required),{'count':len(required)})
check('Main reporting polygon unchanged and shadow context equals 75 m outward squared-corner metric buffer',shape(load('data/processed/site_boundary.geojson')['features'][0]['geometry']).equals(main) and expected.hausdorff_distance(context_m)<0.001)
raw_ids={f.get('id') or f['properties']['id'] for f in raw_features}
context_ids={f.get('id') or f['properties']['id'] for f in ctx}
expected_ids={f.get('id') or f['properties']['id'] for f in raw_features if shape(f['geometry']).intersects(context)}
check('37 main and 123 context complete footprints retained; context selection matches expanded area',len(core)==37 and context_ids==expected_ids and len(context_ids)==123 and set(old_review)<=context_ids)
new_reviews=read_csv('data/processed/building_height_review.csv')
check('All 37 labelled review rows preserve source/derived/ML distinction and unapproved model heights',len(new_reviews)==37 and len({r['building_id'] for r in new_reviews})==37 and all(r['model_height_m']=='' and r['manual_review_complete']=='False' and r['google_ml_estimate_used_in_model']=='False' for r in new_reviews))
check('Height evidence counts and flags verified',counts=={'buildings':37,'source_metre_heights':0,'floor_counts':17,'ml_candidates':33,'observed_heights':0,'approved_model_heights':0} and height_schema['no_ml_estimate_labels']==['B19','B23','B32','B36'] and height_schema['high_priority_ml_review_labels']==['B02','B03','B17','B19','B23','B31','B32','B36','B37'])
with rasterio.open(H/tif) as ds:
    converted=ds.read(1)
    first=rasterio.transform.xy(ds.transform,0,0)
    last=rasterio.transform.xy(ds.transform,3600,3600)
    check('Elevation TIFF retains every original HGT value, correct point centres, CRS, NoData and units',np.array_equal(arr,converted) and ds.crs.to_epsg()==4326 and ds.nodata==-32768 and abs(first[0]-77)<1e-9 and abs(first[1]-13)<1e-9 and abs(last[0]-78)<1e-9 and abs(last[1]-12)<1e-9 and ds.tags()['ELEVATION_UNITS']=='metres')
canonical_table=pq.read_table(H/canonical)
check('Canonical GeoParquet has valid geometry metadata and all 227 source rows/values',canonical_table.num_rows==227 and canonical_table.replace_schema_metadata(None).equals(table.replace_schema_metadata(None)) and 'geometry' in json.loads(canonical_table.schema.metadata[b'geo'])['columns'])
new_forcing=read_csv('data/processed/weather_forcing.csv')[0]
check('Weather classifications, UTC/IST conversion and unresolved solar endpoints remain explicit',new_forcing['forcing_description']==forcing_description and new_forcing['time_utc']=='2024-04-15T09:00:00Z' and new_forcing['time_local_ist']=='2024-04-15T14:30:00+05:30' and new_forcing['solar_interval_start_utc']=='' and new_forcing['solar_interval_end_utc']=='' and len(solar_rows)==24 and sha(H/'data/raw/weather/bengaluru_station_observations.csv')==sha(P/'data/raw/weather/noaa_43295099999_2024_original.csv'))
g=transform(TO_METRIC.transform,shape(panel['modified_geometry']['geometry']))
collisions=sum(g.intersects(transform(TO_METRIC.transform,shape(f['geometry']))) for f in core)
check('Exactly one opaque 18 m2 proposed no-posts panel; numerical azimuths and material assumptions explicit',panel['intervention_count']==1 and panel['intervention_status']=='proposed' and abs(g.area-18)<1e-6 and collisions==0 and panel['supporting_posts_included'] is False and panel['opaque_or_transmissive']=='opaque' and abs(true-103.02790844205673)<1e-6 and abs(grid-102.44250192828962)<1e-6)
check('Four material classes remain explicitly assumed',set(load('data/processed/material_assumptions.json')['classes'])=={'building_wall','building_roof','ground','pavement'} and all(c['albedo']['status']=='assumed' and c['emissivity']['status']=='assumed' for c in load('data/processed/material_assumptions.json')['classes'].values()))
original_inputs=[raw_parquet,'data/raw/buildings/overture_building_context_original.geojson','data/raw/buildings/overture_segment_context_original.parquet','data/raw/buildings/overture_segment_context_original.geojson','data/raw/buildings/google_open_buildings_temporal_2023_context_window.tif',original_hgt,'data/raw/weather/noaa_43295099999_2024_original.csv','data/raw/weather/nasa_power_solar_20240415_original.json','data/raw/weather/isd-history.csv']
check('All nine original data exports/downloads remain byte-identical',all(sha(H/f)==sha(P/f) for f in original_inputs))
dump('data/processed/validation_report.json',{'checked_at_utc':NOW,'checks':checks,'human_review_not_performed':True,'simulation_not_started':True,'status':'AUTOMATED_CHECKS_PASSED_MANUAL_SIGNOFF_STILL_REQUIRED'})

# File lineage supplements original v1 provenance; source records remain readable.
old_prov=load('data/processed/provenance.json',P)
old_inventory={r['path']:r for r in old_prov['all_files_except_provenance_self']}
original_to_dataset={rel:d['dataset_id'] for d in DATASETS for rel in [x['path'] for x in d['original_files']]}

def dataset_ids(rel):
    if rel in original_to_dataset:return [original_to_dataset[rel]]
    if 'floor_count' in rel or 'overture_building' in rel:return ['overture_buildings']
    if 'overture_segment' in rel or 'church_street_centerline' in rel:return ['overture_roads']
    if 'google' in rel or 'estimated_height' in rel:return ['google_ml_heights']
    if 'height_review' in rel or 'buildings_' in rel:return ['overture_buildings','google_ml_heights']
    if 'terrain' in rel or 'elevation' in rel:return ['skadi_elevation']
    if 'solar' in rel:return ['nasa_power_solar']
    if 'station' in rel or 'isd-history' in rel:return ['noaa_station_catalogue']
    if 'weather' in rel:return ['noaa_station_observations','noaa_station_catalogue','nasa_power_solar']
    return []

inventory=[]
for f in sorted(H.rglob('*')):
    if not f.is_file():continue
    rel=f.relative_to(H).as_posix()
    if rel in {'data/processed/provenance.json','SHA256SUMS.txt'}:continue
    inherited=old_inventory.get(rel,{}).get('provenance')
    identical=(P/rel).is_file() and sha(f)==sha(P/rel)
    op=operations.get(rel)
    if op is None:
        op={'operation':'Byte-identical preservation from original v1 acquisition/preparation package' if identical else 'Preserved supporting file; original acquisition/preparation record applies','inputs':[rel+' (v1 source package)'],'original_provenance':inherited}
    role='provider_original_or_original_bounded_acquisition_export' if rel in original_to_dataset else ('generated_raw_folder_handoff_table_or_format_conversion' if rel in operations and rel.startswith('data/raw/') else 'supporting_or_processed_file')
    inventory.append({'path':rel,'bytes':f.stat().st_size,'sha256':sha(f),'data_role':role,'dataset_ids':dataset_ids(rel),'processing':op})
provenance={
    'schema_version':'2.0','package_id':'bengaluru-church-street-manual-handoff-v2','prepared_at_utc':NOW,'prepared_at_ist':IST.isoformat(),'current_date_ist':IST.date().isoformat(),
    'base_package':'Preserved Bengaluru Church Street A1–A9 v1 project; a separate revision, not a simulation result',
    'datasets':DATASETS,'file_inventory_excluding_provenance_and_checksum_index':inventory,
    'checksum_policy':'SHA256SUMS.txt includes this manifest and every other handoff file; the manifest excludes itself and SHA256SUMS.txt to avoid recursive hashes.',
    'coordinate_transformation':old_prov['coordinate_transformation'],'analysis_domains':domains,'building_height_sources_and_approval':height_schema,
    'weather_station':weather['station'],'selected_instant_utc':weather['selected_instant_utc'],'selected_local_time':weather['selected_local_time'],'forcing_description':forcing_description,
    'manual_assumptions_files':['data/processed/material_assumptions.json','data/processed/intervention_definition.json','data/processed/terrain_metadata.json','data/processed/pedestrian_analysis_area.geojson'],
    'missing_data_handling':'Missing heights, measurements, approvals, confidence and solar interval endpoints remain null/blank. No blanket height or invented observation is substituted.',
    'intervention_description':{'id':panel['intervention_id'],'type':panel['type'],'count':1,'status':'proposed','posts_included':False,'researcher_approval':None},
    'license_caveats':['Specific external NOAA station SPDX license not established; no universal CC0 claim; clarify before public redistribution.','NASA CC-BY-4.0 evidence is a provider-managed registry listing, not an embedded point-API label.','Skadi exact contributing source images not independently traced; retain provider source/attribution evidence.'],
    'download_date_note':'Original downloads are 2026-10-06 UTC / 2026-10-07 IST; revision date is separately recorded; these are not source acquisition or observation dates.',
    'noncontemporaneous_inputs':'2026 geometry, 2023 ML imagery, 2024 forcing and older DEM are controlled-scenario inputs, not a validated historical reconstruction.',
    'researcher_manual_signoff':None,'status':'REVIEW_DRAFT_NOT_READY_FOR_SIMULATION_CODING'
}
dump('data/processed/provenance.json',provenance)
# Final integrity check includes the new manifest and all JSON, before packaging.
for f in H.rglob('*'):
    if f.suffix in {'.json','.geojson'}:json.loads(f.read_text(encoding='utf-8-sig'))
for r in inventory:
    assert sha(H/r['path'])==r['sha256']
files=sorted(f for f in H.rglob('*') if f.is_file() and f.name!='SHA256SUMS.txt')
(H/'SHA256SUMS.txt').write_text(''.join(f'{sha(f)}  {f.relative_to(H).as_posix()}\n' for f in files),encoding='utf-8')
archive=SESSION/'bengaluru_church_street_manual_handoff_v2.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for f in sorted(H.rglob('*')):
        if f.is_file():z.write(f,'bengaluru_church_street_manual_handoff_v2/'+f.relative_to(H).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    zip_count=len(z.namelist())
archive_hash=sha(archive)
(SESSION/'bengaluru_church_street_manual_handoff_v2.sha256.txt').write_text(f'{archive_hash}  {archive.name}\n',encoding='utf-8')
print(json.dumps({'handoff':'$STRAWBERRY/default/projects/bengaluru-microclimate-pilot/handoff_v2','archive':'$STRAWBERRY/default/sessions/329d34f1-717f-440d-a0b1-49d789a694a1/'+archive.name,'archive_bytes':archive.stat().st_size,'archive_sha256':archive_hash,'files':zip_count,'automated_checks_passed':len(checks),'height_counts':counts,'panel_true_north_orientation_deg':true,'panel_grid_north_orientation_deg':grid,'geoparquet_note':geoparquet_note,'status':provenance['status']},indent=2))
