# Phase 2 Implementation Brief - Rule Pack Integration

## Overview
**Owner**: Cursor  
**Duration**: 2 days  
**Priority**: CRITICAL - Enables real airline rule compliance  
**Branch**: `feature/rule-pack-integration`

## Current State Analysis
- ✅ **Rule Pack YAML files exist**: `rule_packs/UAL/2025.09.yml`
- ✅ **Rules engine models**: Comprehensive Pydantic models in `app/rules_engine/models.py`
- ✅ **Validator scaffold**: `app/rules_engine/validator.py` with basic structure
- ❌ **CRITICAL GAP**: Optimizer uses hardcoded weights, ignoring rule packs
- ❌ **Missing integration**: No connection between YAML files and optimizer

## Problem Statement
**Current optimizer** (`app/services/optimizer.py:87-107`):
```python
DEFAULT_WEIGHTS: dict[str, float] = {"award_rate": 1.0, "layovers": 1.0}
PERSONA_WEIGHTS: dict[str, dict[str, float]] = {
    "family_first": {"layovers": 1.2},
    "money_maker": {"award_rate": 1.2},
    # Hardcoded values...
}
```

**Rule packs contain real airline constraints** but are **completely unused**.

## Implementation Requirements

### 1. Rule Pack Loader Service
**Create**: `app/services/rule_pack_loader.py`
```python
from pathlib import Path
import yaml
from app.rules_engine.models import RulePack

class RulePackLoader:
    """Load and cache rule packs from YAML files."""
    
    def __init__(self, rule_packs_dir: Path = None):
        self.rule_packs_dir = rule_packs_dir or Path(__file__).parent.parent.parent / "rule_packs"
        self._cache: dict[str, RulePack] = {}
    
    def load_rule_pack(self, airline: str, month: str) -> RulePack:
        """Load rule pack for airline and month."""
        cache_key = f"{airline}/{month}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        yaml_path = self.rule_packs_dir / airline / f"{month}.yml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Rule pack not found: {yaml_path}")
            
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
            
        # Convert YAML format to RulePack model
        rule_pack = self._convert_yaml_to_rulepack(data)
        self._cache[cache_key] = rule_pack
        return rule_pack
    
    def _convert_yaml_to_rulepack(self, yaml_data: dict) -> RulePack:
        """Convert YAML rule pack to Pydantic model."""
        # Implementation needed - convert YAML structure to RulePack
        pass
```

### 2. Integrate Rule Packs with Optimizer
**Modify**: `app/services/optimizer.py`

**Replace hardcoded weights with rule pack data:**
```python
def _get_scoring_weights(bundle: FeatureBundle) -> dict[str, float]:
    """Return normalized scoring weights from rule pack."""
    from app.services.rule_pack_loader import RulePackLoader
    
    loader = RulePackLoader()
    airline = bundle.context.airline  
    month = bundle.context.month  # Need to add month to ContextSnapshot
    
    try:
        rule_pack = loader.load_rule_pack(airline, month)
        
        # Extract weights from soft rules
        weights = {}
        for soft_rule in rule_pack.soft_rules:
            weights[soft_rule.name] = soft_rule.weight
            
        # Fallback to defaults if no soft rules
        if not weights:
            weights = DEFAULT_WEIGHTS.copy()
            
        # Apply persona adjustments (optional)
        source_d = _to_dict(_get(bundle.preference_schema, "source", {}))
        persona = source_d.get("persona")
        if persona in PERSONA_WEIGHTS:
            for key, multiplier in PERSONA_WEIGHTS[persona].items():
                if key in weights:
                    weights[key] *= multiplier
        
        # Normalize weights
        total = sum(weights.values()) or 1.0
        return {k: v / total for k, v in weights.items()}
        
    except (FileNotFoundError, Exception) as e:
        # Fallback to hardcoded weights
        logger.warning(f"Failed to load rule pack {airline}/{month}: {e}")
        return _get_legacy_weights(bundle)
```

### 3. Enhance Hard Constraint Validation
**Modify**: `app/services/optimizer.py:42` (`_rule_hits_misses`)
```python
def _rule_hits_misses(bundle: FeatureBundle, pairing: Any) -> tuple[list[str], list[str]]:
    """Determine which hard rules are satisfied using rule pack."""
    from app.services.rule_pack_loader import RulePackLoader
    from app.rules_engine.validator import RulePackValidator
    
    hits: list[str] = []
    misses: list[str] = []
    
    try:
        loader = RulePackLoader()
        rule_pack = loader.load_rule_pack(bundle.context.airline, bundle.context.month)
        
        # Create validation context
        context = {
            "ctx_id": bundle.context.ctx_id,
            "pilot_id": bundle.context.pilot_id,
            "base": bundle.context.base,
            "seniority": bundle.context.seniority_percentile,
        }
        
        validator = RulePackValidator(rule_pack, context)
        violations = validator.validate_schedule(pairing)
        
        # Convert violations to hits/misses
        violated_rules = {v.rule_id for v in violations}
        for rule in rule_pack.hard_rules:
            if rule.id in violated_rules:
                misses.append(rule.id)
            else:
                hits.append(rule.id)
                
    except Exception:
        # Fallback to legacy validation
        return _legacy_rule_hits_misses(bundle, pairing)
    
    return hits, misses
```

