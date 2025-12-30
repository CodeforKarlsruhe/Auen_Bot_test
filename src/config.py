from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "rawData"
ANIMALS_PLANTS_PATH = RAW_DATA_DIR / "tiere_pflanzen_auen.json"
ANIMAL_KEYS_PATH = RAW_DATA_DIR / "tiereKeys.json"
PLANT_KEYS_PATH = RAW_DATA_DIR / "pflanzenKeys.json"
TASK_LIST_PATH = RAW_DATA_DIR / "taskList.json"
