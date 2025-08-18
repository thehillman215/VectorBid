# Rule Packs

VectorBid encodes airline contract & regulatory rules into YAML rule packs.

## Example (UAL 2025.08)
```yaml
version: "2025.08"
airline: UAL
far117:
  min_rest_hours: 10
union:
  max_duty_hours_per_day: 16
  hard:
    - id: FAR117_MIN_REST
      desc: Rest >= 10h