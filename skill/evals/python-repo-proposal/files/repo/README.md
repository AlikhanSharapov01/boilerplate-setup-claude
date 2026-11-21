# invoicer
Small FastAPI service that generates and stores invoices for the student club shop.
DB migrations live in `migrations/` (Alembic); `src/invoicer/generated/` is produced by `scripts/gen_schemas.py` from the OpenAPI spec — don't edit by hand.
