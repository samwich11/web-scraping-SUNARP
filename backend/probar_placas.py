import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from main import run_pipeline


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "placas_prueba.json"
DEFAULT_REPORT = BASE_DIR / "ocr" / "json" / "reporte_pruebas.json"


def load_plates(json_path: Path) -> list[str]:
    if not json_path.exists():
        raise FileNotFoundError(f"No existe el archivo de placas: {json_path}")

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    plates = data.get("placas")
    if not isinstance(plates, list) or not plates:
        raise ValueError("El JSON debe contener una lista no vacía llamada 'placas'.")

    normalized = []
    for plate in plates:
        value = str(plate).upper().strip()
        if value and value not in normalized:
            normalized.append(value)

    return normalized


def save_report(report_path: Path, results: list[dict]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "total": len(results),
        "exitosas": sum(item["estado"] == "exitoso" for item in results),
        "fallidas": sum(item["estado"] == "fallido" for item in results),
        "resultados": results,
    }

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)


def run_batch(
    json_path: Path,
    report_path: Path,
    start_from: str | None = None,
    limit: int | None = None,
    delay: int = 20,
) -> None:
    plates = load_plates(json_path)

    if start_from:
        start_from = start_from.upper().strip()
        if start_from not in plates:
            raise ValueError(f"La placa {start_from} no está en {json_path.name}.")
        plates = plates[plates.index(start_from):]

    if limit is not None:
        plates = plates[:limit]

    results = []
    total = len(plates)

    for index, plate in enumerate(plates, start=1):
        print(f"\n{'#' * 70}")
        print(f"PRUEBA {index}/{total}: {plate}")
        print(f"{'#' * 70}")

        started_at = time.monotonic()
        try:
            run_pipeline(plate)
            result = {
                "placa": plate,
                "estado": "exitoso",
                "error": None,
                "duracion_segundos": round(time.monotonic() - started_at, 2),
            }
        except KeyboardInterrupt:
            print("\nPruebas interrumpidas por el usuario.")
            save_report(report_path, results)
            raise
        except Exception as error:
            print(f"\nFalló la placa {plate}: {error}")
            result = {
                "placa": plate,
                "estado": "fallido",
                "error": str(error),
                "duracion_segundos": round(time.monotonic() - started_at, 2),
            }

        results.append(result)
        save_report(report_path, results)

        if index < total and delay > 0:
            print(f"Esperando {delay} segundos antes de la siguiente placa...")
            time.sleep(delay)

    print("\nPruebas finalizadas.")
    print(f"Reporte: {report_path}")
    print(f"Exitosas: {sum(item['estado'] == 'exitoso' for item in results)}")
    print(f"Fallidas: {sum(item['estado'] == 'fallido' for item in results)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline para las placas guardadas en un JSON."
    )
    parser.add_argument("--archivo", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--reporte", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--desde", help="Reanudar el lote desde esta placa.")
    parser.add_argument("--limite", type=int, help="Procesar solo esta cantidad de placas.")
    parser.add_argument(
        "--espera",
        type=int,
        default=20,
        help="Segundos de espera entre consultas (predeterminado: 20).",
    )
    args = parser.parse_args()

    if args.limite is not None and args.limite <= 0:
        parser.error("--limite debe ser mayor que cero.")
    if args.espera < 0:
        parser.error("--espera no puede ser negativo.")

    run_batch(
        json_path=args.archivo,
        report_path=args.reporte,
        start_from=args.desde,
        limit=args.limite,
        delay=args.espera,
    )


if __name__ == "__main__":
    main()