### 4. Add Missing Fields to Models
**Modify**: `app/models.py`
```python
class ContextSnapshot(BaseModel):
    # Add missing fields needed for rule pack integration
    month: str  # Add this field for rule pack selection
    # ... existing fields
```

### 5. Rule Pack API Endpoint
**Create**: `app/routes/rule_packs.py`
```python
from fastapi import APIRouter, HTTPException
from app.services.rule_pack_loader import RulePackLoader

router = APIRouter()

@router.get("/api/rule-packs/{airline}/{month}")
async def get_rule_pack(airline: str, month: str):
    """Get rule pack for airline and month."""
    try:
        loader = RulePackLoader()
        rule_pack = loader.load_rule_pack(airline, month)
        return rule_pack.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Rule pack not found for {airline}/{month}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load rule pack: {e}")

@router.get("/api/rule-packs")
async def list_rule_packs():
    """List available rule packs."""
    # Implementation to scan rule_packs/ directory
    pass
```

### 6. YAML Format Conversion
**Key challenge**: Current YAML format doesn't match RulePack model structure.

**Current YAML** (`rule_packs/UAL/2025.09.yml`):
```yaml
rules:
  - id: MIN_DAYS_OFF
    desc: Minimum 8 days off per month
    severity: hard
    evaluate: "context.get('days_off', 0) >= 8"
```

**Needs conversion to**:
```python
HardRule(
    name="MIN_DAYS_OFF",
    description="Minimum 8 days off per month", 
    check="context.get('days_off', 0) >= 8",
    severity="error"
)
```

## Success Criteria
- [ ] Rule packs loaded from YAML files successfully
- [ ] Optimizer uses rule pack weights instead of hardcoded values
- [ ] Hard constraints enforced using rule pack definitions
- [ ] API endpoint returns rule pack data
- [ ] Backward compatibility maintained (fallback to legacy weights)
- [ ] Integration tests pass with real rule data
- [ ] ContextSnapshot includes month field

## Test Requirements

### Unit Tests
**Create**: `tests/services/test_rule_pack_loader.py`
```python
def test_load_ual_rule_pack():
    loader = RulePackLoader()
    pack = loader.load_rule_pack("UAL", "2025.09")
    assert pack.airline == "UAL"
    assert len(pack.hard_rules) > 0

def test_rule_pack_not_found():
    loader = RulePackLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_rule_pack("FAKE", "2025.01")
```

### Integration Tests
**Update**: `fastapi_tests/test_optimizer.py`
```python
def test_optimizer_uses_rule_pack_weights():
    # Test that optimizer loads weights from rule pack
    bundle = create_test_bundle(airline="UAL", month="2025.09")
    candidates = select_topk(bundle, K=10)
    # Verify candidates use rule pack constraints
```

## Dependencies
- `PyYAML` - already in requirements.txt
- No new external dependencies needed

## Implementation Order
1. **Rule Pack Loader** - Core service to load YAML files
2. **YAML Conversion** - Convert current format to RulePack models  
3. **Optimizer Integration** - Replace hardcoded weights
4. **Hard Constraint Integration** - Use rule pack for validation
5. **API Endpoint** - Expose rule pack data
6. **Testing** - Comprehensive test coverage

## Risks & Mitigation
- **YAML format mismatch**: Implement conversion layer
- **Performance**: Cache loaded rule packs
- **Backward compatibility**: Maintain fallback to legacy weights
- **Missing rule packs**: Graceful degradation with clear error messages

## Handoff to Cline
When implementation is complete:
1. Run full test suite: `pytest tests/ fastapi_tests/ -v`
2. Test rule pack loading: `python -c "from app.services.rule_pack_loader import RulePackLoader; print(RulePackLoader().load_rule_pack('UAL', '2025.09'))"`
3. Check API endpoint: `curl localhost:8000/api/rule-packs/UAL/2025.09`
4. Verify optimizer integration with rule pack weights
5. Create PR to `staging` with title: `feat: integrate rule packs with optimizer`

---
**This integration bridges the gap between airline rules and AI optimization!** 🎯