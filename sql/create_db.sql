

drop database if exists bot;

create database bot;

begin;
DROP TABLE if exists cajeros_bot;
CREATE TABLE cajeros_bot
(
    id serial NOT NULL,
    lat double precision NOT NULL,
    lng double precision NOT NULL,
    banco text NOT NULL,
    red text NOT NULL,
    dom_orig text,
    dom_geo text,
    terminal integer,
    web text,
    actualizacion text,
    dom_norma text,
    barrio text,
    comuna text,
    codigo_postal text,
    codigo_postal_argentino text,
    PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
);

commit;

begin;
create EXTENSION if not exists postgis;


ALTER TABLE cajeros_bot
    OWNER to postgres;
commit;

begin;
-- copio el csv con la informacion de los cajeros
copy cajeros_bot FROM '/tmp/cajeros.csv' WITH DELIMITER ',' CSV HEADER ;
commit;

begin;
ALTER TABLE cajeros_bot ADD COLUMN geom geometry(POINT,4326);
UPDATE cajeros_bot SET geom = ST_SetSRID(ST_MakePoint(lng,lat),4326);

DROP INDEX if exists idx_cajeros_bot_geom;
-- creo el indice a partir de los geom para que las busquedas sean mas rapidas
CREATE INDEX idx_cajeros_bot_geom ON cajeros_bot USING GIST(geom);


-- Agrego la columna de extracciones seteada en 0
ALTER TABLE cajeros_bot ADD COLUMN extracciones double precision NOT NULL DEFAULT 0;
commit;

-- Por cada grupo con igual geom se lo ordena por id y 
-- elimino a todos menos al del menor id de cada grupo (cada geom distinto)
begin;
DELETE FROM cajeros_bot
WHERE id IN (SELECT id
              FROM (SELECT id,
                             ROW_NUMBER() OVER (partition BY geom ORDER BY id) AS rnum
                     FROM cajeros_bot) c
              WHERE c.rnum > 1);

commit;