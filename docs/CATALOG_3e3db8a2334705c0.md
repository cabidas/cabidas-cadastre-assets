# Catálogo unificado 3e3db8a2334705c0 — 2026-10-20

## Alcance

La entrega suma 73.811 huellas físicas: Las Condes 34.784, Lo Barnechea
17.691, San Miguel 15.231, Santiago 6.093 y Providencia 12. Santiago y
Providencia tienen cobertura parcial; el inventario de 43 distritos no equivale
a disponer de parcelas en los 43 distritos.

Conserva byte por byte los tres Parquet originales, sus manifiestos revisados
y los tres archivos PMTiles previamente publicados. Incorpora las huellas
aceptadas de Santiago y Providencia con todos sus enlaces fiscales, no sólo un
rol representativo por edificio. Las dos particiones nuevas incluyen
`analysis_eligible=false` y `geometry_verified_for_calculations=false`.
No hay documentos CIP/DOM originales del piloto. Esta entrega habilita consulta
cartográfica y no otorga certificación municipal ni aprobación financiera.

La referencia regional usa los polígonos DPA comunales versionados, con un
nombre nuevo que contiene el hash. Los archivos antiguos con nombres fijos
siguen intactos para respetar el contrato de caché inmutable.

## Artefactos y reproducción

- Contrato de entrega: `asset-manifest-active.json`.
- Metadatos de consulta: `provenance/cadastre_active_manifest.v1.json`.
- Hashes y procedencia de tablas: `provenance/cadastre_active_delivery_receipt.json`.
- Imagen: `ghcr.io/cabidas/cabidas-cadastre-assets@sha256:3fa597ae09e376f31862ee12abce4a1f0a58b6e3f9f882690a6e2e7b5a49c2c7`.
- [Release del paquete](https://github.com/cabidas/cabidas-cadastre-assets/releases/tag/catalog-3e3db8a2334705c0).
- [Construcción verificada](https://github.com/cabidas/cabidas-cadastre-assets/actions/runs/39484239775).

Desde backend, `scripts/prepare_cadastre_release.py` combina las fuentes legadas
con la release normalizada aceptada; valida los hashes de origen, conserva los
roles fiscales, pone en cuarentena el análisis y construye el archivo PMTiles.
El pipeline `publish-catalog.yml` descarga el paquete de release y verifica todos
los hashes antes de publicar una imagen con atestación y digest inmutable.

`python3 scripts/verify_catalog_bundle.py https://assets.cabidas.app` comprueba
Range 206, CORS, caché inmutable, tamaños y SHA-256 completos de los cinco archivos.
La prueba aislada de selección verificó un rol de Santiago y los 162 roles de
una huella de Providencia, todos bloqueados para análisis.

## Operación y rollback

Coolify conserva el servicio de teselas 1 y las aplicaciones API 9 y worker 10.
Los montajes 16 y 17 enlazan el directorio versionado
`/data/cabidas/cadastre/releases/3e3db8a2334705c0/data` con
`/app/data/cadastre` en ambas aplicaciones. El código de backend corresponde a
`6d360f1c24eff3a224199b6a84664abe3fb421cf`, con CI verificada.

Antes del cambio se guardó, exclusivamente en el servidor, un respaldo privado
del servicio de teselas y un dump de Coolify cuya lista de restauración se verificó.
Directorio: `/root/cabidas-rollback-20261020-3e3db8a2`.

Para volver al catálogo anterior, retirar únicamente los montajes 16 y 17 de
las aplicaciones 9 y 10 y volver a desplegarlas: sus imágenes conservan las tres
fuentes originales. Reponer la imagen anterior del servicio 1
`ghcr.io/cabidas/cabidas-cadastre-assets:gran_santiago_2026_s2_s6_release`
y desplegarlo mediante Coolify si también se necesita revertir el servicio de
archivos. No es necesario restaurar toda la base de control para ese rollback.
