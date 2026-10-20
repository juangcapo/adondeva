# IPC (Índice de Precios del Consumo) — INE Uruguay

Source: [INE – Series históricas IPC base Octubre 2022=100](https://www.gub.uy/instituto-nacional-estadistica/datos-y-estadisticas/estadisticas/series-historicas-ipc-base-octubre-2022100). Total País, monthly since July 1937.

| File | Contents |
|---|---|
| `raw/` | Workbooks and methodology note as downloaded from INE |
| `ipc_mensual.csv` | `anio, mes, ipc` |
| `ipc_anual.csv` | `anio, ipc_promedio, ipc_diciembre, inflacion_promedio_pct, inflacion_dic_dic_pct` (complete years only) |
| `build_ipc.py` | Rebuilds both CSVs from `raw/` (standard library only) |

To express a nominal amount from year `Y` in pesos of year `T`, using annual averages (which suit full-year budget flows):

```
monto_T = monto_Y * ipc_promedio[T] / ipc_promedio[Y]
```

`www5.ine.gub.uy` does not send its intermediate certificate, so plain `curl` fails verification. Fetch the issuer from the certificate's AIA URL (Sectigo Public Server Authentication CA DV R36) and pass it with `--cacert`. Do not disable verification.
