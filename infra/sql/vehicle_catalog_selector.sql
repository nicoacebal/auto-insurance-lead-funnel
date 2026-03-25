create or replace function public.vehicle_selector_normalize(input_text text)
returns text
language sql
immutable
as $$
  select nullif(upper(trim(regexp_replace(coalesce(input_text, ''), '\s+', ' ', 'g'))), '');
$$;


create or replace function public.vehicle_selector_model(input_text text)
returns text
language plpgsql
immutable
as $$
declare
  normalized text := public.vehicle_selector_normalize(input_text);
  tokens text[];
begin
  if normalized is null then
    return null;
  end if;

  tokens := regexp_split_to_array(normalized, '\s+');

  if array_length(tokens, 1) is null then
    return null;
  end if;

  if array_length(tokens, 1) >= 2 and (
    (tokens[1] = 'COROLLA' and tokens[2] = 'CROSS') or
    (tokens[1] = 'HILUX' and tokens[2] = 'SW4') or
    (tokens[1] = 'RANGE' and tokens[2] = 'ROVER') or
    (tokens[1] = 'DISCOVERY' and tokens[2] = 'SPORT') or
    (tokens[1] = 'GRAND' and tokens[2] = 'CHEROKEE') or
    (tokens[1] = 'SANTA' and tokens[2] = 'FE') or
    (tokens[1] = 'C4' and tokens[2] in ('CACTUS', 'LOUNGE')) or
    (tokens[1] = 'C3' and tokens[2] in ('AIRCROSS', 'PICASSO'))
  ) then
    return tokens[1] || ' ' || tokens[2];
  end if;

  return tokens[1];
end;
$$;


create or replace function public.vehicle_selector_version(input_text text)
returns text
language plpgsql
immutable
as $$
declare
  normalized text := public.vehicle_selector_normalize(input_text);
  model_name text := public.vehicle_selector_model(input_text);
  remainder text;
  tokens text[];
  token text;
  next_token text;
  idx integer;
  token_count integer;
begin
  if normalized is null or model_name is null then
    return null;
  end if;

  remainder := nullif(btrim(substr(normalized, length(model_name) + 1)), '');
  if remainder is null then
    return null;
  end if;

  tokens := regexp_split_to_array(remainder, '\s+');
  token_count := array_length(tokens, 1);

  if token_count is null then
    return null;
  end if;

  for idx in 1..token_count loop
    token := tokens[idx];
    next_token := case when idx < token_count then tokens[idx + 1] else null end;

    if token is null or token = '' then
      continue;
    end if;

    if token ~ '^\d' then
      continue;
    end if;

    if token ~ '^L/?\d+[A-Z]*$' then
      continue;
    end if;

    if token in (
      'PTAS', 'PTA', 'P', 'RURAL', 'COUPE', 'SEDAN', 'HATCH',
      'CAB', 'DOBLE', 'CHASIS', 'CS', 'SC', 'CD', 'DC', 'D/C',
      'AT', 'AT6', 'AT8', 'AUT', 'AUTO', 'MT', 'MT5', 'MT6', 'A/T', 'M/T',
      'CVT', 'ECVT', 'DSG', 'DGS', 'TIPTRONIC',
      'TDI', 'TSI', 'MSI', 'MPI', 'HEV', 'HV', 'PHEV',
      'DIESEL', 'NAFTA', 'HIBRIDO', 'HYBRID', 'ELECTRICO',
      'BITONO', '2WD', '4WD'
    ) then
      continue;
    end if;

    if token in ('PACK', 'PLUS') then
      continue;
    end if;

    if next_token in ('PACK', 'PLUS') then
      return token || ' ' || next_token;
    end if;

    return token;
  end loop;

  return null;
end;
$$;


create or replace function public.get_vehicle_brands()
returns table (marca text)
language sql
stable
as $$
  select distinct public.vehicle_selector_normalize(marca_descripcion) as marca
  from public.vehicle_catalog
  where public.vehicle_selector_normalize(marca_descripcion) is not null
  order by marca;
$$;


create or replace function public.get_vehicle_models(p_marca text)
returns table (modelo text)
language sql
stable
as $$
  select distinct public.vehicle_selector_model(modelo_descripcion) as modelo
  from public.vehicle_catalog
  where public.vehicle_selector_normalize(marca_descripcion) = public.vehicle_selector_normalize(p_marca)
    and public.vehicle_selector_model(modelo_descripcion) is not null
  order by modelo;
$$;


create or replace function public.get_vehicle_versions(p_marca text, p_modelo text)
returns table (version text)
language sql
stable
as $$
  select distinct public.vehicle_selector_version(modelo_descripcion) as version
  from public.vehicle_catalog
  where public.vehicle_selector_normalize(marca_descripcion) = public.vehicle_selector_normalize(p_marca)
    and public.vehicle_selector_model(modelo_descripcion) = public.vehicle_selector_normalize(p_modelo)
    and public.vehicle_selector_version(modelo_descripcion) is not null
  order by version;
$$;


create or replace function public.get_vehicle_years(p_marca text, p_modelo text, p_version text)
returns table (anio integer)
language sql
stable
as $$
  select distinct fabricado as anio
  from public.vehicle_catalog
  where public.vehicle_selector_normalize(marca_descripcion) = public.vehicle_selector_normalize(p_marca)
    and public.vehicle_selector_model(modelo_descripcion) = public.vehicle_selector_normalize(p_modelo)
    and public.vehicle_selector_version(modelo_descripcion) = public.vehicle_selector_normalize(p_version)
    and fabricado is not null
  order by anio desc;
$$;


create index if not exists idx_vehicle_catalog_selector_brand
  on public.vehicle_catalog (public.vehicle_selector_normalize(marca_descripcion));

create index if not exists idx_vehicle_catalog_selector_brand_model
  on public.vehicle_catalog (
    public.vehicle_selector_normalize(marca_descripcion),
    public.vehicle_selector_model(modelo_descripcion)
  );

create index if not exists idx_vehicle_catalog_selector_brand_model_version
  on public.vehicle_catalog (
    public.vehicle_selector_normalize(marca_descripcion),
    public.vehicle_selector_model(modelo_descripcion),
    public.vehicle_selector_version(modelo_descripcion)
  );

create index if not exists idx_vehicle_catalog_selector_brand_model_version_year
  on public.vehicle_catalog (
    public.vehicle_selector_normalize(marca_descripcion),
    public.vehicle_selector_model(modelo_descripcion),
    public.vehicle_selector_version(modelo_descripcion),
    fabricado
  );
